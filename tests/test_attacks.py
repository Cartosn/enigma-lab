"""El ataque moderno solo con texto cifrado: Gillogly y el hill climbing."""

from __future__ import annotations

import numpy as np
import pytest

from enigma_lab import SEED
from enigma_lab.attacks import gillogly, hillclimb
from enigma_lab.bombe.scrambler import position_index, rotor_orders, scrambler_table
from enigma_lab.core.machine import EnigmaConfig, encrypt
from enigma_lab.core.random_keys import random_config
from enigma_lab.core.stepping import notch_sets, step
from enigma_lab.core.wiring import ALPHABET, ROTORS
from enigma_lab.experiments.e8_coa import to_codes, true_location
from enigma_lab.stats.corpus import random_excerpts


def _message(seed: int, cables: int, length: int, rotors: tuple[str, ...] = ("I", "II", "III")):  # type: ignore[no-untyped-def]
    rng = np.random.default_rng(seed)
    config = random_config(rng, cables=cables, rotors=rotors)
    plain = random_excerpts(rng, "aleman", 1, length, "muestra", "x")[0].astype(np.int64)
    cipher = to_codes(encrypt(config, "".join(ALPHABET[c] for c in plain)))
    return config, plain, cipher


def test_step_table_is_the_machine_stepping() -> None:
    rng = np.random.default_rng(SEED)
    for order in (("I", "II", "III"), ("V", "II", "IV"), ("III", "V", "I")):
        table = gillogly.step_table(order)
        marks = notch_sets([ROTORS[n].notches for n in order])
        for window in rng.integers(0, 26, size=(200, 3)):
            following = step(tuple(int(w) for w in window), marks).positions
            assert table[position_index(*window)] == position_index(*following)


def test_phase1_kernel_matches_python() -> None:
    _, _, cipher = _message(SEED, 6, 120)
    order = ("II", "I", "III")
    table, nxt = scrambler_table(order, "B"), gillogly.step_table(order)
    scores = gillogly._phase1(table, nxt, cipher)
    for start in (0, 1, 777, 17_575):
        pos, counts = start, np.zeros(26, int)
        for c in cipher:
            pos = nxt[pos]
            counts[table[pos, c]] += 1
        expected = (counts * (counts - 1)).sum() / (len(cipher) * (len(cipher) - 1))
        assert scores[start] == pytest.approx(expected)


def test_true_location_and_plugboard_decrypt_like_the_machine() -> None:
    config, plain, cipher = _message(SEED + 1, 10, 700, ("I", "II", "III", "IV", "V"))
    truth = true_location(config)
    plug = np.arange(26)
    for a, b in config.plugboard:
        plug[ALPHABET.index(a)], plug[ALPHABET.index(b)] = ALPHABET.index(b), ALPHABET.index(a)
    paths = gillogly.paths_for(truth.order, truth.start, truth.ring_m, truth.ring_r, len(cipher))
    assert (hillclimb.decrypt(paths, cipher, plug) == plain).all()
    equivalent = gillogly.location_config(
        truth.order, truth.start, truth.ring_m, truth.ring_r, plug
    )
    text = encrypt(equivalent, "".join(ALPHABET[c] for c in cipher))
    assert text == "".join(ALPHABET[c] for c in plain)


def test_hill_climbing_from_the_true_location_finds_the_plugboard() -> None:
    config, plain, cipher = _message(SEED + 2, 10, 300)
    logp3 = hillclimb.trigram_table()
    result = gillogly.climb_at(cipher, true_location(config), logp3)
    assert (result.plaintext == plain).mean() >= 0.95
    found = {tuple(sorted(p)) for p in hillclimb.plug_pairs(result.plug)}
    assert found == {tuple(sorted(p)) for p in config.plugboard}


def test_attack_reads_a_long_message_with_few_cables() -> None:
    """Las tres fases sobre los 6 órdenes de I–III: 800 letras con 6 cables."""
    config, plain, cipher = _message(SEED + 3, 6, 800)
    result = gillogly.attack(cipher, tuple(rotor_orders(("I", "II", "III"))), 100, 10)
    assert (result.best.plaintext == plain).mean() >= 0.9
    assert result.best.candidate.order == tuple(config.rotors)
    assert result.rank_of(config.rotors, true_location(config).start) < 100
    machine = encrypt(result.config, "".join(ALPHABET[c] for c in cipher))
    assert machine == "".join(ALPHABET[c] for c in result.best.plaintext)


def test_e_stecker_starts_include_every_partner_of_e() -> None:
    """La búsqueda parcial nunca empeora el arranque vacío en la ubicación verdadera."""
    config, _, cipher = _message(SEED + 4, 10, 120)
    logp3 = hillclimb.trigram_table()
    truth = true_location(config)
    plain_climb = gillogly.climb_at(cipher, truth, logp3)
    partial = gillogly.climb_at(cipher, truth, logp3, partial=True)
    assert partial.score >= plain_climb.score - 1e-9


def test_location_config_is_a_valid_key() -> None:
    config = gillogly.location_config(("I", "II", "III"), 12_345, 3, 7)
    assert isinstance(config, EnigmaConfig) and config.rings == (0, 3, 7)
