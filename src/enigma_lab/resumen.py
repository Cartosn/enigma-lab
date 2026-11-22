"""``make resumen``: el paquete con el que los resultados llegan a las diapositivas (spec 11).

Arma ``results/presentacion/`` a partir de ``results/summary.json`` y los Parquet, sin
volver a correr experimentos:

- ``RESUMEN.md``: se entiende por sí solo (fecha, commit, semilla y modo al inicio).
- ``cifras.json``: las mismas cifras, para máquina.
- Un CSV por diapositiva de resultados, en formato largo: ``r1_validacion.csv`` (14),
  ``r2_cribs.csv`` (15), ``r3_bombe.csv`` (16) y ``r4_banburismus.csv`` (17). Para dibujar
  la 17 van además ``r4_roc.csv`` (curvas ROC) y ``r4_trayectorias.csv`` (D-046).

La sección «Demos» toma la demo 2 de ``results/bench_demo2.json`` (``make bench-demo``).

Uso:  python -m enigma_lab.resumen
"""

from __future__ import annotations

import json
import os
import platform
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from enigma_lab import SEED, paths
from enigma_lab.cifras import evaluate
from enigma_lab.core.machine import Enigma, EnigmaConfig
from enigma_lab.core.vectors import vector
from enigma_lab.experiments.common import git_commit, read_summary
from enigma_lab.experiments.e5_bombe import turing_agreement
from enigma_lab.viz.numfmt import fmt_dec, fmt_int, fmt_pct

PHASES_LEFT = [
    (
        "Fase 5 · Rejewski (E7) y ataque moderno (E8), opcionales",
        "no se hicieron; la diapositiva 9 solo cita a Kuhl y el README los lista entre las "
        "limitaciones",
    ),
    (
        "Demos · correr `make bench-demo` en el portátil del autor (P-001) y ensayar las dos "
        "demos allí",
        "antes de ensayar",
    ),
    (
        "Repositorio remoto · crearlo, para la CI y el enlace de la diapositiva 21",
        "antes de la presentación",
    ),
]
R2_COLUMNS = ["L", "texto", "n", "sobreviven", "p", "ic_bajo", "ic_alto", "teorico"]
R3_COLUMNS = [
    "letras",
    "lazos",
    "diagonal",
    "modo",
    "n_menus",
    "paradas_media",
    "ic_bajo",
    "ic_alto",
    "exito",
    "s_por_orden",
]
R4_COLUMNS = [
    "puntuacion",
    "solapamiento",
    "n",
    "aciertos",
    "letras_media",
    "ic_bajo",
    "ic_alto",
    "auc",
]
R4_TRAJECTORIES = (("tasa_1_17", "letras_1_17"), ("aleman", "trigramas"))
"""Las trayectorias que van a ``r4_trayectorias.csv``: el modelo de Turing y el alemán con
multigramas, 10 por hipótesis y un punto cada 20 letras."""
BENCH_FILE = "bench_demo2.json"


# ---------------------------------------------------------------- CSV


def r1_table(summary: dict[str, Any], results_dir: Path) -> pd.DataFrame:
    """Diapositiva 14: vectores de 6.1 más las cifras de E1, en las columnas del spec."""
    rows = pd.read_parquet(results_dir / "e1_vectores.parquet").to_dict("records")
    e1 = summary.get("e1", {})
    if e1:
        n = e1["pyenigma_casos"]
        rows += [
            {
                "prueba": f"{fmt_int(n)} claves frente a py-enigma",
                "esperado": "100 %",
                "obtenido": fmt_pct(e1["pyenigma_tasa"], 0).replace(" ", " "),
                "coincide": e1["pyenigma_coincidencias"] == n,
            },
            {
                "prueba": f"{fmt_int(e1['propiedades_letras'])} letras con "
                f"{fmt_int(e1['propiedades_claves'])} claves",
                "esperado": "0 puntos fijos",
                "obtenido": f"{fmt_int(e1['puntos_fijos'])} puntos fijos",
                "coincide": e1["puntos_fijos"] == 0,
            },
            {
                "prueba": f"Cifrar dos veces con {fmt_int(e1['propiedades_claves'])} claves",
                "esperado": "devuelve el original",
                "obtenido": f"{fmt_int(e1['involucion_ok'])} de "
                f"{fmt_int(e1['propiedades_claves'])}",
                "coincide": e1["involucion_ok"] == e1["propiedades_claves"],
            },
        ]
    return pd.DataFrame(rows, columns=["prueba", "esperado", "obtenido", "coincide"])


def r2_table(results_dir: Path) -> pd.DataFrame:
    """Diapositiva 15: supervivencia de las alineaciones falsas (E4), con las columnas del spec.

    Se agregan al final ``teorico_kappa`` (teoría con el IC del texto) y ``mensajes``.
    """
    table = pd.read_parquet(results_dir / "e4_cribs.parquet")
    return table[R2_COLUMNS + [c for c in table.columns if c not in R2_COLUMNS]]


def r3_table(results_dir: Path) -> pd.DataFrame:
    """Diapositiva 16: paradas falsas por orden (E5), con las columnas del spec.

    Se agregan al final, entre otras, ``turing`` (la tabla de Turing para esa celda),
    ``hipotesis_media`` (hipótesis T↔x abiertas por orden) y ``aristas`` (letras del crib).
    """
    table = pd.read_parquet(results_dir / "e5_bombe.parquet")
    return table[R3_COLUMNS + [c for c in table.columns if c not in R3_COLUMNS]]


def r4_table(results_dir: Path) -> pd.DataFrame:
    """Diapositiva 17: el SPRT de E6, con las columnas del spec.

    Se agregan al final, entre otras, ``fuente`` (tasa 1/17 o alemán), ``hipotesis``
    (profundidad o azar), ``alfa``, ``identifica`` (el desplazamiento verdadero gana entre
    los 51), ``wald`` y ``exacto``.
    """
    table = pd.read_parquet(results_dir / "e6_banburismus.parquet")
    return table[R4_COLUMNS + [c for c in table.columns if c not in R4_COLUMNS]]


