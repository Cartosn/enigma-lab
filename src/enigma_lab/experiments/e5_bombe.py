"""E5 · ¿Cuántas paradas falsas deja la Bombe? (spec 7)

**Menús.** Cada menú sale de un crib alemán real (corpus con la X como separador) y su
cifrado con una clave aleatoria de Enigma I (rotores I–V, 10 cables). Las celdas son
las de la tabla de Turing:

- *letras* del menú: sus vértices V, las letras distintas del grafo (8 a 16; D-031);
- *lazos*: el número ciclomático E − V + 1, de 0 a 3.

Un menú conexo con V letras y k lazos tiene E = V − 1 + k aristas: sale de un crib de
E letras. Solo se aceptan menús conexos (una sola componente), como en la tabla. Las
celdas se llenan por muestreo con rechazo: se generan cribs de E letras por lotes hasta
tener ``n`` menús con V letras, o agotar ``max_candidates``; si una celda no se llena,
se documenta.

**Medidas.** Para cada menú se barre un orden de rotores, el verdadero, en modo
Bletchley con y sin diagonal board; en un subconjunto, también en modo robusto.

- *Paradas falsas por orden:* todas las paradas menos la verdadera.
- *Hipótesis falsas:* las hipótesis T↔x que la Bombe deja abiertas (hilos aislados del
  cable de prueba). Con muchas paradas, una posición puede dejar varias abiertas.
- *Éxito:* que aparezca la parada verdadera. El modo Bletchley falla cuando el rotor
  central avanza dentro del tramo del crib; el clave al azar lo hace en cerca de
  (L − 1)/26 de los casos.
- *Tiempo* por orden.

**Referencia.** La tabla de Turing (``data/reference/turing_stops.csv``): con 12 letras,
820, 31, 1,2 y 0,04 paradas por orden con 0, 1, 2 y 3 lazos.
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np
import pandas as pd
from numba import njit

from enigma_lab import SEED, paths
from enigma_lab.bombe.scrambler import Order, position_letters
from enigma_lab.bombe.sweep import BombeSettings, sweep_order, true_stecker, true_stop, warm_up
from enigma_lab.bombe.wiring import wiring_from_menu
from enigma_lab.core.batch import ROTOR_NAMES, KeyBatch, encrypt_batch, to_texts
from enigma_lab.core.machine import EnigmaConfig
from enigma_lab.core.wiring import ALPHABET
from enigma_lab.experiments.common import Mode, RunInfo, save_figure, save_table, update_summary
from enigma_lab.stats.corpus import Source, random_excerpts
from enigma_lab.stats.inference import mean_ci, wilson_interval

PARAMS: dict[str, dict[str, Any]] = {
    "rapido": {
        "letters": [8, 12, 16],
        "loops": [0, 1, 2, 3],
        "n": 10,
        "robust_letters": [12],
        "robust_n": 5,
        "batch": 250_000,
        "max_candidates": 3_000_000,
        "source": "muestra",
    },
    "completo": {
        "letters": [8, 10, 12, 14, 16],
        "loops": [0, 1, 2, 3],
        "n": 100,
        "robust_letters": [12, 16],
        "robust_n": 100,
        "batch": 1_000_000,
        "max_candidates": 30_000_000,
        "source": "completo",
    },
}
TURING_FILE = paths.REFERENCE / "turing_stops.csv"
ORDERS_PER_DAY = 60


def turing_table() -> pd.DataFrame:
    """La tabla de Turing transcrita de Wikipedia: letras, lazos, paradas y cota («<»)."""
    table = pd.read_csv(TURING_FILE, comment="#", dtype={"cota": str})
    table["cota"] = table["cota"].fillna("")
    return table


def turing_value(letters: int, loops: int) -> tuple[float, str]:
    """(paradas por orden según Turing, «<» si es una cota superior)."""
    table = turing_table()
    row = table[(table["letras"] == letters) & (table["lazos"] == loops)]
    if row.empty:
        return float("nan"), ""
    return float(row["paradas"].iloc[0]), str(row["cota"].iloc[0])


# ---------------------------------------------------------------- generación de menús


@njit(cache=True)
def menu_shapes(crib: np.ndarray, cipher: np.ndarray) -> np.ndarray:  # pragma: no cover - Numba
    """(vértices, componentes, E − V + C) del menú de cada fila (crib y cifrado 0–25)."""
    n, length = crib.shape
    out = np.empty((n, 3), np.int64)
    parent = np.empty(26, np.int64)
    present = np.empty(26, np.bool_)
    for s in range(n):
        for v in range(26):
            parent[v] = v
            present[v] = False
        for i in range(length):
            a, b = crib[s, i], cipher[s, i]
            present[a] = True
            present[b] = True
            while parent[a] != a:
                a = parent[a]
            while parent[b] != b:
                b = parent[b]
            if a != b:
                parent[max(a, b)] = min(a, b)
        vertices, components = 0, 0
        for v in range(26):
            if present[v]:
                vertices += 1
                if parent[v] == v:
                    components += 1
        out[s, 0], out[s, 1], out[s, 2] = vertices, components, length - vertices + components
    return out


def random_keys(rng: np.random.Generator, n: int) -> KeyBatch:
    """N claves de Enigma I al azar, vectorizadas: rotores I–V distintos, reflector B, 10 cables."""
    rotors = np.argsort(rng.random((n, 5)), axis=1)[:, :3].astype(np.intp)
    letters = np.argsort(rng.random((n, 26)), axis=1)[:, :20].astype(np.uint8)
    plug = np.tile(np.arange(26, dtype=np.uint8), (n, 1))
    rows = np.arange(n)[:, None]
    plug[rows, letters[:, 0::2]] = letters[:, 1::2]
    plug[rows, letters[:, 1::2]] = letters[:, 0::2]
    return KeyBatch(
        rotors=rotors,
        reflector=np.full(n, 1, dtype=np.intp),  # B
        rings=rng.integers(0, 26, (n, 3)).astype(np.int16),
        positions=rng.integers(0, 26, (n, 3)).astype(np.int16),
        plugboard=plug,
    )


def key_config(keys: KeyBatch, row: int) -> EnigmaConfig:
    """La clave de una fila del lote como ``EnigmaConfig``."""
    plug = keys.plugboard[row]
    pairs = tuple((ALPHABET[a], ALPHABET[int(b)]) for a, b in enumerate(plug) if int(b) > a)
    return EnigmaConfig(
        rotors=tuple(ROTOR_NAMES[int(r)] for r in keys.rotors[row]),
        reflector="B",
        rings=tuple(int(v) for v in keys.rings[row]),
        positions=tuple(int(v) for v in keys.positions[row]),
        plugboard=pairs,
    )


def generate_cell(
    rng: np.random.Generator,
    vertices: int,
    loops: int,
    n: int,
    batch: int,
    max_candidates: int,
    source: Source,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Muestreo con rechazo: hasta ``n`` menús conexos con V letras y k lazos.

    Prueba cribs de E = V − 1 + k letras. Devuelve los menús aceptados (clave, crib y
    cifrado) y cuántos se encontraron entre cuántos candidatos.
    """
    length = vertices - 1 + loops
    accepted: list[dict[str, Any]] = []
    tried = 0
    while tried < max_candidates and len(accepted) < n:
        size = min(batch, max_candidates - tried)
        crib = random_excerpts(rng, "aleman", size, length, source, mode="x")
        keys = random_keys(rng, size)
        cipher = encrypt_batch(keys, crib)
        shape = menu_shapes(crib.astype(np.int64), cipher.astype(np.int64))
        rows = np.flatnonzero((shape[:, 1] == 1) & (shape[:, 0] == vertices))
        for row in rows[: n - len(accepted)]:
            accepted.append(
                {
                    "config": key_config(keys, int(row)),
                    "crib": to_texts(crib[row : row + 1])[0],
                    "cipher": to_texts(cipher[row : row + 1])[0],
                    "vertices": vertices,
                    "lazos": loops,
                }
            )
        tried += size
    return accepted, {"encontrados": len(accepted), "candidatos": tried}


