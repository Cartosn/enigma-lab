"""E7 · ¿Qué tan única es una característica de Rejewski? (spec 7 y 5.7)

**El catálogo** (exacto, sin azar; ``rejewski/catalog.py``). La característica (la estructura
de ciclos de AD, BE y CF) de las 6 × 17.576 = 105.456 configuraciones de los rotores I–III con
el reflector A, con el supuesto del ciclómetro: durante el indicador solo gira el rotor
derecho. Las configuraciones con la misma característica forman una clase; se mide la
distribución de los tamaños de clase y se compara con Kuhl (2007), cifra por cifra
(``data/reference/kuhl_2007.json``).

**El tráfico** (Monte Carlo con semilla; ``rejewski/traffic.py``). Días de 1932 con clave al
azar (rotores I–III, reflector A, 6 cables) y mensajes con claves de mensaje al azar, cifradas
dos veces con la máquina real. Para cada día se cuentan los mensajes hasta reconstruir AD, BE
y CF en cuatro niveles (todas las letras, por eliminación, la permutación y la característica
con el teorema de los ciclos en parejas) y se busca la característica del día en el catálogo.

**Referencias.** Kuhl: 21.230 características, 11.466 únicas y 1.771 en la clase más grande.
El coleccionista de cupones: 26·H₂₆ = 100,2 mensajes para ver las 26 letras en una
permutación. Rejewski (citado por Kuhl): unos 60 u 80 mensajes del mismo día.
"""

from __future__ import annotations

import json
import time
from typing import Any

import numpy as np
import pandas as pd

from enigma_lab import SEED, paths
from enigma_lab.experiments.common import Mode, RunInfo, save_figure, save_table, update_summary
from enigma_lab.rejewski.catalog import CATALOG_REFLECTOR, CATALOG_ROTORS, Catalog, build_catalog
from enigma_lab.rejewski.characteristic import (
    N_TYPES,
    PRODUCTS,
    characteristic,
    characteristic_code,
    format_characteristic,
    middle_moves,
)
from enigma_lab.rejewski.traffic import (
    DAY_CABLES,
    LEVELS,
    core_position,
    coupon_expectation,
    harmonic,
    reconstruction_times,
    simulate_day,
)
from enigma_lab.stats.inference import mean_ci, wilson_interval

PARAMS: dict[str, dict[str, Any]] = {
    "rapido": {"days": 400, "messages": 600},
    "completo": {"days": 4_000, "messages": 600},
}
KUHL_FILE = paths.REFERENCE / "kuhl_2007.json"


def kuhl() -> dict[str, Any]:
    """Las cifras de Kuhl (2007), transcritas con su cita."""
    data: dict[str, Any] = json.loads(KUHL_FILE.read_text(encoding="utf-8"))
    return data


# ---------------------------------------------------------------- el catálogo (exacto)


def run(params: dict[str, Any] | None = None, seed: int = SEED) -> pd.DataFrame:
    """La distribución de los tamaños de clase del catálogo, con la columna de Kuhl.

    Una fila por tamaño: cuántas características tienen clases de ese tamaño y cuántas
    configuraciones suman. ``kuhl`` es su tabla 2 (tamaños 1 a 14 y 16; vacío en los demás).
    """
    table = build_catalog().distribution()
    reference = {row["tamano"]: row["caracteristicas"] for row in kuhl()["tabla_2"]}
    table["kuhl"] = table["tamano"].map(reference).astype("Int64")
    return table


def top_table(catalog: Catalog, n: int = 15) -> pd.DataFrame:
    """Las clases más grandes, con el tamaño que da Kuhl a la misma característica (tabla 1)."""
    top = catalog.top(n)
    reference = {r["caracteristica"]: r["configuraciones"] for r in kuhl()["tabla_1"]}
    top["kuhl"] = top["caracteristica"].map(reference).astype("Int64")
    return top.drop(columns="codigo")


def kuhl_top_table(catalog: Catalog) -> pd.DataFrame:
    """La tabla 1 de Kuhl, con nuestro tamaño para cada característica."""
    from enigma_lab.rejewski.characteristic import parse_characteristic

    rows = []
    for rank, r in enumerate(kuhl()["tabla_1"], start=1):
        code = characteristic_code(parse_characteristic(r["caracteristica"]))
        rows.append(
            {
                "puesto_kuhl": rank,
                "caracteristica": r["caracteristica"],
                "kuhl": r["configuraciones"],
                "e7": catalog.size(code),
            }
        )
    return pd.DataFrame(rows)


