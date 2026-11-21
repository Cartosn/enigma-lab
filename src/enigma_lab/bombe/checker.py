"""El verificador: de una parada a la clave completa (spec 5.5).

Emula el trabajo que seguía a cada parada en Bletchley Park, en dos etapas.

**Etapa 1 · máquina de verificación** (todas las paradas, en Numba; ver
:func:`enigma_lab.bombe.bombe_numba.check_hypotheses`). Para cada hipótesis candidata
T↔x se leen los hilos que enciende: cada hilo u del cable a es un stecker deducido,
P(a) = u, y por simetría P(u) = a. Si una letra queda con dos parejas, la hipótesis cae.
Además, cada otra componente del menú necesita una hipótesis compatible. Las que
sobreviven traen un plugboard parcial P₀, que ya descifra el crib.

**Etapa 2 · descifrado de prueba.** El idioma se mide con un modelo de 4 letras
interpolado (:func:`enigma_lab.stats.ngrams.interpolated`): log₁₀ P(texto) por la regla
de la cadena.

1. *Puntaje rápido.* Con P₀ y las posiciones de la parada se descifran las letras
   vecinas del crib (hasta ``WINDOW`` a cada lado), se completa el plugboard de esas
   letras por hill climbing y se mide su probabilidad. Fuera del crib no se sabe cuándo
   vuelve a avanzar el central, así que se prueba cada punto posible y se queda el
   mejor. Siguen las ``top`` mejores hipótesis.
2. *Anillos derecho y central.* La Bombe supone anillos AAA. Los anillos reales deciden
   cuándo avanza el central (lo arrastra el derecho al pasar su muesca) y cuándo hay
   doble paso. Se prueban los 26 × 26 pares: cada uno, con la parada, fija la ventana de
   arranque y las posiciones de todo el mensaje. Un par se descarta si no reproduce las
   posiciones de la parada dentro del crib. Los pares que dan las mismas posiciones en
   todo el mensaje son equivalentes.
3. *Plugboard.* Para cada secuencia distinta de posiciones se completa el plugboard por
   hill climbing: desde P₀, que no se toca, se prueban todos los cambios de un cable
   entre las letras libres y se aplica el mejor mientras mejore. Después se alterna:
   con el mejor plugboard se vuelve a elegir la secuencia y se sube otra vez.
4. *Elección.* A priori toda clave (anillos y arranque) es igual de probable, así que
   una secuencia que dan k claves pesa log₁₀ k más (D-036). Gana la de mayor
   log₁₀ P(texto) + log₁₀ k.
5. *Clave equivalente.* El anillo izquierdo no cambia nada que no compense la posición
   del izquierdo, así que se fija en A. La clave devuelta da el mismo cifrado que la
   verdadera, aunque sus anillos y posiciones puedan diferir: un anillo y su posición
   se compensan.

El mejor descifrado es **plausible** si su log₁₀ P por letra supera ``PLAUSIBLE``
(alemán: cerca de −0,7; letras al azar: cerca de −2,7).
"""

from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from numba import njit, prange

from enigma_lab.bombe import bombe_numba
from enigma_lab.bombe.scrambler import Order, scrambler_table
from enigma_lab.bombe.sweep import _LOCK, BombeRun, OrderRun, Stop, _bits
from enigma_lab.bombe.wiring import BombeWiring
from enigma_lab.core.batch import NOTCH, ROTOR_NAMES
from enigma_lab.core.machine import EnigmaConfig, clean
from enigma_lab.core.wiring import ALPHABET
from enigma_lab.stats import ngrams

WINDOW = 13
"""Letras a cada lado del crib que usa el puntaje rápido."""
TOP = 25
"""Hipótesis que pasan del puntaje rápido al descifrado completo."""
MAX_EXAMINED = 300
"""Si ninguna de las ``TOP`` da un texto plausible, se siguen examinando hasta este número."""
PLAUSIBLE = -1.5
"""log₁₀ P por letra desde el que un descifrado se acepta como alemán."""
RING_PRIOR = True
"""Sumar log₁₀ del número de claves que dan cada secuencia de posiciones (D-036)."""