# ---------------------------------------------------------------- medición


def measure(menu: dict[str, Any], diagonal: bool, mode: str) -> dict[str, Any]:
    """Barre el orden verdadero de un menú y cuenta paradas, hipótesis y la parada verdadera."""
    config: EnigmaConfig = menu["config"]
    order: Order = (config.rotors[0], config.rotors[1], config.rotors[2])
    crib, cipher = menu["crib"], menu["cipher"]
    wiring = wiring_from_menu(crib, cipher, diagonal=diagonal)
    settings = BombeSettings(orders=(order,), mode="robusto" if mode == "robusto" else "bletchley")
    turns = settings.turns(len(crib))
    start = time.perf_counter()
    lit, singles = sweep_order(wiring, order, "B", turns)
    seconds = time.perf_counter() - start
    stopped = lit < 26
    expected = true_stop(config, 0, len(crib))
    found = False
    if expected is not None and expected[1] in turns:
        v = int(np.flatnonzero(turns == expected[1])[0])
        partner = ALPHABET.index(true_stecker(config, wiring.test_letter))
        found = bool(stopped[expected[0], v] and singles[expected[0], v] >> partner & 1)
    stops = int(stopped.sum())
    hypotheses = int(np.bitwise_count(singles[stopped]).sum())
    return {
        "letras": menu["vertices"],
        "lazos": menu["lazos"],
        "aristas": len(crib),
        "diagonal": diagonal,
        "modo": mode,
        "orden": "-".join(config.rotors),
        "letra_prueba": wiring.test_letter,
        "variantes": len(turns),
        "paradas": stops,
        "paradas_falsas": stops - found,
        "hipotesis_falsas": hypotheses - found,
        "verdadera": found,
        "vuelta": expected is None or expected[1] > 0,
        "posicion_verdadera": position_letters(expected[0]) if expected else "",
        "segundos": seconds,
    }


