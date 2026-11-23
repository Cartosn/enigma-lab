"""El menú convertido en el cableado de la Bombe.

**Cables e hilos.** Cada letra del menú es un cable de 26 hilos. El hilo u del cable a
representa la hipótesis «en el plugboard, a va con u». Los cables se numeran en orden
alfabético de sus letras, y el hilo u del cable c es el nodo c · 26 + u.

**Conexiones.**
- *Aristas del menú.* La arista (a, b, i) dice que en el paso i del crib la máquina
  lleva la letra plana a a la cifrada b. Sin el plugboard: Sᵢ(P(a)) = P(b), con Sᵢ el
  aleatorizador de ese paso. Por eso el hilo u del cable a se une con el hilo Sᵢ(u)
  del cable b, para las 26 hipótesis u a la vez.
- *Diagonal board (Welchman).* El plugboard es simétrico: si P(a) = u, entonces
  P(u) = a. Une el hilo u del cable a con el hilo a del cable u. Solo importan los
  pares entre cables del menú: un cable sin aleatorizadores no lleva la corriente a
  ningún otro lado, así que lo que el diagonal board le conecta no cambia ninguna
  parada.

**Hilo de prueba.** Se energiza el hilo x del cable de la letra de prueba T. Por omisión
x = A: la hipótesis «T va con A». La elección de x no cambia en qué posiciones para la
Bombe, solo cómo se lee el stecker candidato (ver :mod:`enigma_lab.bombe.bombe_numba`).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from enigma_lab.core.machine import clean
from enigma_lab.core.wiring import ALPHABET
from enigma_lab.cribs.menu import build_menu, menu_stats


@dataclass(frozen=True)
class BombeWiring:
    """El cableado de un menú: lo que leen los núcleos de la Bombe.

    Attributes:
        letters: letras del menú en orden alfabético; la letra del cable c es letters[c].
        crib, cipher: el crib y el tramo de cifrado alineado con él.
        edge_a, edge_b, edge_offset: cable de la letra del crib, cable de la letra
            cifrada y paso i de cada arista (arreglos int64 de largo E).
        test_cable: cable de la letra de prueba T.
        test_wire: letra (0–25) del hilo que se energiza.
        diagonal: si el diagonal board está conectado.
        diag_a, diag_b: pares de nodos que une el diagonal board (vacíos si no está).
        cable_component: componente del menú (por aristas) de cada cable.
        component_cables: un cable representativo de cada componente.
    """

    letters: str
    crib: str
    cipher: str
    edge_a: np.ndarray
    edge_b: np.ndarray
    edge_offset: np.ndarray
    test_cable: int
    test_wire: int
    diagonal: bool
    diag_a: np.ndarray
    diag_b: np.ndarray
    cable_component: np.ndarray
    component_cables: np.ndarray

    @property
    def n_cables(self) -> int:
        return len(self.letters)

    @property
    def n_edges(self) -> int:
        return int(self.edge_a.shape[0])

    @property
    def test_letter(self) -> str:
        return self.letters[self.test_cable]

    @property
    def test_node(self) -> int:
        """Primer nodo del cable de prueba: sus hilos son test_node + u."""
        return self.test_cable * 26

    @property
    def letter_codes(self) -> np.ndarray:
        """La letra (0–25) de cada cable."""
        return np.array([ALPHABET.index(c) for c in self.letters], dtype=np.int64)

    @property
    def test_component(self) -> int:
        return int(self.cable_component[self.test_cable])

    @property
    def n_components(self) -> int:
        return int(self.component_cables.shape[0])


def _components(n_cables: int, edge_a: np.ndarray, edge_b: np.ndarray) -> np.ndarray:
    """Componente de cada cable en el grafo del menú (0, 1, … por orden de aparición)."""
    parent = list(range(n_cables))

    def find(x: int) -> int:
        while parent[x] != x:
            x = parent[x]
        return x

    for a, b in zip(edge_a, edge_b, strict=True):
        ra, rb = find(int(a)), find(int(b))
        parent[max(ra, rb)] = min(ra, rb)
    labels: dict[int, int] = {}
    return np.array([labels.setdefault(find(c), len(labels)) for c in range(n_cables)], np.int64)


def _diagonal_pairs(letters: str) -> tuple[np.ndarray, np.ndarray]:
    """Nodos que une el diagonal board: hilo b del cable a con hilo a del cable b (a < b)."""
    codes = [ALPHABET.index(c) for c in letters]
    first, second = [], []
    for c, a in enumerate(codes):
        for d in range(c + 1, len(codes)):
            first.append(c * 26 + codes[d])
            second.append(d * 26 + a)
    return np.array(first, dtype=np.int64), np.array(second, dtype=np.int64)


def wiring_from_menu(
    crib: str,
    cipher_segment: str,
    test_letter: str | None = None,
    test_wire: str = "A",
    diagonal: bool = True,
) -> BombeWiring:
    """El cableado del menú de un crib alineado con su tramo de cifrado.

    Args:
        crib, cipher_segment: misma longitud; ninguna letra del crib puede caer sobre
            la misma letra cifrada (sería un conflicto: la alineación es imposible).
        test_letter: letra de prueba; por omisión, la de :func:`menu_stats` (la de mayor
            grado en la componente con más lazos).
        test_wire: hilo que se energiza en el cable de prueba.
        diagonal: conectar o no el diagonal board.
    """
    word, cipher = clean(crib), clean(cipher_segment)
    if len(word) != len(cipher) or not word:
        raise ValueError("el crib y el tramo de cifrado deben tener la misma longitud")
    if any(p == c for p, c in zip(word, cipher, strict=True)):
        raise ValueError("la alineación tiene un conflicto: una letra cae sobre sí misma")
    letters = "".join(sorted(set(word) | set(cipher)))
    test = (test_letter or menu_stats(build_menu(word, cipher)).test_letter).upper()
    if test not in letters:
        raise ValueError(f"la letra de prueba {test} no está en el menú")
    diag_a, diag_b = _diagonal_pairs(letters) if diagonal else (np.empty(0, np.int64),) * 2
    edge_a = np.array([letters.index(c) for c in word], dtype=np.int64)
    edge_b = np.array([letters.index(c) for c in cipher], dtype=np.int64)
    component = _components(len(letters), edge_a, edge_b)
    return BombeWiring(
        letters=letters,
        crib=word,
        cipher=cipher,
        edge_a=edge_a,
        edge_b=edge_b,
        edge_offset=np.arange(len(word), dtype=np.int64),
        test_cable=letters.index(test),
        test_wire=ALPHABET.index(test_wire.upper()),
        diagonal=diagonal,
        diag_a=diag_a,
        diag_b=diag_b,
        cable_component=component,
        component_cables=np.array(
            [int(np.flatnonzero(component == k)[0]) for k in range(component.max() + 1)], np.int64
        ),
    )