def language_model() -> tuple[np.ndarray, np.ndarray]:
    """El modelo del alemán con la X como separador (muestra): tablas de 3 y de 4 letras."""
    return ngrams.interpolated("aleman", "muestra", "x")


def to_codes(text: str) -> np.ndarray:
    """Texto A–Z a enteros 0–25 (int64)."""
    return np.frombuffer(clean(text).encode("ascii"), dtype=np.uint8).astype(np.int64) - 65


# ---------------------------------------------------------------- resultados


@dataclass(frozen=True)
class Hypothesis:
    """Una hipótesis T↔x que pasó la máquina de verificación.

    ``plug[a]`` es la pareja deducida de la letra a (a misma si va sola), o −1 si la
    hipótesis no dice nada de ella.
    """

    stop: Stop
    wire: int
    plug: tuple[int, ...]

    @property
    def known(self) -> int:
        """Letras cuyo stecker quedó deducido."""
        return sum(1 for v in self.plug if v >= 0)

    def pairs(self) -> str:
        """Los cables deducidos («AG EJ QT»), sin las letras que van solas."""
        return " ".join(sorted(ALPHABET[a] + ALPHABET[b] for a, b in enumerate(self.plug) if b > a))


@dataclass(frozen=True, eq=False)
class Hypotheses:
    """Las hipótesis que sobrevivieron a la etapa 1, como arreglos (pueden ser muchas)."""

    orders: tuple[Order, ...]
    group: np.ndarray  # (H,) índice en ``orders``
    positions: np.ndarray
    turns: np.ndarray
    lit: np.ndarray
    singles: np.ndarray
    wires: np.ndarray
    plugs: np.ndarray  # (H, 26) int8

    def __len__(self) -> int:
        return int(self.positions.shape[0])

    def get(self, k: int) -> Hypothesis:
        stop = Stop(
            self.orders[int(self.group[k])],
            int(self.positions[k]),
            int(self.turns[k]),
            int(self.lit[k]),
            _bits(int(self.singles[k])),
        )
        return Hypothesis(stop, int(self.wires[k]), tuple(int(v) for v in self.plugs[k]))

    def find(self, order: Order, position: int, turn: int, wire: int) -> int | None:
        """Índice de una hipótesis concreta (la verdadera, por ejemplo), o None."""
        if order not in self.orders:
            return None
        hits = np.flatnonzero(
            (self.group == self.orders.index(order))
            & (self.positions == position)
            & (self.turns == turn)
            & (self.wires == wire)
        )
        return int(hits[0]) if len(hits) else None


@dataclass(frozen=True)
class Solution:
    """La clave equivalente que sale de una hipótesis y su descifrado."""

    hypothesis: Hypothesis
    config: EnigmaConfig
    plaintext: str
    score: float  # log₁₀ P por letra del mensaje completo
    quick: float  # puntaje rápido (etapa 2.1)

    @property
    def plausible(self) -> bool:
        return self.score >= PLAUSIBLE


@dataclass(frozen=True)
class Verification:
    """Lo que hizo el verificador con las paradas de un barrido."""

    stops: int
    hypotheses: int
    solutions: tuple[Solution, ...]  # las examinadas en la etapa 2, la mejor primero
    seconds: float

    @property
    def best(self) -> Solution | None:
        return self.solutions[0] if self.solutions else None

    @property
    def plausible(self) -> bool:
        return self.best is not None and self.best.plausible


# ---------------------------------------------------------------- etapa 1


