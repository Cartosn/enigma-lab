"""Casos de prueba para la Bombe: clave, mensaje alemán, crib y su alineación.

Lo usan las pruebas (``tests/test_bombe.py``), el experimento E5 y el banco de la demo 2
(``scripts/bench_demo2.py``), para que todos generen los casos de la misma manera.

- **Mensaje:** un fragmento al azar del corpus alemán con la X como separador, al
  estilo militar (WETTERBERICHTXFUERXDIE…).
- **Clave:** como la de «Clave aleatoria» de la página Máquina: Enigma I, reflector B,
  rotores distintos de los permitidos, anillos y posición al azar y 10 cables.
- **Crib:** un tramo del propio mensaje, así que se sabe dónde va.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from enigma_lab.bombe.scrambler import ENIGMA_I_ROTORS
from enigma_lab.bombe.sweep import crib_cores
from enigma_lab.core.machine import EnigmaConfig, encrypt
from enigma_lab.core.random_keys import random_plugboard
from enigma_lab.stats.corpus import Source, load_letters

DEMO_CRIB = "WETTERBERICHT"


@dataclass(frozen=True)
class BombeCase:
    """Una clave, su mensaje y el crib con su alineación."""

    config: EnigmaConfig
    plaintext: str
    ciphertext: str
    crib_position: int
    crib_length: int

    @property
    def crib(self) -> str:
        return self.plaintext[self.crib_position : self.crib_position + self.crib_length]

    @property
    def cipher_segment(self) -> str:
        return self.ciphertext[self.crib_position : self.crib_position + self.crib_length]


def random_key(
    rng: np.random.Generator, rotors: Sequence[str] = ENIGMA_I_ROTORS, cables: int = 10
) -> EnigmaConfig:
    """Clave de Enigma I al azar: tres rotores distintos de ``rotors``, reflector B."""
    names = tuple(str(r) for r in rng.choice(list(rotors), size=3, replace=False))
    return EnigmaConfig(
        rotors=names,
        reflector="B",
        rings=tuple(int(v) for v in rng.integers(0, 26, size=3)),
        positions=tuple(int(v) for v in rng.integers(0, 26, size=3)),
        plugboard=random_plugboard(rng, cables),
    )


def german_text(rng: np.random.Generator, length: int, source: Source = "muestra") -> str:
    """Un fragmento al azar del corpus alemán, con la X como separador."""
    letters = load_letters("aleman", source, "x")
    start = int(rng.integers(0, len(letters) - length))
    return letters[start : start + length]


def middle_moves(config: EnigmaConfig, crib_position: int, crib_length: int) -> bool:
    """¿Se mueve el rotor central (o el izquierdo) mientras se cifran las letras del crib?"""
    cores = crib_cores(config, crib_position, crib_length)
    return len({c[:2] for c in cores}) > 1


def random_case(
    rng: np.random.Generator,
    crib_length: int,
    message_length: int = 80,
    *,
    crib_position: int | None = None,
    no_turnover: bool = False,
    rotors: Sequence[str] = ENIGMA_I_ROTORS,
    source: Source = "muestra",
) -> BombeCase:
    """Un caso: mensaje alemán, clave al azar y el crib tomado del propio mensaje.

    Con ``no_turnover=True`` se vuelven a sortear clave y posición hasta que el central
    no se mueva dentro del tramo (la condición de la prueba 6.4).
    """
    while True:
        config = random_key(rng, rotors)
        plain = german_text(rng, message_length, source)
        position = (
            int(rng.integers(0, message_length - crib_length + 1))
            if crib_position is None
            else crib_position
        )
        if no_turnover and middle_moves(config, position, crib_length):
            continue
        return BombeCase(config, plain, encrypt(config, plain), position, crib_length)


def demo_case(
    rng: np.random.Generator,
    rotors: Sequence[str] = ENIGMA_I_ROTORS,
    crib: str = DEMO_CRIB,
    message_length: int = 78,
) -> BombeCase:
    """El caso de un compañero en la demo 2: un mensaje alemán que empieza por el crib.

    El mensaje es el crib, una X y texto del corpus hasta ``message_length`` letras (78,
    como el caso de respaldo); la clave es como la de «Clave aleatoria».
    """
    config = random_key(rng, rotors)
    body = german_text(rng, message_length)
    plain = (crib + "X" + body)[:message_length]
    return BombeCase(config, plain, encrypt(config, plain), 0, len(crib))
