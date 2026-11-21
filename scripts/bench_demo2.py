"""Banco de la demo 2 (diapositiva 12): ¿qué configuración rompe a tiempo un cifrado?

Simula casos de compañero como los describe el guion:

- clave como la de «Clave aleatoria» de la página Máquina: Enigma I, reflector B, rotores
  distintos de los permitidos, anillos y posición al azar y 10 cables;
- un mensaje alemán de 78 letras (como el caso de respaldo) que empieza por el crib, con la
  X como separador;
- el crib en la posición 0.

Para cada configuración corre el flujo completo de la página La Bombe: barrido, máquina de
verificación y verificador. Mide el éxito (el texto descifrado es el mensaje, letra por
letra) y el tiempo total (p50 y p95). Configuraciones:

1. ``60_robusto``: los 60 órdenes (rotores I a V) en modo robusto, crib WETTERBERICHT.
2. ``6_robusto``: rotores I, II y III (6 órdenes) en modo robusto, crib WETTERBERICHT. El
   compañero elige sus rotores entre I, II y III.
3. ``crib_largo``: crib acordado más largo, WETTERBERICHTXFUER (18 letras), 60 órdenes en
   modo robusto.

Recomienda la más simple (en ese orden) con éxito de al menos 95 % y p95 de 30 s o menos, y
guarda todo en ``results/bench_demo2.json``; ``make resumen`` lo lleva a «Demos» de
``RESUMEN.md``, con el equipo en que se midió.

Uso:  make bench-demo            (30 casos por configuración)
      uv run python scripts/bench_demo2.py --n 30 --configs 6_robusto
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import numpy as np

from enigma_lab import SEED, paths
from enigma_lab.bombe import checker
from enigma_lab.bombe.cases import DEMO_CRIB, demo_case
from enigma_lab.bombe.scrambler import ENIGMA_I_ROTORS, rotor_orders
from enigma_lab.bombe.sweep import BombeSettings, run_bombe, true_stop, warm_up
from enigma_lab.bombe.wiring import wiring_from_menu
from enigma_lab.cribs.menu import build_menu, menu_stats
from enigma_lab.experiments.common import git_commit
from enigma_lab.stats.inference import wilson_interval

BUDGET_SECONDS = 30.0
MIN_SUCCESS = 0.95
OUTPUT = paths.RESULTS / "bench_demo2.json"


@dataclass(frozen=True)
class DemoConfig:
    """Una configuración de la demo 2: qué rotores elige el compañero, el crib y el modo."""

    key: str
    name: str
    rotors: tuple[str, ...]
    crib: str
    mode: str = "robusto"

    @property
    def orders(self) -> int:
        return len(rotor_orders(self.rotors))


CONFIGS = (
    DemoConfig("60_robusto", "60 órdenes, modo robusto", ENIGMA_I_ROTORS, DEMO_CRIB),
    DemoConfig(
        "6_robusto", "Rotores I, II y III (6 órdenes), modo robusto", ("I", "II", "III"), DEMO_CRIB
    ),
    DemoConfig(
        "crib_largo",
        "Crib WETTERBERICHTXFUER, 60 órdenes, modo robusto",
        ENIGMA_I_ROTORS,
        "WETTERBERICHTXFUER",
    ),
)


def run_case(config: DemoConfig, rng: np.random.Generator) -> dict[str, Any]:
    """Un caso de compañero con el flujo completo de la página La Bombe."""
    case = demo_case(rng, config.rotors, config.crib)
    wiring = wiring_from_menu(case.crib, case.cipher_segment)
    stats = menu_stats(build_menu(case.crib, case.cipher_segment))
    settings = BombeSettings(orders=tuple(rotor_orders(config.rotors)), mode=config.mode)  # type: ignore[arg-type]
    start = time.perf_counter()
    run = run_bombe(wiring, settings)
    swept = time.perf_counter()
    hypotheses = checker.consistent_stops(wiring, run.runs, settings.reflector)
    verification = checker.verify(run, case.ciphertext, 0, hypotheses=hypotheses)
    end = time.perf_counter()
    best = verification.best
    expected = true_stop(case.config, 0, len(case.crib))
    return {
        "exito": best is not None and best.plaintext == case.plaintext,
        "plausible": verification.plausible,
        "segundos": end - start,
        "segundos_barrido": swept - start,
        "segundos_verificacion": end - swept,
        "paradas": run.n_stops,
        "hipotesis": len(hypotheses),
        "lazos": stats.loops,
        "componentes": stats.components,
        "vuelta_en_el_crib": expected is None or expected[1] > 0,
        "cubierta": expected is not None,
        "clave": case.config.describe(),
    }


def summarize(config: DemoConfig, cases: list[dict[str, Any]]) -> dict[str, Any]:
    """Éxito con su IC de Wilson y tiempos p50 y p95 de una configuración."""
    wins = sum(c["exito"] for c in cases)
    low, high = wilson_interval(wins, len(cases))
    total = np.array([c["segundos"] for c in cases])
    sweep = np.array([c["segundos_barrido"] for c in cases])
    summary = {
        "id": config.key,
        "nombre": config.name,
        "rotores": " ".join(config.rotors),
        "ordenes": config.orders,
        "crib": config.crib,
        "modo": config.mode,
        "n": len(cases),
        "exitos": int(wins),
        "exito": wins / len(cases),
        "exito_ic": [low, high],
        "p50": float(np.percentile(total, 50)),
        "p95": float(np.percentile(total, 95)),
        "p50_barrido": float(np.percentile(sweep, 50)),
        "p95_barrido": float(np.percentile(sweep, 95)),
        "maximo": float(total.max()),
        "no_cubiertos": int(sum(not c["cubierta"] for c in cases)),
        "casos": cases,
    }
    summary["cumple"] = summary["exito"] >= MIN_SUCCESS and summary["p95"] <= BUDGET_SECONDS
    return summary


def machine() -> dict[str, Any]:
    """El equipo donde se midió (P-001: la demo se hará en el portátil del autor)."""
    return {
        "nodo": platform.node(),
        "procesador": platform.processor() or platform.machine(),
        "nucleos_logicos": os.cpu_count(),
        "sistema": f"{platform.system()} {platform.release()}",
        "python": platform.python_version(),
    }


def main(argv: list[str] | None = None) -> dict[str, Any]:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(prog="scripts/bench_demo2.py")
    parser.add_argument("--n", type=int, default=30, help="casos por configuración")
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--configs", nargs="*", default=[c.key for c in CONFIGS])
    args = parser.parse_args(argv)

    print("Precalentando la Bombe…", flush=True)
    warm_up(all_tables=True)
    results = []
    for config in (c for c in CONFIGS if c.key in args.configs):
        rng = np.random.default_rng([args.seed, CONFIGS.index(config)])
        cases = []
        for k in range(args.n):
            case = run_case(config, rng)
            cases.append(case)
            mark = "ok" if case["exito"] else "FALLA"
            print(
                f"{config.key} {k + 1:>3}/{args.n}: {mark:5} {case['segundos']:6.1f} s "
                f"(barrido {case['segundos_barrido']:.1f} s) · {case['lazos']} lazos · "
                f"{case['paradas']} paradas",
                flush=True,
            )
        summary = summarize(config, cases)
        results.append(summary)
        print(
            f"== {config.name}: éxito {summary['exitos']}/{summary['n']}, p50 "
            f"{summary['p50']:.1f} s, p95 {summary['p95']:.1f} s\n",
            flush=True,
        )
    recommended = next((r["id"] for r in results if r["cumple"]), None)
    report = {
        "fecha": datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
        "commit": git_commit(),
        "semilla": args.seed,
        "equipo": machine(),
        "letras_mensaje": 78,
        "criterio": f"la más simple con éxito ≥ {MIN_SUCCESS:.0%} y p95 ≤ {BUDGET_SECONDS:.0f} s",
        "configuraciones": results,
        "recomendada": recommended,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Recomendada: {recommended or 'ninguna cumple'} · guardado en {OUTPUT}")
    return report


if __name__ == "__main__":
    main()
