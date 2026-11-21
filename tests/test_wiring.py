"""Cableados: permutaciones válidas, reflectores correctos y coincidencia con py-enigma."""

from __future__ import annotations

import pytest
from enigma.rotors import data as pyenigma_data  # py-enigma, implementación independiente

from enigma_lab.core import wiring


@pytest.mark.parametrize("name", list(wiring.ROTORS))
def test_rotor_is_a_permutation(name: str) -> None:
    assert sorted(wiring.permutation(wiring.ROTORS[name].wiring)) == list(range(26))


@pytest.mark.parametrize("name", list(wiring.REFLECTORS))
def test_reflector_is_involution_without_fixed_points(name: str) -> None:
    assert wiring.is_reflector(wiring.permutation(wiring.REFLECTORS[name]))


@pytest.mark.parametrize("name", list(pyenigma_data.ROTORS))
def test_rotors_match_pyenigma(name: str) -> None:
    theirs = pyenigma_data.ROTORS[name]
    ours = wiring.ROTORS[name]
    assert ours.wiring == theirs["wiring"]
    assert ours.notches == (theirs["stepping"] or "")


@pytest.mark.parametrize("name", list(pyenigma_data.REFLECTORS))
def test_reflectors_match_pyenigma(name: str) -> None:
    assert wiring.REFLECTORS[name] == pyenigma_data.REFLECTORS[name]


def test_models() -> None:
    assert wiring.MODELS["I"].rotors == ("I", "II", "III", "IV", "V")
    assert len(wiring.MODELS["M3"].rotors) == 8
    assert wiring.MODELS["M4"].n_rotors == 4


def test_letter_conversion() -> None:
    assert wiring.to_index("A") == 0 and wiring.to_index("z") == 25
    assert wiring.to_letter(27) == "B"
    with pytest.raises(ValueError):
        wiring.to_index("Ñ")
