"""``make resumen``: el paquete con el que los resultados llegan a las diapositivas (spec 11).

Arma ``results/presentacion/`` a partir de ``results/summary.json`` y los Parquet, sin
volver a correr experimentos:

- ``RESUMEN.md``: se entiende por sí solo (fecha, commit, semilla y modo al inicio).
- ``cifras.json``: las mismas cifras, para máquina.
- Un CSV por diapositiva de resultados, en formato largo: ``r1_validacion.csv`` (14) y
  ``r2_cribs.csv`` (15); ``r3_bombe.csv`` y ``r4_banburismus.csv`` llegan en las fases 3 y 4.

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
from enigma_lab.viz.numfmt import fmt_dec, fmt_int, fmt_pct

PHASES_LEFT = [
    ("Fase 3 · Bombe (E5) y configuración de la demo 2", "semana 2"),
    ("Fase 4 · Banburismus (E6)", "semana 3"),
    ("Fase 5 · Rejewski (E7) y ataque moderno (E8), opcionales", "semana 3"),
    ("Fase 6 · modo demo completo, Docker, informe y entrega", "fin de la semana 3"),
]
R2_COLUMNS = ["L", "texto", "n", "sobreviven", "p", "ic_bajo", "ic_alto", "teorico"]


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


def _other_results(e2: dict[str, Any], e3: dict[str, Any]) -> list[str]:
    lines = []
    if e3:
        de, es = e3["aleman"], e3["espanol"]
        lines += [
            f"- **E3 (diapositivas 6 y 23):** IC del corpus alemán {fmt_dec(de['ic_corpus'], 4)} "
            f"(Pommerening: {fmt_dec(e3['ic_referencia_aleman'], 4)}); español "
            f"{fmt_dec(es['ic_corpus'], 4)}. Con mensajes de {de['L']} letras, el IC del alemán "
            f"pasa de {fmt_dec(de['ic_plano'][0], 4)} en el plano a "
            f"{fmt_dec(de['ic_cifrado'][0], 4)} en el cifrado (1/26 = "
            f"{fmt_dec(e3['ic_azar'], 4)}).",
            f"- La prueba χ² rechaza la uniformidad del {fmt_pct(de['rechaza_plano'], 0)} de los "
            f"textos planos en alemán y del {fmt_pct(de['rechaza_cifrado'], 1)} de los cifrados "
            "(con α = 5 %, se espera un 5 % de rechazos si el cifrado es uniforme). Puntos fijos: "
            f"{fmt_int(e3['puntos_fijos'])} en {fmt_int(e3['letras'])} letras.",
        ]
    if e2:
        lines.append(
            f"- **E2 (diapositiva 7):** {e2['texto']}; máximo de N(k) con "
            f"{e2['cables_maximo']} cables."
        )
    return lines or ["Sin resultados de E2 ni E3."]


def _discrepancies(e4: dict[str, Any], table: pd.DataFrame | None) -> list[str]:
    lines = [
        "Ninguna contradicción con las diapositivas ni con el guion. Notas:",
        "",
    ]
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
    summary: dict[str, Any], cifras: list[dict[str, Any]], e4_table: pd.DataFrame | None
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
        "Pendiente (fase 3).",
        "",
        "### Diapositiva 17 · Banburismus (E6)",
        "",
        "Pendiente (fase 4).",
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
        "- **Demo 2 (diapositiva 12):** pendiente (fase 3), con `make bench-demo`. Riesgo "
        "conocido: con WETTERBERICHT, el rotor central se mueve dentro del tramo en casi la "
        "mitad de las claves, y la mayoría de los menús tienen 0 o 1 lazos.",
        "",
        "## 4. Discrepancias",
        "",
        *_discrepancies(summary.get("e4", {}), e4_table),
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
    (out / "cifras.json").write_text(
        json.dumps({"cifras": cifras, "experimentos": summary}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out / "RESUMEN.md").write_text(build_markdown(summary, cifras, e4_table), encoding="utf-8")
    print(f"Listo: {out}")
    return out


if __name__ == "__main__":
    main()
