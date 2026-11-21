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
