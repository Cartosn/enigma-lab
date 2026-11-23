"""La característica de Rejewski: la estructura de ciclos de AD, BE y CF.

**El indicador.** Hasta mayo de 1940, el operador elegía una clave de mensaje de tres letras
k₁k₂k₃, la tecleaba dos veces en la posición del día (Grundstellung) y transmitía las seis
letras cifradas c₁…c₆ al comienzo del mensaje. Rejewski llamó A, B, C, D, E y F a las seis
permutaciones de la máquina en esas seis pulsaciones:

    c₁ = A(k₁), c₂ = B(k₂), c₃ = C(k₃), c₄ = D(k₁), c₅ = E(k₂), c₆ = F(k₃).

Como A es una involución, k₁ = A(c₁) y c₄ = D(A(c₁)). Cada mensaje da entonces una pareja
c₁ → c₄ de la permutación AD: primero A y luego D, la composición de izquierda a derecha de
Rejewski y de Kuhl. Igual con BE (c₂ → c₅) y con CF (c₃ → c₆). El criptoanalista no conoce
A ni D, pero sí su producto.

**Los ciclos van en parejas.** A y D son involuciones sin puntos fijos: 13 trasposiciones
cada una. El producto de dos permutaciones así se descompone en ciclos disjuntos que van en
parejas de igual longitud, y toda permutación con sus ciclos en parejas es un producto de dos
de ellas (teorema de Rejewski). La mitad de los ciclos forma entonces una partición de 13: hay
p(13) = 101 estructuras posibles para cada producto, y 101³ = 1.030.301 para la terna.

**La característica no depende del plugboard.** Con el plugboard P (una involución) y el
aleatorizador S de cada pulsación, A = P·A′·P y D = P·D′·P, así que

    AD = P·A′·P · P·D′·P = P · (A′D′) · P = P⁻¹ · (A′D′) · P,

que es la conjugada de A′D′ por P. Conjugar renombra las letras de cada ciclo sin cambiar su
longitud. La estructura de ciclos de AD es la de A′D′, que solo depende de los rotores, y por
eso se pudo catalogar de antemano (``rejewski/catalog.py``).
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Sequence
from functools import cache

import numpy as np

from enigma_lab.core.machine import Enigma, EnigmaConfig

N_INDICATOR = 6
"""Letras del indicador: la clave de mensaje cifrada dos veces."""
PRODUCTS = ("AD", "BE", "CF")
PAIRS = ((0, 3), (1, 4), (2, 5))
"""Las pulsaciones que forman cada producto: (A, D), (B, E) y (C, F)."""
HALF = 13

CycleType = tuple[int, ...]
"""Las longitudes de los ciclos de una permutación, de mayor a menor: (13, 13)."""
Characteristic = tuple[CycleType, CycleType, CycleType]
"""La estructura de ciclos de AD, BE y CF."""


# ---------------------------------------------------------------- permutaciones


def compose(first: np.ndarray, then: np.ndarray) -> np.ndarray:
    """El producto «primero ``first``, luego ``then``»: x → then(first(x)).

    Es la composición de izquierda a derecha de Rejewski: AD = ``compose(A, D)``. Sirve para
    una permutación (26,) o para un lote (N, 26).
    """
    result: np.ndarray = np.take_along_axis(np.asarray(then), np.asarray(first), axis=-1)
    return result


def cycles(perm: Sequence[int] | np.ndarray) -> list[list[int]]:
    """Los ciclos disjuntos de una permutación, cada uno desde su letra menor."""
    seen = [False] * len(perm)
    out = []
    for start in range(len(perm)):
        if seen[start]:
            continue
        cycle, x = [], start
        while not seen[x]:
            seen[x] = True
            cycle.append(x)
            x = int(perm[x])
        out.append(cycle)
    return out


def cycle_type(perm: Sequence[int] | np.ndarray) -> CycleType:
    """Las longitudes de los ciclos, de mayor a menor."""
    return tuple(sorted((len(c) for c in cycles(perm)), reverse=True))


def is_paired(lengths: Sequence[int]) -> bool:
    """¿Cada longitud aparece un número par de veces? Así son los ciclos de AD, BE y CF."""
    return all(count % 2 == 0 for count in Counter(lengths).values())


def products(perms6: np.ndarray) -> np.ndarray:
    """AD, BE y CF a partir de las seis permutaciones: (..., 6, 26) → (..., 3, 26)."""
    perms6 = np.asarray(perms6)
    return np.stack([compose(perms6[..., a, :], perms6[..., b, :]) for a, b in PAIRS], axis=-2)


def characteristic(perms6: np.ndarray) -> Characteristic:
    """La característica: la estructura de ciclos de AD, BE y CF."""
    ad, be, cf = products(perms6)
    return (cycle_type(ad), cycle_type(be), cycle_type(cf))


# ---------------------------------------------------------------- la máquina real


def indicator_permutations(config: EnigmaConfig) -> np.ndarray:
    """Las seis permutaciones A…F de la máquina completa en la posición del día: (6, 26).

    La posición del día es ``config.positions``. Los rotores avanzan antes de cada pulsación,
    también el central y el izquierdo cuando les toca (``core/stepping.py``), y la
    permutación incluye el plugboard. Es la máquina real, sin ningún supuesto.
    """
    machine = Enigma(config)
    perms = np.empty((N_INDICATOR, 26), dtype=np.int64)
    for k in range(N_INDICATOR):
        machine.step()
        perms[k] = machine.permutation()
    return perms


def middle_moves(config: EnigmaConfig) -> bool:
    """¿Se mueve el rotor central (o el izquierdo) durante las seis letras del indicador?

    Pasa si el derecho llega a su muesca en esas seis pulsaciones o si el central parte de la
    suya (doble paso): en 176 de cada 676 posiciones de los dos rotores de la derecha.
    """
    machine = Enigma(config)
    moved = False
    for _ in range(N_INDICATOR):
        stepped = machine.step().stepped
        moved = moved or any(stepped[:-1])
    return moved


def machine_characteristic(config: EnigmaConfig) -> Characteristic:
    """La característica del indicador cifrado con la máquina real en la posición del día."""
    return characteristic(indicator_permutations(config))


# ---------------------------------------------------------------- particiones de 13


@cache
def partitions(n: int, largest: int | None = None) -> tuple[tuple[int, ...], ...]:
    """Las particiones de n con partes de a lo sumo ``largest``, de mayor a menor.

    Van en orden lexicográfico inverso: (13), (12, 1), (11, 2), (11, 1, 1), (10, 3)…
    """
    top = n if largest is None else largest
    if n == 0:
        return ((),)
    out = []
    for first in range(min(n, top), 0, -1):
        for rest in partitions(n - first, first):
            out.append((first, *rest))
    return tuple(out)


HALF_TYPES: tuple[tuple[int, ...], ...] = partitions(HALF)
"""Las 101 particiones de 13: la mitad de los ciclos de un producto, una pareja por parte."""
N_TYPES = len(HALF_TYPES)


def doubled(half: Sequence[int]) -> CycleType:
    """La estructura completa de una partición de 13: cada parte, dos veces."""
    return tuple(length for part in half for length in (part, part))


DOUBLED_TYPES: tuple[CycleType, ...] = tuple(doubled(h) for h in HALF_TYPES)
"""Las 101 estructuras posibles de AD, BE o CF, en el orden de ``HALF_TYPES``."""
_TYPE_INDEX = {t: i for i, t in enumerate(DOUBLED_TYPES)}


def type_index(cycle_lengths: CycleType) -> int:
    """El número (0–100) de una estructura con los ciclos en parejas."""
    try:
        return _TYPE_INDEX[tuple(sorted(cycle_lengths, reverse=True))]
    except KeyError:
        raise ValueError(f"los ciclos no van en parejas: {cycle_lengths}") from None


def characteristic_code(ch: Characteristic) -> int:
    """La característica como un entero: índice(AD) · 101² + índice(BE) · 101 + índice(CF)."""
    ad, be, cf = (type_index(t) for t in ch)
    return (ad * N_TYPES + be) * N_TYPES + cf


def from_code(code: int) -> Characteristic:
    """El inverso de :func:`characteristic_code`."""
    ad, rest = divmod(int(code), N_TYPES * N_TYPES)
    be, cf = divmod(rest, N_TYPES)
    return (DOUBLED_TYPES[ad], DOUBLED_TYPES[be], DOUBLED_TYPES[cf])


# ---------------------------------------------------------------- en lote (catálogo)

_POWERS = 14 ** np.arange(HALF, dtype=np.int64)
_HALF_CODES = np.array(
    [sum(int(_POWERS[p - 1]) for p in half) for half in HALF_TYPES], dtype=np.int64
)
_HALF_ORDER = np.argsort(_HALF_CODES)


def cycle_counts(perms: np.ndarray) -> np.ndarray:
    """Cuántos ciclos de cada longitud tiene cada permutación de un lote (N, 26): (N, 27).

    La columna L es el número de ciclos de longitud L. Se calcula la longitud del ciclo de
    cada letra x: el menor k ≥ 1 con Pᵏ(x) = x, subiendo una potencia por vuelta.
    """
    perms = np.asarray(perms)
    n = perms.shape[0]
    identity = np.arange(26)
    length = np.zeros(perms.shape, dtype=np.int64)
    current = perms.copy()
    for k in range(1, 27):
        length[(current == identity) & (length == 0)] = k
        if (length > 0).all():
            break
        current = np.take_along_axis(perms, current, axis=1)
    rows = np.repeat(np.arange(n), 26) * 27
    elements = np.bincount(rows + length.ravel(), minlength=n * 27).reshape(n, 27)
    sizes = np.arange(27)
    sizes[0] = 1
    counts: np.ndarray = elements // sizes
    return counts


def type_indices(perms: np.ndarray) -> np.ndarray:
    """El número (0–100) de la estructura de cada producto de un lote (N, 26)."""
    counts = cycle_counts(perms)
    if np.any(counts[:, HALF + 1 :]) or np.any(counts % 2):
        raise ValueError("hay productos cuyos ciclos no van en parejas")
    codes = (counts[:, 1 : HALF + 1] // 2) @ _POWERS
    found = np.searchsorted(_HALF_CODES[_HALF_ORDER], codes)
    index: np.ndarray = _HALF_ORDER[found]
    return index


# ---------------------------------------------------------------- texto


def format_type(lengths: CycleType) -> str:
    """Una estructura con la notación de Kuhl: «(12 12 1 1)»."""
    return "(" + " ".join(str(n) for n in lengths) + ")"


def format_characteristic(ch: Characteristic) -> str:
    """La característica con la notación de Kuhl: «(13 13)(12 12 1 1)(13 13)»."""
    return "".join(format_type(t) for t in ch)


def parse_characteristic(text: str) -> Characteristic:
    """El inverso de :func:`format_characteristic` (acepta espacios de más)."""
    groups = re.findall(r"\(([^()]*)\)", text)
    if len(groups) != len(PRODUCTS):
        raise ValueError(f"se esperaban tres estructuras entre paréntesis: {text!r}")
    types = [tuple(sorted((int(v) for v in g.split()), reverse=True)) for g in groups]
    for t in types:
        if sum(t) != 26 or not is_paired(t):
            raise ValueError(f"cada estructura suma 26 letras con los ciclos en parejas: {t}")
    return (types[0], types[1], types[2])
