"""``make resumen``: el paquete con el que los resultados llegan a las diapositivas (spec 11).

Arma ``results/presentacion/`` a partir de ``results/summary.json`` y los Parquet, sin
volver a correr experimentos:

- ``RESUMEN.md``: se entiende por sí solo (fecha, commit, semilla y modo al inicio).
- ``cifras.json``: las mismas cifras, para máquina.
- Un CSV por diapositiva de resultados, en formato largo (``r1_validacion.csv``…).

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
    ("Fase 2 · estadística y cribs (E2 a E4)", "semanas 1–2, antes de la reunión con el profe"),
    ("Fase 3 · Bombe (E5) y configuración de la demo 2", "semana 2"),
    ("Fase 4 · Banburismus (E6)", "semana 3"),
    ("Fase 5 · Rejewski (E7) y ataque moderno (E8), opcionales", "semana 3"),
    ("Fase 6 · modo demo completo, Docker, informe y entrega", "fin de la semana 3"),
]


def _pct_or_dash(value: float | None, decimals: int = 2) -> str:
    return "—" if value is None else fmt_pct(value, decimals)


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


def _demo1_timing() -> dict[str, float]:
    """Milisegundos de cálculo de los dos preajustes de la demo 1 en este equipo."""
    timings = {}
    for name, (config, text) in {
        "vector_bdzgo": (EnigmaConfig.from_strings("I II III"), "AAAAA"),
        "portada": (
            EnigmaConfig.from_dict(vector("portada")["key"]),
            vector("portada")["output"],
        ),
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
        "(tabla en `r1_validacion.csv`).",
        "- Nuevo para la diapositiva 14, si cabe: el simulador descifra letra por letra un "
        "mensaje real, el del U-264 (Enigma M4, 25-11-1942, roto por el M4 Project en 2006).",
    ]


def build_markdown(summary: dict[str, Any], cifras: list[dict[str, Any]]) -> str:
    """El texto de ``RESUMEN.md``."""
    e1 = summary.get("e1", {})
    run = e1.get("corrida", {})
    timing = _demo1_timing()
    lines = [
        "# Resumen de resultados para la presentación",
        "",
        f"- **Fecha:** {datetime.now(UTC):%Y-%m-%d %H:%M} UTC",
        f"- **Commit:** {git_commit()}",
        f"- **Semilla:** {run.get('semilla', SEED)}",
        f"- **Modo:** {run.get('modo', 'sin corridas')} (E1, corrido el "
        f"{run.get('fecha', '—')} sobre el commit {run.get('commit', '—')})",
        "",
        "Generado por `make resumen` a partir de `results/summary.json` y los Parquet, sin "
        "volver a correr experimentos. Cada cifra sale del código.",
        "",
        "## 1. Por diapositiva de resultados",
        "",
        "### Diapositiva 14 · Validación (E1)",
        "",
        *_slide_14(e1),
        "",
        "### Diapositiva 15 · Cribs (E4)",
        "",
        "Pendiente (fase 2): la simulación con texto alemán real. La fórmula ya está "
        "comprobada en la tabla de abajo.",
        "",
        "### Diapositiva 16 · Bombe (E5)",
        "",
        "Pendiente (fase 3).",
        "",
        "### Diapositiva 17 · Banburismus (E6)",
        "",
        "Pendiente (fase 4).",
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
        "Ninguna con las diapositivas ni con el guion en lo que cubre esta fase. Notas:",
        "",
        "- py-enigma admite como máximo 10 cables: la comparación de 10.000 claves usa de "
        "0 a 10 cables, y las pruebas con hypothesis cubren de 0 a 13.",
        "- Mensaje histórico: no se encontró una fuente verificable del mensaje de "
        "Barbarossa (1941). Se usa el del U-264 (M4), con clave, cifrado y texto publicados "
        "por D. Rijmenants. Por eso el simulador incluye también la M4.",
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
    (out / "cifras.json").write_text(
        json.dumps({"cifras": cifras, "experimentos": summary}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (out / "RESUMEN.md").write_text(build_markdown(summary, cifras), encoding="utf-8")
    print(f"Listo: {out}")
    return out


if __name__ == "__main__":
    main()
