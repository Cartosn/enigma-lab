"""El tráfico de un día y la reconstrucción de AD, BE y CF.

**El día.** Una clave diaria de 1932: rotores I–III en algún orden, reflector A, anillos al
azar, 6 cables (Kuhl 2007) y una posición del día (Grundstellung) al azar. Cada mensaje trae
una clave de mensaje de tres letras al azar, cifrada dos veces en la posición del día con la
**máquina real** (``characteristic.indicator_permutations``): sin supuestos, con el plugboard
y con el rotor central moviéndose cuando le toca.

**Qué aporta cada mensaje.** Su indicador c₁…c₆ da las parejas c₁ → c₄ de AD, c₂ → c₅ de BE
y c₃ → c₆ de CF. Si las claves de mensaje son al azar, c₁ = A(k₁) también lo es: las primeras
letras de los indicadores son sorteos uniformes e independientes de las 26 letras.

**Cuándo queda reconstruida una permutación.** Cuatro niveles, de más exigente a menos:

1. *Todas las letras*: las 26 aparecieron como primera letra. Es el coleccionista de cupones:
   en promedio 26·H₂₆ = 100,2 mensajes para una permutación.
2. *Por eliminación*: bastan 25; la imagen de la última es la que falta.
3. *La permutación, con el teorema*: es la única completación cuyos ciclos van en parejas.
4. *La característica, con el teorema*: todas las completaciones con los ciclos en parejas
   tienen la misma estructura. Es lo que necesita el catálogo.

**Completar con el teorema.** Lo conocido de AD forma ciclos cerrados y cadenas abiertas
(tramos x → AD(x) → … que terminan en una letra cuya imagen no se conoce). Completar AD es
cerrar las cadenas en ciclos: se agrupan, y un grupo de g cadenas se puede recorrer en
(g − 1)! órdenes. Solo valen las completaciones cuya estructura sea una de las 101 con los
ciclos en parejas (``characteristic.DOUBLED_TYPES``).
"""

from __future__ import annotations

import itertools
import math
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from functools import cache

import numpy as np

from enigma_lab.core.machine import EnigmaConfig
from enigma_lab.core.random_keys import random_config
from enigma_lab.rejewski.catalog import CATALOG_REFLECTOR, CATALOG_ROTORS
from enigma_lab.rejewski.characteristic import (
    DOUBLED_TYPES,
    N_INDICATOR,
    PAIRS,
    PRODUCTS,
    cycle_type,
    indicator_permutations,
    is_paired,
    products,
)

DAY_CABLES = 6
"""Cables del plugboard en 1932 (Kuhl 2007)."""
LEVELS = ("todas", "eliminacion", "permutacion", "caracteristica")
LEVEL_LABELS = {
    "todas": "las 26 letras vistas",
    "eliminacion": "25 letras (la última por eliminación)",
    "permutacion": "la permutación, con el teorema",
    "caracteristica": "la característica, con el teorema",
}
_TYPE_COUNTS = tuple(Counter(t) for t in DOUBLED_TYPES)


def random_day_key(rng: np.random.Generator, cables: int = DAY_CABLES) -> EnigmaConfig:
    """Una clave diaria de 1932: rotores I–III, reflector A, anillos y posición del día al azar."""
    return random_config(
        rng, model="I", cables=cables, reflectors=(CATALOG_REFLECTOR,), rotors=CATALOG_ROTORS
    )


def core_position(config: EnigmaConfig) -> int:
    """La posición del núcleo (ventana − anillo) en la posición del día: el índice del catálogo."""
    left, middle, right = (
        (p - r) % 26 for p, r in zip(config.positions, config.rings, strict=True)
    )
    return left * 676 + middle * 26 + right


def message_keys(rng: np.random.Generator, n: int) -> np.ndarray:
    """N claves de mensaje de tres letras al azar: (N, 3) con valores 0–25."""
    return rng.integers(0, 26, size=(n, 3))


def indicators(perms6: np.ndarray, keys: np.ndarray) -> np.ndarray:
    """Los indicadores de N mensajes: la clave tecleada dos veces, (N, 6).

    La letra k del indicador es la permutación k (A…F) aplicada a la letra k mod 3 de la clave.
    """
    keys = np.asarray(keys)
    columns = [perms6[k][keys[:, k % 3]] for k in range(N_INDICATOR)]
    return np.stack(columns, axis=1)


