"""EnigmaConfig: lectura de hojas de claves y validación."""

from __future__ import annotations

import pytest

from enigma_lab.core.machine import EnigmaConfig, clean, groups_of_five, parse_settings


def test_ring_notations_are_equivalent() -> None:
    by_letters = EnigmaConfig.from_strings("II IV V", rings="BUL")
    by_spaced = EnigmaConfig.from_strings("II IV V", rings="B U L")
    by_numbers = EnigmaConfig.from_strings("II IV V", rings="02 21 12")
    assert by_letters == by_spaced == by_numbers
    assert by_letters.rings == (1, 20, 11)


def test_plugboard_is_canonical() -> None:
    a = EnigmaConfig.from_strings("I II III", plugboard="va SB")
    b = EnigmaConfig.from_strings("I II III", plugboard="AV BS")
    assert a == b
    assert a.plugboard_string == "AV BS"


def test_round_trip_through_dict() -> None:
    config = EnigmaConfig.from_strings("II IV V", "B", "BUL", "WXC", "AV BS CG")
    assert EnigmaConfig.from_dict(config.to_dict()) == config


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"rotors": "I I II"}, "distintos"),
        ({"rotors": "I II VI"}, "no tiene el rotor"),
        ({"rotors": "I II"}, "lleva 3 rotores"),
        ({"rotors": "I II III", "reflector": "B-Thin"}, "no usa el reflector"),
        ({"rotors": "I II III", "plugboard": "AB AC"}, "un solo cable"),
        ({"rotors": "I II III", "plugboard": "AA"}, "un solo cable"),
        ({"rotors": "II IV V", "model": "M4"}, "lleva 4 rotores"),
        ({"rotors": "I II III IV", "model": "M4", "reflector": "B-Thin"}, "Beta o Gamma"),
    ],
)
def test_invalid_configs(kwargs: dict, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        EnigmaConfig.from_strings(**kwargs)


def test_invalid_settings() -> None:
    with pytest.raises(ValueError):
        parse_settings("AB", 3)
    with pytest.raises(ValueError):
        parse_settings("00 01 02", 3)


def test_clean_and_groups() -> None:
    assert clean("Romper Enigma 2026!") == "ROMPERENIGMA"
    with pytest.raises(ValueError):
        clean("Ñandú", strict=True)
    assert groups_of_five("LGNEVYPYZQDVKES") == "LGNEV YPYZQ DVKES"
