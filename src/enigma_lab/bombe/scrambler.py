"""El aleatorizador: Enigma sin plugboard, precalculado por orden de rotores.

La Bombe aparta el plugboard. Lo que queda de la máquina en cada pulsación es el
**aleatorizador**

    S = R⁻¹ · M⁻¹ · L⁻¹ · U · L · M · R,

que depende solo del orden de rotores y de su posición. Como el reflector U es una
involución sin puntos fijos, S también lo es. Con el plugboard P, la máquina completa
es E = P · S · P (P es su propia inversa).

**Posiciones del núcleo.** Un rotor actúa a través de s = ventana − anillo: el cableado
queda corrido s lugares (ver :mod:`enigma_lab.core.machine`). La Bombe busca esos tres
corrimientos con anillos supuestos AAA, así que una «posición» de la Bombe es una
posición del núcleo: con anillos AAA coincide con las ventanas. Hay 26³ = 17.576, y se
numeran

    índice = s_izq · 676 + s_cen · 26 + s_der.

Los anillos verdaderos los recupera el verificador (:mod:`enigma_lab.bombe.checker`).

``scrambler_table(orden)`` devuelve una tabla (17.576, 26): la fila de un índice es la
permutación S en esa posición. Se calcula una sola vez por orden con las tablas
``FORWARD``, ``BACKWARD`` y ``REFLECT`` de :mod:`enigma_lab.core.batch`.
"""

from __future__ import annotations

from collections.abc import Sequence
from functools import cache
from itertools import permutations

import numpy as np

from enigma_lab.core.batch import BACKWARD, FORWARD, REFLECT, REFLECTOR_NAMES, ROTOR_NAMES
from enigma_lab.core.wiring import ALPHABET

N_POSITIONS = 26**3
ENIGMA_I_ROTORS = ("I", "II", "III", "IV", "V")
Order = tuple[str, str, str]


def position_index(left: int, middle: int, right: int) -> int:
    """Índice de una posición del núcleo: s_izq · 676 + s_cen · 26 + s_der."""
    return (left % 26) * 676 + (middle % 26) * 26 + (right % 26)


def position_letters(index: int) -> str:
    """Índice a tres letras («KZY»), de izquierda a derecha."""
    return ALPHABET[index // 676] + ALPHABET[(index // 26) % 26] + ALPHABET[index % 26]


def parse_position(letters: str) -> int:
    """Tres letras («KZY») a índice."""
    if len(letters) != 3 or any(c not in ALPHABET for c in letters.upper()):
        raise ValueError(f"una posición son tres letras de la A a la Z: {letters!r}")
    left, middle, right = (ALPHABET.index(c) for c in letters.upper())
    return position_index(left, middle, right)


def rotor_orders(rotors: Sequence[str] = ENIGMA_I_ROTORS) -> list[Order]:
    """Los órdenes de tres rotores distintos: P(5, 3) = 60 con los rotores I a V."""
    return [(a, b, c) for a, b, c in permutations(rotors, 3)]


def order_label(order: Order) -> str:
    """«II-III-I»."""
    return "-".join(order)


@cache
def scrambler_table(order: Order, reflector: str = "B") -> np.ndarray:
    """S en las 17.576 posiciones del núcleo del orden dado: tabla (17.576, 26) uint8.

    La fila ``position_index(l, m, r)`` es la permutación S con los corrimientos
    (l, m, r): la imagen de la letra x es ``tabla[fila, x]``. La tabla es de solo
    lectura y queda en caché (unos 0,46 MB por orden).
    """
    left, middle, right = (ROTOR_NAMES.index(name) for name in order)
    index = np.arange(N_POSITIONS)
    s_left = (index // 676)[:, None]
    s_middle = ((index // 26) % 26)[:, None]
    s_right = (index % 26)[:, None]
    x = np.broadcast_to(np.arange(26), (N_POSITIONS, 26))
    x = FORWARD[right, s_right, x]
    x = FORWARD[middle, s_middle, x]
    x = FORWARD[left, s_left, x]
    x = REFLECT[REFLECTOR_NAMES.index(reflector), x]
    x = BACKWARD[left, s_left, x]
    x = BACKWARD[middle, s_middle, x]
    x = BACKWARD[right, s_right, x]
    table = np.ascontiguousarray(x, dtype=np.uint8)
    table.flags.writeable = False
    return table
