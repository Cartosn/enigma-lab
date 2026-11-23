"""El ataque de Gillogly (1995), solo con texto cifrado.

Tres fases, como las describen Ostwald y Weierud (2017):

1. **Órdenes y posiciones.** Con los anillos en AAA y el plugboard vacío se descifra el mensaje
   en cada orden y cada una de las 17.576 posiciones (con los 60 órdenes, 1.054.560 casos: los
   mismos que barre la Bombe) y se mide el índice de coincidencia (IC) del resultado. En la
   ubicación correcta, aun sin plugboard, parte del texto sale bien y otra parte como sustituto
   monoalfabético del plano, así que el IC sube por encima del 1/26 del azar.
2. **Anillos.** Para las mejores ubicaciones se prueban los 26 × 26 anillos del central y del
   derecho (el del izquierdo no importa), sin cambiar la posición del núcleo al empezar: solo
   cambia en qué letra avanza el central. También se prueba el central una posición atrás, por
   si giró en las primeras letras y la fase 1 eligió la posición de después del giro (D-066).
3. **Plugboard.** Hill climbing con el IC y luego con trigramas (``hillclimb.py``).

**Numba.** Las fases 1 y 2 son el bucle caliente: un descifrado letra a letra por ubicación, en
paralelo (``prange``). El aleatorizador sale de ``bombe/scrambler.scrambler_table``; el paso de
los rotores, de una tabla de sucesores de las 17.576 ventanas (``step_table``) calculada con las
muescas de ``core/batch.NOTCH``, la misma regla del doble paso que la máquina.
"""

from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from functools import cache

import numpy as np
from numba import njit, prange

from enigma_lab.attacks import hillclimb
from enigma_lab.bombe.checker import _step_windows
from enigma_lab.bombe.scrambler import N_POSITIONS, Order, rotor_orders, scrambler_table
from enigma_lab.bombe.sweep import _LOCK
from enigma_lab.core.batch import ROTOR_NAMES
from enigma_lab.core.machine import EnigmaConfig

ALL_ORDERS: tuple[Order, ...] = tuple(rotor_orders())
"""Los 60 órdenes de Enigma I (rotores I a V)."""
RING_M, RING_R = (a.ravel() for a in np.meshgrid(np.arange(26), np.arange(26), indexing="ij"))
"""Los 676 anillos (central, derecho) de la fase 2."""