def catalog_summary(catalog: Catalog) -> dict[str, Any]:
    """Las cifras del catálogo y su comparación con Kuhl."""
    sizes = catalog.class_sizes()
    largest = catalog.top(1).iloc[0]
    reference = kuhl()
    ours = {
        "caracteristicas_distintas": len(sizes),
        "caracteristicas_unicas": int((sizes == 1).sum()),
        "mayor_clase": int(largest["configuraciones"]),
    }
    their = {
        "caracteristicas_distintas": reference["caracteristicas_distintas"],
        "caracteristicas_unicas": reference["caracteristicas_unicas"],
        "mayor_clase": reference["mayor_clase"]["configuraciones"],
    }
    compare = {
        key: {
            "e7": ours[key],
            "kuhl": their[key],
            "diferencia": ours[key] - their[key],
            "relativa": (ours[key] - their[key]) / their[key],
        }
        for key in ours
    }
    table2 = {row["tamano"]: row["caracteristicas"] for row in reference["tabla_2"]}
    counts = dict(zip(*np.unique(sizes, return_counts=True), strict=True))
    their_top = kuhl_top_table(catalog)
    our_top = set(top_table(catalog)["caracteristica"])
    return {
        "rotores": list(CATALOG_ROTORS),
        "reflector": CATALOG_REFLECTOR,
        "ordenes": len(catalog.orders),
        "configuraciones": catalog.n_configurations,
        **ours,
        "fraccion_unicas": ours["caracteristicas_unicas"] / len(sizes),
        "mayor_caracteristica": str(largest["caracteristica"]),
        "hasta_10": int((sizes <= 10).sum()),
        "fraccion_hasta_10": float((sizes <= 10).mean()),
        "configuraciones_en_hasta_10": int(sizes[sizes <= 10].sum()),
        "candidatos_esperados": catalog.expected_candidates(),
        "mediana_candidatos": _weighted_median(sizes),
        "estructuras_por_producto": N_TYPES,
        "estructuras_terna": N_TYPES**3,
        "kuhl": compare,
        "tabla_2": {
            str(size): {"e7": int(counts.get(size, 0)), "kuhl": int(value)}
            for size, value in table2.items()
        },
        "tabla_1": {
            "comunes": len(our_top & set(their_top["caracteristica"])),
            "de": len(their_top),
            "diferencia_relativa_maxima": float(
                ((their_top["e7"] - their_top["kuhl"]).abs() / their_top["kuhl"]).max()
            ),
        },
        "kuhl_hasta_10_tabla": int(sum(v for k, v in table2.items() if k <= 10)),
    }


def _weighted_median(sizes: np.ndarray) -> int:
    """Tamaño de clase mediano de una configuración al azar (cada clase pesa su tamaño)."""
    ordered = np.sort(sizes)
    cumulative = np.cumsum(ordered)
    return int(ordered[np.searchsorted(cumulative, cumulative[-1] / 2)])


def turnover_fraction() -> dict[str, Any]:
    """Posiciones del día en que el central se mueve durante el indicador (exacto).

    Se recorren las 26 × 26 ventanas del central y del derecho con la máquina real
    (``characteristic.middle_moves``), con los anillos en A: lo que importa son las letras de
    las ventanas frente a las muescas, así que da lo mismo para cualquier anillo.
    """
    from enigma_lab.core.machine import EnigmaConfig

    counts = {}
    for order in build_catalog().orders:
        moved = sum(
            middle_moves(EnigmaConfig(rotors=order, reflector="A", positions=(0, m, r)))
            for m in range(26)
            for r in range(26)
        )
        counts["-".join(order)] = moved
    values = set(counts.values())
    if len(values) != 1:
        raise ValueError(f"la fracción depende del orden: {counts}")
    moved = values.pop()
    return {"posiciones": moved, "de": 676, "fraccion": moved / 676}


# ---------------------------------------------------------------- el tráfico (Monte Carlo)


def run_traffic(params: dict[str, Any], seed: int = SEED) -> pd.DataFrame:
    """Una fila por día: mensajes hasta cada nivel (por producto y del día) y el catálogo."""
    catalog = build_catalog()
    rng = np.random.default_rng(seed)
    rows = []
    for day_index in range(params["days"]):
        day = simulate_day(rng, params["messages"])
        times = reconstruction_times(day.indicators)
        if any(t < 0 for level in LEVELS for t in times[level]):
            raise RuntimeError("faltaron mensajes: sube params['messages']")
        config = day.config
        code = characteristic_code(characteristic(day.perms))
        core = core_position(config)
        row: dict[str, Any] = {
            "dia": day_index,
            "orden": "-".join(config.rotors),
            "anillos": config.ring_letters,
            "posicion_dia": config.position_letters,
            "nucleo": core,
            "vuelta": middle_moves(config),
            "caracteristica": format_characteristic(characteristic(day.perms)),
            "encontrada": catalog.code_at(config.rotors, core) == code,
            "candidatos": catalog.size(code),
        }
        for level in LEVELS:
            for name, value in zip(PRODUCTS, times[level], strict=True):
                row[f"{level}_{name.lower()}"] = value
            row[level] = max(times[level])
        rows.append(row)
    return pd.DataFrame(rows)


