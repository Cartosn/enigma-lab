"""Log-probabilidades de n-gramas para puntuar descifrados (spec 5.3).

Un modelo de n-gramas guarda, para cada grupo de n letras, log₁₀ de su frecuencia en
el corpus. La puntuación de un texto es la suma de las log-probabilidades de todos sus
n-gramas solapados: un texto en alemán puntúa mucho más alto que uno al azar, y así el
verificador de la Bombe y el ataque moderno distinguen el descifrado bueno.

Los n-gramas que no aparecen en el corpus reciben un piso de log₁₀(0,01 / total): un
centésimo de una aparición. Así un solo n-grama raro no anula la puntuación.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view

from enigma_lab.stats.corpus import Language, Mode, Source, load_codes

FLOOR_COUNT = 0.01


def ngram_index(codes: np.ndarray, n: int) -> np.ndarray:
    """Índice de cada n-grama solapado: Σ letra_k · 26^(n − 1 − k), sobre la última dimensión."""
    windows = sliding_window_view(np.asarray(codes, dtype=np.int64), n, axis=-1)
    weights = 26 ** np.arange(n - 1, -1, -1, dtype=np.int64)
    result: np.ndarray = windows @ weights
    return result


@dataclass(frozen=True)
class NgramModel:
    """Modelo de n-gramas: log₁₀ de las probabilidades de los 26ⁿ grupos posibles."""

    n: int
    log_probs: np.ndarray  # (26**n,), float32
    total: int

    @classmethod
    def from_codes(cls, codes: np.ndarray, n: int) -> NgramModel:
        """Cuenta los n-gramas de un corpus (enteros 0–25) y pasa a log-probabilidades."""
        counts = np.bincount(ngram_index(codes, n), minlength=26**n).astype(np.float64)
        total = int(counts.sum())
        counts[counts == 0] = FLOOR_COUNT
        return cls(n=n, log_probs=np.log10(counts / total).astype(np.float32), total=total)

    @property
    def floor(self) -> float:
        """La log-probabilidad de un n-grama que no aparece en el corpus."""
        return float(np.log10(FLOOR_COUNT / self.total))

    def score(self, codes: np.ndarray) -> np.ndarray | float:
        """Suma de log₁₀ p de los n-gramas solapados (un texto o un lote (N, L))."""
        scores = self.log_probs[ngram_index(codes, self.n)].sum(axis=-1, dtype=np.float64)
        return float(scores) if np.ndim(scores) == 0 else scores

    def score_per_ngram(self, codes: np.ndarray) -> np.ndarray | float:
        """Puntuación media por n-grama, comparable entre textos de distinta longitud."""
        length = np.shape(codes)[-1] - self.n + 1
        result = np.asarray(self.score(codes)) / length
        return float(result) if result.ndim == 0 else result


@cache
def model(
    language: Language = "aleman", n: int = 4, source: Source = "muestra", mode: Mode = "letras"
) -> NgramModel:
    """El modelo de n-gramas de un idioma (en caché: se construye una vez por proceso)."""
    return NgramModel.from_codes(load_codes(language, source, mode), n)


INTERPOLATION = (0.6, 0.25, 0.1, 0.05)
"""Pesos λ₄, λ₃, λ₂, λ₁ del modelo interpolado (suman 1)."""


def interpolated_log_probs(
    codes: np.ndarray, weights: tuple[float, ...] = INTERPOLATION
) -> np.ndarray:
    """log₁₀ P(d | a b c) para los 26⁴ cuadrigramas, interpolando de 4 a 1 letras.

    Con c(·) los conteos del corpus:

        P(d | abc) = λ₄ c(abcd)/c(abc) + λ₃ c(bcd)/c(bc) + λ₂ c(cd)/c(c) + λ₁ c(d)/N.

    A diferencia de la suma de cuadrigramas, cada letra se puntúa una sola vez, por la
    probabilidad de que siga a las tres anteriores, y un cuadrigrama que no apareció en
    el corpus hereda la probabilidad de los trigramas, bigramas y letras. Así el modelo
    distingue mejor textos que difieren en una sola letra (lo usa el verificador de la
    Bombe; ver D-036). Devuelve un arreglo (26⁴,) float32 indexado como
    :func:`ngram_index`.
    """
    counts = [
        np.bincount(ngram_index(codes, k), minlength=26**k).astype(np.float64) for k in (1, 2, 3, 4)
    ]
    c1, c2, c3, c4 = counts
    index = np.arange(26**4)
    a, b, c, d = index // 17576, (index // 676) % 26, (index // 26) % 26, index % 26

    def ratio(num: np.ndarray, den: np.ndarray) -> np.ndarray:
        return np.divide(num, den, out=np.zeros_like(num), where=den > 0)

    p4 = ratio(c4, c3[a * 676 + b * 26 + c])
    p3 = ratio(c3[b * 676 + c * 26 + d], c2[b * 26 + c])
    p2 = ratio(c2[c * 26 + d], c1[c])
    p1 = c1[d] / c1.sum()
    l4, l3, l2, l1 = weights
    return np.log10(l4 * p4 + l3 * p3 + l2 * p2 + l1 * p1).astype(np.float32)


def interpolated_head(codes: np.ndarray, weights: tuple[float, ...] = INTERPOLATION) -> np.ndarray:
    """log₁₀ P(a) + log₁₀ P(b | a) + log₁₀ P(c | ab) para las 26³ primeras letras de un texto.

    Las tres primeras letras no tienen tres anteriores. Con ellas la puntuación de un
    texto es la regla de la cadena completa:

        log P(x₀…x_{N−1}) = log P(x₀ x₁ x₂) + Σ_{j ≥ 3} log P(x_j | x_{j−3} x_{j−2} x_{j−1}),

    con P(b | a) y P(c | ab) interpolados con los mismos pesos, renormalizados.
    """
    c1, c2, c3 = (
        np.bincount(ngram_index(codes, k), minlength=26**k).astype(np.float64) for k in (1, 2, 3)
    )
    _, l3, l2, l1 = weights
    index = np.arange(26**3)
    a, b, c = index // 676, (index // 26) % 26, index % 26

    def ratio(num: np.ndarray, den: np.ndarray) -> np.ndarray:
        return np.divide(num, den, out=np.zeros_like(num), where=den > 0)

    p1 = c1 / c1.sum()
    p_b = (l2 * ratio(c2[a * 26 + b], c1[a]) + l1 * p1[b]) / (l2 + l1)
    p_c = (l3 * ratio(c3, c2[a * 26 + b]) + l2 * ratio(c2[b * 26 + c], c1[b]) + l1 * p1[c]) / (
        l3 + l2 + l1
    )
    return (np.log10(p1[a]) + np.log10(p_b) + np.log10(p_c)).astype(np.float32)


@cache
def interpolated(
    language: Language = "aleman", source: Source = "muestra", mode: Mode = "letras"
) -> tuple[np.ndarray, np.ndarray]:
    """El modelo interpolado de un idioma, en caché: (tabla de las 3 primeras letras, de 4)."""
    codes = load_codes(language, source, mode)
    return interpolated_head(codes), interpolated_log_probs(codes)


def chain_score(text: np.ndarray, head: np.ndarray, log_probs: np.ndarray) -> np.ndarray | float:
    """log₁₀ P(texto) con la regla de la cadena del modelo interpolado (un texto o (N, L))."""
    codes = np.asarray(text, dtype=np.int64)
    first = codes[..., 0] * 676 + codes[..., 1] * 26 + codes[..., 2]
    scores = head[first] + log_probs[ngram_index(codes, 4)].sum(axis=-1, dtype=np.float64)
    return float(scores) if np.ndim(scores) == 0 else scores
