"""La Bombe de referencia, en Python puro y lenta: solo para las pruebas.

Es independiente de la versión rápida en todo lo que importa:

- **El aleatorizador** sale de la máquina escalar (:meth:`Enigma.permutation`, con
  anillos AAA y sin plugboard), no de las tablas de ``scrambler.py``.
- **La corriente** se propaga como en la máquina real: se energiza un hilo y se siguen
  las conexiones (búsqueda en anchura) hasta que no se enciende nada nuevo. No usa
  union-find.
- **Los hilos aislados** se hallan energizando, uno por uno, los 26 hilos del cable de
  prueba.

``tests/test_bombe.py`` exige que dé exactamente lo mismo que :mod:`bombe_numba`.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterable

from enigma_lab.core.machine import Enigma, EnigmaConfig, clean
from enigma_lab.core.wiring import ALPHABET

Wire = tuple[str, int]  # (letra del cable, hilo 0–25)


def scrambler(order: tuple[str, str, str], reflector: str, core: tuple[int, int, int]) -> list[int]:
    """El aleatorizador en una posición del núcleo, con la máquina escalar."""
    machine = Enigma(EnigmaConfig(rotors=order, reflector=reflector, positions=core))
    return list(machine.permutation())


def edge_scramblers(
    order: tuple[str, str, str], reflector: str, position: int, turn: int, length: int
) -> list[list[int]]:
    """Sᵢ para cada paso i del crib: rotor derecho en C + i + 1 y, si i ≥ turn ≥ 1, central + 1."""
    left, middle, right = position // 676, (position // 26) % 26, position % 26
    perms = []
    for i in range(length):
        m = middle + 1 if 0 < turn <= i else middle
        perms.append(scrambler(order, reflector, (left, m % 26, (right + i + 1) % 26)))
    return perms


def energize(
    crib: str, cipher: str, perms: list[list[int]], start: Wire, diagonal: bool
) -> set[Wire]:
    """Los hilos que se encienden al energizar ``start`` (búsqueda en anchura).

    Del hilo u del cable a, la corriente pasa por cada arista (a, b, i) al hilo Sᵢ(u) del
    cable b, y, con el diagonal board, al hilo a del cable u si u es una letra del menú.
    """
    letters = set(crib) | set(cipher)
    links: dict[str, list[tuple[str, int]]] = {c: [] for c in letters}
    for i, (a, b) in enumerate(zip(crib, cipher, strict=True)):
        links[a].append((b, i))
        links[b].append((a, i))  # Sᵢ es una involución: sirve en los dos sentidos
    lit = {start}
    queue = deque([start])
    while queue:
        cable, u = queue.popleft()
        neighbours = [(other, perms[i][u]) for other, i in links[cable]]
        if diagonal and ALPHABET[u] in letters:
            neighbours.append((ALPHABET[u], ALPHABET.index(cable)))
        for wire in neighbours:
            if wire not in lit:
                lit.add(wire)
                queue.append(wire)
    return lit


def test_register(
    crib: str,
    cipher: str,
    perms: list[list[int]],
    test_letter: str,
    test_wire: int,
    diagonal: bool,
) -> tuple[int, int]:
    """(hilos encendidos en T al energizar el hilo de prueba, máscara de hilos aislados de T)."""
    lit = energize(crib, cipher, perms, (test_letter, test_wire), diagonal)
    count = sum(1 for cable, _ in lit if cable == test_letter)
    singles = 0
    if count < 26:
        for u in range(26):
            from_u = energize(crib, cipher, perms, (test_letter, u), diagonal)
            if sum(1 for cable, _ in from_u if cable == test_letter) == 1:
                singles |= 1 << u
    return count, singles


def sweep_positions(
    crib: str,
    cipher_segment: str,
    order: tuple[str, str, str],
    positions: Iterable[int],
    turns: Iterable[int] = (0,),
    test_letter: str = "",
    test_wire: str = "A",
    diagonal: bool = True,
    reflector: str = "B",
) -> dict[tuple[int, int], tuple[int, int]]:
    """La Bombe en las posiciones y variantes pedidas.

    Devuelve {(posición, variante): (hilos encendidos, máscara de aislados)}.
    """
    word, cipher = clean(crib), clean(cipher_segment)
    wire = ALPHABET.index(test_wire)
    result = {}
    for position in positions:
        for turn in turns:
            perms = edge_scramblers(order, reflector, position, turn, len(word))
            result[(position, turn)] = test_register(
                word, cipher, perms, test_letter, wire, diagonal
            )
    return result