def theory() -> dict[str, dict[str, float]]:
    """El coleccionista de cupones exacto: una permutación y las tres (el máximo de tres)."""
    return {
        "todas": {"producto": coupon_expectation(26, 1), "dia": coupon_expectation(26, 3)},
        "eliminacion": {"producto": coupon_expectation(25, 1), "dia": coupon_expectation(25, 3)},
    }


def traffic_summary(days: pd.DataFrame, params: dict[str, Any]) -> dict[str, Any]:
    """Mensajes por nivel (media e IC 95 %), teoría y éxito del catálogo."""
    expected = theory()
    levels = {}
    for level in LEVELS:
        entry: dict[str, Any] = {
            "dia": list(mean_ci(days[level].to_numpy(float))),
            "ad": list(mean_ci(days[f"{level}_ad"].to_numpy(float))),
            "mediana_dia": float(days[level].median()),
            "p90_dia": float(days[level].quantile(0.9)),
        }
        if level in expected:
            entry["teoria_dia"] = expected[level]["dia"]
            entry["teoria_producto"] = expected[level]["producto"]
        levels[level] = entry
    found = int(days["encontrada"].sum())
    still = days[~days["vuelta"]]
    moved = days[days["vuelta"]]
    reference = kuhl()["rejewski_mensajes"]
    return {
        "dias": len(days),
        "mensajes_por_dia": params["messages"],
        "cables": DAY_CABLES,
        "por_nivel": levels,
        "coleccionista_26H26": 26 * harmonic(26),
        "rejewski": {"apendice_D": reference["apendice_D"], "apendice_E": reference["apendice_E"]},
        "catalogo": {
            "encontrada": found / len(days),
            "ic": list(wilson_interval(found, len(days))),
            "dias_con_vuelta": len(moved) / len(days),
            "encontrada_sin_vuelta": float(still["encontrada"].mean()) if len(still) else None,
            "encontrada_con_vuelta": float(moved["encontrada"].mean()) if len(moved) else None,
            "candidatos_media": float(still["candidatos"].mean()) if len(still) else None,
            "candidatos_mediana": float(still["candidatos"].median()) if len(still) else None,
            "sin_candidatos_con_vuelta": float((moved["candidatos"] == 0).mean())
            if len(moved)
            else None,
        },
    }


def summary(df: pd.DataFrame, days: pd.DataFrame, params: dict[str, Any]) -> dict[str, Any]:
    """Cifras clave de E7: el catálogo frente a Kuhl, el movimiento del central y el tráfico."""
    catalog = build_catalog()
    return {
        "catalogo": catalog_summary(catalog),
        "vuelta": turnover_fraction(),
        "trafico": traffic_summary(days, params),
    }


# ---------------------------------------------------------------- figura


def _sizes_panel(ax: Any, df: pd.DataFrame, theme: str) -> None:
    """Cuántas características hay de cada tamaño de clase, en escala log-log, frente a Kuhl."""
    from enigma_lab.viz.numfmt import fmt_int
    from enigma_lab.viz.static_figs import es_number, tokens
    from enigma_lab.viz.theme import CATEGORICAL

    t = tokens(theme)
    ax.plot(
        df["tamano"],
        df["caracteristicas"],
        "o",
        markersize=3,
        color=CATEGORICAL[0],
        label="este catálogo (E7)",
    )
    ref = df.dropna(subset=["kuhl"])
    ax.plot(
        ref["tamano"],
        ref["kuhl"].astype(float),
        "D",
        markersize=5,
        markerfacecolor="none",
        markeredgewidth=1.2,
        color=CATEGORICAL[2],
        label="Kuhl (2007), tabla 2",
    )
    data = kuhl()
    largest = data["mayor_clase"]["configuraciones"]
    ax.plot([largest], [1], "D", markersize=5, markerfacecolor="none", color=CATEGORICAL[2])
    ax.annotate(
        f"Kuhl: {data['mayor_clase']['caracteristica']}\n{fmt_int(largest)} configuraciones "
        f"(E7: {fmt_int(int(df['tamano'].max()))})",
        xy=(largest, 1),
        xytext=(-6, 18),
        textcoords="offset points",
        ha="right",
        fontsize="x-small",
        color=t.text_muted,
    )
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("tamaño de la clase (configuraciones con la misma característica)")
    ax.set_ylabel("características con ese tamaño")
    ax.xaxis.set_major_formatter(es_number())
    ax.yaxis.set_major_formatter(es_number())
    ax.legend(fontsize="small", loc="upper right")
    ax.set_title("Tamaños de clase del catálogo")