def _rows(run: OrderRun) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Una fila por hipótesis (parada, hilo aislado): (parada, hilo, inicio de cada parada)."""
    bits = (run.singles.astype(np.int64)[:, None] >> np.arange(26)) & 1
    stop_index, wire = np.nonzero(bits)
    start = np.zeros(len(run) + 1, dtype=np.int64)
    np.cumsum(bits.sum(axis=1), out=start[1:])
    return stop_index, wire.astype(np.int64), start


def consistent_stops(
    wiring: BombeWiring, runs: Sequence[OrderRun], reflector: str = "B"
) -> Hypotheses:
    """Etapa 1: las hipótesis de las paradas que no se contradicen, con su plugboard parcial."""
    parts: list[tuple[int, np.ndarray, np.ndarray, OrderRun, np.ndarray]] = []
    for g, run in enumerate(runs):
        if len(run) == 0:
            continue
        stop_index, wire, start = _rows(run)
        if len(wire) == 0:
            continue
        with _LOCK:
            plugs, ok = bombe_numba.check_hypotheses(
                scrambler_table(run.order, reflector),
                wiring.edge_a,
                wiring.edge_b,
                wiring.edge_offset,
                wiring.diag_a,
                wiring.diag_b,
                wiring.letter_codes,
                wiring.test_node,
                wiring.cable_component,
                wiring.test_component,
                wiring.n_components,
                run.positions,
                run.turns,
                start,
                wire,
            )
        parts.append((g, stop_index[ok], wire[ok], run, plugs[ok]))
    orders = tuple(run.order for run in runs)
    if not parts:
        empty = np.empty(0, dtype=np.int64)
        plugs = np.empty((0, 26), np.int8)
        return Hypotheses(orders, empty, empty, empty, empty, empty, empty, plugs)
    return Hypotheses(
        orders,
        np.concatenate([np.full(len(s), g, dtype=np.int64) for g, s, _, _, _ in parts]),
        np.concatenate([run.positions[s] for _, s, _, run, _ in parts]),
        np.concatenate([run.turns[s] for _, s, _, run, _ in parts]),
        np.concatenate([run.lit[s] for _, s, _, run, _ in parts]),
        np.concatenate([run.singles[s] for _, s, _, run, _ in parts]),
        np.concatenate([w for _, _, w, _, _ in parts]),
        np.concatenate([p for _, _, _, _, p in parts]),
    )


# ---------------------------------------------------------------- núcleos de Numba


@njit(cache=True)
def _text_score(
    text: np.ndarray, head: np.ndarray, logp4: np.ndarray
) -> float:  # pragma: no cover - Numba
    """log₁₀ P(texto) por la regla de la cadena: las 3 primeras letras y luego de a 4."""
    n = text.shape[0]
    if n < 3:
        return 0.0
    total = float(head[(text[0] * 26 + text[1]) * 26 + text[2]])
    for k in range(n - 3):
        total += logp4[((text[k] * 26 + text[k + 1]) * 26 + text[k + 2]) * 26 + text[k + 3]]
    return total


@njit(cache=True)
def _decrypt(
    paths: np.ndarray, cipher: np.ndarray, plug: np.ndarray, out: np.ndarray
) -> None:  # pragma: no cover - Numba
    """Descifrado con el plugboard P: letra j = P(S_j(P(c_j)))."""
    for j in range(cipher.shape[0]):
        out[j] = plug[paths[j, plug[cipher[j]]]]


@njit(cache=True)
def _toggle(plug: np.ndarray, p: int, q: int) -> None:  # pragma: no cover - Numba
    """Cambia un cable: si p y q iban juntos los separa; si no, los une (sueltan a sus parejas)."""
    if plug[p] == q:
        plug[p] = p
        plug[q] = q
        return
    rp = plug[p]
    rq = plug[q]
    plug[rp] = rp
    plug[rq] = rq
    plug[p] = q
    plug[q] = p


@njit(cache=True)
def _climb(
    paths: np.ndarray,
    cipher: np.ndarray,
    plug: np.ndarray,
    free: np.ndarray,
    n_free: int,
    head: np.ndarray,
    logp4: np.ndarray,
    buf: np.ndarray,
    saved: np.ndarray,
) -> float:  # pragma: no cover - Numba
    """Hill climbing del plugboard (en el sitio): el mejor cambio de cable, mientras mejore."""
    _decrypt(paths, cipher, plug, buf)
    best = _text_score(buf, head, logp4)
    while True:
        move_p, move_q, move_score = -1, -1, best
        for a in range(n_free):
            for b in range(a + 1, n_free):
                p, q = free[a], free[b]
                saved[:] = plug
                _toggle(plug, p, q)
                _decrypt(paths, cipher, plug, buf)
                score = _text_score(buf, head, logp4)
                plug[:] = saved
                if score > move_score + 1e-9:
                    move_p, move_q, move_score = p, q, score
        if move_p < 0:
            return best
        _toggle(plug, move_p, move_q)
        best = move_score


@njit(cache=True)
def hill_climb(
    paths: np.ndarray,
    cipher: np.ndarray,
    plug: np.ndarray,
    free: np.ndarray,
    head: np.ndarray,
    logp4: np.ndarray,
) -> tuple[np.ndarray, float]:  # pragma: no cover - Numba
    """Completa el plugboard dejando fijas las letras que no están en ``free``.

    ``paths[j]`` es el aleatorizador al cifrar la letra j. Devuelve el plugboard y
    log₁₀ P del descifrado.
    """
    plug = plug.copy()
    buf = np.empty(cipher.shape[0], np.int64)
    saved = np.empty(26, np.int64)
    score = _climb(paths, cipher, plug, free, free.shape[0], head, logp4, buf, saved)
    return plug, score


@njit(cache=True, parallel=True)
def _window_scores(
    table: np.ndarray,
    cipher: np.ndarray,
    crib_pos: int,
    crib_len: int,
    j0: int,
    j1: int,
    positions: np.ndarray,
    turns: np.ndarray,
    plugs: np.ndarray,
    head: np.ndarray,
    logp4: np.ndarray,
) -> np.ndarray:  # pragma: no cover - Numba
    """Puntaje rápido: hill climbing del plugboard sobre las letras j0 ≤ j < j1.

    Fuera del crib no se sabe cuándo vuelve a avanzar el central: lo arrastra el
    derecho una vez cada 26 letras. Con d la letra relativa al crib y t₀ una vuelta, el
    central en la letra d es C_cen + ⌊(d − t₀)/26⌋ − ⌊−t₀/26⌋. En la variante k, t₀ = k;
    sin vuelta dentro del crib (k = 0), t₀ puede ser 0 o cualquier letra de L a 25. Se
    prueba cada t₀ y se queda el mejor puntaje.
    """
    n = positions.shape[0]
    width = j1 - j0
    out = np.empty(n)
    for s in prange(n):
        p = positions[s]
        left, middle, right = p // 676, (p // 26) % 26, p % 26
        paths = np.empty((width, 26), np.int64)
        plug = np.empty(26, np.int64)
        free = np.empty(26, np.int64)
        buf = np.empty(width, np.int64)
        saved = np.empty(26, np.int64)
        best = -np.inf
        first, last = turns[s], turns[s]
        if turns[s] == 0:
            first, last = crib_len - 1, 25  # crib_len − 1 representa t₀ = 0
        for option in range(first, last + 1):
            t0 = 0 if (turns[s] == 0 and option == crib_len - 1) else option
            for j in range(j0, j1):
                d = j - crib_pos
                m = middle + (d - t0) // 26 - (-t0) // 26
                row = left * 676 + (m % 26) * 26 + (right + d + 1) % 26
                for u in range(26):
                    paths[j - j0, u] = table[row, u]
            n_free = 0
            for a in range(26):
                if plugs[s, a] < 0:
                    plug[a] = a
                    free[n_free] = a
                    n_free += 1
                else:
                    plug[a] = plugs[s, a]
            score = _climb(paths, cipher[j0:j1], plug, free, n_free, head, logp4, buf, saved)
            if score > best:
                best = score
        out[s] = best
    return out


def warm_up_kernels() -> None:
    """Compila los núcleos del verificador con datos pequeños (lo usa ``sweep.warm_up``)."""
    head, logp4 = language_model()
    table = scrambler_table(("I", "II", "III"))
    cipher = np.arange(20, dtype=np.int64) % 26
    plugs = np.full((2, 26), -1, np.int8)
    one = np.zeros(2, dtype=np.int64)
    _window_scores(table, cipher, 0, 13, 0, 20, one, one, plugs, head, logp4)
    paths = np.ascontiguousarray(table[:20].astype(np.int64))
    free = np.arange(4, dtype=np.int64)
    hill_climb(paths, cipher, np.arange(26, dtype=np.int64), free, head, logp4)


# ---------------------------------------------------------------- etapa 2


def quick_scores(
    wiring: BombeWiring,
    hypotheses: Hypotheses,
    cipher: np.ndarray,
    crib_position: int,
    reflector: str = "B",
) -> np.ndarray:
    """Etapa 2.1: el puntaje rápido de cada hipótesis (en el orden recibido)."""
    head, logp4 = language_model()
    j0 = max(0, crib_position - WINDOW)
    j1 = min(len(cipher), crib_position + len(wiring.crib) + WINDOW)
    scores = np.empty(len(hypotheses))
    for g, order in enumerate(hypotheses.orders):
        index = np.flatnonzero(hypotheses.group == g)
        if len(index) == 0:
            continue
        with _LOCK:
            scores[index] = _window_scores(
                scrambler_table(order, reflector),
                cipher,
                crib_position,
                len(wiring.crib),
                j0,
                j1,
                hypotheses.positions[index],
                hypotheses.turns[index],
                hypotheses.plugs[index],
                head,
                logp4,
            )
    return scores


def _step_windows(windows: np.ndarray, middle: int, right: int) -> None:
    """Un paso del odómetro para muchas ventanas a la vez (con doble paso)."""
    middle_at = NOTCH[middle, windows[:, 1]]
    right_at = NOTCH[right, windows[:, 2]]
    windows[:, 0] += middle_at
    windows[:, 1] += middle_at | right_at
    windows[:, 2] += 1
    windows %= 26


def ring_settings(
    stop: Stop, crib_position: int, crib_length: int, n_letters: int
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Etapa 2.2: anillos y arranques compatibles con la parada.

    Para cada par de anillos (central, derecho), la ventana al cifrar la primera letra
    del crib es C + (0, anillo central, anillo derecho + 1). La ventana de arranque se
    busca entre las que llegan a ella en ``crib_position + 1`` pasos (el derecho retrocede
    ese número de pasos; el central y el izquierdo, los pocos que pudieron arrastrarse).
    Devuelve, para las filas válidas, los anillos (R, 3), las ventanas de arranque (R, 3)
    y la posición del núcleo de cada letra del mensaje (R, N), como índices de la tabla.
    """
    middle_rotor, right_rotor = (ROTOR_NAMES.index(n) for n in stop.order[1:])
    left, middle, right = stop.position // 676, (stop.position // 26) % 26, stop.position % 26
    ring_m, ring_r = (a.ravel() for a in np.meshgrid(np.arange(26), np.arange(26), indexing="ij"))
    target = np.stack([np.full(676, left), (middle + ring_m) % 26, (right + 1 + ring_r) % 26], 1)
    rings = np.stack([np.zeros(676, np.int64), ring_m, ring_r], 1)
    presses = crib_position + 1
    starts = [
        (target - [back_left, back_middle, presses]) % 26
        for back_left in range(presses // 600 + 2)
        for back_middle in range(presses // 26 + 3)
    ]
    start = np.concatenate(starts).astype(np.int64)
    ring = np.tile(rings, (len(starts), 1))
    windows = start.copy()
    cores = np.empty((len(start), n_letters, 3), dtype=np.int64)
    for t in range(n_letters):
        _step_windows(windows, middle_rotor, right_rotor)
        cores[:, t] = (windows - ring) % 26
    i = np.arange(crib_length)
    expected_middle = (middle + ((stop.turn > 0) & (i >= stop.turn))) % 26
    expected = np.stack([np.full(crib_length, left), expected_middle, (right + i + 1) % 26], 1)
    span = cores[:, crib_position : crib_position + crib_length]
    valid = (span == expected).all(axis=(1, 2))
    index = cores[valid] @ np.array([676, 26, 1])
    return ring[valid], start[valid], index


def solve(
    hypothesis: Hypothesis,
    cipher: np.ndarray,
    crib_position: int,
    crib_length: int,
    reflector: str = "B",
    quick: float = float("nan"),
) -> Solution | None:
    """Etapas 2.2 a 2.5 para una hipótesis: anillos, plugboard y clave equivalente."""
    stop = hypothesis.stop
    rings, starts, index = ring_settings(stop, crib_position, crib_length, len(cipher))
    if len(index) == 0:
        return None
    table = scrambler_table(stop.order, reflector)
    head, logp4 = language_model()
    plug0 = np.array([v if v >= 0 else a for a, v in enumerate(hypothesis.plug)], dtype=np.int64)
    free = np.array([a for a, v in enumerate(hypothesis.plug) if v < 0], dtype=np.int64)
    # Secuencias distintas de posiciones y cuántas claves (anillos y arranque) dan cada una.
    distinct, first, counts = np.unique(index, axis=0, return_index=True, return_counts=True)
    prior = np.log10(counts) if RING_PRIOR else np.zeros(len(counts))
    all_paths = table[distinct].astype(np.int64)  # (D, N, 26)
    columns = np.arange(len(cipher))
    best_post, best_score, best_plug, best_row = -np.inf, -np.inf, plug0, 0
    with _LOCK:
        for row in range(len(distinct)):
            plug, total = hill_climb(
                np.ascontiguousarray(all_paths[row]), cipher, plug0, free, head, logp4
            )
            if total + prior[row] > best_post:
                best_post, best_score, best_plug, best_row = total + prior[row], total, plug, row
        # Alternar: con el mejor plugboard, elegir de nuevo la secuencia de posiciones y
        # volver a subir desde ahí. Sale de los óptimos locales en que el hill climbing de
        # la secuencia correcta se quedó corto por conocer pocas letras.
        for _ in range(4):
            plain = best_plug[all_paths[:, columns, best_plug[cipher]]]
            row = int(np.argmax(ngrams.chain_score(plain, head, logp4) + prior))
            plug, total = hill_climb(
                np.ascontiguousarray(all_paths[row]), cipher, best_plug, free, head, logp4
            )
            if total + prior[row] <= best_post + 1e-9:
                break
            best_post, best_score, best_plug, best_row = total + prior[row], total, plug, row
    plug, row = best_plug, int(first[best_row])
    paths = table[index[row]].astype(np.int64)
    text = "".join(ALPHABET[int(plug[paths[j, plug[c]]])] for j, c in enumerate(cipher))
    pairs = tuple(sorted((ALPHABET[a], ALPHABET[int(b)]) for a, b in enumerate(plug) if int(b) > a))
    config = EnigmaConfig(
        rotors=stop.order,
        reflector=reflector,
        rings=tuple(int(v) for v in rings[row]),
        positions=tuple(int(v) for v in starts[row]),
        plugboard=pairs,
    )
    return Solution(hypothesis, config, text, float(best_score) / max(1, len(cipher)), quick)


def ranking(
    run: BombeRun, ciphertext: str, crib_position: int, hypotheses: Hypotheses | None = None
) -> tuple[Hypotheses, np.ndarray]:
    """Etapas 1 y 2.1: las hipótesis consistentes (si no vienen ya) y su puntaje rápido."""
    cipher = to_codes(ciphertext)
    if hypotheses is None:
        hypotheses = consistent_stops(run.wiring, run.runs, run.settings.reflector)
    if len(hypotheses) == 0:
        return hypotheses, np.empty(0)
    scores = quick_scores(run.wiring, hypotheses, cipher, crib_position, run.settings.reflector)
    return hypotheses, scores


def verify(
    run: BombeRun,
    ciphertext: str,
    crib_position: int,
    top: int = TOP,
    hypotheses: Hypotheses | None = None,
) -> Verification:
    """El verificador completo sobre las paradas de un barrido.

    Descifra las ``top`` hipótesis con mejor puntaje rápido. Si ninguna da un texto
    plausible, sigue bajando por el ranking, como seguía Bletchley con la parada siguiente,
    hasta encontrar una o examinar ``MAX_EXAMINED``.
    """
    start = time.perf_counter()
    cipher = to_codes(ciphertext)
    hypotheses, quick = ranking(run, ciphertext, crib_position, hypotheses)
    solutions: list[Solution] = []
    for count, k in enumerate(np.argsort(-quick, kind="stable")):
        if count >= MAX_EXAMINED or (count >= top and any(s.plausible for s in solutions)):
            break
        solution = solve(
            hypotheses.get(int(k)),
            cipher,
            crib_position,
            len(run.wiring.crib),
            run.settings.reflector,
            float(quick[k]),
        )
        if solution is not None:
            solutions.append(solution)
    solutions.sort(key=lambda s: -s.score)
    return Verification(run.n_stops, len(hypotheses), tuple(solutions), time.perf_counter() - start)