@cache
def step_table(order: Order) -> np.ndarray:
    """La ventana siguiente de cada una de las 17.576 ventanas, con el doble paso: (17.576,)."""
    middle, right = (ROTOR_NAMES.index(name) for name in order[1:])
    index = np.arange(N_POSITIONS)
    windows = np.stack([index // 676, (index // 26) % 26, index % 26], axis=1)
    _step_windows(windows, middle, right)
    table = (windows @ np.array([676, 26, 1])).astype(np.int32)
    table.flags.writeable = False
    return table


@njit(cache=True)
def _ic_from(
    table: np.ndarray, nxt: np.ndarray, cipher: np.ndarray, start: int, ring_m: int, ring_r: int
) -> float:  # pragma: no cover - Numba
    """IC del descifrado sin plugboard desde una posición del núcleo, con esos anillos.

    La ventana al empezar es núcleo + anillo (el izquierdo en A). Antes de cada letra avanza con
    la tabla de sucesores, y la letra t se descifra en el núcleo ventana − anillo.
    """
    n = cipher.shape[0]
    left, middle, right = start // 676, (start // 26) % 26, start % 26
    w = left * 676 + ((middle + ring_m) % 26) * 26 + (right + ring_r) % 26
    counts = np.zeros(26, np.int64)
    for t in range(n):
        w = nxt[w]
        core = (w // 676) * 676 + (((w // 26) % 26 - ring_m) % 26) * 26 + (w % 26 - ring_r) % 26
        counts[table[core, cipher[t]]] += 1
    total = 0
    for c in range(26):
        total += counts[c] * (counts[c] - 1)
    return total / (n * (n - 1))


@njit(cache=True, parallel=True)
def _phase1(
    table: np.ndarray, nxt: np.ndarray, cipher: np.ndarray
) -> np.ndarray:  # pragma: no cover
    """IC del descifrado sin plugboard y con anillos AAA en cada posición inicial."""
    out = np.empty(table.shape[0])
    for start in prange(table.shape[0]):
        out[start] = _ic_from(table, nxt, cipher, start, 0, 0)
    return out


@njit(cache=True, parallel=True)
def _phase2(
    table: np.ndarray,
    nxt: np.ndarray,
    cipher: np.ndarray,
    starts: np.ndarray,
    ring_m: np.ndarray,
    ring_r: np.ndarray,
) -> np.ndarray:  # pragma: no cover
    """IC de cada posición del núcleo inicial con cada par de anillos (central, derecho)."""
    width = ring_m.shape[0]
    out = np.empty((starts.shape[0], width))
    for job in prange(starts.shape[0] * width):
        k, j = job // width, job % width
        out[k, j] = _ic_from(table, nxt, cipher, starts[k], ring_m[j], ring_r[j])
    return out


@njit(cache=True)
def _trigrams_from(
    table: np.ndarray,
    nxt: np.ndarray,
    cipher: np.ndarray,
    plug: np.ndarray,
    start: int,
    ring_m: int,
    ring_r: int,
    logp3: np.ndarray,
) -> float:  # pragma: no cover - Numba
    """Σ log₁₀ p de los trigramas del descifrado con plugboard desde esa ubicación."""
    n = cipher.shape[0]
    left, middle, right = start // 676, (start // 26) % 26, start % 26
    w = left * 676 + ((middle + ring_m) % 26) * 26 + (right + ring_r) % 26
    a = b = 0
    total = 0.0
    for t in range(n):
        w = nxt[w]
        core = (w // 676) * 676 + (((w // 26) % 26 - ring_m) % 26) * 26 + (w % 26 - ring_r) % 26
        x = plug[table[core, plug[cipher[t]]]]
        if t >= 2:
            total += logp3[(a * 26 + b) * 26 + x]
        a, b = b, x
    return total


@njit(cache=True, parallel=True)
def _refine(
    table: np.ndarray,
    nxt: np.ndarray,
    cipher: np.ndarray,
    plug: np.ndarray,
    starts: np.ndarray,
    ring_m: np.ndarray,
    ring_r: np.ndarray,
    logp3: np.ndarray,
) -> np.ndarray:  # pragma: no cover
    """Trigramas del descifrado con el plugboard en cada arranque y par de anillos."""
    width = ring_m.shape[0]
    out = np.empty((starts.shape[0], width))
    for job in prange(starts.shape[0] * width):
        k, j = job // width, job % width
        out[k, j] = _trigrams_from(table, nxt, cipher, plug, starts[k], ring_m[j], ring_r[j], logp3)
    return out


def neighbours(start: int, both: bool = False) -> list[int]:
    """La posición y sus vecinas con el izquierdo o el central una posición corridos (D-066).

    Con anillos supuestos, el central o el izquierdo giran en la fase 1 en otra letra que en
    la máquina verdadera, y la fase 1 puede preferir la posición de después del giro: por eso
    la fase 2 prueba también la posición de antes (4 variantes). El reajuste final, que ya
    tiene el plugboard, prueba las dos direcciones (``both``: 9 variantes).
    """
    left, middle, right = start // 676, (start // 26) % 26, start % 26
    steps = (-1, 0, 1) if both else (0, 1)
    return [
        ((left - dl) % 26) * 676 + ((middle - dm) % 26) * 26 + right for dl in steps for dm in steps
    ]


def ic_at(cipher: np.ndarray, order: Order, start: int, ring_m: int = 0, ring_r: int = 0) -> float:
    """El IC del descifrado sin plugboard en una ubicación (con esos anillos)."""
    codes = np.asarray(cipher, dtype=np.int64)
    return float(
        _ic_from(scrambler_table(order, "B"), step_table(order), codes, start, ring_m, ring_r)
    )


def core_path(order: Order, start: int, ring_m: int, ring_r: int, length: int) -> np.ndarray:
    """Las posiciones del núcleo de cada letra (índices del aleatorizador): (L,)."""
    nxt = step_table(order)
    left, middle, right = start // 676, (start // 26) % 26, start % 26
    w = left * 676 + ((middle + ring_m) % 26) * 26 + (right + ring_r) % 26
    out = np.empty(length, dtype=np.int64)
    for t in range(length):
        w = int(nxt[w])
        out[t] = (w // 676) * 676 + (((w // 26) % 26 - ring_m) % 26) * 26 + (w % 26 - ring_r) % 26
    return out


def paths_for(order: Order, start: int, ring_m: int, ring_r: int, length: int) -> np.ndarray:
    """El aleatorizador de cada letra con esa ubicación: (L, 26) int64 (sin plugboard)."""
    table = scrambler_table(order, "B")
    return np.ascontiguousarray(table[core_path(order, start, ring_m, ring_r, length)], np.int64)


def location_config(
    order: Order, start: int, ring_m: int, ring_r: int, plug: np.ndarray | None = None
) -> EnigmaConfig:
    """La clave de una ubicación (anillo izquierdo en A): ventana = núcleo + anillo."""
    left, middle, right = start // 676, (start // 26) % 26, start % 26
    pairs = hillclimb.plug_pairs(plug) if plug is not None else ()
    return EnigmaConfig(
        rotors=tuple(order),
        reflector="B",
        rings=(0, ring_m, ring_r),
        positions=(left, (middle + ring_m) % 26, (right + ring_r) % 26),
        plugboard=pairs,
    )


# ---------------------------------------------------------------- las tres fases


@dataclass(frozen=True)
class Candidate:
    """Una ubicación candidata: orden, posición del núcleo al empezar, anillos e IC."""

    order: Order
    start: int
    ring_m: int = 0
    ring_r: int = 0
    ic: float = 0.0


def phase1(
    cipher: np.ndarray, orders: Sequence[Order] = ALL_ORDERS, top: int = 100
) -> tuple[list[Candidate], dict[Order, np.ndarray]]:
    """Fase 1: el IC de todas las posiciones de cada orden; las ``top`` mejores ubicaciones."""
    codes = np.asarray(cipher, dtype=np.int64)
    scores: dict[Order, np.ndarray] = {}
    for order in orders:
        table, nxt = scrambler_table(order, "B"), step_table(order)
        with _LOCK:  # un núcleo paralelo a la vez, como la Bombe (D-076)
            scores[order] = _phase1(table, nxt, codes)
    flat = np.concatenate([scores[o] for o in orders])
    best = np.argpartition(-flat, min(top, len(flat) - 1))[:top]
    best = best[np.argsort(-flat[best], kind="stable")]
    ranked = [
        Candidate(orders[int(i) // N_POSITIONS], int(i) % N_POSITIONS, ic=float(flat[i]))
        for i in best
    ]
    return ranked, scores


def phase2(cipher: np.ndarray, candidates: Sequence[Candidate], top: int = 10) -> list[Candidate]:
    """Fase 2: los 676 anillos de cada candidata y de sus vecinas (``neighbours``)."""
    codes = np.asarray(cipher, dtype=np.int64)
    found: list[Candidate] = []
    by_order: dict[Order, list[int]] = {}
    for c in candidates:
        by_order.setdefault(c.order, []).extend(neighbours(c.start))
    for order, starts in by_order.items():
        unique = np.unique(np.array(starts, dtype=np.int64))
        table, nxt = scrambler_table(order, "B"), step_table(order)
        with _LOCK:
            ic = _phase2(table, nxt, codes, unique, RING_M, RING_R)
        for k, start in enumerate(unique):
            j = int(np.argmax(ic[k]))
            found.append(
                Candidate(order, int(start), int(RING_M[j]), int(RING_R[j]), float(ic[k, j]))
            )
    found.sort(key=lambda c: -c.ic)
    return found[:top]


def refine(
    cipher: np.ndarray, candidate: Candidate, plug: np.ndarray, logp3: np.ndarray
) -> Candidate:
    """Con el plugboard ya hallado, vuelve a elegir anillos y vecina por trigramas (D-066)."""
    codes = np.asarray(cipher, dtype=np.int64)
    starts = np.array(neighbours(candidate.start, both=True), dtype=np.int64)
    table, nxt = scrambler_table(candidate.order, "B"), step_table(candidate.order)
    with _LOCK:
        scores = _refine(
            table, nxt, codes, np.asarray(plug, dtype=np.int64), starts, RING_M, RING_R, logp3
        )
    k, j = np.unravel_index(int(np.argmax(scores)), scores.shape)
    return Candidate(candidate.order, int(starts[k]), int(RING_M[j]), int(RING_R[j]), candidate.ic)


@dataclass(frozen=True)
class ClimbResult:
    """El plugboard que encontró el hill climbing en una ubicación, con su puntaje."""

    candidate: Candidate
    plug: np.ndarray
    score: float
    """Σ log₁₀ p de los trigramas, por trigrama."""
    plaintext: np.ndarray


def climb_at(
    cipher: np.ndarray,
    candidate: Candidate,
    logp3: np.ndarray,
    partial: bool = False,
    start_plug: np.ndarray | None = None,
) -> ClimbResult:
    """Hill climbing del plugboard en una ubicación (desde vacío o desde ``start_plug``)."""
    codes = np.asarray(cipher, dtype=np.int64)
    c = candidate
    paths = paths_for(c.order, c.start, c.ring_m, c.ring_r, len(codes))
    if partial and start_plug is None:
        plug, score = hillclimb.e_stecker(paths, codes, logp3, True)
    else:
        first = np.arange(26) if start_plug is None else np.asarray(start_plug, dtype=np.int64)
        plug, score, _, _ = hillclimb.climb_plugboard(paths, codes, first, logp3, True)
    text = hillclimb.decrypt(paths, codes, plug)
    return ClimbResult(c, np.asarray(plug), score / max(1, len(codes) - 2), text)


def phase3(
    cipher: np.ndarray, candidates: Sequence[Candidate], partial: bool = False, refined: int = 3
) -> list[ClimbResult]:
    """Fase 3: hill climbing del plugboard en cada candidata; las ``refined`` mejores se afinan.

    Afinar: con el plugboard hallado se vuelven a elegir los anillos y la vecina por trigramas
    (``refine``) y se sube otra vez desde ese plugboard, mientras mejore (hasta 3 veces).
    """
    logp3 = hillclimb.trigram_table()
    out = sorted((climb_at(cipher, c, logp3, partial) for c in candidates), key=lambda r: -r.score)
    for k in range(min(refined, len(out))):
        for _ in range(3):
            better = refine(cipher, out[k].candidate, out[k].plug, logp3)
            if better == out[k].candidate:
                break
            again = climb_at(cipher, better, logp3, start_plug=out[k].plug)
            if again.score <= out[k].score:
                break
            out[k] = again
    out.sort(key=lambda r: -r.score)
    return out


@dataclass(frozen=True)
class AttackResult:
    """El resultado del ataque: la mejor clave, el texto y lo que pasó en cada fase."""

    best: ClimbResult
    phase1: list[Candidate]
    phase2: list[Candidate]
    phase3: list[ClimbResult]
    seconds: dict[str, float] = field(default_factory=dict)
    scores: dict[Order, np.ndarray] = field(default_factory=dict)
    """El IC de la fase 1 de cada orden en sus 17.576 posiciones (para medir y dibujar)."""

    def rank_of(self, order: Sequence[str], start: int) -> int:
        """Cuántas ubicaciones de la fase 1 superan a la mejor de las que llevan a esa (D-066).

        Con anillos supuestos, la fase 1 puede preferir la posición con el izquierdo o el
        central una posición corridos; las fases 2 y 3 las recuperan (``neighbours``).
        """
        scores = self.scores[(order[0], order[1], order[2])]
        best = max(float(scores[s]) for s in neighbours(start, both=True))
        return int(sum(int((v > best).sum()) for v in self.scores.values()))

    @property
    def config(self) -> EnigmaConfig:
        c = self.best.candidate
        return location_config(c.order, c.start, c.ring_m, c.ring_r, self.best.plug)


def attack(
    cipher: np.ndarray,
    orders: Sequence[Order] = ALL_ORDERS,
    top1: int = 100,
    top2: int = 10,
    partial: bool = False,
) -> AttackResult:
    """Las tres fases de Gillogly sobre un cifrado (enteros 0–25), con anillos y plugboard."""
    seconds = {}
    start = time.perf_counter()
    first, scores = phase1(cipher, orders, top1)
    seconds["fase1"] = time.perf_counter() - start
    start = time.perf_counter()
    second = phase2(cipher, first, top2)
    seconds["fase2"] = time.perf_counter() - start
    start = time.perf_counter()
    third = phase3(cipher, second, partial)
    seconds["fase3"] = time.perf_counter() - start
    return AttackResult(third[0], first, second, third, seconds, scores)


def warm_up() -> float:
    """Compila (o carga de su caché) los núcleos de Numba con un cifrado corto (segundos)."""
    start = time.perf_counter()
    order = ALL_ORDERS[0]
    cipher = np.arange(40, dtype=np.int64) % 26
    table, nxt, one = scrambler_table(order, "B"), step_table(order), np.array([0], np.int64)
    logp3 = hillclimb.trigram_table()
    with _LOCK:
        _phase1(table, nxt, cipher)
        _phase2(table, nxt, cipher, one, RING_M[:2], RING_R[:2])
        _refine(table, nxt, cipher, np.arange(26), one, RING_M[:2], RING_R[:2], logp3)
    hillclimb.warm_up()
    return time.perf_counter() - start
