"""La Bombe: aleatorizador, Numba frente a la referencia, la parada
verdadera y el verificador, y el caso de respaldo."""

from __future__ import annotations

import json
import time

import numpy as np
import pytest

from enigma_lab import SEED, paths
from enigma_lab.bombe import bombe_reference, checker
from enigma_lab.bombe.cases import middle_moves, random_case
from enigma_lab.bombe.scrambler import (
    N_POSITIONS,
    parse_position,
    position_index,
    position_letters,
    rotor_orders,
    scrambler_table,
)
from enigma_lab.bombe.sweep import (
    BombeSettings,
    is_true_stop,
    run_bombe,
    run_order,
    sweep_order,
    true_stop,
)
from enigma_lab.bombe.wiring import wiring_from_menu
from enigma_lab.core.machine import Enigma, EnigmaConfig, encrypt


def _backup() -> dict[str, object]:
    data: dict[str, object] = json.loads(
        (paths.DEMO / "respaldo_bombe.json").read_text(encoding="utf-8")
    )
    return data


# ---------------------------------------------------------------- aleatorizador


def test_sixty_rotor_orders() -> None:
    orders = rotor_orders()
    assert len(orders) == len(set(orders)) == 60
    assert all(len(set(o)) == 3 for o in orders)


def test_position_letters_roundtrip() -> None:
    assert position_index(7, 4, 2) == 7 * 676 + 4 * 26 + 2
    assert position_letters(parse_position("HEC")) == "HEC"
    with pytest.raises(ValueError):
        parse_position("AB")


def test_scrambler_table_matches_scalar_machine() -> None:
    rng = np.random.default_rng(SEED)
    orders = rotor_orders()
    for _ in range(40):
        order = orders[int(rng.integers(len(orders)))]
        core = tuple(int(v) for v in rng.integers(0, 26, size=3))
        machine = Enigma(EnigmaConfig(rotors=order, positions=core))
        assert tuple(scrambler_table(order)[position_index(*core)]) == machine.permutation()


def test_scrambler_is_a_fixed_point_free_involution() -> None:
    table = scrambler_table(("IV", "I", "V")).astype(np.int64)
    rows = np.arange(N_POSITIONS)[:, None]
    assert (table[rows, table] == np.arange(26)).all()
    assert (table != np.arange(26)).all()


# ---------------------------------------------------------------- Numba = referencia

REFERENCE_CASES = 24


@pytest.mark.parametrize("k", range(REFERENCE_CASES))
def test_numba_matches_reference(k: int) -> None:
    """La Bombe en Numba y la de referencia dan los mismos hilos encendidos y aislados."""
    rng = np.random.default_rng(SEED + k)
    case = random_case(rng, crib_length=8 + k % 9, message_length=60)
    diagonal = k % 3 != 2
    settings = BombeSettings(mode="robusto" if k % 4 == 3 else "bletchley")
    wiring = wiring_from_menu(case.crib, case.cipher_segment, diagonal=diagonal)
    order = case.config.rotors
    turns = settings.turns(case.crib_length)
    lit, singles = sweep_order(wiring, order, "B", turns)

    stops = np.flatnonzero((lit < 26).any(axis=1))
    chosen = set(rng.choice(N_POSITIONS, size=6, replace=False).tolist())
    chosen |= set(rng.choice(stops, size=min(6, len(stops)), replace=False).tolist())
    expected = true_stop(case.config, case.crib_position, case.crib_length)
    if expected is not None:
        chosen.add(expected[0])
    reference = bombe_reference.sweep_positions(
        case.crib,
        case.cipher_segment,
        order,
        sorted(chosen),
        turns.tolist(),
        test_letter=wiring.test_letter,
        diagonal=diagonal,
    )
    variant = {int(t): v for v, t in enumerate(turns)}
    for (position, turn), (ref_lit, ref_singles) in reference.items():
        v = variant[turn]
        assert (int(lit[position, v]), int(singles[position, v])) == (ref_lit, ref_singles)


def test_stops_do_not_depend_on_the_energised_wire() -> None:
    rng = np.random.default_rng(SEED)
    case = random_case(rng, crib_length=12)
    order = case.config.rotors
    turns = np.zeros(1, dtype=np.int64)
    a = wiring_from_menu(case.crib, case.cipher_segment, test_wire="A")
    q = wiring_from_menu(case.crib, case.cipher_segment, test_wire="Q")
    lit_a, singles_a = sweep_order(a, order, "B", turns)
    lit_q, singles_q = sweep_order(q, order, "B", turns)
    assert ((lit_a < 26) == (lit_q < 26)).all()
    assert (singles_a == singles_q).all()