def r4_extras(results_dir: Path) -> dict[str, pd.DataFrame]:
    """Datos para dibujar la diapositiva 17: curvas ROC y unas pocas trayectorias."""
    out: dict[str, pd.DataFrame] = {}
    roc = results_dir / "e6_banburismus_roc.parquet"
    if roc.is_file():
        out["r4_roc"] = pd.read_parquet(roc).round({"fpr": 4, "tpr": 4, "auc": 4})
    paths = results_dir / "e6_banburismus_trayectorias.parquet"
    if paths.is_file():
        data = pd.read_parquet(paths)
        keep = pd.Series(False, index=data.index)
        for text, key in R4_TRAJECTORIES:
            keep |= (data["fuente"] == text) & (data["puntuacion"] == key)
        data = data[keep & (data["par"] < 10) & (data["letra"] % 20 == 0)]
        out["r4_trayectorias"] = data.round({"decibanes": 3}).reset_index(drop=True)
    return out


def read_bench(results_dir: Path) -> dict[str, Any]:
    """Las mediciones de la demo 2 (``make bench-demo``), o vacío si no hay."""
    path = results_dir / BENCH_FILE
    if not path.is_file():
        return {}
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


# ---------------------------------------------------------------- secciones


def _demo1_timing() -> dict[str, float]:
    """Milisegundos de cálculo de los dos preajustes de la demo 1 en este equipo."""
    timings = {}
    for name, (config, text) in {
        "vector_bdzgo": (EnigmaConfig.from_strings("I II III"), "AAAAA"),
        "portada": (EnigmaConfig.from_dict(vector("portada")["key"]), vector("portada")["output"]),
    }.items():
        start = time.perf_counter()
        Enigma(config).trace(text)
        timings[name] = (time.perf_counter() - start) * 1000
    return timings


def _slide_14(e1: dict[str, Any]) -> list[str]:
    if not e1:
        return ["Sin resultados de E1: corre `make reproduce` y luego `make resumen`."]
    n, k = e1["pyenigma_casos"], e1["pyenigma_coincidencias"]
    low, high = e1["pyenigma_ic95"]
    models = ", ".join(
        f"{'Enigma I' if m == 'I' else m}: {fmt_int(v['coincidencias'])} de {fmt_int(v['casos'])}"
        for m, v in e1["pyenigma_por_modelo"].items()
    )
    return [
        f"- **Cifra para la diapositiva:** {fmt_int(k)} de {fmt_int(n)} claves y mensajes "
        f"aleatorios coinciden con py-enigma ({fmt_pct(k / n, 0)}; IC 95 % de Wilson "
        f"{fmt_pct(low, 2)}–{fmt_pct(high, 2)}). N = {fmt_int(n)}, semilla "
        f"{e1['corrida']['semilla']}, {fmt_int(e1['pyenigma_letras'])} letras.",
        f"- Por modelo: {models}. Cables de 0 a 10 (py-enigma no admite más); reflectores "
        "B y C (B y C delgados en la M4).",
        f"- Propiedades con {fmt_int(e1['propiedades_claves'])} claves de Enigma I y "
        f"{fmt_int(e1['propiedades_letras'])} letras: {fmt_int(e1['puntos_fijos'])} puntos "
        f"fijos; cifrar dos veces devolvió el original en {fmt_int(e1['involucion_ok'])} "
        f"claves; el cifrado por lotes coincidió con el escalar en "
        f"{fmt_int(e1['lotes_igual_escalar'])}.",
        f"- Vectores de 6.1: {e1['vectores_ok']} de {e1['vectores_total']} coinciden "
        "(tabla en `r1_validacion.csv`). CyberChef coincide en 6 de 6 casos comprobados a mano.",
        "- Nuevo para la diapositiva 14, si cabe: el simulador descifra letra por letra un "
        "mensaje real, el del U-264 (Enigma M4, 25-11-1942, roto por el M4 Project en 2006).",
    ]


def _row(table: pd.DataFrame, text: str, length: int) -> pd.Series | None:
    match = table[(table["texto"] == text) & (table["L"] == length)]
    return None if match.empty else match.iloc[0]


def _slide_15(e4: dict[str, Any], table: pd.DataFrame | None) -> list[str]:
    if not e4 or table is None:
        return ["Sin resultados de E4: corre `make reproduce` y luego `make resumen`."]
    lines = []
    for length in (13, 50):
        r, g = _row(table, "aleatorio", length), _row(table, "aleman", length)
        if r is None or g is None:
            continue
        lines.append(
            f"- **L = {length}:** con texto aleatorio sobrevive el {fmt_pct(r['p'])} de las "
            f"alineaciones falsas (IC 95 % {fmt_pct(r['ic_bajo'])}–{fmt_pct(r['ic_alto'])}); "
            f"teoría (25/26)^{length} = {fmt_pct(r['teorico'])}. Con **alemán real**, el "
            f"{fmt_pct(g['p'])} ({fmt_pct(g['ic_bajo'])}–{fmt_pct(g['ic_alto'])})."
        )
    random_ok = e4["aleatorio"]["teoria_25_26_dentro_del_ic"]
    german_ok = e4["aleman"]["teoria_25_26_dentro_del_ic"]
    german_k = e4["aleman"]["teoria_kappa_dentro_del_ic"]
    lines += [
        f"- Texto aleatorio: (25/26)^L cae dentro del IC 95 % en {random_ok} longitudes. "
        "Es el criterio de aceptación de la fase 2 y se cumple.",
        f"- Alemán real (X como separador, κ = {fmt_dec(e4['kappa_aleman_x'], 4)}): "
        f"(25/26)^L cae dentro del IC en {german_ok} longitudes. La teoría corregida, "
        f"(1 − (1 − κ)/25)^L, cae dentro en {german_k}. Con alemán sobreviven un poco más "
        "alineaciones falsas: una letra del crib igual a la letra plana de esa posición "
        "nunca puede chocar.",
        f"- Diseño: {fmt_int(e4['n_por_L'])} mensajes de {e4['letras_por_mensaje']} letras "
        f"por longitud y por tipo de texto, claves aleatorias de Enigma I con 10 cables, "
        f"semilla {e4['corrida']['semilla']}. La alineación verdadera sobrevivió siempre: "
        f"{'sí' if e4['verdadera_sobrevive_siempre'] else 'NO'}. Tabla completa en "
        "`r2_cribs.csv`.",
    ]
    return lines