def _messages_panel(ax: Any, days: pd.DataFrame, theme: str) -> None:
    """Mensajes del día hasta reconstruir AD, BE y CF, por nivel, con la teoría y Rejewski."""
    from enigma_lab.rejewski.traffic import coupon_pmf
    from enigma_lab.viz.numfmt import fmt_dec
    from enigma_lab.viz.static_figs import es_number, tokens
    from enigma_lab.viz.theme import CATEGORICAL

    t = tokens(theme)
    bins = np.arange(0, 301, 5)
    labels = {
        "caracteristica": "la característica (teorema)",
        "permutacion": "las permutaciones (teorema)",
        "todas": "las 26 letras vistas",
    }
    for color, level in zip(CATEGORICAL, labels, strict=False):
        ax.hist(
            days[level],
            bins=bins,
            density=True,
            histtype="step",
            linewidth=1.5,
            color=color,
            label=f"{labels[level]}: {fmt_dec(days[level].mean(), 1)}",
        )
    pmf = coupon_pmf(26, 3)
    n = np.arange(len(pmf))
    keep = n <= 300
    ax.plot(
        n[keep],
        pmf[keep],
        color=t.text_muted,
        linestyle="--",
        linewidth=1,
        label=f"teoría de las 26 letras: {fmt_dec(coupon_expectation(26, 3), 1)}",
    )
    reference = kuhl()["rejewski_mensajes"]
    for value in (reference["apendice_D"], reference["apendice_E"]):
        ax.axvline(value, color=t.text_muted, linestyle=":", linewidth=1)
    ax.annotate(
        "Rejewski: 60 y 80",
        xy=(reference["apendice_E"], 1),
        xycoords=("data", "axes fraction"),
        xytext=(4, -12),
        textcoords="offset points",
        fontsize="x-small",
        color=t.text_muted,
    )
    ax.set_xlabel("mensajes del día")
    ax.set_ylabel("fracción de días por mensaje")
    ax.set_xlim(0, 300)
    ax.xaxis.set_major_formatter(es_number())
    ax.yaxis.set_major_formatter(es_number(3))
    ax.legend(fontsize="x-small", loc="upper right")
    ax.set_title("Mensajes hasta reconstruir AD, BE y CF")


def figure(df: pd.DataFrame, theme: str = "enigma_print", days: pd.DataFrame | None = None) -> Any:
    """Tamaños de clase frente a Kuhl y, si hay tráfico, los mensajes que pide cada nivel."""
    import matplotlib.pyplot as plt

    from enigma_lab.viz.numfmt import fmt_int
    from enigma_lab.viz.theme import mpl_style_context

    catalog = catalog_summary(build_catalog())
    with mpl_style_context(theme):
        if days is None:
            fig, ax = plt.subplots()
            _sizes_panel(ax, df, theme)
        else:
            # En las diapositivas manda el 16:9 del estilo; en el informe, una figura ancha.
            size = None if theme == "enigma_slides" else (13, 5)
            fig, (left, right) = plt.subplots(1, 2, figsize=size)
            _sizes_panel(left, df, theme)
            _messages_panel(right, days, theme)
        fig.suptitle(
            f"{fmt_int(catalog['caracteristicas_unicas'])} de las "
            f"{fmt_int(catalog['caracteristicas_distintas'])} características señalan una sola "
            f"configuración (Kuhl: {fmt_int(catalog['kuhl']['caracteristicas_unicas']['kuhl'])} "
            f"de {fmt_int(catalog['kuhl']['caracteristicas_distintas']['kuhl'])})"
        )
        fig.tight_layout()
    return fig


def main(mode: Mode = "completo", seed: int = SEED) -> dict[str, Any]:
    """Corre E7 (el catálogo es exacto; el tráfico, Monte Carlo) y guarda sus resultados."""
    started = time.perf_counter()
    params = PARAMS[mode]
    df = run(params, seed)
    days = run_traffic(params, seed)
    figures = summary(df, days, params) | {"segundos": round(time.perf_counter() - started, 1)}
    catalog = build_catalog()
    save_table(df, "e7_rejewski")
    save_table(top_table(catalog), "e7_rejewski_top")
    save_table(kuhl_top_table(catalog), "e7_rejewski_kuhl_tabla1")
    save_table(days, "e7_rejewski_trafico")
    update_summary("e7", figures, RunInfo("e7", mode, seed))

    import matplotlib.pyplot as plt

    fig = figure(df, days=days)
    save_figure(fig, "e7_rejewski")
    plt.close(fig)
    return figures
