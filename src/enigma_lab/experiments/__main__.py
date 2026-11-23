"""Corre experimentos desde la consola.

python -m enigma_lab.experiments e1 --mode completo --seed 2026
python -m enigma_lab.experiments todos --mode rapido
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys

from enigma_lab import SEED, paths
from enigma_lab.experiments import EXPERIMENTS
from enigma_lab.experiments.common import MODES, output_dir


def main(argv: list[str] | None = None) -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(prog="python -m enigma_lab.experiments")
    parser.add_argument("experimento", choices=[*EXPERIMENTS, "todos"])
    parser.add_argument("--mode", choices=MODES, default="completo")
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args(argv)

    chosen = list(EXPERIMENTS) if args.experimento == "todos" else [args.experimento]
    for name in chosen:
        folder = output_dir(args.mode).relative_to(paths.ROOT).as_posix()
        print(
            f"== {name.upper()} · modo {args.mode} · semilla {args.seed} · guarda en {folder}/",
            flush=True,
        )
        module = importlib.import_module(EXPERIMENTS[name])
        figures = module.main(args.mode, args.seed)
        print(json.dumps(figures, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