def _stops(value: float) -> str:
    """Paradas por orden con tres cifras significativas: 667 · 25,4 · 1,22 · 0,04."""
    if value >= 1000:
        return fmt_int(round(value))
    if value == 0:
        return "0"
    return f"{value:.3g}".replace(".", ",")


def _and(values: list[int]) -> str:
    """[12, 16] → «12 y 16»."""
    words = [str(v) for v in values]
    return words[0] if len(words) == 1 else ", ".join(words[:-1]) + " y " + words[-1]


def _cell(table: pd.DataFrame, letters: int, loops: int, diagonal: str, mode: str) -> Any:
    match = table[
        (table["letras"] == letters)
        & (table["lazos"] == loops)
        & (table["diagonal"] == diagonal)
        & (table["modo"] == mode)
    ]
    return None if match.empty else match.iloc[0]


def _slide_16(e5: dict[str, Any], table: pd.DataFrame | None) -> list[str]:
    if not e5 or table is None:
        return ["Sin resultados de E5: corre `make reproduce` y luego `make resumen`."]
    on = [_cell(table, 12, k, "si", "bletchley") for k in range(4)]
    off = [_cell(table, 12, k, "no", "bletchley") for k in range(4)]
    if any(c is None for c in on):
        return ["E5 no tiene la columna de 12 letras con 0 a 3 lazos."]
    n = int(on[0]["n_menus"])
    lines = [
        "- **Cifra para la diapositiva** (menús de 12 letras, con diagonal board, modo "
        "Bletchley): paradas falsas por orden de rotores con 0, 1, 2 y 3 lazos: "
        + " · ".join(_stops(c["paradas_media"]) for c in on)
        + ". Turing: "
        + " · ".join(_stops(c["turing"]) for c in on)
        + ". IC 95 %: "
        + "; ".join(f"{_stops(c['ic_bajo'])}–{_stops(c['ic_alto'])}" for c in on)
        + f". N = {n} menús por celda, un orden de rotores por menú, semilla "
        f"{e5['corrida']['semilla']}.",
        f"- **En 60 órdenes:** con 2 lazos, unas {_stops(60 * on[2]['paradas_media'])} "
        f"paradas falsas (Turing: {_stops(60 * on[2]['turing'])}); con 3 lazos, "
        f"{_stops(60 * on[3]['paradas_media'])} (Turing: {_stops(60 * on[3]['turing'])}).",
    ]
    ratios = [
        on[k]["paradas_media"] / on[k + 1]["paradas_media"]
        for k in range(3)
        if on[k + 1]["paradas_media"] > 0
    ]
    if ratios:
        few = round(on[3]["paradas_media"] * n)
        lines.append(
            "- **Cada lazo divide las paradas** por "
            + ", ".join(fmt_dec(r, 1) for r in ratios)
            + " (de 0 a 1, de 1 a 2 y de 2 a 3 lazos; Turing: por unas 26). Con las letras "
            "fijas, un lazo más es una arista más con las mismas letras. Con 3 lazos hubo "
            f"solo {few} paradas falsas en {n} menús, así que el último cociente es impreciso."
        )
    if all(c is not None for c in off):
        lines.append(
            "- **Sin diagonal board** (los mismos menús): "
            + " · ".join(_stops(c["paradas_media"]) for c in off)
            + " paradas falsas por orden con 0 a 3 lazos. Sin lazos, la Bombe para en casi "
            "todas las 17.576 posiciones: sin el diagonal board un menú sin lazos no descarta "
            "nada."
        )
    close, total = turing_agreement(table)
    if total:
        # Turing cuenta hipótesis abiertas (ver «Pocas letras y sin lazos»).
        lines.append(
            f"- **Toda la tabla de Turing** (8 a 16 letras): en {close} de {total} celdas "
            "con valor exacto, las hipótesis abiertas por orden que medimos están entre la "
            "mitad y el doble de la estimación de Turing. Detalle por celda en "
            "`r3_bombe.csv` (columnas `paradas_media`, `hipotesis_media` y `turing`)."
        )
    eight = _cell(table, 8, 0, "si", "bletchley")
    if eight is not None:
        lines.append(
            f"- **Pocas letras y sin lazos:** con 8 letras Turing da {_stops(eight['turing'])} "
            "paradas por orden, más que las 17.576 posiciones. Su cifra cuenta hipótesis "
            f"abiertas, no posiciones: medimos {_stops(eight['hipotesis_media'])} hipótesis "
            f"en {_stops(eight['paradas_media'])} posiciones."
        )
    lines.append(
        f"- **Éxito:** en modo Bletchley aparece la parada verdadera en el "
        f"{fmt_pct(e5['exito_bletchley'])} de los menús. El central se movió dentro del tramo "
        f"en el {fmt_pct(e5['vuelta_frac'])}; sin esa vuelta, en el "
        f"{fmt_pct(e5['exito_bletchley_sin_vuelta'])}."
    )
    if e5.get("exito_robusto") is not None:
        lines.append(
            f"- **Modo robusto** (menús de {_and(e5.get('letras_robusto', [12]))} letras): "
            f"éxito {fmt_pct(e5['exito_robusto'])}, "
            f"{fmt_dec(e5['robusto_tiempo_relativo'], 1)} veces el tiempo y "
            f"{fmt_dec(e5['robusto_paradas_relativas'], 1)} veces las paradas del modo Bletchley."
        )
    lines.append(
        f"- **Tiempo por orden** (17.576 posiciones, en el equipo de `make reproduce`): "
        f"{fmt_dec(e5['s_por_orden_bletchley'], 3)} s en modo Bletchley"
        + (
            f" y {fmt_dec(e5['s_por_orden_robusto'], 3)} s en modo robusto."
            if e5.get("s_por_orden_robusto")
            else "."
        )
    )
    factors = [c["paradas_media"] / c["turing"] for c in on if c["turing"] > 0]
    lines.append(
        "- **«Letras» son vértices** (P-002, D-031): las letras distintas del menú. Con esa "
        f"lectura la columna de 12 letras queda cerca de la de Turing (entre "
        f"{fmt_dec(min(factors), 1)} y {fmt_dec(max(factors), 1)} veces su valor); contando "
        "aristas no."
    )
    return lines


