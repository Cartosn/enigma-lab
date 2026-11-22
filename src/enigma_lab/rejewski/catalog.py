"""El catálogo de Rejewski: la característica de cada configuración de los rotores (spec 5.7).

En 1932 la Enigma tenía tres rotores (I, II y III) y el reflector A, que los alemanes
cambiaron por el B el 2 de noviembre de 1937 (Rejewski, citado por Kuhl 2007). Hay 3! = 6
órdenes y 26³ = 17.576 posiciones: 6 × 17.576 = 105.456 configuraciones. Para cada una se
calcula la característica (``characteristic.py``) y se agrupan las configuraciones que
comparten característica: son las **clases**. Una clase de tamaño 1 señala una sola
configuración; una grande obliga a probar muchas a mano.

**Supuestos** (D-062; Kuhl dice que su programa simula el proceso del ciclómetro, sin más
detalle):

1. *Solo gira el rotor derecho* durante las seis letras del indicador: el central y el
   izquierdo no se mueven. La permutación de la pulsación k (k = 1…6) es el aleatorizador
   en (izq, cen, der + k): los rotores avanzan antes de cada letra. En la máquina real el
   central sí se mueve en el 26 % de las posiciones del día (176 de cada 676); para esos
   días la característica no es la del catálogo (``traffic.py`` lo mide).
2. *Los anillos no importan.* Con el supuesto 1, cada permutación depende solo de la
   posición del núcleo (ventana − anillo, ``bombe/scrambler.py``). El catálogo se indexa por
   la posición del núcleo al empezar el indicador; los anillos solo cambian qué ventanas
   corresponden a cada entrada.
3. *Sin plugboard*: conjugar no cambia la estructura de ciclos.

Las permutaciones salen de las tablas del aleatorizador de la Bombe
(``bombe/scrambler.scrambler_table`` con el reflector A): la máquina existe una sola vez.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from functools import cache

import numpy as np
import pandas as pd

from enigma_lab.bombe.scrambler import (
    N_POSITIONS,
    Order,
    order_label,
    position_letters,
    rotor_orders,
    scrambler_table,
)
from enigma_lab.rejewski.characteristic import (
    N_INDICATOR,
    N_TYPES,
    PAIRS,
    Characteristic,
    compose,
    format_characteristic,
    from_code,
    type_indices,
)

CATALOG_ROTORS = ("I", "II", "III")
CATALOG_REFLECTOR = "A"


def indicator_rows(press: int) -> np.ndarray:
    """La fila del aleatorizador en la pulsación ``press`` (1…6) para cada posición inicial.

    Solo avanza el derecho: (izq, cen, der) → (izq, cen, der + press).
    """
    index = np.arange(N_POSITIONS)
    right = index % 26
    rows: np.ndarray = index - right + (right + press) % 26
    return rows


def order_codes(order: Order, reflector: str = CATALOG_REFLECTOR) -> np.ndarray:
    """La característica (como entero, ``characteristic_code``) de las 17.576 posiciones."""
    table = scrambler_table(order, reflector).astype(np.int64)
    perms = [table[indicator_rows(k + 1)] for k in range(N_INDICATOR)]
    index = [type_indices(compose(perms[a], perms[b])) for a, b in PAIRS]
    codes: np.ndarray = (index[0] * N_TYPES + index[1]) * N_TYPES + index[2]
    return codes


@dataclass(frozen=True)
class Catalog:
    """El catálogo: la característica de cada configuración (orden, posición del núcleo).

    ``codes[o · 17.576 + p]`` es la característica del orden ``orders[o]`` en la posición del
    núcleo p (``bombe/scrambler.position_index``), y ``sizes[c]``, cuántas configuraciones
    tienen la característica c: el tamaño de su clase.
    """

    orders: tuple[Order, ...]
    reflector: str
    codes: np.ndarray
    sizes: np.ndarray

    @property
    def n_configurations(self) -> int:
        return int(self.codes.shape[0])

    def code_at(self, order: Sequence[str], position: int) -> int:
        """La característica de una configuración."""
        return int(self.codes[self.orders.index(tuple(order)) * N_POSITIONS + position])

    def characteristic_at(self, order: Sequence[str], position: int) -> Characteristic:
        return from_code(self.code_at(order, position))

    def size(self, code: int) -> int:
        """Cuántas configuraciones tienen esa característica (0 si ninguna)."""
        return int(self.sizes[code])

    def matches(self, code: int) -> list[tuple[Order, int]]:
        """Las configuraciones (orden, posición del núcleo) con esa característica."""
        found = np.flatnonzero(self.codes == code)
        return [(self.orders[i // N_POSITIONS], int(i % N_POSITIONS)) for i in found]

    def class_sizes(self) -> np.ndarray:
        """El tamaño de la clase de cada característica que aparece."""
        sizes: np.ndarray = self.sizes[self.sizes > 0]
        return sizes

    def distribution(self) -> pd.DataFrame:
        """Cuántas características tienen cada tamaño de clase (y cuántas configuraciones)."""
        sizes, count = np.unique(self.class_sizes(), return_counts=True)
        return pd.DataFrame(
            {
                "tamano": sizes.astype(np.int64),
                "caracteristicas": count.astype(np.int64),
                "configuraciones": (sizes * count).astype(np.int64),
            }
        )

    def top(self, n: int = 15) -> pd.DataFrame:
        """Las ``n`` características más frecuentes (empates por código): la tabla 1 de Kuhl."""
        codes = np.flatnonzero(self.sizes)
        order = np.lexsort((codes, -self.sizes[codes]))[:n]
        return pd.DataFrame(
            {
                "caracteristica": [format_characteristic(from_code(c)) for c in codes[order]],
                "configuraciones": self.sizes[codes[order]].astype(np.int64),
                "codigo": codes[order].astype(np.int64),
            }
        )

    def expected_candidates(self) -> float:
        """Configuraciones que comparten la característica de una configuración al azar.

        Es la media del tamaño de clase pesada por el tamaño: Σ nᵢ² / N. Es lo que había que
        probar a mano, en promedio, un día cualquiera.
        """
        sizes = self.class_sizes().astype(np.float64)
        return float((sizes**2).sum() / sizes.sum())


@cache
def build_catalog(
    rotors: Sequence[str] = CATALOG_ROTORS, reflector: str = CATALOG_REFLECTOR
) -> Catalog:
    """El catálogo de los órdenes posibles con esos rotores (6 con I–III), en caché."""
    orders = tuple(rotor_orders(tuple(rotors)))
    codes = np.concatenate([order_codes(order, reflector) for order in orders])
    sizes = np.bincount(codes, minlength=N_TYPES**3)
    return Catalog(orders=orders, reflector=reflector, codes=codes, sizes=sizes)


def describe(order: Order, position: int) -> str:
    """«II-I-III · KZY» (orden y posición del núcleo)."""
    return f"{order_label(order)} · {position_letters(position)}"