def run(params: dict[str, Any], seed: int = SEED) -> pd.DataFrame:
    """Una fila por menú, diagonal board (sí o no) y modo."""
    rngs = np.random.default_rng(seed).spawn(len(params["letters"]))
    rows, coverage = [], []
    # Antes de medir tiempos: compilar (o cargar de la caché) y precalcular los 60 órdenes.
    warm_up(all_tables=True)
    for rng, letters in zip(rngs, params["letters"], strict=True):
        for loops in params["loops"]:
            menus, info = generate_cell(
                rng,
                letters,
                loops,
                params["n"],
                params["batch"],
                params["max_candidates"],
                params["source"],
            )
            coverage.append({"letras": letters, "lazos": loops, **info})
            for menu in menus:
                for diagonal in (True, False):
                    rows.append(measure(menu, diagonal, "bletchley"))
            if letters in params["robust_letters"]:
                rows.extend(measure(m, True, "robusto") for m in menus[: params["robust_n"]])
    df = pd.DataFrame(rows)
    df.attrs["cobertura"] = coverage
    return df


def aggregate(df: pd.DataFrame) -> pd.DataFrame:
    """Tabla de la diapositiva 16 (``r3_bombe.csv``): una fila por celda, diagonal y modo."""
    out = []
    for (letters, loops, diagonal, mode), g in df.groupby(
        ["letras", "lazos", "diagonal", "modo"], sort=True
    ):
        mean, low, high = mean_ci(g["paradas_falsas"].to_numpy())
        hyp, hyp_low, hyp_high = mean_ci(g["hipotesis_falsas"].to_numpy())
        wins = int(g["verdadera"].sum())
        win_low, win_high = wilson_interval(wins, len(g))
        no_turn = g[~g["vuelta"]]
        turing, bound = turing_value(int(letters), int(loops))
        out.append(
            {
                "letras": int(letters),
                "lazos": int(loops),
                "diagonal": "si" if diagonal else "no",
                "modo": mode,
                "n_menus": len(g),
                "paradas_media": mean,
                "ic_bajo": max(0.0, low),
                "ic_alto": high,
                "exito": wins / len(g),
                "s_por_orden": float(g["segundos"].mean()),
                "exito_ic_bajo": win_low,
                "exito_ic_alto": win_high,
                "exito_sin_vuelta": float(no_turn["verdadera"].mean()) if len(no_turn) else np.nan,
                "vuelta_frac": float(g["vuelta"].mean()),
                "hipotesis_media": hyp,
                "hipotesis_ic_bajo": max(0.0, hyp_low),
                "hipotesis_ic_alto": hyp_high,
                "turing": turing,
                "turing_cota": bound,
                "aristas": int(g["aristas"].iloc[0]),
            }
        )
    return pd.DataFrame(out)


def _cell(
    table: pd.DataFrame, letters: int, loops: int, diagonal: str = "si", mode: str = "bletchley"
) -> pd.Series | None:
    match = table[
        (table["letras"] == letters)
        & (table["lazos"] == loops)
        & (table["diagonal"] == diagonal)
        & (table["modo"] == mode)
    ]
    return None if match.empty else match.iloc[0]


