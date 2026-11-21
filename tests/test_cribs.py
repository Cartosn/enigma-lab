"""Cribs y menús: los casos deterministas de la sección 6.5 (diapositivas 10 y 11)."""

from __future__ import annotations

import json

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from enigma_lab import paths
from enigma_lab.core.wiring import ALPHABET
from enigma_lab.cribs.dragging import alignments, survives, valid_positions
from enigma_lab.cribs.menu import menu_at, menu_edges, menu_stats

SLIDE_CIPHER = "BBGCCKITCTTEZZZLCZ"
CRIB = "WETTERBERICHT"


def test_slide_10_dragging() -> None:
    """6 alineaciones; la 0 a la 3 sin conflictos; en la 4 y la 5 una T cae sobre la T de la 7."""
    result = alignments(SLIDE_CIPHER, CRIB)
    assert [a.position for a in result] == [0, 1, 2, 3, 4, 5]
    assert [a.valid for a in result] == [True, True, True, True, False, False]
    for a in result[4:]:
        assert 7 in a.conflict_positions()
        assert any(CRIB[j] == "T" and a.position + j == 7 for j in a.conflicts)
    assert valid_positions(SLIDE_CIPHER, CRIB) == [0, 1, 2, 3]


def test_slide_11_menu() -> None:
    """11 letras, 13 aristas, 1 componente y 3 lazos; letra de prueba T, de grado 6."""
    stats = menu_stats(menu_at(SLIDE_CIPHER, CRIB, 0))
    assert (stats.letters, stats.edges, stats.components, stats.loops) == (11, 13, 1, 3)
    assert (stats.test_letter, stats.test_degree) == ("T", 6)


def test_slide_11_loop_edges() -> None:
    """Los lazos: E–B–I–T, el triángulo E–C–T y las dos aristas entre T y C (pasos 3 y 10)."""
    edges = menu_edges(menu_at(SLIDE_CIPHER, CRIB, 0))
    in_loop = {(frozenset((e.a, e.b)), e.offset) for e in edges if e.in_loop}
    expected = {
        (frozenset("EB"), 1),
        (frozenset("BI"), 6),
        (frozenset("IT"), 9),
        (frozenset("ET"), 7),
        (frozenset("EC"), 4),
        (frozenset("TC"), 3),
        (frozenset("TC"), 10),
    }
    assert in_loop == expected


def test_backup_case_menu() -> None:
    """Caso de respaldo: 11 letras, 13 aristas y 3 lazos; letra de prueba T, de grado 4."""
    data = json.loads((paths.DEMO / "respaldo_bombe.json").read_text(encoding="utf-8"))
    stats = menu_stats(menu_at(data["ciphertext"], data["crib"], data["crib_position"]))
    expected = data["expected_menu"]
    assert (stats.letters, stats.edges, stats.loops) == (
        expected["letters"],
        expected["edges"],
        expected["loops"],
    )
    assert (stats.test_letter, stats.test_degree) == ("T", 4)


def test_crib_longer_than_cipher() -> None:
    with pytest.raises(ValueError):
        alignments("ABC", "ABCD")


@given(st.text(alphabet=ALPHABET, min_size=20, max_size=60), st.integers(1, 15), st.data())
def test_vectorized_survival_matches_scalar(cipher: str, length: int, data: st.DataObject) -> None:
    crib = data.draw(st.text(alphabet=ALPHABET, min_size=length, max_size=length))
    as_codes = np.frombuffer(cipher.encode(), np.uint8)[None, :] - 65
    crib_codes = np.frombuffer(crib.encode(), np.uint8)[None, :] - 65
    vector = survives(as_codes, crib_codes)[0].tolist()
    assert vector == [a.valid for a in alignments(cipher, crib)]
