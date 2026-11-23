"""Hill climbing del plugboard: Gillogly (1995) y Ostwald y Weierud (2017).

**El problema.** En la ubicación correcta (orden, anillos y posiciones) se conoce el
aleatorizador de cada letra, ``paths[j]`` = Sⱼ. Falta el plugboard P: la letra plana es
P(Sⱼ(P(cⱼ))) (``bombe/checker._decrypt``). P no cambia en todo el mensaje, así que se ataca
como una sustitución monoalfabética: por hill climbing.

**El paso.** Se prueban, uno por uno, los 325 cambios de un cable (unir dos letras, separarlas
o cambiar sus parejas; ``bombe/checker._toggle``). Un cambio se queda si sube el puntaje; si
no, se deshace. Se repiten pasadas hasta que ninguna mejora. Es el método de los «cables de
prueba» de Gillogly, como lo describen Ostwald y Weierud.

**Dos puntajes, en este orden.**

1. *El IC* (Σ nᵢ(nᵢ − 1), proporcional al índice de coincidencia). Ostwald y Weierud cuentan
   que, con 10 cables y el plugboard vacío, en la ubicación correcta solo el 10,1 % de las
   letras sale como texto plano, pero otro 18,5 % sale como sustituto monoalfabético del
   plano: el IC lo ve, y por eso encuentra los primeros cables mejor que los trigramas.
2. *Los trigramas del alemán* (Σ log₁₀ p, ``stats/ngrams.py``), que afinan los últimos cables.

**Búsqueda parcial (Ostwald y Weierud, «E-Stecker»).** Además del plugboard vacío, se prueban
como arranque las otras 25 parejas posibles de la E, la letra más frecuente: 26 arranques. Se
sube desde cada uno y gana el mejor puntaje final.
"""

from __future__ import annotations

import numpy as np
from numba import njit

from enigma_lab.bombe.checker import _decrypt, _toggle
from enigma_lab.stats import ngrams

KIND_IC = 0
KIND_TRIGRAMS = 1
MAX_TRACE = 4_096
"""Cambios aceptados que se anotan para dibujar la subida (la app)."""
E = 4
"""La E, la letra más frecuente del alemán: la de la búsqueda parcial."""


def trigram_table() -> np.ndarray:
    """log₁₀ p de los 26³ trigramas del alemán con la X como separador (muestra, float64)."""
    return ngrams.model("aleman", 3, "muestra", "x").log_probs.astype(np.float64)


@njit(cache=True)
def _ic_sum(text: np.ndarray) -> float:  # pragma: no cover - Numba
    """Σ nᵢ(nᵢ − 1): el IC sin dividir por L(L − 1)."""
    counts = np.zeros(26, np.int64)
    for k in range(text.shape[0]):
        counts[text[k]] += 1
    total = 0
    for k in range(26):
        total += counts[k] * (counts[k] - 1)
    return float(total)


@njit(cache=True)
def _trigram_sum(text: np.ndarray, logp3: np.ndarray) -> float:  # pragma: no cover - Numba
    """Σ log₁₀ p de los trigramas solapados."""
    total = 0.0
    for k in range(text.shape[0] - 2):
        total += logp3[(text[k] * 26 + text[k + 1]) * 26 + text[k + 2]]
    return total


@njit(cache=True)
def _score(text: np.ndarray, kind: int, logp3: np.ndarray) -> float:  # pragma: no cover - Numba
    if kind == KIND_IC:
        return _ic_sum(text)
    return _trigram_sum(text, logp3)