def summary(df: pd.DataFrame, params: dict[str, Any]) -> dict[str, Any]:
    """Cifras clave de E5."""
    table = aggregate(df)
    letters12 = {}
    for loops in params["loops"]:
        on, off = _cell(table, 12, loops), _cell(table, 12, loops, "no")
        robust = _cell(table, 12, loops, mode="robusto")
        if on is None:
            continue
        turing, bound = turing_value(12, loops)
        letters12[str(loops)] = {
            "paradas": on["paradas_media"],
            "ic": [on["ic_bajo"], on["ic_alto"]],
            "hipotesis": on["hipotesis_media"],
            "en_60_ordenes": on["paradas_media"] * ORDERS_PER_DAY,
            "turing": turing,
            "turing_cota": bound,
            "turing_en_60": turing * ORDERS_PER_DAY,
            "sin_diagonal": None if off is None else off["paradas_media"],
            "robusto": None if robust is None else robust["paradas_media"],
            "n": int(on["n_menus"]),
        }
    bletchley = df[(df["modo"] == "bletchley") & df["diagonal"]]
    robust = df[df["modo"] == "robusto"]
    same = bletchley[bletchley["letras"].isin(params["robust_letters"])]
    return {
        "n_por_celda": params["n"],
        "letras": params["letters"],
        "lazos": params["loops"],
        "letras_robusto": params["robust_letters"],
        "fuente": params["source"],
        "cobertura": df.attrs.get("cobertura", []),
        "doce_letras": letters12,
        "exito_bletchley": float(bletchley["verdadera"].mean()),
        "exito_bletchley_sin_vuelta": float(
            bletchley.loc[~bletchley["vuelta"], "verdadera"].mean()
        ),
        "vuelta_frac": float(bletchley["vuelta"].mean()),
        "exito_robusto": float(robust["verdadera"].mean()) if len(robust) else None,
        "robusto_tiempo_relativo": float(robust["segundos"].mean() / same["segundos"].mean())
        if len(robust)
        else None,
        "robusto_paradas_relativas": float(
            (robust["paradas_falsas"].mean() + 1) / (same["paradas_falsas"].mean() + 1)
        )
        if len(robust)
        else None,
        "s_por_orden_bletchley": float(bletchley["segundos"].mean()),
        "s_por_orden_robusto": float(robust["segundos"].mean()) if len(robust) else None,
        "menus": int(df[(df["modo"] == "bletchley") & df["diagonal"]].shape[0]),
    }


def figure(df: pd.DataFrame, theme: str = "enigma_print") -> Any:
    """Mapa de calor letras × lazos de las paradas falsas por orden, con y sin diagonal board."""
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap, LogNorm

    from enigma_lab.viz.numfmt import fmt_dec, fmt_int
    from enigma_lab.viz.static_figs import tokens
    from enigma_lab.viz.theme import SEQUENTIAL_DARK, SEQUENTIAL_PRINT, mpl_style_context

    t = tokens(theme)
    table = aggregate(df)
    table = table[table["modo"] == "bletchley"]
    letters = sorted(table["letras"].unique())
    loops = sorted(table["lazos"].unique(), reverse=True)
    ramp = SEQUENTIAL_PRINT if theme == "enigma_print" else SEQUENTIAL_DARK
    cmap = ListedColormap(list(ramp))

    def short(value: float) -> str:
        if value >= 100:
            return fmt_int(round(value))
        if value >= 1:
            return fmt_dec(value, 1)
        return fmt_dec(value, 2)

    with mpl_style_context(theme):
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.8), sharey=True)
        norm = LogNorm(vmin=0.01, vmax=20_000)
        for ax, diagonal in zip(axes, ("si", "no"), strict=True):
            part = table[table["diagonal"] == diagonal]
            grid = np.full((len(loops), len(letters)), np.nan)
            for r in part.itertuples():
                grid[loops.index(r.lazos), letters.index(r.letras)] = max(r.paradas_media, 0.01)
            image = ax.imshow(grid, cmap=cmap, norm=norm, aspect="auto")
            for r in part.itertuples():
                y, x = loops.index(r.lazos), letters.index(r.letras)
                label = short(r.paradas_media)
                if diagonal == "si" and not np.isnan(r.turing):
                    label += f"\n({r.turing_cota}{short(r.turing)})"
                light = grid[y, x] > 30
                ax.text(
                    x,
                    y,
                    label,
                    ha="center",
                    va="center",
                    fontsize="small",
                    color=t.background if light else t.text,
                )
            ax.set_xticks(range(len(letters)), [str(v) for v in letters])
            ax.set_yticks(range(len(loops)), [str(v) for v in loops])
            ax.set_xlabel("letras (vértices) del menú")
            ax.set_title(
                "con diagonal board (entre paréntesis, Turing)"
                if diagonal == "si"
                else "sin diagonal board"
            )
        axes[0].set_ylabel("lazos del menú")
        fig.colorbar(image, ax=axes, label="paradas falsas por orden de rotores", shrink=0.9)
        cell = _cell(aggregate(df), 12, 3)
        title = "Cada lazo divide las paradas falsas de la Bombe"
        if cell is not None:
            title = (
                f"Con 12 letras y 3 lazos, {short(cell['paradas_media'])} paradas falsas por orden "
                f"(Turing: {short(cell['turing'])})"
            )
        fig.suptitle(title)
    return fig


def main(mode: Mode = "completo", seed: int = SEED) -> dict[str, Any]:
    """Corre E5 y guarda sus resultados."""
    started = time.perf_counter()
    params = PARAMS[mode]
    df = run(params, seed)
    figures = summary(df, params) | {"segundos": round(time.perf_counter() - started, 1)}
    save_table(df, "e5_bombe_menus")
    save_table(aggregate(df), "e5_bombe")
    update_summary("e5", figures, RunInfo("e5", mode, seed))

    import matplotlib.pyplot as plt

    fig = figure(df)
    save_figure(fig, "e5_bombe")
    plt.close(fig)
    return figures
