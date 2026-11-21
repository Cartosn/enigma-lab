"""Formato español de números."""

from __future__ import annotations

import pytest

from enigma_lab.viz.numfmt import MINUS, NBSP, fmt_dec, fmt_int, fmt_pct, fmt_sci


@pytest.mark.parametrize(
    ("value", "expected"),
    [(0, "0"), (999, "999"), (1_054_560, "1.054.560"), (-17_576, f"{MINUS}17.576")],
)
def test_fmt_int(value: int, expected: str) -> None:
    assert fmt_int(value) == expected


@pytest.mark.parametrize(
    ("value", "decimals", "expected"),
    [
        (67.107, 2, "67,11"),
        (0.0211, 4, "0,0211"),
        (-0.0930, 3, f"{MINUS}0,093"),
        (-0.0001, 2, "0,00"),  # sin «−0,00»
        (12345.678, 1, "12.345,7"),
    ],
)
def test_fmt_dec(value: float, decimals: int, expected: str) -> None:
    assert fmt_dec(value, decimals) == expected


def test_fmt_pct() -> None:
    assert fmt_pct(0.70185) == f"70,2{NBSP}%"
    assert fmt_pct(0.0198, 2) == f"1,98{NBSP}%"


@pytest.mark.parametrize(
    ("value", "digits", "expected"),
    [
        (1.5896e20, 2, "1,6 × 10²⁰"),
        (1.07459e23, 5, "1,0746 × 10²³"),
        (9.96e2, 2, "1,0 × 10³"),  # el redondeo sube el exponente
        (2.5e-3, 2, "2,5 × 10⁻³"),
    ],
)
def test_fmt_sci(value: float, digits: int, expected: str) -> None:
    assert fmt_sci(value, digits) == expected
