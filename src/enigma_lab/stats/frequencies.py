"""Frecuencias, índice de coincidencia y prueba χ² de uniformidad (spec 5.3).

Los textos se manejan como arreglos de enteros 0–25 (A = 0). Las funciones aceptan un
texto (1 dimensión) o un lote de textos de igual longitud (2 dimensiones: una fila por
texto), para que los experimentos midan miles de mensajes a la vez.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import chisquare

RANDOM_IC = 1 / 26
"""IC de un texto de letras uniformes al azar: 1/26 ≈ 0,0385."""

GERMAN_IC_REFERENCE = 0.0758
"""IC del alemán según Pommerening (Universidad de Mainz); ver docs/FUENTES.md."""


def counts(codes: np.ndarray) -> np.ndarray:
    """Cuántas veces aparece cada letra: (26,) para un texto, (N, 26) para un lote."""
    codes = np.asarray(codes)
    if codes.ndim == 1:
        return np.bincount(codes, minlength=26)
    n = codes.shape[0]
    out = np.zeros((n, 26), dtype=np.int64)
    np.add.at(out, (np.repeat(np.arange(n), codes.shape[1]), codes.ravel()), 1)
    return out


def frequencies(codes: np.ndarray) -> np.ndarray:
    """Frecuencias relativas de cada letra (suman 1)."""
    c = counts(codes)
    return c / c.sum(axis=-1, keepdims=True)


def index_of_coincidence(codes: np.ndarray) -> np.ndarray | float:
    """IC = Σ nᵢ(nᵢ − 1) / (N(N − 1)).

    Es la probabilidad de que dos letras tomadas al azar del texto, sin reponer, sean
    iguales: ≈ 0,0758 en alemán y 1/26 ≈ 0,0385 en un texto uniforme. Una sustitución
    fija (César, por ejemplo) no lo cambia; Enigma, que cambia de sustitución en cada
    letra, lo lleva casi a 1/26.
    """
    c = counts(codes)
    n = c.sum(axis=-1)
    ic = (c * (c - 1)).sum(axis=-1) / (n * (n - 1))
    return float(ic) if np.ndim(ic) == 0 else ic


def chi2_uniform(codes: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Prueba χ² de que las 26 letras son igual de probables: (estadístico, valor p).

    χ² = Σ (Oᵢ − Eᵢ)² / Eᵢ con Eᵢ = N/26 y 25 grados de libertad. Un valor p pequeño
    rechaza la uniformidad: pasa con el texto plano, no con el cifrado de Enigma.
    """
    statistic, p_value = chisquare(counts(codes), axis=-1)
    return statistic, p_value


def pair_matrix(plain: np.ndarray, cipher: np.ndarray) -> np.ndarray:
    """Matriz 26 × 26: cuántas veces la letra plana i salió cifrada como j.

    En Enigma la diagonal es siempre cero: ninguna letra se cifra a sí misma.
    """
    matrix = np.zeros((26, 26), dtype=np.int64)
    np.add.at(matrix, (np.asarray(plain).ravel(), np.asarray(cipher).ravel()), 1)
    return matrix
