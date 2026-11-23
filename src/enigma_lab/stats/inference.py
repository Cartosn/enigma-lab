"""Inferencia: intervalos de confianza y la probabilidad del distinguidor.

- Proporciones con el **intervalo de Wilson**, que se porta bien aunque la proporción
  sea 0 o 1 (el intervalo normal daría [1, 1] con 10.000 aciertos de 10.000).
- **Distinguidor por puntos fijos:** en Enigma ninguna letra se cifra a sí misma. Si
  cada letra se cifrara con una sustitución al azar, coincidiría con su original con
  probabilidad 1/26, y que ninguna de L coincida pasaría con probabilidad (25/26)^L.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.stats import norm


def wilson_interval(successes: int, n: int, confidence: float = 0.95) -> tuple[float, float]:
    """Intervalo de Wilson para una proporción.

    Con p̂ = k/n y z el cuantil normal, el centro es (p̂ + z²/2n) / (1 + z²/n) y la
    semiamplitud z·√(p̂(1 − p̂)/n + z²/4n²) / (1 + z²/n).
    """
    if n <= 0 or not 0 <= successes <= n:
        raise ValueError("se requiere 0 ≤ aciertos ≤ n y n > 0")
    z = float(norm.ppf(0.5 + confidence / 2))
    p = successes / n
    denominator = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denominator
    half = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denominator
    return max(0.0, center - half), min(1.0, center + half)


def mean_ci(values: np.ndarray, confidence: float = 0.95) -> tuple[float, float, float]:
    """Media y su IC normal: media ± z · s/√n. Devuelve (media, bajo, alto)."""
    data = np.asarray(values, dtype=float)
    mean = float(data.mean())
    if len(data) < 2:
        return mean, mean, mean
    z = float(norm.ppf(0.5 + confidence / 2))
    half = z * float(data.std(ddof=1)) / math.sqrt(len(data))
    return mean, mean - half, mean + half


def no_fixed_point_probability(length: int, alphabet: int = 26) -> float:
    """Probabilidad de que ninguna de L letras se cifre a sí misma al azar: (25/26)^L.

    Es la base del distinguidor de la diapositiva 6 y del filtro de cribs: con
    L = 100, (25/26)^100 ≈ 1,98 %; en Enigma pasa siempre.
    """
    return ((alphabet - 1) / alphabet) ** length
