"""¿Qué supuesto reproduce las cifras de Kuhl (2007)? Variantes del catálogo de Rejewski.

El catálogo de E7 (supuesto del ciclómetro: durante el indicador solo gira el rotor derecho)
da 21.225 características, 11.578 únicas y 1.728 en la clase más grande; Kuhl publica
21.230, 11.466 y 1.771. Kuhl no detalla qué supone del rotor central ni de los anillos, así
que aquí se prueban las variantes razonables y se compara cada una con su tabla 2.

Uso:  uv run python scripts/kuhl_variantes.py      (unos 2 minutos)

Lo que se prueba (VALIDACION, E7):
- el paso real del central (con y sin doble paso), registrando antes o después de avanzar,
  con anillos AAA o ZZZ, y con la muesca corrida una letra (la convención de CyberChef);
- un odómetro puro, con la vuelta del central al pasar el derecho de Z a A;
- recorrer las 17.576 posiciones avanzando un odómetro real desde AAA (visita 16.900);
- los rotores con el cableado inverso, el reflector A girado k letras y los reflectores B y C.
"""

from __future__ import annotations

import json
import sys
from collections.abc import Callable

import numpy as np

from enigma_lab import paths
from enigma_lab.bombe.scrambler import N_POSITIONS, Order, position_index, rotor_orders
from enigma_lab.bombe.scrambler import scrambler_table as table_of
from enigma_lab.core.batch import ROTOR_NAMES, _shifted_tables
from enigma_lab.core.stepping import notch_sets, step
from enigma_lab.core.wiring import ALPHABET, REFLECTORS, ROTORS, inverse, permutation
from enigma_lab.rejewski.catalog import indicator_rows, order_codes
from enigma_lab.rejewski.characteristic import N_TYPES, PAIRS, compose, type_indices

ORDERS = rotor_orders(("I", "II", "III"))
KUHL = json.loads((paths.REFERENCE / "kuhl_2007.json").read_text(encoding="utf-8"))
TABLE2 = {row["tamano"]: row["caracteristicas"] for row in KUHL["tabla_2"]}
Stepper = Callable[[np.ndarray, Order], np.ndarray]


def codes_from(perms: list[np.ndarray]) -> np.ndarray:
    """La característica (como entero) a partir de las seis permutaciones de cada posición."""
    index = [type_indices(compose(perms[a], perms[b])) for a, b in PAIRS]
    codes: np.ndarray = (index[0] * N_TYPES + index[1]) * N_TYPES + index[2]
    return codes


def notches(order: Order, shift: int = 0, letter: int | None = None) -> list[np.ndarray]:
    """Las muescas del central y del derecho como máscaras de 26 (corridas o fijas en una letra)."""
    out = []
    for name in order[1:]:
        mask = np.zeros(26, dtype=bool)
        positions = (
            [letter] if letter is not None else [ALPHABET.index(c) for c in ROTORS[name].notches]
        )
        for p in positions:
            mask[(p + shift) % 26] = True
        out.append(mask)
    return out


def stepper(shift: int = 0, double: bool = True, letter: int | None = None) -> Stepper:
    """Un paso de las ventanas de todas las posiciones a la vez."""

    def advance(w: np.ndarray, order: Order) -> np.ndarray:
        middle, right = notches(order, shift, letter)
        m_at, r_at = middle[w[:, 1]], right[w[:, 2]]
        w = w.copy()
        if double:
            w[:, 0] += m_at
            w[:, 1] += m_at | r_at
        else:
            w[:, 0] += m_at & r_at
            w[:, 1] += r_at
        w[:, 2] += 1
        return w % 26

    return advance


