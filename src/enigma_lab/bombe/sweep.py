"""La Bombe completa: ajustes, barrido por órdenes y lista de paradas (spec 5.5).

Uso:

    wiring = wiring_from_menu("WETTERBERICHT", cifrado[:13])
    run = run_bombe(wiring, BombeSettings(mode="robusto"))
    run.stops  # orden, posición, variante, hilos encendidos y steckers candidatos

**Modos** (D-032):
- *Bletchley* (por defecto): dentro del tramo del crib solo gira el rotor derecho, el
  supuesto de la Bombe histórica. Falla si el central avanza dentro del tramo, lo que
  con L letras pasa en cerca de (L − 1)/26 de las claves.
- *Robusto*: prueba además, para cada letra k = 1, …, L − 1 del crib, la variante en la
  que el central avanza justo al cifrar esa letra. Son L variantes: unas L veces el
  tiempo y las paradas falsas. No cubre dos movimientos dentro del tramo (la vuelta
  seguida de un doble paso), que pasa en cerca de 1 de cada 26 vueltas.

**La parada verdadera.** Con la clave conocida, :func:`true_stop` dice en qué posición
y variante debe parar la Bombe, y :func:`is_true_stop` si una parada es esa.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Literal

import numpy as np

from enigma_lab.bombe import bombe_numba
from enigma_lab.bombe.scrambler import (
    Order,
    position_index,
    position_letters,
    rotor_orders,
    scrambler_table,
)
from enigma_lab.bombe.wiring import BombeWiring, wiring_from_menu
from enigma_lab.core.machine import Enigma, EnigmaConfig
from enigma_lab.core.wiring import ALPHABET

Mode = Literal["bletchley", "robusto"]
MODES: dict[str, str] = {"bletchley": "Bletchley", "robusto": "Robusto"}

_LOCK = threading.Lock()
"""Un barrido a la vez. Streamlit corre cada sesión en su propio hilo, y no todas las
capas de hilos de Numba admiten lanzamientos paralelos simultáneos (la «workqueue» no)."""


@dataclass(frozen=True)
class BombeSettings:
    """Qué órdenes probar, con qué reflector y en qué modo."""

    orders: tuple[Order, ...] = field(default_factory=lambda: tuple(rotor_orders()))
    reflector: str = "B"
    mode: Mode = "bletchley"

    def turns(self, crib_length: int) -> np.ndarray:
        """Las variantes: 0 (sin vuelta) y, en modo robusto, la vuelta en cada letra 1…L − 1."""
        if self.mode == "bletchley":
            return np.zeros(1, dtype=np.int64)
        return np.arange(crib_length, dtype=np.int64)


@dataclass(frozen=True)
class Stop:
    """Una parada: dónde se detuvo la Bombe y qué stecker sugiere para la letra de prueba.

    Attributes:
        order: orden de rotores, de izquierda a derecha.
        position: índice de la posición del núcleo (anillos AAA) antes del crib.
        turn: variante; 0 = sin vuelta del central, k = el central avanza en la letra k.
        lit: hilos encendidos en el cable de prueba al energizar el hilo de prueba.
        candidates: letras (0–25) de los hilos aislados del cable de prueba.
    """

    order: Order
    position: int
    turn: int
    lit: int
    candidates: tuple[int, ...]

    @property
    def position_letters(self) -> str:
        return position_letters(self.position)

    def stecker_label(self, test_letter: str) -> str:
        """«T↔K» (o «T↔K / T↔M» si hay varios candidatos); «sin candidato» si no hay."""
        if not self.candidates:
            return "sin candidato"
        return " / ".join(f"{test_letter}↔{ALPHABET[c]}" for c in self.candidates)


def _bits(mask: int) -> tuple[int, ...]:
    return tuple(u for u in range(26) if mask >> u & 1)


@dataclass(frozen=True, eq=False)
class OrderRun:
    """El barrido de un orden de rotores: cuánto tardó y sus paradas, como arreglos.

    Con menús de pocos lazos puede haber cientos de miles de paradas, así que se guardan
    en arreglos de NumPy; :meth:`stop` arma una parada como objeto cuando hace falta.
    """

    order: Order
    seconds: float
    positions: np.ndarray  # (S,) índice de la posición del núcleo
    turns: np.ndarray  # (S,) variante
    lit: np.ndarray  # (S,) hilos encendidos en el cable de prueba
    singles: np.ndarray  # (S,) máscara de bits de sus hilos aislados

    def __len__(self) -> int:
        return int(self.positions.shape[0])

    def stop(self, k: int) -> Stop:
        return Stop(
            self.order,
            int(self.positions[k]),
            int(self.turns[k]),
            int(self.lit[k]),
            _bits(int(self.singles[k])),
        )

    @property
    def stops(self) -> list[Stop]:
        return [self.stop(k) for k in range(len(self))]


@dataclass(frozen=True, eq=False)
class BombeRun:
    """Un barrido completo: el cableado, los ajustes y el resultado de cada orden."""

    wiring: BombeWiring
    settings: BombeSettings
    runs: tuple[OrderRun, ...]

    @property
    def n_stops(self) -> int:
        return sum(len(run) for run in self.runs)

    @property
    def stops(self) -> list[Stop]:
        """Todas las paradas como objetos (con muchas paradas, mejor recorrer ``runs``)."""
        return [stop for run in self.runs for stop in run.stops]

    @property
    def seconds(self) -> float:
        return sum(run.seconds for run in self.runs)


def runs_from_stops(stops: Sequence[Stop]) -> tuple[OrderRun, ...]:
    """Agrupa paradas sueltas por orden (para verificar solo algunas, como en la app)."""
    groups: dict[Order, list[Stop]] = {}
    for stop in stops:
        groups.setdefault(stop.order, []).append(stop)
    return tuple(
        OrderRun(
            order,
            0.0,
            np.array([s.position for s in group], dtype=np.int64),
            np.array([s.turn for s in group], dtype=np.int64),
            np.array([s.lit for s in group], dtype=np.uint8),
            np.array([sum(1 << c for c in s.candidates) for s in group], dtype=np.uint32),
        )
        for order, group in groups.items()
    )


def sweep_order(
    wiring: BombeWiring, order: Order, reflector: str, turns: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """El barrido de Numba para un orden: (hilos encendidos, máscara de aislados)."""
    table = scrambler_table(order, reflector)
    with _LOCK:
        return bombe_numba.sweep(
            table,
            wiring.edge_a,
            wiring.edge_b,
            wiring.edge_offset,
            wiring.diag_a,
            wiring.diag_b,
            wiring.n_cables,
            wiring.test_node,
            wiring.test_wire,
            turns,
        )


def run_order(wiring: BombeWiring, order: Order, settings: BombeSettings) -> OrderRun:
    """Barre un orden de rotores: las paradas son las posiciones y variantes con menos de 26
    hilos encendidos en el cable de prueba."""
    turns = settings.turns(len(wiring.crib))
    start = time.perf_counter()
    lit, singles = sweep_order(wiring, order, settings.reflector, turns)
    positions, variants = np.nonzero(lit < 26)
    return OrderRun(
        order,
        time.perf_counter() - start,
        positions.astype(np.int64),
        turns[variants],
        lit[positions, variants],
        singles[positions, variants],
    )


def run_bombe(
    wiring: BombeWiring,
    settings: BombeSettings | None = None,
    progress: Callable[[int, OrderRun], None] | None = None,
) -> BombeRun:
    """Barre todos los órdenes de los ajustes, uno tras otro.

    ``progress(k, resultado)`` se llama al terminar cada orden (la barra de la app).
    """
    settings = settings or BombeSettings()
    runs = []
    for k, order in enumerate(settings.orders):
        run = run_order(wiring, order, settings)
        runs.append(run)
        if progress is not None:
            progress(k, run)
    return BombeRun(wiring, settings, tuple(runs))


# ---------------------------------------------------------------- la parada verdadera


def crib_cores(config: EnigmaConfig, crib_position: int, crib_length: int) -> list[tuple[int, ...]]:
    """Las posiciones del núcleo (ventana − anillo) al cifrar cada letra del crib."""
    machine = Enigma(config)
    for _ in range(crib_position):
        machine.step()
    cores = []
    for _ in range(crib_length):
        machine.step()
        cores.append(
            tuple((p - r) % 26 for p, r in zip(machine.positions, config.rings, strict=True))
        )
    return cores


def true_stop(config: EnigmaConfig, crib_position: int, crib_length: int) -> tuple[int, int] | None:
    """(posición, variante) en que debe parar la Bombe con la clave verdadera, o None.

    Con K_i la posición del núcleo al cifrar la letra i del crib: si el izquierdo y el
    central no cambian, la parada es C = K_0 − (0, 0, 1) en la variante 0 (Bletchley).
    Si el central avanza una sola vez, en la letra k, es la variante k del modo
    robusto. Si se mueve el izquierdo o el central se mueve dos veces, ninguna variante
    la cubre.
    """
    cores = crib_cores(config, crib_position, crib_length)
    left, middle, right = cores[0]
    if any(c[0] != left for c in cores):
        return None
    changes = [k for k in range(1, crib_length) if cores[k][1] != cores[k - 1][1]]
    if not changes:
        turn = 0
    elif len(changes) == 1 and cores[changes[0]][1] == (middle + 1) % 26:
        turn = changes[0]
    else:
        return None
    return position_index(left, middle, right - 1), turn


def true_stecker(config: EnigmaConfig, letter: str) -> str:
    """La pareja de una letra en el plugboard de la clave (ella misma si no tiene cable)."""
    for a, b in config.plugboard:
        if letter == a:
            return b
        if letter == b:
            return a
    return letter


def is_true_stop(stop: Stop, config: EnigmaConfig, crib_position: int, wiring: BombeWiring) -> bool:
    """¿Es la parada que da la clave verdadera, con su stecker verdadero entre los candidatos?"""
    expected = true_stop(config, crib_position, len(wiring.crib))
    if expected is None or tuple(config.rotors) != stop.order:
        return False
    partner = ALPHABET.index(true_stecker(config, wiring.test_letter))
    return (stop.position, stop.turn) == expected and partner in stop.candidates


def warm_up(all_tables: bool = False) -> float:
    """Compila (o carga de la caché) los núcleos de Numba con un menú pequeño; devuelve segundos.

    La app lo llama al arrancar, para que la primera corrida de la demo no espere al
    compilador. Con ``all_tables`` precalcula además el aleatorizador de los 60 órdenes
    (unos 27 MB en memoria).
    """
    from enigma_lab.bombe import checker

    start = time.perf_counter()
    if all_tables:
        for order in rotor_orders():
            scrambler_table(order, "B")
    wiring = wiring_from_menu("WETTERBERICHT", "ICGWNXTXINRGB")
    settings = BombeSettings(orders=(("II", "III", "I"),), mode="robusto")
    run = run_bombe(wiring, settings)
    checker.consistent_stops(wiring, run.runs, "B")
    checker.warm_up_kernels()
    return time.perf_counter() - start


def all_orders(rotors: Sequence[str]) -> tuple[Order, ...]:
    """Los órdenes posibles con un juego de rotores (6 con I–III, 60 con I–V)."""
    return tuple(rotor_orders(rotors))
