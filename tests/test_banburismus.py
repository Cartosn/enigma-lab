"""Banburismus: decibanes, el SPRT de Wald y los mensajes en profundidad."""

from __future__ import annotations

import math

import numpy as np
import pytest

from enigma_lab import SEED
from enigma_lab.banburismus import depth, scoring, sprt
from enigma_lab.banburismus.scoring import TURING
from enigma_lab.core.machine import Enigma, EnigmaConfig
from enigma_lab.core.wiring import ALPHABET

# ---------------------------------------------------------------- decibanes y Wald


def test_turing_weights_match_section_56() -> None:
    """+1,845 dB por repetición, −0,093 por no repetición; +0,0211 y −0,0184 por letra."""
    assert round(scoring.repeat_weight(), 3) == 1.845
    assert round(scoring.non_repeat_weight(), 3) == -0.093
    assert round(scoring.expected_weight(1 / 17), 4) == 0.0211
    assert round(scoring.expected_weight(1 / 26), 4) == -0.0184
    assert TURING.drift(True) == pytest.approx(scoring.expected_weight(1 / 17))
    assert TURING.drift(False) == pytest.approx(scoring.expected_weight(1 / 26))


def test_wald_thresholds_and_expected_letters() -> None:
    """±19,96 dB con α = β = 1 %; 929 letras en profundidad y 1.062 al azar."""
    upper, lower = sprt.thresholds(0.01)
    assert round(upper, 2) == 19.96 and lower == pytest.approx(-upper)
    assert round(sprt.wald_letters(TURING.drift(True), True)) == 929
    assert round(sprt.wald_letters(TURING.drift(False), False)) == 1062


@pytest.mark.parametrize("depth_hypothesis", [True, False])
def test_exact_sprt_obeys_wald_identity(depth_hypothesis: bool) -> None:
    """El cálculo exacto cumple E[S_N] = μ·E[N] y pide más letras que Wald por el sobrepaso."""
    exact = sprt.exact_turing(0.01, depth_hypothesis)
    mu = TURING.drift(depth_hypothesis)
    assert exact.tail < 1e-12
    assert exact.mean_final / mu == pytest.approx(exact.letters, rel=1e-9)
    assert exact.letters > sprt.wald_letters(mu, depth_hypothesis)
    assert 0 < exact.overshoot_upper < TURING.plus[0]
    assert 0 < exact.overshoot_lower < -TURING.minus[0]
    wrong = exact.reject_depth if depth_hypothesis else exact.accept_depth
    assert wrong < 0.01  # el sobrepaso deja los errores reales bajo el nominal


@pytest.mark.parametrize("depth_hypothesis", [True, False])
def test_wald_gap_adds_up(depth_hypothesis: bool) -> None:
    gap = sprt.wald_gap(0.01, depth_hypothesis)
    parts = gap["errores"] + gap["sobrepaso_arriba"] + gap["sobrepaso_abajo"]
    assert parts == pytest.approx(gap["total"], abs=1e-6)
    # En profundidad casi toda la diferencia es el sobrepaso de arriba.
    if depth_hypothesis:
        assert gap["sobrepaso_arriba"] > 0.9 * gap["total"]


@pytest.mark.parametrize("depth_hypothesis", [True, False])
def test_simulation_matches_exact_calculation(depth_hypothesis: bool) -> None:
    """2.000 secuencias de Bernoulli: la media de letras cae a menos de 4 errores estándar."""
    p = 1 / 17 if depth_hypothesis else 1 / 26
    rng = np.random.default_rng(SEED)
    result = sprt.run_sprt(rng.random((2_000, 10_000)) < p, TURING, (0.01,))
    letters = result.letters[:, 0]
    assert np.isfinite(letters).all()
    exact = sprt.exact_turing(0.01, depth_hypothesis)
    standard_error = letters.std(ddof=1) / math.sqrt(len(letters))
    assert abs(letters.mean() - exact.letters) < 4 * standard_error
    accepted = (result.decision[:, 0] == 1).mean()
    assert accepted == pytest.approx(exact.accept_depth, abs=0.01)