@dataclass(frozen=True)
class Day:
    """El tráfico de un día: la clave, sus seis permutaciones y los indicadores de N mensajes."""

    config: EnigmaConfig
    perms: np.ndarray
    """A…F de la máquina real en la posición del día: (6, 26)."""
    keys: np.ndarray
    """Las claves de mensaje: (N, 3)."""
    indicators: np.ndarray
    """Los indicadores: (N, 6)."""

    @property
    def true_products(self) -> np.ndarray:
        """AD, BE y CF verdaderos: (3, 26)."""
        return products(self.perms)


def simulate_day(rng: np.random.Generator, n_messages: int, cables: int = DAY_CABLES) -> Day:
    """Un día de tráfico: clave diaria al azar y ``n_messages`` mensajes con su indicador doble."""
    config = random_day_key(rng, cables)
    perms = indicator_permutations(config)
    keys = message_keys(rng, n_messages)
    return Day(config=config, perms=perms, keys=keys, indicators=indicators(perms, keys))


def known_after(indicator_rows: np.ndarray, product: int) -> np.ndarray:
    """Lo que se sabe de un producto con esos indicadores: imagen de cada letra o −1."""
    a, b = PAIRS[product]
    known = np.full(26, -1, dtype=np.int64)
    known[indicator_rows[:, a]] = indicator_rows[:, b]
    return known


# ---------------------------------------------------------------- completar con el teorema


def partial_cycles(known: Sequence[int] | np.ndarray) -> tuple[list[list[int]], list[list[int]]]:
    """(ciclos cerrados, cadenas abiertas) de una permutación conocida en parte, con sus letras.

    ``known[x]`` es la imagen de x, o −1 si no se sabe. Un ciclo cerrado se lista desde su letra
    menor, siguiendo la permutación. Una cadena empieza en una letra que no es imagen de
    ninguna conocida y termina en la primera cuya imagen no se sabe (una letra sin datos es una
    cadena de longitud 1).
    """
    image = [int(v) for v in known]
    has_preimage = [False] * 26
    for y in image:
        if y >= 0:
            has_preimage[y] = True
    seen = [False] * 26
    chains = []
    for start in range(26):
        if has_preimage[start]:
            continue
        chain, x = [], start
        while True:
            seen[x] = True
            chain.append(x)
            if image[x] < 0:
                break
            x = image[x]
        chains.append(chain)
    closed = []
    for start in range(26):
        if seen[start]:
            continue
        cycle, x = [], start
        while not seen[x]:
            seen[x] = True
            cycle.append(x)
            x = image[x]
        closed.append(cycle)
    return closed, chains


def partial_structure(known: Sequence[int] | np.ndarray) -> tuple[list[int], list[int]]:
    """Las longitudes de :func:`partial_cycles`, de mayor a menor: (ciclos, cadenas)."""
    closed, chains = partial_cycles(known)
    return (
        sorted((len(c) for c in closed), reverse=True),
        sorted((len(c) for c in chains), reverse=True),
    )


def _remove_one(items: tuple[int, ...], value: int) -> tuple[int, ...]:
    index = items.index(value)
    return items[:index] + items[index + 1 :]


@cache
def _groupings(chains: tuple[tuple[int, int], ...], parts: tuple[int, ...], cap: int) -> int:
    """Formas de cerrar las cadenas en ciclos de esas longitudes (hasta ``cap``).

    ``chains`` es el multiconjunto de longitudes de cadena como ((longitud, cuántas), …), de
    mayor a menor; las cadenas son distintas aunque midan lo mismo. ``parts`` son las
    longitudes de los ciclos nuevos. Se toma una cadena de la mayor longitud como ancla, se
    elige con qué otras forma su ciclo (C(m, j) formas de tomar j de m iguales) y en qué
    orden se recorren ((g − 1)! con g cadenas), y se sigue con el resto.
    """
    if not chains:
        return 1 if not parts else 0
    if not parts:
        return 0
    (anchor, count), *others = chains
    pool = ([(anchor, count - 1)] if count > 1 else []) + list(others)
    total = 0
    for size in sorted(set(parts), reverse=True):
        need = size - anchor
        if need < 0:
            continue
        rest_parts = _remove_one(parts, size)
        for choice in _sub_multisets(tuple(pool), need):
            ways = math.factorial(sum(choice))
            for (_, m), j in zip(pool, choice, strict=True):
                ways *= math.comb(m, j)
            left = tuple((length, m - j) for (length, m), j in zip(pool, choice, strict=True))
            left = tuple(item for item in left if item[1] > 0)
            total += ways * _groupings(left, rest_parts, cap)
            if total >= cap:
                return cap
    return total


