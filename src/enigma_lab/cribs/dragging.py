"""Arrastre del crib: dónde puede ir una palabra probable dentro del cifrado.

Un crib es un trozo de texto plano que se adivina (WETTERBERICHT, «parte
meteorológico»). No se sabe en qué posición del mensaje está, así que se desliza sobre
el cifrado. Como Enigma nunca cifra una letra en sí misma, toda alineación en la que una
letra del crib cae sobre la misma letra del cifrado es imposible: hay un **conflicto** y
se descarta.

Una alineación falsa sobrevive si ninguna de sus L letras choca. Si las letras del
cifrado fueran independientes y uniformes, cada letra chocaría con probabilidad 1/26,
así que sobreviviría con probabilidad (25/26)^L: el 60,1 % con L = 13 (diapositiva 15).
El filtro descarta algunas posiciones, no todas.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

from enigma_lab.core.machine import clean
from enigma_lab.stats.inference import no_fixed_point_probability


@dataclass(frozen=True)
class Alignment:
    """El crib puesto en la posición ``position`` del cifrado.

    ``conflicts`` son los índices j del crib con crib[j] = cifrado[position + j].
    """

    position: int
    conflicts: tuple[int, ...]

    @property
    def valid(self) -> bool:
        """Sin conflictos: la alineación es posible."""
        return not self.conflicts

    def conflict_positions(self) -> tuple[int, ...]:
        """Las posiciones del cifrado donde ocurren los conflictos."""
        return tuple(self.position + j for j in self.conflicts)


def alignments(ciphertext: str, crib: str) -> list[Alignment]:
    """Todas las alineaciones del crib sobre el cifrado, de la 0 a la len(cifrado) − L."""
    cipher, word = clean(ciphertext), clean(crib)
    if not word or len(word) > len(cipher):
        raise ValueError("el crib debe tener al menos una letra y no ser más largo que el cifrado")
    result = []
    for position in range(len(cipher) - len(word) + 1):
        conflicts = tuple(j for j, letter in enumerate(word) if cipher[position + j] == letter)
        result.append(Alignment(position, conflicts))
    return result


def valid_positions(ciphertext: str, crib: str) -> list[int]:
    """Las posiciones donde el crib no choca con el cifrado."""
    return [a.position for a in alignments(ciphertext, crib) if a.valid]


def survival_probability(length: int) -> float:
    """(25/26)^L: probabilidad de que una alineación falsa sobreviva, con letras al azar."""
    return no_fixed_point_probability(length)


def survives(cipher_codes: np.ndarray, crib_codes: np.ndarray) -> np.ndarray:
    """Qué alineaciones sobreviven, para un lote: (N, M) cifrados y (N, L) cribs → (N, M − L + 1).

    Versión vectorizada del arrastre, para el experimento E4.
    """
    windows = sliding_window_view(cipher_codes, crib_codes.shape[-1], axis=-1)
    clash = windows == crib_codes[:, None, :]
    return np.asarray(~clash.any(axis=-1))