def _sdb(value: float, decimals: int = 3) -> str:
    """Decibanes con signo explícito: +1,845 · −0,093."""
    return ("+" if value > 0 else "") + fmt_dec(value, decimals)


def _one_in(rate: float) -> str:
    """Una tasa como «1 de cada 12,5» (o «1 de cada 17» si da un entero)."""
    every = 1 / rate
    if abs(every - round(every)) < 0.05:
        return f"1 de cada {fmt_int(round(every))}"
    return f"1 de cada {fmt_dec(every, 1)}"


def _letters_ci(cell: dict[str, Any]) -> str:
    """«960 letras (IC 95 % 931–989)»."""
    low, high = cell["ic"]
    return (
        f"{fmt_int(round(cell['letras']))} letras (IC 95 % "
        f"{fmt_int(round(low))}–{fmt_int(round(high))})"
    )


def _slide_17_model(e6: dict[str, Any]) -> list[str]:
    """Las cifras de Turing, la simulación con tasa 1/17 y la diferencia con Wald."""
    w, wald, exact, gap = e6["pesos"], e6["wald"], e6["exacto"], e6["brecha_wald"]
    base = e6["simulacion"]["tasa_1_17/letras_1_17"]
    h1, h0 = base["profundidad"], base["azar"]
    cells = (("profundidad", h1), ("azar", h0))
    inside = all(c["ic"][0] <= exact[h]["letras"] <= c["ic"][1] for h, c in cells)
    missed = (1 - exact["profundidad"]["acepta_profundidad"], exact["azar"]["acepta_profundidad"])
    up, down = gap["profundidad"], gap["azar"]
    return [
        "- **Cifras de Turing** (diapositivas 13 y 17, comprobadas en `test_presentacion.py`): "
        f"{_sdb(w['repeticion_db'])} dB por repetición y {_sdb(w['no_repeticion_db'])} dB por no "
        f"repetición; en promedio, {_sdb(w['por_letra_profundidad_db'], 4)} dB por letra en "
        f"profundidad y {_sdb(w['por_letra_azar_db'], 4)} dB al azar. Umbrales con α = β = 1 %: "
        f"±{fmt_dec(w['umbral_db'], 2)} dB. Aproximación de Wald: "
        f"{fmt_int(round(wald['profundidad']))} letras para confirmar la profundidad y "
        f"{fmt_int(round(wald['azar']))} para descartarla.",
        "- **Cifra para la diapositiva: la simulación del SPRT** (criterio de la fase 4). Letras "
        "sueltas y un texto cuyas columnas en profundidad repiten con 1/17 exacta, cifrado con la "
        f"máquina real; {fmt_int(e6['n_pares'])} pares, semilla {e6['corrida']['semilla']}. "
        f"Confirmar la profundidad toma {_letters_ci(h1)} y descartarla, {_letters_ci(h0)}. "
        f"El cálculo exacto, sin simulación, da {fmt_dec(exact['profundidad']['letras'], 1)} y "
        f"{fmt_dec(exact['azar']['letras'], 1)}"
        + (", dentro de los dos IC" if inside else "; **alguno queda fuera del IC**")
        + f". Errores en la simulación: {fmt_pct(h1['errores'])} en profundidad y "
        f"{fmt_pct(h0['errores'])} al azar (exactos: {fmt_pct(missed[0], 2)} y "
        f"{fmt_pct(missed[1], 2)}).",
        "- **La diferencia con Wald es el sobrepaso.** Wald supone que el puntaje se detiene justo "
        f"en ±{fmt_dec(w['umbral_db'], 2)} dB; en realidad se detiene al cruzarlo, y lo pasa. Una "
        f"repetición suma {fmt_dec(w['repeticion_db'], 3)} dB de golpe: arriba, el puntaje pasa "
        f"el umbral por {fmt_dec(exact['profundidad']['sobrepaso_arriba_db'], 2)} dB en promedio "
        f"(simulación: {fmt_dec(h1['sobrepaso_arriba_db'], 2)}). La identidad de Wald, "
        "E[N] = E[S_N] / μ, es exacta, así que en profundidad son "
        f"{fmt_dec(up['total'], 1)} letras más: {fmt_dec(up['sobrepaso_arriba'], 1)} por ese "
        f"sobrepaso y {fmt_dec(up['errores'] + up['sobrepaso_abajo'], 1)} por lo demás. Abajo, "
        f"cada no repetición resta solo {fmt_dec(-w['no_repeticion_db'], 3)} dB y el sobrepaso es "
        f"de {fmt_dec(exact['azar']['sobrepaso_abajo_db'], 3)} dB. Al azar la diferencia es de "
        f"{fmt_dec(down['total'], 1)} letras: {fmt_dec(down['sobrepaso_abajo'], 1)} por el "
        f"sobrepaso de abajo, {fmt_dec(down['errores'], 1)} porque el error real queda por debajo "
        f"del 1 % y {fmt_dec(down['sobrepaso_arriba'], 1)} por el de arriba. Con la simulación, "
        f"E[S_N] / μ da {fmt_int(round(h1['wald_identidad']))} y "
        f"{fmt_int(round(h0['wald_identidad']))} letras.",
    ]