def real_machine(advance: Stepper, record_first: bool = False, rings: int = 0) -> np.ndarray:
    """El catálogo con el paso real de las ventanas (anillos iguales en los tres rotores)."""
    codes = []
    for order in ORDERS:
        table = table_of(order, "A").astype(np.int64)
        index = np.arange(N_POSITIONS)
        w = np.stack([index // 676, (index // 26) % 26, index % 26], axis=1)
        perms = []
        for _ in range(6):
            if not record_first:
                w = advance(w, order)
            core = (w - rings) % 26
            perms.append(table[core[:, 0] * 676 + core[:, 1] * 26 + core[:, 2]])
            if record_first:
                w = advance(w, order)
        codes.append(codes_from(perms))
    return np.concatenate(codes)


def odometer_walk() -> np.ndarray:
    """Posiciones recorridas avanzando un odómetro real 17.576 veces desde AAA."""
    codes = []
    for order in ORDERS:
        marks = notch_sets([ROTORS[n].notches for n in order])
        position: tuple[int, ...] = (0, 0, 0)
        visited: list[int] = []
        for _ in range(N_POSITIONS):
            visited.append(position_index(*position))
            position = step(position, marks).positions
        codes.append(order_codes(order)[np.array(visited)])
    return np.concatenate(codes)


def custom_wiring(forward: np.ndarray, backward: np.ndarray, reflector: np.ndarray) -> np.ndarray:
    """El catálogo con otros cableados (solo gira el derecho)."""
    codes = []
    index = np.arange(N_POSITIONS)
    s_l, s_m, s_r = (index // 676)[:, None], ((index // 26) % 26)[:, None], (index % 26)[:, None]
    for order in ORDERS:
        left, middle, right = (ROTOR_NAMES.index(n) for n in order)
        x = np.broadcast_to(np.arange(26), (N_POSITIONS, 26))
        x = forward[right, s_r, x]
        x = forward[middle, s_m, x]
        x = forward[left, s_l, x]
        x = reflector[x]
        x = backward[left, s_l, x]
        x = backward[middle, s_m, x]
        x = backward[right, s_r, x]
        table = np.asarray(x, dtype=np.int64)
        codes.append(codes_from([table[indicator_rows(k + 1)] for k in range(6)]))
    return np.concatenate(codes)


def report(name: str, codes: np.ndarray) -> dict[str, object]:
    """Características distintas, únicas, la clase mayor y la distancia a la tabla 2 de Kuhl."""
    sizes = np.bincount(codes, minlength=N_TYPES**3)
    sizes = sizes[sizes > 0]
    count = dict(zip(*np.unique(sizes, return_counts=True), strict=True))
    distance = sum(abs(int(count.get(k, 0)) - v) for k, v in TABLE2.items())
    row = {
        "variante": name,
        "distintas": len(sizes),
        "unicas": int((sizes == 1).sum()),
        "mayor": int(sizes.max()),
        "distancia_tabla_2": distance,
    }
    print(
        f"{name:62s} {row['distintas']:7d} {row['unicas']:7d} {row['mayor']:6d} {distance:6d}",
        flush=True,
    )
    return row


def main() -> list[dict[str, object]]:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(f"{'variante':62s} {'distin.':>7s} {'únicas':>7s} {'mayor':>6s} {'|dif|':>6s}")
    print(f"{'Kuhl (2007)':62s} {21230:7d} {11466:7d} {1771:6d} {0:6d}")
    rows = [
        report(
            "E7: solo gira el derecho (ciclómetro)",
            np.concatenate([order_codes(o) for o in ORDERS]),
        )
    ]
    for record_first in (False, True):
        for rings in (0, 25):
            for shift in (0, 1, -1):
                for double in (True, False):
                    name = (
                        f"paso real: {'registra y avanza' if record_first else 'avanza y registra'}"
                        ", "
                        f"anillos {'AAA' if rings == 0 else 'ZZZ'}, muesca {shift:+d}, "
                        f"{'doble paso' if double else 'sin doble paso'}"
                    )
                    rows.append(
                        report(name, real_machine(stepper(shift, double), record_first, rings))
                    )
    for letter, label in ((25, "Z → A"), (0, "A → B")):
        rows.append(
            report(
                f"odómetro puro, vuelta en {label}",
                real_machine(stepper(letter=letter, double=False)),
            )
        )
    rows.append(report("posiciones de un odómetro real desde AAA", odometer_walk()))
    perms = [permutation(ROTORS[n].wiring) for n in ROTOR_NAMES]
    forward, backward = _shifted_tables(perms), _shifted_tables([inverse(p) for p in perms])
    u = np.array(permutation(REFLECTORS["A"]))
    rows.append(report("rotores con el cableado inverso", custom_wiring(backward, forward, u)))
    x = np.arange(26)
    for k in (1, 7, 13):
        rotated = (u[(x + k) % 26] - k) % 26
        rows.append(
            report(f"reflector A girado {k} letras", custom_wiring(forward, backward, rotated))
        )
    for name in ("B", "C"):
        rows.append(
            report(
                f"reflector {name}",
                custom_wiring(forward, backward, np.array(permutation(REFLECTORS[name]))),
            )
        )
    return rows


if __name__ == "__main__":
    main()
