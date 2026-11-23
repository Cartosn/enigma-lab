"""El paso de los rotores: un odómetro con un tropiezo, el doble paso.

Antes de cifrar cada letra, el mecanismo hace avanzar los rotores. Solo giran los tres
de la derecha (en la M4, el rotor griego queda fijo). Con las ventanas (L, M, R):

- el rotor derecho avanza siempre;
- el central avanza si el derecho está en su muesca (arrastre normal) **o si el
  propio central está en su muesca**;
- el izquierdo avanza si el central está en su muesca.

La segunda regla del central es el **doble paso**. El trinquete que empuja al rotor
izquierdo engancha la muesca del central, y al empujar mueve a los dos. Por eso el
central puede avanzar en dos pulsaciones seguidas: ADU → ADV → AEW → BFX con los
rotores I-II-III. El odómetro ya no recorre las 26³ = 17.576 posiciones: con I-II-III
su ciclo tiene 26 × 25 × 26 = 16.900 y deja 676 posiciones fuera.

Las posiciones son letras de ventana (0–25). Las muescas van en el anillo, así que el
paso no depende del Ringstellung.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

N_STEPPING = 3
"""Rotores que giran: los tres de la derecha."""


@dataclass(frozen=True)
class StepResult:
    """Resultado de un paso: posiciones nuevas, qué rotores avanzaron y si hubo doble paso."""

    positions: tuple[int, ...]
    stepped: tuple[bool, ...]
    double_step: bool


def step(positions: Sequence[int], notches: Sequence[frozenset[int]]) -> StepResult:
    """Un paso del mecanismo, el que ocurre antes de cifrar cada letra.

    Args:
        positions: ventanas de izquierda a derecha (3 rotores, o 4 en la M4).
        notches: para cada rotor, las posiciones de ventana en las que arrastra.
    """
    *fixed, left, middle, right = positions
    middle_notches, right_notches = notches[-2], notches[-1]
    middle_at_notch = middle in middle_notches
    right_at_notch = right in right_notches
    step_left = middle_at_notch
    step_middle = middle_at_notch or right_at_notch
    new_positions = (
        *fixed,
        (left + step_left) % 26,
        (middle + step_middle) % 26,
        (right + 1) % 26,
    )
    stepped = (*(False for _ in fixed), step_left, step_middle, True)
    return StepResult(tuple(new_positions), stepped, double_step=middle_at_notch)


def notch_sets(notch_letters: Sequence[str]) -> tuple[frozenset[int], ...]:
    """Muescas en letras ("Q", "ZM", "") a conjuntos de posiciones 0–25."""
    return tuple(frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZ".index(c) for c in n) for n in notch_letters)


def cycle_structure(notches: Sequence[frozenset[int]]) -> tuple[list[int], int]:
    """Ciclos del odómetro de tres rotores: (largos de los ciclos, posiciones fuera de ellos).

    El paso es una función de las 26³ posiciones en sí mismas. Toda trayectoria cae
    tarde o temprano en un ciclo. Las posiciones que están en algún ciclo son las que
    sobreviven a aplicar la función una y otra vez a todo el conjunto. Las demás son
    estados de los que se sale para no volver: con I-II-III son 676, y el ciclo tiene
    16.900 posiciones (``tests/test_stepping.py``).
    """
    triples: list[tuple[int, ...]] = [
        (a, b, c) for a in range(26) for b in range(26) for c in range(26)
    ]
    successor = {t: step(t, notches).positions for t in triples}

    alive = set(triples)
    while True:
        image = {successor[t] for t in alive}
        if image == alive:
            break
        alive = image

    lengths, seen = [], set()
    for start in sorted(alive):
        if start in seen:
            continue
        length, state = 0, start
        while True:
            seen.add(state)
            state = successor[state]
            length += 1
            if state == start:
                break
        lengths.append(length)
    return sorted(lengths, reverse=True), len(triples) - len(alive)