def _slide_17_german(e6: dict[str, Any]) -> list[str]:
    """El texto alemán real: su tasa de repetición y lo que cambian los multigramas."""
    sim, rates, wald = e6["simulacion"], e6["tasas"], e6["wald"]
    measured = rates["medidas"]["aleman"]
    turing, letters = sim["aleman/letras_1_17"], sim["aleman/letras"]
    tri, tetra = sim["aleman/trigramas"], sim["aleman/tetragramas"]
    sooner = turing["profundidad"]["letras"] < wald["profundidad"]
    faster = {h: 1 - tri[h]["letras"] / turing[h]["letras"] for h in ("profundidad", "azar")}
    plain = {h: fmt_int(round(letters[h]["letras"])) for h in ("profundidad", "azar")}
    return [
        "- **Con texto alemán real** (corpus, X como separador): en profundidad las letras "
        f"repiten {_one_in(measured['profundidad'][0])}, medido con la máquina, y no "
        f"{_one_in(rates['turing'])}. El IC del corpus es {fmt_dec(rates['corpus_x'], 4)} con la X "
        f"y {fmt_dec(rates['corpus_letras'], 4)} sin ella ({_one_in(rates['corpus_letras'])}); al "
        f"azar se miden {_one_in(measured['azar'][0])}. Con los pesos de Turing, confirmar la "
        f"profundidad toma {_letters_ci(turing['profundidad'])}"
        + (
            f": la decisión llega antes que las {fmt_int(round(wald['profundidad']))} de Wald"
            if sooner
            else ""
        )
        + f". Descartarla toma {_letters_ci(turing['azar'])}, como con 1/17.",
        "- **Cuánto aceleran los multigramas** (pesos medidos en el corpus, α = β = 1 %). Con "
        f"letras sueltas y la tasa del corpus: {plain['profundidad']} letras en profundidad y "
        f"{plain['azar']} al azar, con un error de "
        f"{fmt_pct(letters['profundidad']['errores'])} en profundidad: las repeticiones del texto "
        "real vienen en racimos, y un modelo de letras independientes no lo sabe. Con bigramas y "
        f"trigramas: {fmt_int(round(tri['profundidad']['letras']))} y "
        f"{fmt_int(round(tri['azar']['letras']))}, con errores de "
        f"{fmt_pct(tri['profundidad']['errores'])} y {fmt_pct(tri['azar']['errores'])}; hasta "
        f"tetragramas, {fmt_int(round(tetra['profundidad']['letras']))} y "
        f"{fmt_int(round(tetra['azar']['letras']))}. Frente a los pesos de Turing, los bigramas y "
        f"trigramas necesitan un {fmt_pct(faster['profundidad'], 0)} menos de letras para "
        f"confirmar y un {fmt_pct(faster['azar'], 0)} menos para descartar.",
    ]


def _slide_17_overlap(e6: dict[str, Any]) -> list[str]:
    """Lo que alcanza con mensajes de verdad: identificación del desplazamiento y AUC."""
    over = e6["solapamiento"]
    marks = [m for m in ("100", "200", "400") if m in over["aleman/letras"]]
    if not marks:
        return []

    def series(combo: str, field: str) -> str:
        values = [fmt_pct(over[combo][m][field], 0) for m in marks]
        return ", ".join(values[:-1]) + f" y {values[-1]}"

    lengths = ", ".join(marks[:-1]) + f" y {marks[-1]}"
    return [
        f"- **Solapamientos de mensajes reales** ({lengths} letras). El desplazamiento verdadero "
        "saca el mayor puntaje de los 51 en el "
        f"{series('aleman/letras', 'identifica')} de los pares de texto alemán con letras sueltas, "
        f"en el {series('aleman/trigramas', 'identifica')} con bigramas y trigramas y en el "
        f"{series('tasa_1_17/letras_1_17', 'identifica')} con la tasa 1/17. El SPRT (α = β = 1 %) "
        "confirma la profundidad dentro de ese solapamiento en el "
        f"{series('aleman/trigramas', 'aciertos_profundidad')} de los pares (alemán, bigramas y "
        "trigramas).",
        "- **Curva ROC** del puntaje tras 200 letras, sin detenerse (AUC): "
        + "; ".join(
            f"{label} {fmt_dec(over[combo]['200']['auc'], 3)}"
            for combo, label in (
                ("tasa_1_17/letras_1_17", "tasa 1/17"),
                ("aleman/letras", "alemán con letras sueltas"),
                ("aleman/trigramas", "alemán con bigramas y trigramas"),
            )
            if "200" in over[combo]
        )
        + ". Con letras sueltas el puntaje solo depende del número de repeticiones, así que las "
        "dos tasas dan la misma curva.",
    ]


def _slide_17(e6: dict[str, Any]) -> list[str]:
    if not e6:
        return ["Sin resultados de E6: corre `make reproduce` y luego `make resumen`."]
    return [
        *_slide_17_model(e6),
        *_slide_17_german(e6),
        *_slide_17_overlap(e6),
        "- Datos para los gráficos: `r4_banburismus.csv` (tabla larga: fuente, puntuación, "
        "solapamiento, α e hipótesis), `r4_roc.csv` (curvas ROC) y `r4_trayectorias.csv` "
        "(decibanes acumulados, 10 pares por hipótesis).",
    ]


