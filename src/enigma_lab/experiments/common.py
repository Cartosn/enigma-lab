"""Piezas comunes de los experimentos: modos, guardado de resultados y figuras.

Toda corrida registra su semilla, su modo, la fecha y el commit, para que cada cifra
de ``results/summary.json`` se pueda reproducir.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

import pandas as pd

from enigma_lab import SEED, paths

Mode = Literal["rapido", "completo"]
MODES: tuple[Mode, ...] = ("rapido", "completo")


@dataclass(frozen=True)
class RunInfo:
    """Datos de una corrida: experimento, modo, semilla, fecha y commit."""

    experiment: str
    mode: Mode
    seed: int = SEED

    def as_dict(self) -> dict[str, Any]:
        return {
            "experimento": self.experiment,
            "modo": self.mode,
            "semilla": self.seed,
            "fecha": datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC"),
            "commit": git_commit(),
        }


def git_commit() -> str:
    """Commit corto del repositorio, o «sin commit» si no hay git."""
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=paths.ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
        # Los resultados (results/) son salidas: que cambien no ensucia el código.
        dirty = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=no", "--", ".", ":!results"],
            cwd=paths.ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return "sin commit"
    return out.stdout.strip() + ("+cambios" if dirty.stdout.strip() else "")


def save_table(df: pd.DataFrame, name: str, results_dir: Path | None = None) -> Path:
    """Guarda un resultado como Parquet en ``results/<name>.parquet``."""
    folder = results_dir or paths.RESULTS
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{name}.parquet"
    df.to_parquet(path, index=False)
    return path


def load_table(name: str, results_dir: Path | None = None) -> pd.DataFrame:
    """Lee ``results/<name>.parquet``."""
    return pd.read_parquet((results_dir or paths.RESULTS) / f"{name}.parquet")


def summary_path(results_dir: Path | None = None) -> Path:
    return (results_dir or paths.RESULTS) / "summary.json"


def read_summary(results_dir: Path | None = None) -> dict[str, Any]:
    """Cifras clave de todos los experimentos (vacío si aún no hay)."""
    path = summary_path(results_dir)
    if not path.is_file():
        return {}
    data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    return data


def update_summary(
    experiment: str, figures: dict[str, Any], info: RunInfo, results_dir: Path | None = None
) -> None:
    """Escribe las cifras de un experimento en ``results/summary.json`` sin tocar las demás."""
    data = read_summary(results_dir)
    data[experiment] = {"corrida": info.as_dict(), **figures}
    path = summary_path(results_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


PNG_DPI = 200
"""PNG a 2x: el doble de los 100 puntos por pulgada de la figura (spec 7)."""


def save_figure(fig: Any, name: str, results_dir: Path | None = None) -> list[Path]:
    """Guarda una figura de Matplotlib en PNG (a 2x), SVG y PDF en ``results/figures/``.

    La resolución y el recorte van explícitos: la figura se guarda fuera del bloque
    ``with`` del estilo, donde ya no rigen sus ``savefig.dpi`` y ``savefig.bbox`` (D-047).
    """
    folder = (results_dir or paths.RESULTS) / "figures"
    folder.mkdir(parents=True, exist_ok=True)
    saved = []
    for ext in ("png", "svg", "pdf"):
        path = folder / f"{name}.{ext}"
        fig.savefig(path, dpi=PNG_DPI, bbox_inches="tight")
        saved.append(path)
    return saved
