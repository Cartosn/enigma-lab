"""El entorno de la sección 3 del spec: Python 3.12 y las bibliotecas obligatorias."""

from __future__ import annotations

import sys

import numpy as np
from numba import njit

from enigma_lab import SEED, paths


def test_python_version() -> None:
    assert sys.version_info[:2] == (3, 12)


def test_numba_compiles() -> None:
    """Numba compila en esta máquina (los bucles de la Bombe dependerán de esto)."""

    @njit(cache=False)
    def total(values: np.ndarray) -> int:
        acc = 0
        for v in values:
            acc += v
        return acc

    assert total(np.arange(26, dtype=np.int64)) == 325


def test_seeded_generator_is_reproducible() -> None:
    a = np.random.default_rng(SEED).integers(0, 26, size=10)
    b = np.random.default_rng(SEED).integers(0, 26, size=10)
    assert (a == b).all()


def test_paths_point_to_the_repository() -> None:
    assert (paths.ROOT / "pyproject.toml").is_file()
    assert (paths.DOCS / "PROGRESS.md").is_file()
