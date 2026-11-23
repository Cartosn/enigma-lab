"""Espacio de claves de Enigma: conteos exactos con enteros de Python.

Una clave diaria de Enigma tiene cuatro componentes que se eligen por separado, así
que el número total de claves es el producto de sus opciones:

* **Orden de los rotores.** Se colocan 3 de los n rotores disponibles y el orden
  importa: variaciones sin repetición, P(n, 3) = n! / (n − 3)!. Con los 5 rotores de
  Enigma I son 60; con los 8 de la M3 naval, 336.
* **Posiciones iniciales.** Cada rotor arranca en una de 26 letras: 26³ = 17.576.
* **Anillos (Ringstellung).** Hay 26³ ajustes, pero el anillo del rotor izquierdo es
  redundante: ese rotor nunca arrastra a otro, así que su anillo solo desplaza su
  posición inicial, que ya se cuenta aparte. Quedan 26² = 676 ajustes efectivos.
* **Plugboard con k cables.** N(k) = 26! / ((26 − 2k)! · k! · 2^k), explicado en
  :func:`plugboard_settings`.

La información de cada componente se mide en bits, log₂(opciones). Como las opciones
se multiplican, los bits se suman: 5,91 + 14,10 + 47,10 = 67,11 bits sin anillos.

La Bombe aparta el plugboard y solo recorre órdenes ×
posiciones: 60 × 17.576 = 1.054.560 configuraciones, unos 20 bits.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

ALPHABET_SIZE = 26
"""Letras del alfabeto de Enigma (A–Z)."""

SLOTS = 3
"""Rotores en la máquina: Enigma I y M3 llevan tres (la M4 cuatro; no se usa aquí)."""

SECONDS_PER_YEAR = 365.25 * 24 * 3600
"""Segundos de un año juliano (365,25 días), la unidad del estimador de fuerza bruta."""

COMPONENT_LABELS = {
    "orders": "Orden de rotores",
    "positions": "Posiciones",
    "rings": "Anillos",
    "plugboard": "Plugboard",
}
"""Nombres en español de cada componente, para la interfaz y las figuras."""


@dataclass(frozen=True)
class Model:
    """Un modelo de Enigma para el conteo: cuántos rotores hay para elegir."""

    name: str
    n_rotors: int


ENIGMA_I = Model("Enigma I", n_rotors=5)
M3 = Model("Enigma M3 (naval)", n_rotors=8)

DEFAULT_CABLES = 10
"""Cables del procedimiento habitual de la Wehrmacht desde 1939."""


def rotor_orders(n_rotors: int, slots: int = SLOTS) -> int:
    """Órdenes de rotores: variaciones sin repetición, P(n, slots) = n! / (n − slots)!."""
    return math.perm(n_rotors, slots)


def rotor_positions(slots: int = SLOTS) -> int:
    """Posiciones iniciales de los rotores: 26^slots."""
    return ALPHABET_SIZE**slots


def effective_ring_settings(slots: int = SLOTS) -> int:
    """Ajustes de anillos que cambian el cifrado: 26^(slots − 1).

    El anillo del rotor izquierdo no cuenta: solo desplaza su posición inicial.
    """
    return ALPHABET_SIZE ** (slots - 1)


def plugboard_settings(cables: int, letters: int = ALPHABET_SIZE) -> int:
    """Formas de conectar k cables en el plugboard: N(k) = 26! / ((26 − 2k)! · k! · 2^k).

    Se cuentan las listas ordenadas de 2k letras distintas, 26! / (26 − 2k)!, y se
    agrupan de dos en dos para formar k parejas. Esa cuenta repite cada plugboard
    k! veces (el orden de las parejas no importa) y 2^k veces más (la pareja AB es
    la misma que BA), así que se divide por k! · 2^k.

    Raises:
        ValueError: si k es negativo o no caben k cables (2k > 26).
    """
    if cables < 0 or 2 * cables > letters:
        raise ValueError(f"no caben {cables} cables en un plugboard de {letters} letras")
    ordered = math.factorial(letters) // math.factorial(letters - 2 * cables)
    return ordered // (math.factorial(cables) * 2**cables)


def max_cables(letters: int = ALPHABET_SIZE) -> int:
    """Máximo de cables posibles: 13 con 26 letras."""
    return letters // 2


def best_cable_count(letters: int = ALPHABET_SIZE) -> int:
    """Número de cables que maximiza N(k): 11 con 26 letras, no 13.

    Con 13 cables ya no quedan letras libres y el conteo baja: pasar de 11 a 13
    cables reduce las opciones, aunque «suene» más seguro.
    """
    return max(range(max_cables(letters) + 1), key=lambda k: plugboard_settings(k, letters))


def bits(count: int | float) -> float:
    """Bits de información de un número de opciones: log₂(count)."""
    return math.log2(count)


@dataclass(frozen=True)
class KeySpace:
    """Las opciones de cada componente de la clave para un modelo y número de cables."""

    orders: int
    positions: int
    rings: int
    plugboard: int

    @property
    def total_without_rings(self) -> int:
        """Claves sin contar anillos: órdenes × posiciones × plugboard."""
        return self.orders * self.positions * self.plugboard

    @property
    def total_with_rings(self) -> int:
        """Claves contando también los anillos efectivos."""
        return self.total_without_rings * self.rings

    @property
    def bombe_sweep(self) -> int:
        """Configuraciones que recorre la Bombe: órdenes × posiciones, sin el plugboard."""
        return self.orders * self.positions

    def component_bits(self) -> dict[str, float]:
        """Bits que aporta cada componente (claves de ``COMPONENT_LABELS``)."""
        return {
            "orders": bits(self.orders),
            "positions": bits(self.positions),
            "rings": bits(self.rings),
            "plugboard": bits(self.plugboard),
        }

    @property
    def plugboard_share(self) -> float:
        """Fracción de los bits sin anillos que aporta el plugboard (≈ 0,702)."""
        return bits(self.plugboard) / bits(self.total_without_rings)


def keyspace(model: Model = ENIGMA_I, cables: int = DEFAULT_CABLES) -> KeySpace:
    """Espacio de claves de un modelo con k cables en el plugboard."""
    return KeySpace(
        orders=rotor_orders(model.n_rotors),
        positions=rotor_positions(),
        rings=effective_ring_settings(),
        plugboard=plugboard_settings(cables),
    )


def brute_force_years(keys: int, tests_per_second: float) -> float:
    """Años que tarda probar todas las claves: claves / (pruebas por segundo × s por año).

    Con 158.962.555.217.826.360.000 claves a 10⁹ pruebas por segundo da unos
    5.037 años (años de 365,25 días).
    """
    if tests_per_second <= 0:
        raise ValueError("las pruebas por segundo deben ser positivas")
    return keys / tests_per_second / SECONDS_PER_YEAR