@njit(cache=True)
def _climb(
    paths: np.ndarray,
    cipher: np.ndarray,
    plug: np.ndarray,
    kind: int,
    logp3: np.ndarray,
    buf: np.ndarray,
    saved: np.ndarray,
    trace: np.ndarray,
    n_trace: int,
) -> tuple[float, int]:  # pragma: no cover - Numba
    """Una etapa del hill climbing (en el sitio): pasadas de los 325 cambios hasta no mejorar.

    Anota cada cambio aceptado en ``trace`` (puntaje, IC normalizado del texto, cables).
    """
    _decrypt(paths, cipher, plug, buf)
    best = _score(buf, kind, logp3)
    n = cipher.shape[0]
    improved = True
    while improved:
        improved = False
        for a in range(26):
            for b in range(a + 1, 26):
                saved[:] = plug
                _toggle(plug, a, b)
                _decrypt(paths, cipher, plug, buf)
                score = _score(buf, kind, logp3)
                if score > best + 1e-9:
                    best = score
                    improved = True
                    if n_trace < trace.shape[0]:
                        cables = 0
                        for x in range(26):
                            if plug[x] > x:
                                cables += 1
                        trace[n_trace, 0] = kind
                        trace[n_trace, 1] = _ic_sum(buf) / (n * (n - 1))
                        trace[n_trace, 2] = _trigram_sum(buf, logp3) / max(1, n - 2)
                        trace[n_trace, 3] = cables
                        n_trace += 1
                else:
                    plug[:] = saved
    return best, n_trace


@njit(cache=True)
def climb_plugboard(
    paths: np.ndarray, cipher: np.ndarray, start: np.ndarray, logp3: np.ndarray, use_ic: bool
) -> tuple[np.ndarray, float, np.ndarray, int]:  # pragma: no cover - Numba
    """Hill climbing desde el plugboard ``start``: con el IC (si ``use_ic``) y luego trigramas.

    Devuelve el plugboard, Σ log₁₀ p de los trigramas, la traza y cuántas filas tiene.
    """
    plug = start.copy()
    buf = np.empty(cipher.shape[0], np.int64)
    saved = np.empty(26, np.int64)
    trace = np.zeros((MAX_TRACE, 4))
    n_trace = 0
    if use_ic:
        _, n_trace = _climb(paths, cipher, plug, KIND_IC, logp3, buf, saved, trace, n_trace)
    score, n_trace = _climb(paths, cipher, plug, KIND_TRIGRAMS, logp3, buf, saved, trace, n_trace)
    return plug, score, trace, n_trace


@njit(cache=True)
def e_stecker(
    paths: np.ndarray, cipher: np.ndarray, logp3: np.ndarray, use_ic: bool
) -> tuple[np.ndarray, float]:  # pragma: no cover - Numba
    """Búsqueda parcial: la E sola o con cada una de las otras 25 letras, y hill climbing."""
    best_plug = np.arange(26)
    best = -np.inf
    for partner in range(26):
        start = np.arange(26)
        if partner != E:
            start[E] = partner
            start[partner] = E
        plug, score, _, _ = climb_plugboard(paths, cipher, start, logp3, use_ic)
        if score > best:
            best = score
            best_plug = plug
    return best_plug, best


def decrypt(paths: np.ndarray, cipher: np.ndarray, plug: np.ndarray) -> np.ndarray:
    """El texto descifrado con el aleatorizador de cada letra y el plugboard."""
    out = np.empty(len(cipher), dtype=np.int64)
    _decrypt(paths, np.asarray(cipher, dtype=np.int64), np.asarray(plug, dtype=np.int64), out)
    return out


def plug_pairs(plug: np.ndarray) -> tuple[tuple[str, str], ...]:
    """El plugboard como parejas de letras ordenadas (para ``EnigmaConfig``)."""
    letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    return tuple((letters[a], letters[int(b)]) for a, b in enumerate(plug) if b > a)


def warm_up() -> None:
    """Compila (o carga de la caché) los núcleos con datos pequeños."""
    paths = np.tile(np.roll(np.arange(26), 1), (30, 1)).astype(np.int64)
    cipher = np.arange(30, dtype=np.int64) % 26
    logp3 = trigram_table()
    climb_plugboard(paths, cipher, np.arange(26), logp3, True)
    e_stecker(paths[:5], cipher[:5], logp3, True)
