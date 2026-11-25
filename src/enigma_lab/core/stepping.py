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

**La ρ.** Como toda función de un conjunto finito en sí mismo, el paso iterado termina en
un ciclo, y las posiciones de fuera forman una cola que cae en él: la figura del método
rho (:func:`rho_structure`). El doble paso hace que el paso no sea inyectivo: 650
posiciones del ciclo tienen dos predecesoras, y de ellas cuelga la cola de 676.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

Position = tuple[int, ...]

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


def _successors(notches: Sequence[frozenset[int]]) -> dict[Position, Position]:
    """El paso como tabla: cada una de las 26³ posiciones de tres rotores, con su siguiente."""
    triples = [(a, b, c) for a in range(26) for b in range(26) for c in range(26)]
    return {t: step(t, notches).positions for t in triples}


def _cycle_positions(successor: dict[Position, Position]) -> set[Position]:
    """Las posiciones que están en algún ciclo.

    Son las que sobreviven a aplicar la función una y otra vez a todo el conjunto: cada
    vuelta descarta las posiciones a las que ya no llega nadie.
    """
    alive = set(successor)
    while True:
        image = {successor[t] for t in alive}
        if image == alive:
            return alive
        alive = image


def cycle_structure(notches: Sequence[frozenset[int]]) -> tuple[list[int], int]:
    """Ciclos del odómetro de tres rotores: (largos de los ciclos, posiciones fuera de ellos).

    El paso es una función de las 26³ posiciones en sí mismas. Toda trayectoria cae
    tarde o temprano en un ciclo. Las posiciones fuera de los ciclos son estados de los
    que se sale para no volver: con I-II-III son 676, y el ciclo tiene 16.900 posiciones
    (``tests/test_stepping.py``).
    """
    successor = _successors(notches)
    triples = list(successor)
    alive = _cycle_positions(successor)

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


@dataclass(frozen=True)
class Rho:
    """La forma de ρ del paso: el ciclo, la cola que cae en él y las colisiones.

    - ``cycle``: posiciones que están en algún ciclo (16.900 con I-II-III);
    - ``tail``: posiciones de la cola, por pasos que les faltan para entrar al ciclo
      (con I-II-III, 650 a un paso y 26 a dos: {1: 650, 2: 26});
    - ``in_degree``: posiciones del ciclo según cuántas predecesoras tienen. Con I-II-III,
      16.250 tienen una y 650 tienen dos: una en el ciclo y otra en la cola.
    """

    cycle: int
    tail: dict[int, int]
    in_degree: dict[int, int]

    @property
    def collisions(self) -> int:
        """Posiciones del ciclo con dos o más predecesoras: donde el paso no es inyectivo."""
        return sum(count for degree, count in self.in_degree.items() if degree >= 2)


def rho_structure(notches: Sequence[frozenset[int]]) -> Rho:
    """La ρ del odómetro de tres rotores: cola, ciclo y colisiones (método rho).

    Iterar una función de un conjunto finito en sí mismo dibuja una ρ: una cola que
    entra a un ciclo y no vuelve. El método rho busca colisiones con esa figura (dos
    entradas distintas con la misma salida); aquí la colisión la pone el doble paso.
    Con I-II-III y el central en su muesca (posiciones ·E·), la máquina avanza el central
    y el izquierdo a la vez, así que, para R distinta de V, (L, E, R) y (L + 1, F, R)
    llevan a la misma posición (L + 1, F, R + 1). A (L, E, R) solo se llega desde
    (L, D, V), que da R = W, así que las otras 650 posiciones (L, E, R) no tienen
    predecesora. Las 26 con R = V caen primero en (L + 1, F, W), que solo se alcanza desde
    ellas, y entran al ciclo al segundo paso; las demás, al primero. La cola tiene así
    650 + 26 = 676 posiciones, 650 a un paso del ciclo y 26 a dos, y el ciclo tiene 650
    colisiones (``tests/test_stepping.py``).
    """
    successor = _successors(notches)
    cycle = _cycle_positions(successor)
    tail: Counter[int] = Counter()
    for start in successor:
        steps, state = 0, start
        while state not in cycle:
            state = successor[state]
            steps += 1
        if steps:
            tail[steps] += 1
    predecessors = Counter(successor.values())
    in_degree = Counter(predecessors[position] for position in cycle)
    return Rho(len(cycle), dict(sorted(tail.items())), dict(sorted(in_degree.items())))
