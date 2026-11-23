"""Dos mensajes en profundidad, cifrados con la máquina real.

**El procedimiento naval.** Los mensajes de un día comparten la clave diaria (orden de
rotores, anillos y plugboard), y cada uno empieza en su propia clave de mensaje: la
posición inicial de los rotores. Si dos claves de mensaje coinciden en el rotor
izquierdo y en el central y solo difieren en el derecho (VFG y VFX), las dos máquinas
recorren la *misma* sucesión de estados del odómetro, una adelantada respecto de la otra.
Donde los estados coinciden, la permutación es la misma y los dos mensajes quedan **en
profundidad**: dos letras cifradas coinciden si y solo si coinciden las planas, porque el
cifrado en un estado es una biyección.

**El desplazamiento.** La letra j del mensaje 2 se cifra en el mismo estado que la letra
j + d del mensaje 1. Si los derechos difieren en δ = (derecho₂ − derecho₁) mod 26, entre
1 y 25, hay dos casos:

- si el central no avanza mientras el derecho del mensaje 1 recorre esos δ pasos, el
  mensaje 1 llega al arranque del 2: d = +δ;
- si avanza, es el mensaje 2 el que llega al arranque del 1, tras 26 − δ pasos: d = δ − 26.

Por eso Banburismus probaba los desplazamientos de −25 a +25, y el signo del bueno decía
en qué tramo estaba la muesca del rotor derecho (el «scritchmus»). Una vez alineados, el
central avanza en el mismo estado en las dos máquinas, así que la profundidad dura todo
el solapamiento (D-042). :func:`true_offset` no usa esta regla: compara los estados de la
máquina.

**Textos planos.** Dos fuentes (D-043):

- ``"aleman"``: dos fragmentos independientes del corpus alemán, que no se solapan;
- ``"tasa_1_17"``: texto sintético en el que cada columna en profundidad repite con
  probabilidad 1/17 exacta, columna por columna e independiente: el modelo de Turing.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

import numpy as np

from enigma_lab.core.batch import KeyBatch, encrypt_batch, random_key_batch
from enigma_lab.core.machine import EnigmaConfig
from enigma_lab.core.stepping import notch_sets, step
from enigma_lab.core.wiring import ROTORS
from enigma_lab.stats.corpus import Mode, Source, load_codes

TextSource = Literal["aleman", "tasa_1_17"]
TEXT_SOURCES: dict[str, str] = {
    "aleman": "Alemán del corpus",
    "tasa_1_17": "Sintético, tasa 1/17",
}

MAX_OFFSET = 25
OFFSETS = np.arange(-MAX_OFFSET, MAX_OFFSET + 1)
"""Los 51 desplazamientos que se prueban, de −25 a +25."""

TURING_RATE = 1 / 17
"""Tasa de repetición en profundidad del texto naval alemán (Wikipedia, «Banburismus»)."""


# ---------------------------------------------------------------- el desplazamiento verdadero


def encryption_states(
    rotors: Sequence[str], start: Sequence[int], count: int
) -> list[tuple[int, ...]]:
    """Las ventanas con que se cifran las primeras ``count`` letras desde ``start``.

    Los rotores avanzan antes de cifrar cada letra, así que la letra 0 ya usa el estado
    siguiente al de la clave de mensaje.
    """
    notches = notch_sets([ROTORS[name].notches for name in rotors])
    states, position = [], tuple(start)
    for _ in range(count):
        position = step(position, notches).positions
        states.append(position)
    return states


def true_offset(rotors: Sequence[str], start1: Sequence[int], right2: int) -> int | None:
    """El desplazamiento d en que la letra j del mensaje 2 usa el estado de la letra j + d del 1.

    El mensaje 2 empieza con los mismos rotores izquierdo y central que el 1 y con el
    derecho en ``right2``. Basta con que coincida un estado: desde ahí el odómetro sigue
    igual en las dos máquinas. Devuelve ``None`` si ningún desplazamiento de −25 a +25
    los pone en profundidad (con los rotores I–V no pasa).
    """
    start2 = (start1[0], start1[1], right2)
    span = 2 * MAX_OFFSET + 2
    s1 = encryption_states(rotors, start1, span)
    s2 = encryption_states(rotors, start2, span)
    for d in range(-MAX_OFFSET, MAX_OFFSET + 1):
        j = max(0, -d)
        if s2[j] == s1[j + d]:
            return d
    return None


# ---------------------------------------------------------------- columnas alineadas


def aligned(
    cipher1: np.ndarray, cipher2: np.ndarray, offsets: np.ndarray | int, length: int
) -> tuple[np.ndarray, np.ndarray]:
    """Las primeras ``length`` columnas del solapamiento: (letra j + d del 1, letra j del 2).

    Acepta un par (1 dimensión) con un desplazamiento, o un lote (N, L) con un
    desplazamiento por fila. Los mensajes deben medir ``length + 25`` letras o más, para
    que todo desplazamiento de −25 a +25 tenga ``length`` columnas.
    """
    c1, c2 = np.atleast_2d(cipher1), np.atleast_2d(cipher2)
    d = np.broadcast_to(np.asarray(offsets), (c1.shape[0],))
    j = np.maximum(0, -d)[:, None] + np.arange(length)
    rows = np.arange(c1.shape[0])[:, None]
    top, bottom = c1[rows, j + d[:, None]], c2[rows, j]
    if np.ndim(cipher1) == 1:
        return top[0], bottom[0]
    return top, bottom


def repeats(
    cipher1: np.ndarray, cipher2: np.ndarray, offsets: np.ndarray | int, length: int
) -> np.ndarray:
    """Columnas con repetición (letra igual arriba y abajo) en el desplazamiento dado."""
    top, bottom = aligned(cipher1, cipher2, offsets, length)
    result: np.ndarray = top == bottom
    return result


# ---------------------------------------------------------------- textos planos


def independent_fragments(
    rng: np.random.Generator,
    n: int,
    length: int,
    source: Source = "muestra",
    mode: Mode = "x",
) -> tuple[np.ndarray, np.ndarray]:
    """N pares de fragmentos del corpus alemán que no se solapan en el corpus: (N, L) y (N, L)."""
    codes = load_codes("aleman", source, mode)
    if 2 * length > len(codes):
        raise ValueError(f"el corpus tiene {len(codes)} letras; no alcanza para dos de {length}")
    high = len(codes) - length + 1
    first, second = rng.integers(0, high, n), rng.integers(0, high, n)
    clash = np.abs(first - second) < length
    while clash.any():
        second[clash] = rng.integers(0, high, int(clash.sum()))
        clash = np.abs(first - second) < length
    window = np.arange(length)
    return codes[first[:, None] + window], codes[second[:, None] + window]


def turing_plaintexts(
    rng: np.random.Generator, offsets: np.ndarray, length: int, rate: float = TURING_RATE
) -> tuple[np.ndarray, np.ndarray]:
    """Textos sintéticos con la tasa de Turing: en profundidad, cada columna repite con «rate».

    El mensaje 1 son letras uniformes. La letra j del mensaje 2 es la letra j + d del 1
    con probabilidad «rate», y si no, una de las otras 25 al azar. Así, en el desplazamiento
    verdadero d, las columnas repiten con probabilidad «rate», independientes entre sí, y
    en cualquier otro, con 1/26.
    """
    n = len(offsets)
    plain1 = rng.integers(0, 26, (n, length)).astype(np.uint8)
    source_index = np.arange(length)[None, :] + offsets[:, None]
    inside = (source_index >= 0) & (source_index < length)
    partner = plain1[np.arange(n)[:, None], np.clip(source_index, 0, length - 1)]
    same = inside & (rng.random((n, length)) < rate)
    other = (partner + rng.integers(1, 26, (n, length))) % 26
    plain2 = np.where(same, partner, np.where(inside, other, rng.integers(0, 26, (n, length))))
    return plain1, plain2.astype(np.uint8)


# ---------------------------------------------------------------- pares de mensajes


@dataclass(frozen=True)
class DepthPairs:
    """N pares de mensajes con la misma clave diaria y claves de mensaje que solo difieren
    en el rotor derecho.

    Attributes:
        configs: la clave diaria de cada par, con la clave de mensaje 1 como posición.
        right2: (N,) letra 0–25 del rotor derecho en la clave de mensaje 2.
        offsets: (N,) desplazamiento verdadero: la letra j del 2 va con la j + d del 1.
        plain1, plain2, cipher1, cipher2: (N, L) letras 0–25.
        source: de dónde salen los textos planos.
    """

    configs: tuple[EnigmaConfig, ...]
    right2: np.ndarray
    offsets: np.ndarray
    plain1: np.ndarray
    plain2: np.ndarray
    cipher1: np.ndarray
    cipher2: np.ndarray
    source: str

    def __len__(self) -> int:
        return len(self.configs)

    def message_key(self, i: int, which: int) -> str:
        """La clave de mensaje del par i (1 o 2), en letras: «VFG»."""
        config = self.configs[i]
        right = config.positions[2] if which == 1 else int(self.right2[i])
        return "".join(chr(65 + v) for v in (*config.positions[:2], right))


def _second_keys(keys: KeyBatch, right2: np.ndarray) -> KeyBatch:
    """El lote de claves del mensaje 2: igual al del 1 salvo el rotor derecho."""
    positions = keys.positions.copy()
    positions[:, 2] = right2
    return KeyBatch(keys.rotors, keys.reflector, keys.rings, positions, keys.plugboard)


def _draw_keys(
    rng: np.random.Generator, n: int, cables: int
) -> tuple[list[EnigmaConfig], np.ndarray, np.ndarray]:
    """Claves diarias, el derecho del mensaje 2 y el desplazamiento verdadero de cada par."""
    configs: list[EnigmaConfig] = []
    right2: list[int] = []
    offsets: list[int] = []
    while len(configs) < n:
        _, batch = random_key_batch(rng, n - len(configs), model="I", cables=cables)
        for config in batch:
            other = (config.positions[2] + int(rng.integers(1, 26))) % 26
            d = true_offset(config.rotors, config.positions, other)
            if d is not None:
                configs.append(config)
                right2.append(other)
                offsets.append(d)
    return configs, np.array(right2, dtype=np.int16), np.array(offsets, dtype=np.int64)


def make_pairs(
    rng: np.random.Generator,
    n: int,
    length: int,
    text: TextSource = "aleman",
    corpus: Source = "muestra",
    mode: Mode = "x",
    cables: int = 10,
) -> DepthPairs:
    """N pares en profundidad, de ``length`` letras cada mensaje, cifrados con la máquina.

    Clave diaria al azar de Enigma I (rotores I–V, reflector B, ``cables`` cables);
    claves de mensaje con el mismo izquierdo y central y el derecho distinto.
    """
    configs, right2, offsets = _draw_keys(rng, n, cables)
    if text == "aleman":
        plain1, plain2 = independent_fragments(rng, n, length, corpus, mode)
    else:
        plain1, plain2 = turing_plaintexts(rng, offsets, length)
    keys1 = KeyBatch.from_configs(configs)
    keys2 = _second_keys(keys1, right2)
    both = KeyBatch(
        rotors=np.concatenate([keys1.rotors, keys2.rotors]),
        reflector=np.concatenate([keys1.reflector, keys2.reflector]),
        rings=np.concatenate([keys1.rings, keys2.rings]),
        positions=np.concatenate([keys1.positions, keys2.positions]),
        plugboard=np.concatenate([keys1.plugboard, keys2.plugboard]),
    )
    cipher = encrypt_batch(both, np.concatenate([plain1, plain2]))
    return DepthPairs(
        configs=tuple(configs),
        right2=right2,
        offsets=offsets,
        plain1=plain1,
        plain2=plain2,
        cipher1=cipher[:n],
        cipher2=cipher[n:],
        source=text,
    )


def false_offsets(rng: np.random.Generator, offsets: np.ndarray) -> np.ndarray:
    """Un desplazamiento falso al azar por par, entre los otros 50 de −25 a +25."""
    shift = rng.integers(1, len(OFFSETS), len(offsets))
    index = (offsets + MAX_OFFSET + shift) % len(OFFSETS)
    return np.asarray(OFFSETS[index], dtype=np.int64)
