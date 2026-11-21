"""La prueba secuencial de Wald (SPRT) con los decibanes del Banburismus (spec 5.6).

**La prueba.** Los decibanes se suman columna por columna. La profundidad (H1) se acepta
en cuanto el puntaje llega a A = 10·log₁₀((1 − β)/α) y se descarta (H0) en cuanto baja a
B = 10·log₁₀(β/(1 − α)); entre los dos se sigue leyendo. α es la probabilidad de aceptar
una profundidad que no existe, y β la de descartar una verdadera. Con α = β = 1 %,
A = −B = 10·log₁₀ 99 = 19,96 dB. Turing usó este análisis secuencial en Bletchley Park
antes de que Wald lo publicara (1945).

**La aproximación de Wald.** La identidad de Wald es exacta: E[S_N] = μ·E[N], con S_N el
puntaje al decidir, N las letras leídas y μ los decibanes por letra en promedio. Si el
puntaje se detuviera justo en un umbral, E[S_N] valdría (1 − β)·A + β·B en profundidad y
α·A + (1 − α)·B al azar. Con letras sueltas y 1/17:

- E[N | H1] ≈ (0,99 · 19,96 − 0,01 · 19,96) / 0,0211 = 929 letras;
- E[N | H0] ≈ (0,01 · 19,96 − 0,99 · 19,96) / (−0,0184) = 1.062 letras.

**El sobrepaso.** El puntaje no se detiene en el umbral sino al cruzarlo, y lo pasa. Una
repetición suma 1,845 dB de golpe, así que arriba el sobrepaso llega hasta 1,845 dB; una
no repetición resta solo 0,093 dB, así que abajo apenas se nota. Arriba, E[S_N] es mayor
que A y por la identidad hacen falta más letras que las 929. El sobrepaso además deja los
errores reales por debajo del α y el β nominales.

- :func:`exact_letters` calcula exactamente la prueba con letras sueltas independientes,
  sin simulación.
- :func:`run_sprt` la corre sobre miles de secuencias de repeticiones reales (en Numba).
- :func:`sprt_reference` es la misma prueba en Python puro, para las pruebas.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from functools import cache

import numpy as np
from numba import njit

from enigma_lab.banburismus.scoring import TURING, RepeatModel, decibans


def thresholds(alpha: float = 0.01, beta: float | None = None) -> tuple[float, float]:
    """Umbrales de Wald en decibanes: (A, B) = (10·log₁₀((1 − β)/α), 10·log₁₀(β/(1 − α))).

    Con α = β = 1 % son ±19,96 dB; con 5 %, ±12,79; con 0,1 %, ±29,99.
    """
    beta = alpha if beta is None else beta
    return decibans((1 - beta) / alpha), decibans(beta / (1 - alpha))


def wald_letters(
    drift: float, depth: bool, alpha: float = 0.01, beta: float | None = None
) -> float:
    """Letras esperadas hasta decidir según la aproximación de Wald (sin sobrepaso).

    - En profundidad (H1): E[N] ≈ ((1 − β)·A + β·B) / μ₁.
    - Al azar (H0): E[N] ≈ (α·A + (1 − α)·B) / μ₀.

    ``drift`` es μ, los decibanes por letra en promedio bajo esa hipótesis.
    """
    beta = alpha if beta is None else beta
    upper, lower = thresholds(alpha, beta)
    if depth:
        return ((1 - beta) * upper + beta * lower) / drift
    return (alpha * upper + (1 - alpha) * lower) / drift


# ---------------------------------------------------------------- cálculo exacto


@dataclass(frozen=True)
class ExactSPRT:
    """El SPRT con letras sueltas independientes, calculado exactamente.

    Attributes:
        p_repeat: probabilidad de repetición de cada columna (1/17 o 1/26).
        upper, lower: umbrales A y B, en decibanes.
        letters: E[N], las letras esperadas hasta decidir.
        accept_depth: probabilidad de aceptar la profundidad.
        final_upper, final_lower: puntaje medio al decidir, arriba y abajo.
        tail: probabilidad de seguir sin decidir al cortar el cálculo.
    """

    p_repeat: float
    upper: float
    lower: float
    letters: float
    accept_depth: float
    final_upper: float
    final_lower: float
    tail: float

    @property
    def reject_depth(self) -> float:
        return 1 - self.accept_depth - self.tail

    @property
    def overshoot_upper(self) -> float:
        """Cuánto pasa el puntaje el umbral A, en promedio, cuando lo cruza."""
        return self.final_upper - self.upper

    @property
    def overshoot_lower(self) -> float:
        """Cuánto baja el puntaje de B, en promedio, cuando lo cruza."""
        return self.lower - self.final_lower

    @property
    def mean_final(self) -> float:
        """E[S_N]: el puntaje medio al decidir."""
        return self.accept_depth * self.final_upper + self.reject_depth * self.final_lower


@cache
def exact_letters(
    p_repeat: float,
    plus: float,
    minus: float,
    upper: float,
    lower: float,
    max_letters: int = 100_000,
    tolerance: float = 1e-13,
) -> ExactSPRT:
    """Distribución exacta del SPRT con letras sueltas independientes.

    Tras n letras con r repeticiones, el puntaje es S = r·más + (n − r)·menos: el estado
    es el par (n, r). Se lleva la probabilidad de cada r que sigue sin decidir. En cada
    letra, r pasa a r + 1 con probabilidad p o se queda igual con 1 − p, y las que cruzan
    un umbral se retiran con su puntaje. Como S crece con r, las que cruzan están siempre
    en los extremos de la lista: arriba cruzan las de más repeticiones.
    """
    alive, low = [1.0], 0  # alive[i] = P(r = low + i y todavía sin decidir)
    letters = accept = sum_upper = sum_lower = 0.0
    for n in range(1, max_letters + 1):
        grown = [0.0] * (len(alive) + 1)
        for i, prob in enumerate(alive):
            grown[i] += prob * (1 - p_repeat)
            grown[i + 1] += prob * p_repeat
        alive = grown
        while alive:  # arriba: la r más alta es la de mayor puntaje
            r = low + len(alive) - 1
            score = r * plus + (n - r) * minus
            if score < upper:
                break
            prob = alive.pop()
            accept += prob
            sum_upper += prob * score
            letters += prob * n
        while alive:  # abajo: la r más baja es la de menor puntaje
            score = low * plus + (n - low) * minus
            if score > lower:
                break
            prob = alive.pop(0)
            low += 1
            sum_lower += prob * score
            letters += prob * n
        if sum(alive) < tolerance:
            break
    tail = sum(alive)
    reject = 1 - accept - tail
    return ExactSPRT(
        p_repeat=p_repeat,
        upper=upper,
        lower=lower,
        letters=letters,
        accept_depth=accept,
        final_upper=sum_upper / accept if accept else float("nan"),
        final_lower=sum_lower / reject if reject else float("nan"),
        tail=tail,
    )


def exact_turing(alpha: float = 0.01, depth: bool = True) -> ExactSPRT:
    """El cálculo exacto con el modelo de Turing: columnas que repiten con 1/17 o con 1/26."""
    upper, lower = thresholds(alpha)
    p = TURING.probs[0] if depth else TURING.p_random
    return exact_letters(p, float(TURING.plus[0]), float(TURING.minus[0]), upper, lower)


def wald_gap(alpha: float = 0.01, depth: bool = True) -> dict[str, float]:
    """De dónde salen las letras de diferencia entre el cálculo exacto y Wald (α = β).

    La identidad E[N] = E[S_N]/μ es exacta, así que la diferencia es la de los puntajes
    finales dividida por μ. Con α' y β' los errores reales y δ↑, δ↓ los sobrepasos medios
    de cada umbral, en profundidad

        E[S_N] − ((1 − β)·A + β·B) = (β − β')·(A − B) + (1 − β')·δ↑ − β'·δ↓,

    y al azar, (α' − α)·(A − B) + α'·δ↑ − (1 − α')·δ↓. Cada término, dividido por μ, son
    letras: ``errores``, ``sobrepaso_arriba`` y ``sobrepaso_abajo``; ``total`` es la suma.
    """
    exact = exact_turing(alpha, depth)
    mu = TURING.drift(depth)
    upper, lower = thresholds(alpha)
    wrong = exact.reject_depth if depth else exact.accept_depth
    error_term = (alpha - wrong) if depth else (wrong - alpha)
    return {
        "errores": error_term * (upper - lower) / mu,
        "sobrepaso_arriba": exact.accept_depth * exact.overshoot_upper / mu,
        "sobrepaso_abajo": -exact.reject_depth * exact.overshoot_lower / mu,
        "total": exact.letters - wald_letters(mu, depth, alpha),
    }


# ---------------------------------------------------------------- simulación


@njit(cache=True)
def _sprt_kernel(
    repeated: np.ndarray,
    plus: np.ndarray,
    minus: np.ndarray,
    uppers: np.ndarray,
    lowers: np.ndarray,
    checkpoints: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:  # pragma: no cover - Numba
    """El SPRT en cada fila de ``repeated`` (N, L), con m pares de umbrales a la vez.

    Devuelve las letras hasta decidir (0 si no decidió), la decisión (+1 profundidad, −1
    azar, 0 sin decidir), el puntaje al decidir y el puntaje tras cada número de letras de
    ``checkpoints`` (ordenados), que no se detiene.
    """
    n, length = repeated.shape
    k, m, c_total = plus.shape[0], uppers.shape[0], checkpoints.shape[0]
    letters = np.zeros((n, m), np.int64)
    decision = np.zeros((n, m), np.int8)
    final = np.full((n, m), np.nan)
    at = np.full((n, c_total), np.nan)
    for i in range(n):
        score, run, c = 0.0, 0, 0
        for j in range(length):
            state = run if run < k - 1 else k - 1
            if repeated[i, j]:
                score += plus[state]
                run += 1
            else:
                score += minus[state]
                run = 0
            while c < c_total and checkpoints[c] == j + 1:
                at[i, c] = score
                c += 1
            for t in range(m):
                if decision[i, t] != 0:
                    continue
                if score >= uppers[t]:
                    decision[i, t], letters[i, t], final[i, t] = 1, j + 1, score
                elif score <= lowers[t]:
                    decision[i, t], letters[i, t], final[i, t] = -1, j + 1, score
    return letters, decision, final, at


@dataclass(frozen=True)
class SPRTResult:
    """El SPRT sobre N secuencias con m pares de umbrales.

    Attributes:
        alphas: α = β de cada par de umbrales.
        uppers, lowers: (m,) umbrales A y B, en decibanes.
        letters: (N, m) letras hasta decidir; NaN si no decidió.
        decision: (N, m) +1 si aceptó la profundidad, −1 si la descartó, 0 si no decidió.
        final: (N, m) puntaje al decidir.
        checkpoints: (c,) números de letras en los que se anotó el puntaje.
        at: (N, c) puntaje tras esas letras, sin detenerse.
    """

    alphas: tuple[float, ...]
    uppers: np.ndarray
    lowers: np.ndarray
    letters: np.ndarray
    decision: np.ndarray
    final: np.ndarray
    checkpoints: np.ndarray
    at: np.ndarray


def run_sprt(
    repeated: np.ndarray,
    model: RepeatModel = TURING,
    alphas: Sequence[float] = (0.01,),
    checkpoints: Sequence[int] = (),
) -> SPRTResult:
    """Corre el SPRT sobre cada fila de ``repeated`` (N, L) con los umbrales de cada α = β."""
    pairs = [thresholds(a) for a in alphas]
    uppers = np.array([u for u, _ in pairs])
    lowers = np.array([b for _, b in pairs])
    marks = np.array(sorted(checkpoints), dtype=np.int64)
    letters, decision, final, at = _sprt_kernel(
        np.ascontiguousarray(repeated, dtype=np.bool_),
        model.plus.astype(np.float64),
        model.minus.astype(np.float64),
        uppers,
        lowers,
        marks,
    )
    return SPRTResult(
        alphas=tuple(alphas),
        uppers=uppers,
        lowers=lowers,
        letters=np.where(decision != 0, letters, np.nan),
        decision=decision,
        final=final,
        checkpoints=marks,
        at=at,
    )


def sprt_reference(
    repeated: np.ndarray, model: RepeatModel, upper: float, lower: float
) -> tuple[int | None, int, float]:
    """La misma prueba en Python puro: (letras hasta decidir o None, decisión, puntaje)."""
    plus, minus = model.plus, model.minus
    score, run = 0.0, 0
    for j, hit in enumerate(np.asarray(repeated, dtype=bool)):
        state = min(run, model.order - 1)
        if hit:
            score += float(plus[state])
            run += 1
        else:
            score += float(minus[state])
            run = 0
        if score >= upper:
            return j + 1, 1, score
        if score <= lower:
            return j + 1, -1, score
    return None, 0, score


def warm_up() -> None:
    """Compila (o carga de la caché) el núcleo de Numba con una secuencia corta."""
    run_sprt(np.zeros((1, 4), dtype=bool), TURING, (0.01,), (2,))
