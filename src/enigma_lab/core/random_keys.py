"""Claves aleatorias con ``numpy.random.Generator`` y semilla (spec 5.1).

Una clave aleatoria elige tres rotores distintos en orden, anillos y posiciones al azar
y k cables. Para el plugboard se baraja el alfabeto y se emparejan las 2k primeras
letras de dos en dos, lo que da cada plugboard de k cables con la misma probabilidad.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from enigma_lab.core.machine import EnigmaConfig
from enigma_lab.core.wiring import ALPHABET, MODELS


def random_plugboard(rng: np.random.Generator, cables: int) -> tuple[tuple[str, str], ...]:
    """k cables al azar, todos los plugboards de k cables igual de probables."""
    letters = rng.permutation(26)[: 2 * cables]
    pairs = (sorted((ALPHABET[a], ALPHABET[b])) for a, b in letters.reshape(-1, 2))
    return tuple(sorted((a, b) for a, b in pairs))


def random_config(
    rng: np.random.Generator,
    model: str = "I",
    cables: int = 10,
    reflectors: Sequence[str] | None = None,
) -> EnigmaConfig:
    """Una clave aleatoria del modelo dado.

    Args:
        rng: generador con semilla (``numpy.random.default_rng(2026)``).
        model: "I", "M3" o "M4".
        cables: cables del plugboard (0 a 13).
        reflectors: reflectores entre los que elegir; por defecto, B (o B-Thin en la M4).
    """
    spec = MODELS[model]
    default = ("B-Thin",) if model == "M4" else ("B",)
    choices = list(reflectors) if reflectors else list(default)
    rotors = tuple(str(r) for r in rng.choice(spec.rotors, size=3, replace=False))
    if spec.greek:
        rotors = (str(rng.choice(spec.greek)), *rotors)
    n = spec.n_rotors
    return EnigmaConfig(
        rotors=rotors,
        reflector=str(rng.choice(choices)),
        rings=tuple(int(v) for v in rng.integers(0, 26, size=n)),
        positions=tuple(int(v) for v in rng.integers(0, 26, size=n)),
        plugboard=random_plugboard(rng, cables),
        model=model,
    )


def random_text(rng: np.random.Generator, length: int) -> str:
    """Texto de letras uniformes al azar (para las pruebas de propiedades)."""
    return "".join(ALPHABET[i] for i in rng.integers(0, 26, size=length))
