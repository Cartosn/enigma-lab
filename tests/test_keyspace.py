"""Espacio de claves: las cifras exactas."""

from __future__ import annotations

import math

import pytest
from hypothesis import given
from hypothesis import strategies as st

from enigma_lab.core import keyspace as ks


def test_plugboard_exact_counts() -> None:
    assert ks.plugboard_settings(0) == 1
    assert ks.plugboard_settings(1) == 325  # C(26, 2)
    assert ks.plugboard_settings(6) == 100_391_791_500
    assert ks.plugboard_settings(10) == 150_738_274_937_250
    assert ks.plugboard_settings(11) == 205_552_193_096_250
    assert ks.plugboard_settings(13) == 7_905_853_580_625  # 25!! = 25 · 23 · … · 1


def test_plugboard_maximum_is_eleven_cables() -> None:
    assert ks.best_cable_count() == 11
    assert ks.plugboard_settings(13) < ks.plugboard_settings(11)


@given(st.integers(min_value=1, max_value=13))
def test_plugboard_recurrence(k: int) -> None:
    """Agregar un cable: N(k) · k = N(k − 1) · C(26 − 2(k − 1), 2).

    De cada plugboard con k − 1 cables se elige una pareja nueva entre las letras
    libres; cada plugboard con k cables se obtiene así de k maneras distintas.
    """
    free = 26 - 2 * (k - 1)
    assert ks.plugboard_settings(k) * k == ks.plugboard_settings(k - 1) * math.comb(free, 2)


@pytest.mark.parametrize("cables", [-1, 14])
def test_plugboard_rejects_impossible_cable_counts(cables: int) -> None:
    with pytest.raises(ValueError):
        ks.plugboard_settings(cables)


def test_rotor_orders() -> None:
    assert ks.rotor_orders(ks.ENIGMA_I.n_rotors) == 60
    assert ks.rotor_orders(ks.M3.n_rotors) == 336


def test_enigma_i_totals() -> None:
    space = ks.keyspace(ks.ENIGMA_I, cables=10)
    assert space.positions == 17_576
    assert space.rings == 676
    assert space.total_without_rings == 158_962_555_217_826_360_000
    assert round(ks.bits(space.total_without_rings), 2) == 67.11
    assert f"{space.total_with_rings:.4e}" == "1.0746e+23"
    assert round(ks.bits(space.total_with_rings), 2) == 76.51


def test_bombe_sweep() -> None:
    space = ks.keyspace(ks.ENIGMA_I)
    assert space.bombe_sweep == 1_054_560
    assert round(ks.bits(space.bombe_sweep), 2) == 20.01


def test_component_bits_add_up() -> None:
    space = ks.keyspace(ks.ENIGMA_I)
    parts = space.component_bits()
    assert {k: round(v, 2) for k, v in parts.items()} == {
        "orders": 5.91,
        "positions": 14.10,
        "rings": 9.40,
        "plugboard": 47.10,
    }
    without_rings = parts["orders"] + parts["positions"] + parts["plugboard"]
    assert math.isclose(without_rings, ks.bits(space.total_without_rings))
    assert round(space.plugboard_share, 3) == 0.702


def test_brute_force_years() -> None:
    space = ks.keyspace(ks.ENIGMA_I)
    years = ks.brute_force_years(space.total_without_rings, 1e9)
    assert round(years) == 5_037


def test_brute_force_rejects_non_positive_rate() -> None:
    with pytest.raises(ValueError):
        ks.brute_force_years(10, 0)


def test_parallel_brute_force_divides_the_time() -> None:
    """Ataque paralelo: con 1.000 máquinas, 1.000 veces menos; unos 5,04 años."""
    keys = ks.keyspace(ks.ENIGMA_I).total_without_rings
    one = ks.brute_force_years(keys, 1e9)
    thousand = ks.brute_force_years(keys, 1e9, machines=1_000)
    assert math.isclose(thousand * 1_000, one)
    assert round(thousand, 2) == 5.04
    with pytest.raises(ValueError):
        ks.brute_force_years(keys, 1e9, machines=0)


def test_fixed_point_free_involutions_are_the_full_plugboards() -> None:
    """25!! = 7.905.853.580.625 = N(13): emparejar las 26 letras es poner los 13 cables."""
    assert ks.fixed_point_free_involutions() == 7_905_853_580_625
    assert ks.fixed_point_free_involutions() == ks.plugboard_settings(13)
    assert ks.permutations() == 403_291_461_126_605_635_584_000_000


def test_fixed_point_free_involutions_by_brute_force() -> None:
    """Para alfabetos pequeños, contar las permutaciones σ con σ(σ(x)) = x y σ(x) ≠ x."""
    from itertools import permutations

    for n in range(0, 9):
        found = sum(
            all(p[p[x]] == x and p[x] != x for x in range(n)) for p in permutations(range(n))
        )
        if n % 2:
            assert found == 0
            with pytest.raises(ValueError):
                ks.fixed_point_free_involutions(n)
        else:
            assert ks.fixed_point_free_involutions(n) == found