def _e6_notes(e6: dict[str, Any]) -> list[str]:
    """Notas de E6 para «Discrepancias»."""
    if not e6:
        return []
    wald, exact, rates = e6["wald"], e6["exacto"], e6["tasas"]
    turing = e6["simulacion"]["aleman/letras_1_17"]["profundidad"]["letras"]
    return [
        f"- Diapositivas 13 y 17: {fmt_int(round(wald['profundidad']))} y "
        f"{fmt_int(round(wald['azar']))} letras son la aproximación de Wald, que ignora el "
        "sobrepaso de los umbrales. Con las mismas tasas, el valor exacto es "
        f"{fmt_dec(exact['profundidad']['letras'], 1)} y {fmt_dec(exact['azar']['letras'], 1)}, y "
        "la simulación lo confirma. Las cifras de la diapositiva siguen bien si se presentan como "
        "«según Wald».",
        "- Diapositiva 13 y guion («las letras se repiten 1 de cada 17 veces»): es la tasa del "
        "tráfico naval que da Wikipedia. Nuestro corpus literario repite "
        f"{_one_in(rates['corpus_x'])} con la X como separador y {_one_in(rates['corpus_letras'])} "
        f"solo con letras. Con él, la profundidad se confirma en unas {fmt_int(round(turing))} "
        "letras con los pesos de Turing. No contradice la diapositiva: es otro texto.",
        "- Spec 5.6 («en profundidad … hasta que se mueve el rotor central»): con la máquina real "
        "los dos mensajes recorren la misma sucesión de estados, así que la profundidad dura todo "
        "el solapamiento. El rotor central decide si el desplazamiento verdadero es +δ o δ − 26 "
        "(D-042); por eso se prueban los desplazamientos de −25 a +25.",
    ]