@pytest.mark.parametrize("key", ["letras_1_17", "trigramas"])
def test_numba_sprt_matches_reference(key: str) -> None:
    model = scoring.scoring_model(key)
    rng = np.random.default_rng(SEED + 1)
    x = rng.random((200, 2_500)) < 0.07
    upper, lower = sprt.thresholds(0.01)
    result = sprt.run_sprt(x, model, (0.05, 0.01), checkpoints=(100, 2_500))
    for i in range(len(x)):
        letters, decision, final = sprt.sprt_reference(x[i], model, upper, lower)
        assert decision == result.decision[i, 1]
        if letters is None:
            assert np.isnan(result.letters[i, 1])
        else:
            assert letters == result.letters[i, 1]
            assert final == pytest.approx(result.final[i, 1])
    path = scoring.trajectory(x, model)
    assert np.allclose(result.at[:, 0], path[:, 99])
    assert np.allclose(result.at[:, 1], path[:, -1])


# ---------------------------------------------------------------- multigramas


def test_run_state_counts_previous_repeats() -> None:
    x = np.array([True, True, False, True, True, True])
    assert scoring.run_state(x, 3).tolist() == [0, 1, 2, 0, 1, 2]
    assert scoring.run_state(x, 2).tolist() == [0, 1, 1, 0, 1, 1]
    assert scoring.run_state(x, 1).tolist() == [0] * 6


def test_corpus_repeat_rate_is_above_turing() -> None:
    """El corpus alemán repite más que el tráfico naval de Turing (1/17 ≈ 0,059)."""
    letters_only = scoring.ngram_coincidence(1, "muestra", "letras")
    with_x = scoring.ngram_coincidence(1, "muestra", "x")
    assert 0.072 < letters_only < with_x < 0.085
    assert letters_only > scoring.P_DEPTH


@pytest.mark.parametrize("order", [1, 3, 4])
def test_run_model_reproduces_corpus_coincidences(order: int) -> None:
    """La cadena de rachas repite, a la larga, con ρ₁; y dos columnas seguidas, con ρ₂."""
    model = scoring.corpus_model(order)
    rho1, rho2 = scoring.ngram_coincidence(1), scoring.ngram_coincidence(2)
    pi = model.stationary(True)
    probs = np.array(model.probs)
    assert pi @ probs == pytest.approx(rho1)
    if order > 1:
        # P(dos seguidas) = Σ_r P(racha r y repite) · P(repite de nuevo desde min(r + 1, k − 1)).
        nxt = probs[np.minimum(np.arange(order) + 1, order - 1)]
        assert (pi * probs) @ nxt == pytest.approx(rho2)


def test_bigram_repeat_weighs_more_than_two_letters() -> None:
    """Dos repeticiones juntas (un bigrama) pesan más que separadas; con letras sueltas, igual."""
    together = np.array([True, True, False, False])
    apart = np.array([True, False, True, False])
    multigram = scoring.scoring_model("trigramas")
    assert (
        scoring.column_weights(together, multigram).sum()
        > scoring.column_weights(apart, multigram).sum()
    )
    assert scoring.column_weights(together, TURING).sum() == pytest.approx(
        scoring.column_weights(apart, TURING).sum()
    )


# ---------------------------------------------------------------- profundidad


def test_true_offset_is_delta_or_delta_minus_26() -> None:
    """Con rotores I–V siempre hay profundidad: +δ si el central no se mueve, δ − 26 si sí."""
    rng = np.random.default_rng(SEED)
    signs = []
    for _ in range(1_500):
        rotors = tuple(rng.choice(["I", "II", "III", "IV", "V"], 3, replace=False))
        start = tuple(int(v) for v in rng.integers(0, 26, 3))
        right2 = (start[2] + int(rng.integers(1, 26))) % 26
        offset = depth.true_offset(rotors, start, right2)
        delta = (right2 - start[2]) % 26
        assert offset in (delta, delta - 26)
        signs.append(offset > 0)
    assert np.mean(signs) == pytest.approx(0.5, abs=0.05)


