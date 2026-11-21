"""El paso de los rotores: doble paso, periodo del odómetro, rotores de dos muescas."""

from __future__ import annotations

from enigma_lab.core.machine import Enigma, EnigmaConfig
from enigma_lab.core.stepping import cycle_structure, notch_sets, step

I_II_III = notch_sets(["Q", "E", "V"])


def test_double_step_sequence() -> None:
    machine = Enigma(EnigmaConfig.from_strings("I II III", positions="ADU"))
    flags = []
    windows = [machine.window]
    for _ in range(4):
        flags.append(machine.step().double_step)
        windows.append(machine.window)
    assert windows == ["ADU", "ADV", "AEW", "BFX", "BFY"]
    assert flags == [False, False, True, False]


def test_odometer_period_i_ii_iii() -> None:
    lengths, off_cycle = cycle_structure(I_II_III)
    assert lengths == [16_900]  # 26 × 25 × 26: un solo ciclo
    assert off_cycle == 676


def test_right_rotor_always_steps() -> None:
    result = step((0, 0, 25), I_II_III)
    assert result.positions == (0, 0, 0)
    assert result.stepped == (False, False, True)


def test_two_notch_rotor_turns_over_at_z_and_m() -> None:
    """Los rotores VI–VIII arrastran al pasar por Z y por M."""
    notches = notch_sets(["Q", "E", "ZM"])
    for right in ("Z", "M"):
        r = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".index(right)
        assert step((0, 0, r), notches).stepped == (False, True, True)
    assert step((0, 0, 0), notches).stepped == (False, False, True)


def test_greek_rotor_never_steps() -> None:
    """En la M4 solo giran los tres rotores de la derecha."""
    config = EnigmaConfig.from_strings(
        "Beta II IV I", "B-Thin", "AAAV", "VJNA", "AT BL DF GJ HM NW OP QY RZ VX", model="M4"
    )
    machine = Enigma(config)
    for _ in range(26 * 26 + 5):
        assert not machine.step().stepped[0]
    assert machine.window[0] == "V"
