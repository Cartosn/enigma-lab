"""Cada cifra de la presentación, comprobada contra el código (spec, sección 11.3).

Las diapositivas redondean. Aquí se compara lo que imprime el código, con el formato
español de ``enigma_lab.viz.numfmt``, contra la cifra de la tabla 11.3 del spec y
contra la que aparece en la diapositiva. Las cifras de módulos que aún no existen
quedan marcadas como pendientes, con la fase en que llegan: ``pytest -ra`` las lista.
"""

from __future__ import annotations

import pytest

from enigma_lab.core import keyspace as ks
from enigma_lab.viz.numfmt import NBSP, fmt_dec, fmt_int, fmt_pct, fmt_sci

SPACE = ks.keyspace(ks.ENIGMA_I, cables=10)
BITS = SPACE.component_bits()
YEARS = ks.brute_force_years(SPACE.total_without_rings, tests_per_second=1e9)

# (diapositivas, cifra, valor que da el código, valor esperado)
KEYSPACE_FIGURES = [
    (
        "2, 7, 20",
        "claves sin anillos",
        fmt_int(SPACE.total_without_rings),
        "158.962.555.217.826.360.000",
    ),
    (
        "2, 7, 20",
        "claves sin anillos, redondeado",
        fmt_sci(SPACE.total_without_rings, 2),
        "1,6 × 10²⁰",
    ),
    ("7, 8", "bits sin anillos", fmt_dec(ks.bits(SPACE.total_without_rings)), "67,11"),
    ("7", "claves con anillos", fmt_sci(SPACE.total_with_rings, 5), "1,0746 × 10²³"),
    ("7", "claves con anillos, redondeado", fmt_sci(SPACE.total_with_rings, 3), "1,07 × 10²³"),
    ("7", "bits con anillos", fmt_dec(ks.bits(SPACE.total_with_rings)), "76,51"),
    ("7", "bits del orden de rotores", fmt_dec(BITS["orders"]), "5,91"),
    ("7", "bits de las posiciones", fmt_dec(BITS["positions"]), "14,10"),
    ("7", "bits de los anillos", fmt_dec(BITS["rings"]), "9,40"),
    ("7", "bits del plugboard", fmt_dec(BITS["plugboard"]), "47,10"),
    (
        "7",
        "fracción del plugboard en los 67,11 bits",
        fmt_pct(SPACE.plugboard_share),
        f"70,2{NBSP}%",
    ),
    ("8, 20", "configuraciones que barre la Bombe", fmt_int(SPACE.bombe_sweep), "1.054.560"),
    ("8, 20", "bits del barrido de la Bombe", fmt_dec(ks.bits(SPACE.bombe_sweep)), "20,01"),
    ("7", "años de fuerza bruta a 10⁹ claves por segundo", fmt_int(round(YEARS)), "5.037"),
]


@pytest.mark.parametrize(
    ("slides", "figure", "obtained", "expected"),
    KEYSPACE_FIGURES,
    ids=[f"diap {s}: {f}" for s, f, _, _ in KEYSPACE_FIGURES],
)
def test_keyspace_figures(slides: str, figure: str, obtained: str, expected: str) -> None:
    assert obtained == expected, f"diapositivas {slides}, {figure}"


def _pending(slides: str, figure: str, phase: str) -> pytest.ParameterSet:
    return pytest.param(slides, figure, marks=pytest.mark.skip(reason=phase), id=f"diap {slides}")


PENDING = [
    _pending(
        "3, 5, 14",
        "periodo 16.900; 676 fuera del ciclo; ADU → ADV → AEW → BFX",
        "fase 1: core/stepping.py",
    ),
    _pending(
        "1, 4",
        "vectores de 6.1: mensaje de la portada y traza de la letra A",
        "fase 1: core/machine.py",
    ),
    _pending(
        "6",
        "(25/26)¹⁰⁰ = 1,98 %; involución en 2.000 claves; 0 puntos fijos en 200.000",
        "fases 1 y 2: core/ y E3",
    ),
    _pending("9", "Kuhl: 105.456 · 21.230 · 11.466", "fase 5 (P2): rejewski/; si no, cita a Kuhl"),
    _pending("10, 11", "casos deterministas de 6.5 (arrastre y menú)", "fase 2: cribs/"),
    _pending(
        "13, 17",
        "+1,845 dB; +0,0211 y −0,0184 dB; ±19,96 dB; 929 y 1.062 letras",
        "fase 4: banburismus/",
    ),
    _pending("15", "(25/26)¹³ = 60,1 %; (25/26)⁵⁰ = 14,1 %", "fase 2: E4"),
    _pending(
        "16",
        "Turing, 12 letras: 820 · 31 · 1,2 · 0,04; 72 y 2,4 en 60 órdenes",
        "fase 3: turing_stops.csv y E5",
    ),
]


@pytest.mark.parametrize(("slides", "figure"), PENDING)
def test_pending_figures(slides: str, figure: str) -> None:  # pragma: no cover
    raise AssertionError("pendiente")
