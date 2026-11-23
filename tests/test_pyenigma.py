"""Sección 6.2: el simulador frente a py-enigma, una implementación independiente."""

from __future__ import annotations

import numpy as np
import pytest

from enigma_lab import SEED
from enigma_lab.core.machine import EnigmaConfig
from enigma_lab.experiments.e1_validation import compare_with_pyenigma, pyenigma_encrypt


def test_pyenigma_documentation_example() -> None:
    config = EnigmaConfig.from_strings(
        "II IV V", "B", "BUL", "WXC", "AV BS CG DL FU HZ IN KM OW RX"
    )
    assert pyenigma_encrypt(config, "KCH") == "BLA"


def test_quick_sample_matches_pyenigma() -> None:
    df = compare_with_pyenigma(300, np.random.default_rng(SEED))
    assert df["coincide"].all()
    assert set(df["modelo"]) == {"I", "M3", "M4"}


@pytest.mark.lento
def test_10000_random_keys_match_pyenigma() -> None:
    """La meta: 100 % de coincidencia en 10.000 claves y mensajes aleatorios."""
    df = compare_with_pyenigma(10_000, np.random.default_rng(SEED).spawn(2)[0])
    mismatches = df[~df["coincide"]]
    assert mismatches.empty, mismatches.head().to_string()
    assert df["puntos_fijos"].sum() == 0
    assert df["involucion"].all()
