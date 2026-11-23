"""El método de Rejewski: la característica, el catálogo y el tráfico de un día."""

from __future__ import annotations

import itertools
from collections import Counter
from dataclasses import replace

import numpy as np
import pytest
from hypothesis import given
from hypothesis import strategies as st

from enigma_lab import SEED
from enigma_lab.core.machine import EnigmaConfig
from enigma_lab.rejewski import traffic
from enigma_lab.rejewski.catalog import build_catalog
from enigma_lab.rejewski.characteristic import (
    DOUBLED_TYPES,
    HALF_TYPES,
    characteristic_code,
    compose,
    cycle_type,
    format_characteristic,
    from_code,
    is_paired,
    machine_characteristic,
    middle_moves,
    parse_characteristic,
)
from test_properties import configs  # pytest pone tests/ en sys.path


@given(configs(models=("I", "M3", "M4")))
def test_characteristic_does_not_depend_on_the_plugboard(config: EnigmaConfig) -> None:
    """Conjugar no cambia la estructura de ciclos: AD, BE y CF dan lo mismo sin plugboard."""
    assert machine_characteristic(config) == machine_characteristic(replace(config, plugboard=()))


@given(configs(models=("I", "M3")))
def test_products_have_their_cycles_in_pairs(config: EnigmaConfig) -> None:
    """Teorema de Rejewski: el producto de dos involuciones sin puntos fijos."""
    assert all(is_paired(t) and sum(t) == 26 for t in machine_characteristic(config))


@st.composite
def day_keys(draw: st.DrawFn) -> EnigmaConfig:
    """Una clave de 1932 (rotores I–III, reflector A) en una posición sin vuelta del central."""
    order = tuple(draw(st.permutations(("I", "II", "III"))))
    cables = draw(st.integers(0, 13))
    shuffled = draw(st.permutations("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
    pairs = tuple(sorted(tuple(sorted(shuffled[2 * i : 2 * i + 2])) for i in range(cables)))
    settings = st.lists(st.integers(0, 25), min_size=3, max_size=3).map(tuple)
    config = EnigmaConfig(
        rotors=order,  # type: ignore[arg-type]
        reflector="A",
        rings=draw(settings),
        positions=draw(settings),
        plugboard=pairs,  # type: ignore[arg-type]
    )
    return config


@given(day_keys())
def test_catalog_entry_is_the_machine_characteristic(config: EnigmaConfig) -> None:
    """Sin vuelta del central, la entrada del catálogo (posición del núcleo) es la de la máquina."""
    catalog = build_catalog()
    entry = catalog.characteristic_at(config.rotors, traffic.core_position(config))
    if middle_moves(config):
        return  # el supuesto 1 del catálogo no vale en ese día (lo mide E7)
    assert entry == machine_characteristic(config)


def test_catalog_counts() -> None:
    """105.456 configuraciones; las cifras propias, que difieren de las de Kuhl (VALIDACION)."""
    catalog = build_catalog()
    sizes = catalog.class_sizes()
    assert catalog.n_configurations == 105_456 == sizes.sum()
    assert len(HALF_TYPES) == 101 and len(DOUBLED_TYPES) == 101
    assert (len(sizes), int((sizes == 1).sum()), int(sizes.max())) == (21_225, 11_578, 1_728)
    top = catalog.top(1).iloc[0]
    assert top["caracteristica"] == "(13 13)(13 13)(13 13)"
    table = catalog.distribution()
    assert table["configuraciones"].sum() == 105_456
    assert table["caracteristicas"].sum() == 21_225


def test_catalog_lookup_returns_the_configuration() -> None:
    catalog = build_catalog()
    order, position = ("II", "I", "III"), 12_345
    code = catalog.code_at(order, position)
    assert (order, position) in catalog.matches(code)
    assert len(catalog.matches(code)) == catalog.size(code)


def test_middle_rotor_moves_in_176_of_676_positions() -> None:
    moved = sum(
        middle_moves(EnigmaConfig(rotors=("I", "II", "III"), reflector="A", positions=(0, m, r)))
        for m in range(26)
        for r in range(26)
    )
    assert moved == 176


def test_characteristic_text_round_trip() -> None:
    text = "(13 13)(12 12 1 1)(13 13)"
    ch = parse_characteristic(text)
    assert format_characteristic(ch) == text
    assert from_code(characteristic_code(ch)) == ch
    with pytest.raises(ValueError):
        parse_characteristic("(13 12 1)(13 13)(13 13)")


def _random_involution(rng: np.random.Generator) -> np.ndarray:
    pairs = rng.permutation(26).reshape(-1, 2)
    inv = np.empty(26, dtype=np.int64)
    inv[pairs[:, 0]], inv[pairs[:, 1]] = pairs[:, 1], pairs[:, 0]
    return inv


def _brute_force(known: np.ndarray) -> dict[int, int]:
    """Todas las completaciones de lo conocido con los ciclos en parejas, por estructura."""
    unknown = [x for x in range(26) if known[x] < 0]
    images = sorted(set(range(26)) - {int(v) for v in known if v >= 0})
    found: Counter[int] = Counter()
    for choice in itertools.permutations(images):
        full = known.copy()
        full[unknown] = choice
        lengths = cycle_type(full)
        if is_paired(lengths):
            found[DOUBLED_TYPES.index(lengths)] += 1
    return dict(found)


def test_completions_match_brute_force() -> None:
    rng = np.random.default_rng(SEED)
    for _ in range(150):
        ad = compose(_random_involution(rng), _random_involution(rng))
        known = ad.copy()
        known[rng.choice(26, int(rng.integers(1, 6)), replace=False)] = -1
        assert traffic.completions(known, cap=10**9) == _brute_force(known)


def test_partial_structure_splits_cycles_and_chains() -> None:
    known = np.full(26, -1)
    known[[0, 1]] = [1, 0]  # el ciclo cerrado (A B)
    known[[2, 3]] = [3, 4]  # la cadena C → D → E
    closed, chains = traffic.partial_structure(known)
    assert closed == [2]
    assert chains[0] == 3 and len(chains) == 22  # C D E y 21 letras sueltas


def test_coupon_collector_theory() -> None:
    assert traffic.coupon_expectation(26, 1) == pytest.approx(26 * traffic.harmonic(26))
    assert traffic.coupon_expectation(25, 1) == pytest.approx(26 * (traffic.harmonic(26) - 1))
    assert traffic.coupon_expectation(26, 3) > traffic.coupon_expectation(26, 1)
    assert traffic.coupon_pmf(26, 3).sum() == pytest.approx(1)


def test_a_day_of_traffic() -> None:
    """Lo conocido coincide con AD, BE y CF verdaderos y los niveles van en orden."""
    rng = np.random.default_rng(SEED)
    day = traffic.simulate_day(rng, 400)
    truth = day.true_products
    for product in range(3):
        known = traffic.known_after(day.indicators[:60], product)
        seen = known >= 0
        assert (known[seen] == truth[product][seen]).all()
    times = traffic.reconstruction_times(day.indicators)
    for k in range(3):
        assert (
            times["caracteristica"][k]
            <= times["permutacion"][k]
            <= times["eliminacion"][k]
            <= times["todas"][k]
        )