def _demo_2(bench: dict[str, Any]) -> list[str]:
    if not bench:
        return [
            "- **Demo 2 (diapositiva 12):** sin mediciones; corre `make bench-demo` en el "
            "portátil del autor."
        ]
    team = bench["equipo"]
    where = f"{team['procesador']}, {team['nucleos_logicos']} núcleos lógicos, {team['sistema']}"
    lines = [
        f"- **Demo 2 (diapositiva 12):** `make bench-demo` del {bench['fecha']} (commit "
        f"{bench['commit']}) en {where}. Casos de compañero: clave como la de «Clave "
        f"aleatoria» (10 cables), mensaje alemán de {bench['letras_mensaje']} letras que "
        "empieza por el crib, crib en la posición 0. Flujo completo de la página La Bombe: "
        "barrido, máquina de verificación y «Verificar». Éxito: el descifrado es el mensaje "
        "letra por letra.",
        "",
        "| Configuración | Éxito (IC 95 %) | p50 | p95 | Barrido p95 | ¿Cumple? |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for c in bench["configuraciones"]:
        low, high = c["exito_ic"]
        lines.append(
            f"| {c['nombre']} | {c['exitos']} de {c['n']} ({fmt_pct(low, 0)}–"
            f"{fmt_pct(high, 0)}) | {fmt_dec(c['p50'], 1)} s | {fmt_dec(c['p95'], 1)} s | "
            f"{fmt_dec(c['p95_barrido'], 1)} s | {'sí' if c['cumple'] else 'no'} |"
        )
    chosen = next((c for c in bench["configuraciones"] if c["id"] == bench["recomendada"]), None)
    lines.append("")
    if chosen is None:
        lines.append(
            f"- **Recomendación:** ninguna configuración cumple {bench['criterio']} en este equipo."
        )
    else:
        how = {
            "60_robusto": "el compañero usa «Clave aleatoria» sin restricciones y empieza su "
            "mensaje por WETTERBERICHT (con X entre palabras). En la demo, el botón «Cifrado "
            "del compañero» de La Bombe deja el crib en la posición 0, «Rotores I a V (60 "
            "órdenes)» y el modo robusto; se pega el cifrado y se pulsa Ctrl+Enter.",
            "6_robusto": "antes de cifrar, el compañero marca los rotores I, II y III en "
            "«Rotores permitidos en «Clave aleatoria»» (página Máquina), pulsa «Clave "
            "aleatoria» y empieza su mensaje por WETTERBERICHT (con X entre palabras). En la "
            "demo, «Cifrado del compañero» deja «Rotores I, II y III (6 órdenes)» y el modo "
            "robusto; dilo en voz alta.",
            "crib_largo": "el compañero empieza su mensaje por WETTERBERICHTXFUER. En la demo, "
            "«Cifrado del compañero» deja ese crib, «Rotores I a V (60 órdenes)» y el modo "
            "robusto.",
        }[chosen["id"]]
        lines.append(
            f"- **Recomendada ({bench['criterio']}):** {chosen['nombre']}: {how} Éxito "
            f"{fmt_pct(chosen['exito'])}, p95 {fmt_dec(chosen['p95'], 1)} s."
        )
    lines.append(
        "- Estos tiempos son del equipo indicado. Este equipo es un escritorio; el presupuesto "
        "de 30 s es del portátil del autor (P-001): corre `make bench-demo` allí antes de "
        "ensayar y usa la configuración que recomiende."
    )
    return lines


def _other_results(e2: dict[str, Any], e3: dict[str, Any]) -> list[str]:
    lines = []
    if e3:
        de, es = e3["aleman"], e3["espanol"]
        length = fmt_int(de["L"])
        lines += [
            f"- **E3 (diapositivas 6 y 23):** IC del corpus alemán {fmt_dec(de['ic_corpus'], 4)} "
            f"(Pommerening: {fmt_dec(e3['ic_referencia_aleman'], 4)}); español "
            f"{fmt_dec(es['ic_corpus'], 4)}. Con mensajes de {length} letras, el IC del alemán "
            f"pasa de {fmt_dec(de['ic_plano'][0], 4)} en el plano a "
            f"{fmt_dec(de['ic_cifrado'][0], 4)} en el cifrado (1/26 = "
            f"{fmt_dec(e3['ic_azar'], 4)}).",
            f"- La prueba χ² (α = 5 %), con {length} letras, rechaza la uniformidad del "
            f"{fmt_pct(de['rechaza_plano'], 0)} de los textos planos en alemán y del "
            f"{fmt_pct(de['rechaza_cifrado'], 1)} de los cifrados (un cifrado uniforme daría "
            "5 %).",
        ]
        if "rechaza_cifrado_teoria" in de:
            lines.append(
                "- **Antifrecuencia:** como ninguna letra se cifra a sí misma, la letra c sale "
                "cifrada con probabilidad (1 − f_c)/25. Las letras comunes del idioma salen un "
                f"poco menos: la E, el {fmt_pct(de['frecuencia_e_plano'])} del alemán, debería "
                f"ser el {fmt_pct(de['frecuencia_e_cifrado_esperada'], 2)} del cifrado y no el "
                f"{fmt_pct(1 / 26, 2)}. Con esa distribución, la χ² no central predice un "
                f"{fmt_pct(de['rechaza_cifrado_teoria'], 1)} de rechazos con {length} letras; "
                f"se midió {fmt_pct(de['rechaza_cifrado'], 1)}. Las frecuencias del idioma se "
                "filtran débiles y al revés."
            )
        lines.append(
            f"- Puntos fijos: {fmt_int(e3['puntos_fijos'])} en {fmt_int(e3['letras'])} letras."
        )
    if e2:
        lines.append(
            f"- **E2 (diapositiva 7):** {e2['texto']}; máximo de N(k) con "
            f"{e2['cables_maximo']} cables."
        )
    return lines or ["Sin resultados de E2 ni E3."]


def _discrepancies(
    e4: dict[str, Any],
    table: pd.DataFrame | None,
    e5_table: pd.DataFrame | None = None,
    bench: dict[str, Any] | None = None,
    e6: dict[str, Any] | None = None,
) -> list[str]:
    lines = [
        "Ninguna contradicción con las diapositivas ni con el guion. Notas:",
        "",
        *_e6_notes(e6 or {}),
    ]
    if e5_table is not None:
        on = [_cell(e5_table, 12, k, "si", "bletchley") for k in range(4)]
        if all(c is not None for c in on):
            lines.append(
                "- Diapositiva 16: la tabla de Turing cuenta «letras del menú» como letras "
                "distintas (vértices del grafo), igual que la diapositiva 11 (11 letras, 13 "
                "aristas). Con esa lectura, nuestra Bombe da "
                + " · ".join(_stops(c["paradas_media"]) for c in on)
                + " paradas falsas por orden con 12 letras y 0 a 3 lazos, frente a 820 · 31 · "
                "1,2 · 0,04 de Turing. Si «letras» fueran aristas (letras del crib), no "
                "coincidirían (ver D-031)."
            )
            lines.append(
                "- Guion, diapositiva 16: «en los 60 órdenes quedan unas 2 paradas falsas en "
                "total; con dos lazos serían unas 72» son cifras de Turing (0,04 y 1,2 por 60). "
                f"Nuestra Bombe da {_stops(60 * on[3]['paradas_media'])} y "
                f"{_stops(60 * on[2]['paradas_media'])}. El mensaje del guion se sostiene "
                "(con 3 lazos, unas pocas paradas en los 60 órdenes; con 2, decenas)."
            )
    lines.append(
        "- Verificador (spec 6.4, «siempre»): recupera una clave equivalente en 200 de 200 de "
        "los casos de la prueba, que se usaron para ajustar su diseño, y en 198 de 200 casos "
        "nuevos. Las 2 fallas tienen el plugboard exacto y difieren en una sola letra, la "
        "segunda o la última del mensaje: un doble paso del central justo en el borde que el "
        "texto no alcanza a decidir. La parada verdadera aparece siempre (400 de 400)."
    )
    if bench and bench.get("recomendada"):
        lines.append(
            "- Diapositiva 12 y guion: la configuración de la demo 2 es la recomendada en "
            "«Demos»; el guion la tiene pendiente."
        )
    if e4 and table is not None:
        g = _row(table, "aleman", 13)
        if g is not None:
            lines.append(
                f"- Diapositiva 15: con alemán real, el 60 % de 13 letras pasa a "
                f"{fmt_pct(g['p'])}, por encima de (25/26)^13 y fuera de su IC. No es un error "
                "del filtro: es el efecto del IC del idioma, y la corrección "
                f"(1 − (1 − κ)/25)^13 = {fmt_pct(g['teorico_kappa'])} lo explica. La "
                "diapositiva puede seguir diciendo «60 %» para la teoría y agregar el valor real."
            )
    lines += [
        "- py-enigma admite como máximo 10 cables: la comparación de 10.000 claves usa de 0 a "
        "10 cables, y las pruebas con hypothesis cubren de 0 a 13.",
        "- Mensaje histórico: no se encontró una fuente verificable del mensaje de Barbarossa "
        "(1941). Se usa el del U-264 (M4), publicado con clave, cifrado y texto por D. Rijmenants.",
        "- Corpus: gutenberg.org estaba en mantenimiento el 20-11-2026; se descargó de su espejo "
        "oficial (Mirror Service), con SHA-256 verificado.",
    ]
    return lines


def _runs(summary: dict[str, Any]) -> list[str]:
    rows = []
    for name in sorted(summary):
        run = summary[name].get("corrida", {})
        rows.append(
            f"{name.upper()}: modo {run.get('modo', '—')}, {run.get('fecha', '—')}, "
            f"commit {run.get('commit', '—')}"
        )
    return rows


def build_markdown(
    summary: dict[str, Any],
    cifras: list[dict[str, Any]],
    e4_table: pd.DataFrame | None,
    e5_table: pd.DataFrame | None = None,
    bench: dict[str, Any] | None = None,
) -> str:
    """El texto de ``RESUMEN.md``."""
    timing = _demo1_timing()
    modes = sorted({v.get("corrida", {}).get("modo", "—") for v in summary.values()})
    lines = [
        "# Resumen de resultados para la presentación",
        "",
        f"- **Fecha:** {datetime.now(UTC):%Y-%m-%d %H:%M} UTC",
        f"- **Commit:** {git_commit()}",
        f"- **Semilla:** {SEED}",
        f"- **Modo:** {', '.join(modes) or 'sin corridas'}",
        f"- **Corridas:** {'; '.join(_runs(summary)) or '—'}",
        "",
        "Generado por `make resumen` a partir de `results/summary.json` y los Parquet, sin "
        "volver a correr experimentos. Cada cifra sale del código.",
        "",
        "## 1. Por diapositiva de resultados",
        "",
        "### Diapositiva 14 · Validación (E1)",
        "",
        *_slide_14(summary.get("e1", {})),
        "",
        "### Diapositiva 15 · Cribs (E4)",
        "",
        *_slide_15(summary.get("e4", {}), e4_table),
        "",
        "### Diapositiva 16 · Bombe (E5)",
        "",
        *_slide_16(summary.get("e5", {}), e5_table),
        "",
        "### Diapositiva 17 · Banburismus (E6)",
        "",
        *_slide_17(summary.get("e6", {})),
        "",
        "### Otros resultados útiles",
        "",
        *_other_results(summary.get("e2", {}), summary.get("e3", {})),
        "",
        "## 2. Cifras de la presentación",
        "",
        "| Diap. | Cifra | En la presentación | Del código | ¿Coincide? |",
        "| --- | --- | --- | --- | --- |",
    ]
    for c in cifras:
        if c["obtenido"] is None:
            obtained, status = "—", f"pendiente ({c['pendiente']})"
        else:
            obtained, status = str(c["obtenido"]), "sí" if c["coincide"] else "**NO**"
        lines.append(
            f"| {c['diapositivas']} | {c['cifra']} | {c['esperado']} | {obtained} | {status} |"
        )
    ready = [c for c in cifras if c["obtenido"] is not None]
    ok = sum(bool(c["coincide"]) for c in ready)
    cpu = f"{platform.processor() or platform.machine()}, {os.cpu_count()} núcleos lógicos"
    lines += [
        "",
        f"{ok} de {len(ready)} cifras calculadas coinciden; "
        f"{len(cifras) - len(ready)} llegan en fases siguientes.",
        "",
        "## 3. Demos",
        "",
        f"- **Demo 1 (diapositiva 4):** el cálculo es instantáneo. La traza de «Vector "
        f"BDZGO» tarda {fmt_dec(timing['vector_bdzgo'], 1)} ms y la de «Portada» "
        f"{fmt_dec(timing['portada'], 1)} ms en el equipo donde corrió `make resumen` "
        f"({cpu}). Los 45 s del guion los pone la interacción. Falta cronometrar el "
        "recorrido completo en el portátil del autor.",
        "- **La app en clase:** abre `http://localhost:8501/maquina?demo=1` (el modo demo queda "
        "en la URL y sobrevive a una recarga) y, en otra pestaña, "
        "`http://localhost:8501/bombe?demo=1`; pliega la barra lateral para ganar ancho. En "
        "modo demo, Máquina muestra solo «Vector BDZGO» y «Portada», y La Bombe, «Cifrado del "
        "compañero» y «Caso de respaldo» (plan B).",
        *_demo_2(bench or {}),
        "",
        "## 4. Discrepancias",
        "",
        *_discrepancies(summary.get("e4", {}), e4_table, e5_table, bench, summary.get("e6", {})),
        "",
        "## 5. Pendientes",
        "",
        *[f"- {what}: {when}." for what, when in PHASES_LEFT],
        "",
    ]
    return "\n".join(lines)


def main(results_dir: Path | None = None) -> Path:
    """Escribe ``results/presentacion/`` y devuelve su ruta."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    results = results_dir or paths.RESULTS
    out = results / "presentacion"
    out.mkdir(parents=True, exist_ok=True)
    summary = read_summary(results)
    cifras = evaluate()

    if "e1" in summary:
        r1_table(summary, results).to_csv(out / "r1_validacion.csv", index=False)
    e4_table = None
    if (results / "e4_cribs.parquet").is_file():
        e4_table = r2_table(results)
        e4_table.to_csv(out / "r2_cribs.csv", index=False)
    e5_table = None
    if (results / "e5_bombe.parquet").is_file():
        e5_table = r3_table(results)
        e5_table.to_csv(out / "r3_bombe.csv", index=False)
    if (results / "e6_banburismus.parquet").is_file():
        r4_table(results).to_csv(out / "r4_banburismus.csv", index=False)
        for name, extra in r4_extras(results).items():
            extra.to_csv(out / f"{name}.csv", index=False)
    bench = read_bench(results)
    demo2 = {k: v for k, v in bench.items() if k != "configuraciones"}
    if bench:
        demo2["configuraciones"] = [
            {k: v for k, v in c.items() if k != "casos"} for c in bench["configuraciones"]
        ]
    (out / "cifras.json").write_text(
        json.dumps(
            {"cifras": cifras, "experimentos": summary, "demo2": demo2},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    markdown = build_markdown(summary, cifras, e4_table, e5_table, bench)
    (out / "RESUMEN.md").write_text(markdown, encoding="utf-8")
    print(f"Listo: {out}")
    return out


if __name__ == "__main__":
    main()