@cache
def _sub_multisets(pool: tuple[tuple[int, int], ...], need: int) -> tuple[tuple[int, ...], ...]:
    """Cuántas cadenas tomar de cada longitud para sumar ``need`` letras."""
    if not pool:
        return ((),) if need == 0 else ()
    (length, count), *rest = pool
    out = []
    for j in range(min(count, need // length) + 1):
        for tail in _sub_multisets(tuple(rest), need - j * length):
            out.append((j, *tail))
    return tuple(out)


def _as_multiset(lengths: Sequence[int]) -> tuple[tuple[int, int], ...]:
    counts = Counter(lengths)
    return tuple(sorted(counts.items(), reverse=True))


def completions(known: Sequence[int] | np.ndarray, cap: int = 2) -> dict[int, int]:
    """Completaciones con los ciclos en parejas, por estructura (índice en ``DOUBLED_TYPES``).

    Cada cuenta va hasta ``cap``, y la búsqueda para cuando la suma llega a ``cap``: para saber
    si la permutación o la característica ya quedaron determinadas basta con distinguir 0, 1 y
    «2 o más».
    """
    closed, chains = partial_structure(known)
    have = Counter(closed)
    multiset = _as_multiset(chains)
    found: dict[int, int] = {}
    total = 0
    for index, target in enumerate(_TYPE_COUNTS):
        if any(target[length] < n for length, n in have.items()):
            continue
        parts = tuple(sorted((target - have).elements(), reverse=True))
        ways = _groupings(multiset, parts, cap)
        if ways:
            found[index] = ways
            total += ways
            if total >= cap and len(found) >= 2:
                break
    return found


def possible_types(known: Sequence[int] | np.ndarray) -> list[int]:
    """Todas las estructuras (índices en ``DOUBLED_TYPES``) que aún admite lo conocido."""
    closed, chains = partial_structure(known)
    have = Counter(closed)
    multiset = _as_multiset(chains)
    out = []
    for index, target in enumerate(_TYPE_COUNTS):
        if any(target[length] < n for length, n in have.items()):
            continue
        parts = tuple(sorted((target - have).elements(), reverse=True))
        if _groupings(multiset, parts, 1):
            out.append(index)
    return out


def unique_completion(known: Sequence[int] | np.ndarray, max_chains: int = 7) -> np.ndarray | None:
    """La permutación completa, si el teorema deja una sola completación (si no, ``None``).

    Prueba todas las formas de unir el final de cada cadena con el comienzo de otra (k! con k
    cadenas), así que solo se usa con pocas cadenas: con más de ``max_chains`` devuelve ``None``.
    """
    known = np.asarray(known, dtype=np.int64)
    _, chains = partial_cycles(known)
    if len(chains) > max_chains:
        return None
    ends, starts = [c[-1] for c in chains], [c[0] for c in chains]
    found = None
    for choice in itertools.permutations(range(len(chains))):
        full = known.copy()
        for i, j in enumerate(choice):
            full[ends[i]] = starts[j]
        if is_paired(cycle_type(full)):
            if found is not None:
                return None
            found = full
    return found


def permutation_determined(known: Sequence[int] | np.ndarray) -> bool:
    """¿Hay una sola completación con los ciclos en parejas?"""
    found = completions(known, cap=2)
    return len(found) == 1 and next(iter(found.values())) == 1


def characteristic_determined(known: Sequence[int] | np.ndarray) -> bool:
    """¿Todas las completaciones con los ciclos en parejas tienen la misma estructura?"""
    return len(completions(known, cap=2)) == 1


# ---------------------------------------------------------------- mensajes necesarios


def first_letter_times(first_letters: np.ndarray) -> tuple[int, int]:
    """Mensajes hasta ver 26 y 25 primeras letras distintas (o −1 si no alcanzan)."""
    seen: set[int] = set()
    at_25 = at_26 = -1
    for i, letter in enumerate(first_letters, start=1):
        seen.add(int(letter))
        if len(seen) == 25 and at_25 < 0:
            at_25 = i
        if len(seen) == 26:
            at_26 = i
            break
    return at_26, at_25


def theorem_times(indicator_rows: np.ndarray, product: int) -> tuple[int, int]:
    """Mensajes hasta que el teorema determina (la permutación, la característica), o −1.

    Solo se revisa cuando llega una primera letra nueva: lo demás no cambia lo conocido.
    Una vez determinada, sigue determinada (más parejas solo descartan completaciones).
    """
    a, b = PAIRS[product]
    known = np.full(26, -1, dtype=np.int64)
    perm_at = char_at = -1
    for i, row in enumerate(indicator_rows, start=1):
        letter = int(row[a])
        if known[letter] >= 0:
            continue
        known[letter] = int(row[b])
        found = completions(known, cap=2)
        if char_at < 0 and len(found) == 1:
            char_at = i
        if len(found) == 1 and next(iter(found.values())) == 1:
            perm_at = i
            break
    return perm_at, char_at


@dataclass(frozen=True)
class DayResult:
    """Lo que pide reconstruir un día: mensajes por nivel y por producto, y la clave."""

    config: EnigmaConfig
    times: dict[str, tuple[int, int, int]]
    """Para cada nivel, los mensajes que pide cada producto (AD, BE, CF)."""
    middle_moves: bool

    def day_time(self, level: str) -> int:
        """Mensajes hasta reconstruir los tres productos en ese nivel: el mayor de los tres."""
        return max(self.times[level])


def reconstruction_times(indicator_rows: np.ndarray) -> dict[str, tuple[int, int, int]]:
    """Mensajes que pide cada nivel para cada producto, con esos indicadores en orden."""
    out: dict[str, list[int]] = {level: [] for level in LEVELS}
    for product in range(len(PRODUCTS)):
        a, _ = PAIRS[product]
        all_letters, by_elimination = first_letter_times(indicator_rows[:, a])
        perm_at, char_at = theorem_times(indicator_rows, product)
        out["todas"].append(all_letters)
        out["eliminacion"].append(by_elimination)
        out["permutacion"].append(perm_at)
        out["caracteristica"].append(char_at)
    return {level: (v[0], v[1], v[2]) for level, v in out.items()}


# ---------------------------------------------------------------- coleccionista de cupones


def harmonic(n: int) -> float:
    """H_n = 1 + 1/2 + … + 1/n."""
    return sum(1 / k for k in range(1, n + 1))


@cache
def distinct_cdf(letters: int = 26, n_max: int = 3_000) -> np.ndarray:
    """P(D_n = d) para n = 0…n_max: D_n, las letras distintas tras n sorteos uniformes.

    Una cadena de Markov: con d letras vistas, el sorteo siguiente repite una con probabilidad
    d/26 y trae una nueva con (26 − d)/26. Devuelve (n_max + 1, 27).
    """
    probs = np.zeros((n_max + 1, letters + 1))
    probs[0, 0] = 1.0
    d = np.arange(letters + 1)
    stay, move = d / letters, (letters - d) / letters
    for n in range(n_max):
        probs[n + 1] = probs[n] * stay
        probs[n + 1, 1:] += probs[n, :-1] * move[:-1]
    probs.flags.writeable = False
    return probs


def coupon_cdf(needed: int, products: int = 1, letters: int = 26) -> np.ndarray:
    """P(T ≤ n) para n = 0…: T, mensajes hasta ver ``needed`` letras en cada uno de los productos.

    Las primeras letras de AD, BE y CF son sorteos independientes, así que la de varios
    productos es la del uno elevada a su número: P(máx ≤ n) = P(T₁ ≤ n)^productos.
    """
    probs = distinct_cdf(letters)
    single = probs[:, needed:].sum(axis=1)
    cdf: np.ndarray = single**products
    return cdf


def coupon_expectation(needed: int = 26, products: int = 1, letters: int = 26) -> float:
    """E[T] = Σₙ P(T > n). Con 26 letras y un producto es 26·H₂₆ = 100,2."""
    return float((1 - coupon_cdf(needed, products, letters)).sum())


def coupon_pmf(needed: int = 26, products: int = 1, letters: int = 26) -> np.ndarray:
    """P(T = n) para n = 0…"""
    cdf = coupon_cdf(needed, products, letters)
    pmf: np.ndarray = np.diff(cdf, prepend=0.0)
    return pmf
