"""Las cifras de la presentación (spec 11.3), cada una calculada por el código.

Un solo registro para dos usos: ``tests/test_presentacion.py`` comprueba cada cifra y
``make resumen`` las lista en ``RESUMEN.md``. ``expected`` es la cifra como la escribe
el spec o la diapositiva; ``compute`` la calcula con el formato español de
:mod:`enigma_lab.viz.numfmt`. Las de módulos que aún no existen quedan como
pendientes, con la fase en que llegan.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from functools import cache

import numpy as np

from enigma_lab import SEED, paths
from enigma_lab.core import keyspace as ks
from enigma_lab.core.machine import Enigma, EnigmaConfig, encrypt, groups_of_five
from enigma_lab.core.stepping import cycle_structure, notch_sets
from enigma_lab.core.vectors import vector
from enigma_lab.cribs.dragging import alignments, valid_positions
from enigma_lab.cribs.menu import MenuStats, menu_at, menu_stats
from enigma_lab.stats.inference import no_fixed_point_probability
from enigma_lab.viz.numfmt import NBSP, fmt_dec, fmt_int, fmt_pct, fmt_sci


@dataclass(frozen=True)
class Cifra:
    """Una cifra de la presentación: dónde aparece, cuánto vale y cómo se calcula."""

    slides: str
    description: str
    expected: str
    compute: Callable[[], str] | None = None
    pending: str = ""

    @property
    def is_pending(self) -> bool:
        return self.compute is None


# ---------------------------------------------------------------- cálculos

SPACE = ks.keyspace(ks.ENIGMA_I, cables=ks.DEFAULT_CABLES)
BITS = SPACE.component_bits()


def _years() -> str:
    return fmt_int(round(ks.brute_force_years(SPACE.total_without_rings, 1e9)))


@cache
def _cycle() -> tuple[list[int], int]:
    return cycle_structure(notch_sets(["Q", "E", "V"]))


def _windows_from_adu(presses: int = 3) -> str:
    machine = Enigma(EnigmaConfig.from_strings("I II III", positions="ADU"))
    windows = [machine.window]
    for _ in range(presses):
        machine.step()
        windows.append(machine.window)
    return " → ".join(windows)


def _encrypt_vector(vector_id: str, field: str) -> str:
    v = vector(vector_id)
    return encrypt(EnigmaConfig.from_dict(v["key"]), v[field])


def _trace_slide_4() -> str:
    trace = Enigma(EnigmaConfig.from_strings("I II III")).trace("A")[0]
    words = {"plugboard": "plugboard", "reflector": "reflector"}
    parts = []
    for stage in trace.stages[1:-1]:
        name = words.get(stage.component) or stage.label.removeprefix("Rotor ")
        parts.append(f"{name} {stage.letter}")
    return " → ".join(parts)


@cache
def _pilot_properties() -> tuple[int, int, int]:
    """(claves con involución, letras, puntos fijos) en 2.000 claves × 100 letras."""
    from enigma_lab.experiments.e1_validation import check_properties

    df = check_properties(2_000, 100, np.random.default_rng(SEED))
    return int(df["involucion"].sum()), int(df["letras"].sum()), int(df["puntos_fijos"].sum())


def _pct(fraction: float, decimals: int = 1) -> str:
    return fmt_pct(fraction, decimals)


SLIDE_10 = ("BBGCCKITCTTEZZZLCZ", "WETTERBERICHT")


def _slide10_count() -> str:
    return str(len(alignments(*SLIDE_10)))


def _slide10_valid() -> str:
    return ", ".join(str(p) for p in valid_positions(*SLIDE_10))


def _slide10_conflict() -> str:
    """La letra del crib que choca en la posición 7 en las alineaciones 4 y 5."""
    crib = SLIDE_10[1]
    found: set[tuple[str, int]] = set()
    for a in alignments(*SLIDE_10)[4:]:
        found |= {(crib[j], a.position + j) for j in a.conflicts if a.position + j == 7}
    return "; ".join(
        f"{letter} sobre la {letter} de la posición {p}" for letter, p in sorted(found)
    )


def _menu(which: str) -> MenuStats:
    """Métricas del menú de la diapositiva 11 («slide») o del caso de respaldo («backup»)."""
    if which == "slide":
        return menu_stats(menu_at(*SLIDE_10, 0))
    import json

    data = json.loads((paths.DEMO / "respaldo_bombe.json").read_text(encoding="utf-8"))
    return menu_stats(menu_at(data["ciphertext"], data["crib"], data["crib_position"]))


def _menu_numbers(which: str) -> str:
    s = _menu(which)
    return f"{s.letters} · {s.edges} · {s.components} · {s.loops}"


def _test_letter(which: str) -> str:
    s = _menu(which)
    return f"{s.test_letter}, grado {s.test_degree}"


def _short(value: float) -> str:
    """Número con los decimales justos y coma: 820 → «820», 1,2 → «1,2», 0,04 → «0,04»."""
    if float(value).is_integer():
        return fmt_int(int(value))
    return fmt_dec(value, 2).rstrip("0")


def _signed_db(value: float, decimals: int) -> str:
    """Decibanes con signo explícito, como en las diapositivas: «+1,845 dB», «−0,093 dB»."""
    return ("+" if value > 0 else "") + fmt_dec(value, decimals) + f"{NBSP}dB"


def _banburismus_weight(which: str) -> str:
    """Decibanes de Turing (1/17 frente a 1/26): por repetición, por no repetición o por letra."""
    from enigma_lab.banburismus.scoring import TURING

    values = {
        "repeticion": (float(TURING.plus[0]), 3),
        "no_repeticion": (float(TURING.minus[0]), 3),
        "profundidad": (TURING.drift(True), 4),
        "azar": (TURING.drift(False), 4),
    }
    return _signed_db(*values[which])


def _wald_thresholds() -> str:
    """Umbrales del SPRT con α = β = 1 %: «±19,96 dB»."""
    from enigma_lab.banburismus.sprt import thresholds

    upper, lower = thresholds(0.01)
    if not math.isclose(upper, -lower):
        raise ValueError("con α = β los umbrales son simétricos")
    return f"±{fmt_dec(upper, 2)}{NBSP}dB"


def _wald_letters() -> str:
    """Letras esperadas según la aproximación de Wald: en profundidad y al azar."""
    from enigma_lab.banburismus.scoring import TURING
    from enigma_lab.banburismus.sprt import wald_letters

    depth = wald_letters(TURING.drift(True), True, 0.01)
    chance = wald_letters(TURING.drift(False), False, 0.01)
    return f"{fmt_int(round(depth))} y {fmt_int(round(chance))}"


def _turing_slide_16() -> str:
    """Turing con 12 letras (diapositiva 16): paradas por orden y, con 2 y 3 lazos, en 60."""
    from enigma_lab.experiments.e5_bombe import ORDERS_PER_DAY, turing_value

    per_order = [turing_value(12, loops)[0] for loops in (0, 1, 2, 3)]
    in_sixty = [round(v * ORDERS_PER_DAY, 6) for v in per_order[2:]]
    return (
        " · ".join(_short(v) for v in per_order)
        + f"; {_short(in_sixty[0])} y {_short(in_sixty[1])} en {ORDERS_PER_DAY}"
    )


# ---------------------------------------------------------------- registro

CIFRAS: tuple[Cifra, ...] = (
    # Diapositivas 2, 7, 8 y 20 · core/keyspace.py
    Cifra(
        "2, 7, 20",
        "claves sin anillos",
        "158.962.555.217.826.360.000",
        lambda: fmt_int(SPACE.total_without_rings),
    ),
    Cifra(
        "2, 7, 20",
        "claves sin anillos, redondeado",
        "1,6 × 10²⁰",
        lambda: fmt_sci(SPACE.total_without_rings, 2),
    ),
    Cifra("7, 8", "bits sin anillos", "67,11", lambda: fmt_dec(ks.bits(SPACE.total_without_rings))),
    Cifra("7", "claves con anillos", "1,0746 × 10²³", lambda: fmt_sci(SPACE.total_with_rings, 5)),
    Cifra(
        "7",
        "claves con anillos, redondeado",
        "1,07 × 10²³",
        lambda: fmt_sci(SPACE.total_with_rings, 3),
    ),
    Cifra("7", "bits con anillos", "76,51", lambda: fmt_dec(ks.bits(SPACE.total_with_rings))),
    Cifra("7", "bits del orden de rotores", "5,91", lambda: fmt_dec(BITS["orders"])),
    Cifra("7", "bits de las posiciones", "14,10", lambda: fmt_dec(BITS["positions"])),
    Cifra("7", "bits de los anillos", "9,40", lambda: fmt_dec(BITS["rings"])),
    Cifra("7", "bits del plugboard", "47,10", lambda: fmt_dec(BITS["plugboard"])),
    Cifra(
        "7",
        "fracción del plugboard en los 67,11 bits",
        f"70,2{NBSP}%",
        lambda: _pct(SPACE.plugboard_share),
    ),
    Cifra(
        "8, 20",
        "configuraciones que barre la Bombe",
        "1.054.560",
        lambda: fmt_int(SPACE.bombe_sweep),
    ),
    Cifra(
        "8, 20",
        "bits del barrido de la Bombe",
        "20,01",
        lambda: fmt_dec(ks.bits(SPACE.bombe_sweep)),
    ),
    Cifra("7", "años de fuerza bruta a 10⁹ claves por segundo", "5.037", _years),
    # Diapositivas 3, 5 y 14 · core/stepping.py
    Cifra(
        "3, 5, 14",
        "periodo del odómetro I-II-III",
        "16.900",
        lambda: " + ".join(fmt_int(n) for n in _cycle()[0]),
    ),
    Cifra("5", "posiciones fuera del ciclo", "676", lambda: fmt_int(_cycle()[1])),
    Cifra("5, 14", "doble paso desde ADU", "ADU → ADV → AEW → BFX", _windows_from_adu),
    # Diapositivas 1, 4 y 14 · core/machine.py
    Cifra(
        "1",
        "mensaje cifrado de la portada",
        "LGNEV YPYZQ DVKES NPUYY QVWSK YNZJH E",
        lambda: groups_of_five(_encrypt_vector("portada", "input")),
    ),
    Cifra(
        "1, 4",
        "la portada descifrada",
        "ROMPERXENIGMAXCRIPTOGRAFIAXUNAL",
        lambda: _encrypt_vector("portada", "output"),
    ),
    Cifra(
        "4",
        "traza de la letra A",
        "plugboard A → III C → II D → I F → reflector S → I S → II E → III B → plugboard B",
        _trace_slide_4,
    ),
    Cifra(
        "14", "AAAAA con I-II-III y anillos AAA", "BDZGO", lambda: _encrypt_vector("bdzgo", "input")
    ),
    Cifra("14", "lo mismo con anillos BBB", "EWTYX", lambda: _encrypt_vector("ewtyx", "input")),
    Cifra(
        "14",
        "ejemplo de py-enigma (10 cables)",
        "THEXRUSSIANSXAREXCOMINGX",
        lambda: encrypt(
            EnigmaConfig.from_dict(vector("py_enigma")["key"]).with_positions("BLA"),
            vector("py_enigma")["input"],
        ),
    ),
    # Diapositiva 6 · stats/inference.py y E1
    Cifra(
        "6",
        "(25/26)¹⁰⁰: ningún punto fijo en 100 letras al azar",
        f"1,98{NBSP}%",
        lambda: _pct(no_fixed_point_probability(100), 2),
    ),
    Cifra(
        "6, 14",
        "claves con involución (de 2.000)",
        "2.000",
        lambda: fmt_int(_pilot_properties()[0]),
    ),
    Cifra(
        "6, 14",
        "letras cifradas con esas 2.000 claves",
        "200.000",
        lambda: fmt_int(_pilot_properties()[1]),
    ),
    Cifra(
        "6, 14", "puntos fijos en esas 200.000 letras", "0", lambda: fmt_int(_pilot_properties()[2])
    ),
    # Diapositiva 15 · fórmula; la simulación con alemán real es E4 (fase 2)
    Cifra(
        "15, 20",
        "(25/26)¹³: sobreviven a un crib de 13 letras",
        f"60,1{NBSP}%",
        lambda: _pct(no_fixed_point_probability(13)),
    ),
    Cifra(
        "15",
        "(25/26)⁵⁰: sobreviven a un crib de 50 letras",
        f"14,1{NBSP}%",
        lambda: _pct(no_fixed_point_probability(50)),
    ),
    # Diapositivas 10 y 11 · cribs/ (casos deterministas de 6.5)
    Cifra("10", "alineaciones de WETTERBERICHT sobre BBGCCKITCTTEZZZLCZ", "6", _slide10_count),
    Cifra("10", "alineaciones sin conflictos", "0, 1, 2, 3", _slide10_valid),
    Cifra(
        "10",
        "conflicto de las alineaciones 4 y 5",
        "T sobre la T de la posición 7",
        _slide10_conflict,
    ),
    Cifra(
        "11",
        "menú de la alineación 0: letras, aristas, componentes y lazos",
        "11 · 13 · 1 · 3",
        lambda: _menu_numbers("slide"),
    ),
    Cifra("11", "letra de prueba y su grado", "T, grado 6", lambda: _test_letter("slide")),
    Cifra(
        "6.5",
        "menú del caso de respaldo: letras, aristas, componentes y lazos",
        "11 · 13 · 1 · 3",
        lambda: _menu_numbers("backup"),
    ),
    Cifra(
        "6.5", "letra de prueba del caso de respaldo", "T, grado 4", lambda: _test_letter("backup")
    ),
    # Pendientes
    Cifra(
        "9",
        "Kuhl: 105.456 · 21.230 · 11.466",
        "105.456 · 21.230 · 11.466",
        pending="fase 5 (P2), que no se hizo: la diapositiva solo cita a Kuhl (2007)",
    ),
    # Diapositivas 13 y 17 · banburismus/ (tasas 1/17 y 1/26 de Wikipedia, «Banburismus»)
    Cifra(
        "13, 17",
        "decibanes por repetición: 10·log₁₀((1/17)/(1/26))",
        f"+1,845{NBSP}dB",
        lambda: _banburismus_weight("repeticion"),
    ),
    Cifra(
        "5.6",
        "decibanes por no repetición: 10·log₁₀((16/17)/(25/26))",
        f"−0,093{NBSP}dB",
        lambda: _banburismus_weight("no_repeticion"),
    ),
    Cifra(
        "17",
        "decibanes por letra, en promedio, en profundidad",
        f"+0,0211{NBSP}dB",
        lambda: _banburismus_weight("profundidad"),
    ),
    Cifra(
        "17",
        "decibanes por letra, en promedio, al azar",
        f"−0,0184{NBSP}dB",
        lambda: _banburismus_weight("azar"),
    ),
    Cifra("13, 17", "umbrales de Wald con α = β = 1 %", f"±19,96{NBSP}dB", _wald_thresholds),
    Cifra(
        "13, 17",
        "letras esperadas según Wald, en profundidad y al azar",
        "929 y 1.062",
        _wald_letters,
    ),
    # Diapositiva 16 · data/reference/turing_stops.csv (las cifras medidas van en RESUMEN.md)
    Cifra(
        "16",
        "Turing, 12 letras: paradas por orden con 0, 1, 2 y 3 lazos; en 60 órdenes con 2 y 3",
        "820 · 31 · 1,2 · 0,04; 72 y 2,4 en 60",
        _turing_slide_16,
    ),
)
"""Todas las cifras de la tabla 11.3, en el orden de las diapositivas."""


def evaluate() -> list[dict[str, object]]:
    """Calcula todas las cifras: lo esperado, lo obtenido y si coinciden."""
    rows: list[dict[str, object]] = []
    for c in CIFRAS:
        obtained = c.compute() if c.compute else None
        rows.append(
            {
                "diapositivas": c.slides,
                "cifra": c.description,
                "esperado": c.expected,
                "obtenido": obtained,
                "coincide": None if obtained is None else obtained == c.expected,
                "pendiente": c.pending,
            }
        )
    return rows