# ---------------------------------------------------------------- 6.5: caso de respaldo


def test_backup_case_stops_in_bletchley_mode_and_decrypts() -> None:
    data = _backup()
    config = EnigmaConfig.from_dict(data["key"])  # type: ignore[arg-type]
    cipher, crib = str(data["ciphertext"]), str(data["crib"])
    wiring = wiring_from_menu(crib, cipher[: len(crib)])
    assert not middle_moves(config, 0, len(crib))
    run = run_bombe(wiring, BombeSettings())
    assert any(is_true_stop(s, config, 0, wiring) for s in run.stops)
    assert any(s.order == ("II", "III", "I") for s in run.stops)
    best = checker.verify(run, cipher, 0).best
    assert best is not None and best.plausible
    assert best.plaintext == data["plaintext"]
    assert best.config.rotors == ("II", "III", "I")
    assert encrypt(best.config, best.plaintext) == cipher


# ---------------------------------------------------------------- 6.4


def _check_case(case_seed: int) -> tuple[bool, bool]:
    """(¿hubo parada verdadera?, ¿el verificador recuperó una clave equivalente?)."""
    rng = np.random.default_rng(case_seed)
    case = random_case(rng, crib_length=int(rng.integers(12, 17)), no_turnover=True)
    wiring = wiring_from_menu(case.crib, case.cipher_segment)
    settings = BombeSettings(orders=(case.config.rotors,))
    run = run_bombe(wiring, settings)
    found = any(is_true_stop(s, case.config, case.crib_position, wiring) for s in run.stops)
    best = checker.verify(run, case.ciphertext, case.crib_position).best
    recovered = (
        best is not None
        and best.plaintext == case.plaintext
        and encrypt(best.config, case.plaintext) == case.ciphertext
    )
    return found, recovered


@pytest.mark.parametrize("k", range(20))
def test_true_stop_and_key_recovered(k: int) -> None:
    found, recovered = _check_case(SEED * 1000 + k)
    assert found and recovered


@pytest.mark.lento
def test_two_hundred_random_cases() -> None:
    """En 200 casos aleatorios (crib de 12 a 16 letras, sin vuelta del central), la clave
    verdadera siempre da parada y el verificador recupera una clave equivalente."""
    results = [_check_case(SEED * 1000 + 100 + k) for k in range(200)]
    assert all(found for found, _ in results)
    assert all(recovered for _, recovered in results)


def test_robust_mode_covers_a_turnover_in_the_crib() -> None:
    rng = np.random.default_rng(SEED)
    while True:
        case = random_case(rng, crib_length=13, crib_position=0)
        expected = true_stop(case.config, 0, 13)
        if expected is not None and expected[1] > 0:
            break
    wiring = wiring_from_menu(case.crib, case.cipher_segment)
    order = case.config.rotors
    robust = run_order(wiring, order, BombeSettings(orders=(order,), mode="robusto"))
    assert any(is_true_stop(s, case.config, 0, wiring) for s in robust.stops)


# ---------------------------------------------------------------- rendimiento (fase 3)


@pytest.mark.lento
def test_performance_one_order_and_sixty() -> None:
    """Criterio de la fase 3: un orden en menos de 3 s y los 60 en menos de 2 min."""
    rng = np.random.default_rng(SEED)
    case = random_case(rng, crib_length=14)
    wiring = wiring_from_menu(case.crib, case.cipher_segment)
    run_order(wiring, ("I", "II", "III"), BombeSettings())  # compila o carga de la caché
    start = time.perf_counter()
    run_order(wiring, ("III", "V", "II"), BombeSettings())
    assert time.perf_counter() - start < 3
    assert run_bombe(wiring, BombeSettings()).seconds < 120


def test_verify_short_ciphertext() -> None:
    """Con un cifrado de menos de 4 letras, «Verificar» termina sin error."""
    wiring = wiring_from_menu("BA", "AB")
    run = run_bombe(wiring, BombeSettings(orders=(("I", "II", "III"),)))
    verification = checker.verify(run, "ABC", 0)
    assert verification.stops == run.n_stops