def test_depth_against_the_scalar_machine() -> None:
    """La máquina escalar cifra igual y, en el desplazamiento, usa los mismos estados."""
    pairs = depth.make_pairs(np.random.default_rng(SEED), 3, 120, "aleman")
    for i in range(len(pairs)):
        config = pairs.configs[i]
        second = config.with_positions(pairs.message_key(i, 2))
        traces = [
            Enigma(key).trace("".join(ALPHABET[c] for c in plain))
            for key, plain in ((config, pairs.plain1[i]), (second, pairs.plain2[i]))
        ]
        cipher = ["".join(t.lamp for t in trace) for trace in traces]
        assert cipher[0] == "".join(ALPHABET[c] for c in pairs.cipher1[i])
        assert cipher[1] == "".join(ALPHABET[c] for c in pairs.cipher2[i])
        d = int(pairs.offsets[i])
        for j in range(max(0, -d), min(120, 120 - d)):
            assert traces[1][j].positions == traces[0][j + d].positions


def test_cipher_repeats_follow_plain_repeats_in_depth() -> None:
    pairs = depth.make_pairs(np.random.default_rng(SEED), 200, 425, "aleman")
    x = depth.repeats(pairs.cipher1, pairs.cipher2, pairs.offsets, 400)
    top, bottom = depth.aligned(pairs.plain1, pairs.plain2, pairs.offsets, 400)
    assert (x == (top == bottom)).all()
    wrong = depth.false_offsets(np.random.default_rng(SEED), pairs.offsets)
    assert (wrong != pairs.offsets).all() and (np.abs(wrong) <= depth.MAX_OFFSET).all()
    chance = depth.repeats(pairs.cipher1, pairs.cipher2, wrong, 400).mean()
    assert chance == pytest.approx(1 / 26, abs=0.003)


def test_turing_plaintexts_repeat_one_in_seventeen() -> None:
    pairs = depth.make_pairs(np.random.default_rng(SEED), 300, 1_025, "tasa_1_17")
    rate = depth.repeats(pairs.cipher1, pairs.cipher2, pairs.offsets, 1_000).mean()
    assert rate == pytest.approx(1 / 17, abs=0.002)


def test_independent_fragments_do_not_overlap() -> None:
    first, second = depth.independent_fragments(np.random.default_rng(SEED), 50, 2_000)
    assert first.shape == second.shape == (50, 2_000)
    assert not (first == second).all(axis=1).any()


def test_offset_scores_find_the_true_offset() -> None:
    """Con 1.500 letras de texto alemán, el desplazamiento verdadero saca más decibanes."""
    pairs = depth.make_pairs(np.random.default_rng(SEED + 2), 5, 1_525, "aleman")
    for i in range(len(pairs)):
        table = scoring.offset_scores(pairs.cipher1[i], pairs.cipher2[i], 1_500)
        best = table.loc[table["decibanes"].idxmax(), "desplazamiento"]
        assert best == pairs.offsets[i]
        true_row = table[table["desplazamiento"] == pairs.offsets[i]].iloc[0]
        assert true_row["decibanes"] > sprt.thresholds(0.01)[0]


def test_message_keys_share_left_and_middle() -> None:
    pairs = depth.make_pairs(np.random.default_rng(SEED), 4, 60, "tasa_1_17")
    for i in range(len(pairs)):
        first, second = pairs.message_key(i, 1), pairs.message_key(i, 2)
        assert first[:2] == second[:2] and first[2] != second[2]
        assert isinstance(pairs.configs[i], EnigmaConfig)
