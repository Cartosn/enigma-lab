"""Cifrado por lotes con tablas precalculadas, para los Monte Carlo.

Cifra N mensajes de igual longitud con N claves de tres rotores a la vez: en cada
instante t, todas las máquinas avanzan sus rotores y cifran su letra t con búsquedas
en tablas de NumPy. Es la misma máquina que :mod:`enigma_lab.core.machine`, escrita
en forma vectorizada. La prueba ``test_batch_matches_scalar`` exige que den lo mismo.

**Tablas precalculadas.** Para cada rotor r y cada desplazamiento s = ventana − anillo,
``FORWARD[r, s, x]`` es la salida del rotor para la entrada x (y ``BACKWARD`` la del
camino de vuelta). Así cada etapa del camino es una sola búsqueda en una tabla, para
las N máquinas a la vez.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from enigma_lab.core.machine import EnigmaConfig
from enigma_lab.core.random_keys import random_config
from enigma_lab.core.wiring import ALPHABET, REFLECTORS, ROTORS, inverse, permutation

ROTOR_NAMES = ("I", "II", "III", "IV", "V", "VI", "VII", "VIII")
REFLECTOR_NAMES = ("A", "B", "C")


def _shifted_tables(perms: Sequence[tuple[int, ...]]) -> np.ndarray:
    """T[r, s, x] = (P_r[(x + s) mod 26] − s) mod 26 para cada rotor r y desplazamiento s."""
    x = np.arange(26)
    table = np.empty((len(perms), 26, 26), dtype=np.uint8)
    for r, perm in enumerate(perms):
        p = np.asarray(perm)
        for s in range(26):
            table[r, s] = (p[(x + s) % 26] - s) % 26
    return table


_FORWARD_PERMS = [permutation(ROTORS[name].wiring) for name in ROTOR_NAMES]
FORWARD = _shifted_tables(_FORWARD_PERMS)
BACKWARD = _shifted_tables([inverse(p) for p in _FORWARD_PERMS])
REFLECT = np.array([permutation(REFLECTORS[name]) for name in REFLECTOR_NAMES], dtype=np.uint8)
NOTCH = np.zeros((len(ROTOR_NAMES), 26), dtype=bool)
for _r, _name in enumerate(ROTOR_NAMES):
    for _c in ROTORS[_name].notches:
        NOTCH[_r, ALPHABET.index(_c)] = True


@dataclass(frozen=True)
class KeyBatch:
    """N claves de tres rotores (Enigma I o M3) guardadas en arreglos de NumPy.

    Attributes:
        rotors: (N, 3) índices en ``ROTOR_NAMES``, de izquierda a derecha.
        reflector: (N,) índices en ``REFLECTOR_NAMES``.
        rings, positions: (N, 3) valores 0–25.
        plugboard: (N, 26) la permutación del plugboard de cada clave.
    """

    rotors: np.ndarray
    reflector: np.ndarray
    rings: np.ndarray
    positions: np.ndarray
    plugboard: np.ndarray

    def __len__(self) -> int:
        return int(self.rotors.shape[0])

    @classmethod
    def from_configs(cls, configs: Sequence[EnigmaConfig]) -> KeyBatch:
        """Empaqueta claves de tres rotores (la M4 no está soportada por lotes)."""
        if any(len(c.rotors) != 3 for c in configs):
            raise ValueError("el cifrado por lotes es para máquinas de tres rotores")
        plug = np.tile(np.arange(26, dtype=np.uint8), (len(configs), 1))
        for i, config in enumerate(configs):
            for a, b in config.plugboard:
                ia, ib = ALPHABET.index(a), ALPHABET.index(b)
                plug[i, ia], plug[i, ib] = ib, ia
        return cls(
            rotors=np.array([[ROTOR_NAMES.index(n) for n in c.rotors] for c in configs], np.intp),
            reflector=np.array([REFLECTOR_NAMES.index(c.reflector) for c in configs], np.intp),
            rings=np.array([c.rings for c in configs], dtype=np.int16),
            positions=np.array([c.positions for c in configs], dtype=np.int16),
            plugboard=plug,
        )


def random_key_batch(
    rng: np.random.Generator, n: int, model: str = "I", cables: int = 10
) -> tuple[KeyBatch, list[EnigmaConfig]]:
    """N claves aleatorias (reflector B), como lote y como lista de claves."""
    configs = [random_config(rng, model=model, cables=cables) for _ in range(n)]
    return KeyBatch.from_configs(configs), configs


def encrypt_batch(keys: KeyBatch, plaintexts: np.ndarray) -> np.ndarray:
    """Cifra N mensajes (N, L) de letras 0–25 con N claves; devuelve (N, L) uint8.

    En cada instante t:

    1. **Paso.** El central avanza si el derecho está en su muesca o si él mismo
       está en la suya (doble paso); el izquierdo, si el central está en su muesca;
       el derecho, siempre.
    2. **Camino.** Plugboard, tres rotores de ida, reflector, tres de vuelta y
       plugboard, cada uno como una búsqueda en su tabla.
    """
    plaintexts = np.asarray(plaintexts)
    n, length = plaintexts.shape
    if n != len(keys):
        raise ValueError("debe haber una clave por mensaje")
    rows = np.arange(n)
    r_left, r_mid, r_right = keys.rotors[:, 0], keys.rotors[:, 1], keys.rotors[:, 2]
    pos = keys.positions.astype(np.int16).copy()
    out = np.empty((n, length), dtype=np.uint8)
    for t in range(length):
        middle_at_notch = NOTCH[r_mid, pos[:, 1]]
        right_at_notch = NOTCH[r_right, pos[:, 2]]
        pos[:, 0] += middle_at_notch
        pos[:, 1] += middle_at_notch | right_at_notch
        pos[:, 2] += 1
        pos %= 26
        shift = (pos - keys.rings) % 26
        x = keys.plugboard[rows, plaintexts[:, t]]
        x = FORWARD[r_right, shift[:, 2], x]
        x = FORWARD[r_mid, shift[:, 1], x]
        x = FORWARD[r_left, shift[:, 0], x]
        x = REFLECT[keys.reflector, x]
        x = BACKWARD[r_left, shift[:, 0], x]
        x = BACKWARD[r_mid, shift[:, 1], x]
        x = BACKWARD[r_right, shift[:, 2], x]
        out[:, t] = keys.plugboard[rows, x]
    return out


def to_codes(texts: Sequence[str]) -> np.ndarray:
    """Textos de igual longitud (A–Z) a un arreglo (N, L) de enteros 0–25."""
    return np.array([[ALPHABET.index(c) for c in t] for t in texts], dtype=np.uint8)


def to_texts(codes: np.ndarray) -> list[str]:
    """Arreglo (N, L) de enteros 0–25 a textos."""
    return ["".join(ALPHABET[int(c)] for c in row) for row in codes]
