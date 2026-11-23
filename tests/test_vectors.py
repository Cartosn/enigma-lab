"""Vectores de prueba: deben pasar siempre."""

from __future__ import annotations

import json

import pytest

from enigma_lab import paths
from enigma_lab.core import vectors
from enigma_lab.core.machine import Enigma, EnigmaConfig, encrypt

ALL = vectors.load_vectors()


@pytest.mark.parametrize("v", ALL, ids=[v["id"] for v in ALL])
def test_vector(v: dict) -> None:
    result = vectors.check(v)
    assert result.ok, f"{result.label}: esperado {result.expected}, obtenido {result.obtained}"


def test_all_section_61_vectors_present() -> None:
    ids = {v["id"] for v in ALL}
    expected = {"bdzgo", "ewtyx", "doble_paso", "py_enigma", "odometro", "traza_a", "portada"}
    assert expected | {"respaldo_bombe", "m4_u264"} <= ids


def test_trace_of_first_letter_matches_slide_4() -> None:
    """Plugboard A → III C → II D → I F → reflector S → I S → II E → III B → plugboard B."""
    trace = Enigma(EnigmaConfig.from_strings("I II III")).trace("A")[0]
    labels = [f"{s.label} {s.letter}" for s in trace.stages[1:-1]]
    assert labels == [
        "Plugboard A",
        "Rotor III C",
        "Rotor II D",
        "Rotor I F",
        "Reflector B S",
        "Rotor I S",
        "Rotor II E",
        "Rotor III B",
        "Plugboard B",
    ]
    assert (trace.positions_before, trace.positions) == ("AAA", "AAB")
    assert trace.stepped == (False, False, True)


@pytest.mark.parametrize("name", ["portada.json", "respaldo_bombe.json"])
def test_demo_files_agree_with_vectors(name: str) -> None:
    """Los casos de data/demo/ cifran bien."""
    data = json.loads((paths.DEMO / name).read_text(encoding="utf-8"))
    config = EnigmaConfig.from_dict(data["key"])
    assert encrypt(config, data["plaintext"]) == data["ciphertext"]
    assert encrypt(config, data["ciphertext"]) == data["plaintext"]


def test_backup_case_has_78_letters() -> None:
    data = json.loads((paths.DEMO / "respaldo_bombe.json").read_text(encoding="utf-8"))
    assert len(data["plaintext"]) == 78
    assert data["plaintext"].startswith(data["crib"])
