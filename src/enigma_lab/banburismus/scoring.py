"""El peso de la evidencia en decibanes, con letras sueltas o con multigramas (spec 5.6).

**Decibanes.** Turing medía la evidencia a favor de una hipótesis con el logaritmo del
factor de Bayes. Un ban es un factor 10, y un decibán, su décima parte:

    peso = 10 · log₁₀( P(datos | profundidad) / P(datos | azar) )   [dB].

El logaritmo convierte productos en sumas, así que la evidencia de observaciones
independientes se suma: es el puntaje que se acumula columna por columna.

**Letras sueltas** (Wikipedia, «Banburismus»). En profundidad, dos mensajes navales
alemanes repiten letra en la misma columna 1 de cada 17 veces; dos textos al azar, 1 de
cada 26. Cada columna aporta:

- si repite, 10·log₁₀((1/17)/(1/26)) = +1,845 dB;
- si no repite, 10·log₁₀((16/17)/(25/26)) = −0,093 dB.

En promedio, el puntaje avanza (1/17)(+1,845) + (16/17)(−0,093) = +0,0211 dB por letra en
profundidad, y (1/26)(+1,845) + (25/26)(−0,093) = −0,0184 dB al azar. Son las
divergencias de Kullback-Leibler entre las dos hipótesis, medidas en decibanes: muy
poca evidencia por letra.

**Multigramas.** En texto real las repeticiones vienen en racimos: si dos textos
alineados coinciden en una letra, es más probable que coincidan también en la siguiente.
Por eso Turing puntuaba aparte las repeticiones de bigramas, trigramas y tetragramas.
Aquí se hace con la regla de la cadena: la probabilidad de repetir depende de la racha r
de columnas que acaban de repetir (0, 1, 2… hasta k − 1):

    h_r = P(la columna repite | las r anteriores repiten y la previa a ellas no).

Con ρₙ, la probabilidad de que dos n-gramas del corpus tomados al azar coincidan (el IC
de los n-gramas, con ρ₀ = 1):

    h_r = (ρ_{r+1} − ρ_{r+2}) / (ρ_r − ρ_{r+1})   y, en la última racha,  h_{k−1} = ρ_k / ρ_{k−1}.

Con k = 1 queda h₀ = ρ₁: la tasa de repetición del corpus. Al azar la probabilidad es
siempre 1/26, así que una columna aporta 10·log₁₀(h_r / (1/26)) si repite y
10·log₁₀((1 − h_r) / (25/26)) si no. Un bigrama repetido pesa más que dos letras sueltas
repetidas: la segunda letra llega con la racha r = 1.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from functools import cache

import numpy as np
import pandas as pd

from enigma_lab.banburismus.depth import OFFSETS, repeats
from enigma_lab.stats.corpus import Mode, Source, load_codes
from enigma_lab.stats.ngrams import ngram_index

P_DEPTH = 1 / 17
"""Tasa de repetición en profundidad del texto naval alemán (Wikipedia, «Banburismus»)."""

P_RANDOM = 1 / 26
"""Tasa de repetición de dos textos al azar."""


def decibans(ratio: float) -> float:
    """10 · log₁₀ de un cociente de probabilidades (un factor de Bayes), en decibanes."""
    return 10 * math.log10(ratio)


def repeat_weight(p_depth: float = P_DEPTH, p_random: float = P_RANDOM) -> float:
    """Decibanes de una repetición: 10·log₁₀(p_depth / p_random) = +1,845 con 1/17 y 1/26."""
    return decibans(p_depth / p_random)


def non_repeat_weight(p_depth: float = P_DEPTH, p_random: float = P_RANDOM) -> float:
    """Decibanes de una no repetición: 10·log₁₀((1 − p_depth)/(1 − p_random)) = −0,093."""
    return decibans((1 - p_depth) / (1 - p_random))


def expected_weight(p_true: float, p_depth: float = P_DEPTH, p_random: float = P_RANDOM) -> float:
    """Decibanes por letra, en promedio, si las columnas repiten con probabilidad ``p_true``.

    Con p_true = 1/17 (profundidad) da +0,0211; con 1/26 (azar), −0,0184.
    """
    plus, minus = repeat_weight(p_depth, p_random), non_repeat_weight(p_depth, p_random)
    return p_true * plus + (1 - p_true) * minus


# ---------------------------------------------------------------- el modelo de repeticiones


@dataclass(frozen=True)
class RepeatModel:
    """Probabilidad de repetición en profundidad según la racha de repeticiones previas.

    ``probs[r]`` es h_r, la probabilidad de que una columna repita si las r anteriores
    repitieron; la última vale para «r o más». Al azar es siempre ``p_random``.
    """

    key: str
    label: str
    probs: tuple[float, ...]
    p_random: float = P_RANDOM

    @property
    def order(self) -> int:
        """Hasta qué n-grama puntúa: 1 con letras sueltas, 3 con bigramas y trigramas."""
        return len(self.probs)

    @property
    def plus(self) -> np.ndarray:
        """Decibanes de una repetición según la racha previa: 10·log₁₀(h_r / (1/26))."""
        return np.array([decibans(h / self.p_random) for h in self.probs])

    @property
    def minus(self) -> np.ndarray:
        """Decibanes de una no repetición según la racha: 10·log₁₀((1 − h_r) / (25/26))."""
        return np.array([decibans((1 - h) / (1 - self.p_random)) for h in self.probs])

    def _chance(self, depth: bool) -> np.ndarray:
        """Probabilidad de repetir en cada racha: h_r en profundidad, 1/26 al azar."""
        return np.array(self.probs) if depth else np.full(self.order, self.p_random)

    def stationary(self, depth: bool) -> np.ndarray:
        """Frecuencia de cada racha a la larga.

        La racha es una cadena de Markov: desde r se pasa a min(r + 1, k − 1) si la columna
        repite y a 0 si no. Su distribución estacionaria cumple π_r = π_{r−1}·p_{r−1} y, en la
        última, π_{k−1}·(1 − p_{k−1}) = π_{k−2}·p_{k−2}.
        """
        p = self._chance(depth)
        weights = np.ones(self.order)
        for r in range(1, self.order):
            weights[r] = weights[r - 1] * p[r - 1]
        if self.order > 1:
            weights[-1] /= 1 - p[-1]
        result: np.ndarray = weights / weights.sum()
        return result

    def drift(self, depth: bool) -> float:
        """Decibanes por letra en promedio, si el texto sigue este modelo (o es azar).

        Σ_r π_r · (p_r · más_r + (1 − p_r) · menos_r). Con letras sueltas y 1/17 da +0,0211
        en profundidad y −0,0184 al azar.
        """
        p = self._chance(depth)
        per_state = p * self.plus + (1 - p) * self.minus
        return float(self.stationary(depth) @ per_state)


TURING = RepeatModel("letras_1_17", "Letras sueltas, tasa 1/17 (Turing)", (P_DEPTH,))
"""El modelo de Turing: letras sueltas, 1/17 en profundidad y 1/26 al azar."""

SCORINGS: dict[str, str] = {
    "letras_1_17": "Letras sueltas, tasa 1/17 (Turing)",
    "letras": "Letras sueltas, tasa del corpus",
    "trigramas": "Bigramas y trigramas",
    "tetragramas": "Hasta tetragramas",
}
"""Las puntuaciones de E6 y de la página Banburismus."""

ORDERS = {"letras": 1, "trigramas": 3, "tetragramas": 4}
"""Hasta qué n-grama puntúa cada modelo medido en el corpus."""


@cache
def ngram_coincidence(n: int, source: Source = "muestra", mode: Mode = "x") -> float:
    """ρₙ: probabilidad de que dos n-gramas tomados al azar del corpus alemán sean iguales.

    Es Σ_g f_g², con f_g la frecuencia del n-grama g. Con n = 1 es el IC del corpus: la
    tasa de repetición de dos textos alemanes en profundidad.
    """
    codes = load_codes("aleman", source, mode)
    counts = np.bincount(ngram_index(codes, n), minlength=26**n).astype(np.float64)
    freq = counts / counts.sum()
    return float(freq @ freq)


def run_probabilities(rho: list[float]) -> tuple[float, ...]:
    """h_0 … h_{k−1} a partir de ρ₀ = 1, ρ₁ … ρ_k (ver el docstring del módulo)."""
    k = len(rho) - 1
    probs = [(rho[r + 1] - rho[r + 2]) / (rho[r] - rho[r + 1]) for r in range(k - 1)]
    return (*probs, rho[k] / rho[k - 1])


@cache
def corpus_model(order: int, source: Source = "muestra", mode: Mode = "x") -> RepeatModel:
    """El modelo de rachas hasta el n-grama ``order``, medido en el corpus alemán."""
    rho = [1.0] + [ngram_coincidence(n, source, mode) for n in range(1, order + 1)]
    key = {v: k for k, v in ORDERS.items()}[order]
    return RepeatModel(key, SCORINGS[key], run_probabilities(rho))


def scoring_model(key: str, source: Source = "muestra", mode: Mode = "x") -> RepeatModel:
    """El modelo de una puntuación de ``SCORINGS``: el de Turing o uno medido en el corpus."""
    if key == TURING.key:
        return TURING
    if key not in ORDERS:
        raise ValueError(f"puntuación desconocida: {key!r} (usa una de {list(SCORINGS)})")
    return replace(corpus_model(ORDERS[key], source, mode), key=key, label=SCORINGS[key])


# ---------------------------------------------------------------- puntuar columnas


def run_state(repeated: np.ndarray, order: int) -> np.ndarray:
    """Racha de cada columna: cuántas de las anteriores repitieron seguidas (hasta order − 1).

    Vale para una fila o para un lote (N, L), sobre la última dimensión.
    """
    x = np.asarray(repeated, dtype=bool)
    index = np.arange(x.shape[-1])
    last_miss = np.maximum.accumulate(np.where(x, -1, index), axis=-1)
    ending_here = index - last_miss  # repeticiones seguidas que terminan en cada columna
    state = np.zeros(x.shape, dtype=np.int64)
    state[..., 1:] = ending_here[..., :-1]
    return np.minimum(state, order - 1)


def column_weights(repeated: np.ndarray, model: RepeatModel = TURING) -> np.ndarray:
    """Decibanes que aporta cada columna, según repita o no y según su racha."""
    state = run_state(repeated, model.order)
    weights: np.ndarray = np.where(repeated, model.plus[state], model.minus[state])
    return weights


def trajectory(repeated: np.ndarray, model: RepeatModel = TURING) -> np.ndarray:
    """El puntaje acumulado tras cada columna: la trayectoria de decibanes."""
    cumulative: np.ndarray = np.cumsum(column_weights(repeated, model), axis=-1)
    return cumulative


def offset_scores(
    cipher1: np.ndarray,
    cipher2: np.ndarray,
    length: int,
    model: RepeatModel = TURING,
    offsets: np.ndarray = OFFSETS,
) -> pd.DataFrame:
    """Para cada desplazamiento: repeticiones, bigramas y trigramas repetidos y decibanes.

    Se comparan ``length`` columnas en cada desplazamiento, como en la mesa de luz de
    Bletchley Park: los dos mensajes, uno sobre otro, corridos d lugares.
    """
    rows = []
    for d in offsets:
        x = repeats(cipher1, cipher2, int(d), length)
        rows.append(
            {
                "desplazamiento": int(d),
                "repeticiones": int(x.sum()),
                "bigramas": int((x[1:] & x[:-1]).sum()),
                "trigramas": int((x[2:] & x[1:-1] & x[:-2]).sum()),
                "decibanes": float(column_weights(x, model).sum()),
            }
        )
    return pd.DataFrame(rows)
