"""Estadística del idioma: normalización, IC, χ², matriz plano × cifrado y n-gramas."""

from __future__ import annotations

import numpy as np
import pytest

from enigma_lab import SEED
from enigma_lab.core.batch import encrypt_batch, random_key_batch
from enigma_lab.stats.corpus import load_codes, normalize, random_excerpts
from enigma_lab.stats.frequencies import (
    RANDOM_IC,
    chi2_uniform,
    counts,
    index_of_coincidence,
    pair_matrix,
)
from enigma_lab.stats.inference import mean_ci, no_fixed_point_probability, wilson_interval
from enigma_lab.stats.ngrams import NgramModel, model


@pytest.mark.parametrize(
    ("text", "language", "mode", "expected"),
    [
        ("Grüße aus Köln", "aleman", "letras", "GRUESSEAUSKOELN"),
        ("Grüße aus Köln", "aleman", "x", "GRUESSEXAUSXKOELN"),
        ("Äpfel, Öl und Übermut.", "aleman", "x", "AEPFELXOELXUNDXUEBERMUT"),
        ("Señor, ¿dónde está?", "espanol", "letras", "SENORDONDEESTA"),
        ("El niño — y la cigüeña", "espanol", "x", "ELXNINOXYXLAXCIGUENA"),
    ],
)
def test_normalization(text: str, language: str, mode: str, expected: str) -> None:
    assert normalize(text, language, mode) == expected  # type: ignore[arg-type]


def test_index_of_coincidence_known_values() -> None:
    assert index_of_coincidence(np.array([0, 0, 1, 1])) == pytest.approx(2 * 2 / 12)
    uniform = np.random.default_rng(SEED).integers(0, 26, 200_000)
    assert index_of_coincidence(uniform) == pytest.approx(RANDOM_IC, abs=0.001)


def test_german_sample_ic_close_to_reference() -> None:
    ic = index_of_coincidence(load_codes("aleman"))
    assert 0.072 < ic < 0.080  # Pommerening: 0,0758


def test_chi2_rejects_german_not_uniform_noise() -> None:
    rng = np.random.default_rng(SEED)
    german = random_excerpts(rng, "aleman", 50, 500)
    noise = rng.integers(0, 26, (50, 500))
    _, p_german = chi2_uniform(german)
    _, p_noise = chi2_uniform(noise)
    assert (p_german < 0.05).all()
    assert (p_noise < 0.05).mean() < 0.2


def test_counts_batch_matches_single() -> None:
    rng = np.random.default_rng(SEED)
    batch = rng.integers(0, 26, (5, 40))
    assert (counts(batch) == np.array([counts(row) for row in batch])).all()


def test_enigma_pair_matrix_has_zero_diagonal() -> None:
    rng = np.random.default_rng(SEED)
    plain = random_excerpts(rng, "aleman", 100, 200)
    keys, _ = random_key_batch(rng, 100)
    matrix = pair_matrix(plain, encrypt_batch(keys, plain))
    assert np.trace(matrix) == 0
    assert matrix.sum() == 100 * 200


def test_ngram_scores_separate_german_from_noise() -> None:
    quad = model("aleman", 4)
    german = load_codes("aleman")[:300]
    noise = np.random.default_rng(SEED).integers(0, 26, 300)
    assert quad.score_per_ngram(german) > quad.score_per_ngram(noise) + 2
    assert quad.score_per_ngram(noise) > quad.floor - 0.5


def test_ngram_model_counts() -> None:
    m = NgramModel.from_codes(np.array([0, 1, 0, 1, 0]), 2)  # AB, BA, AB, BA
    assert m.total == 4
    assert m.log_probs[0 * 26 + 1] == pytest.approx(np.log10(0.5))


def test_inference_helpers() -> None:
    low, high = wilson_interval(10_000, 10_000)
    assert high == 1.0 and 0.9995 < low < 0.9997
    mean, lo, hi = mean_ci(np.array([1.0, 2.0, 3.0]))
    assert mean == 2.0 and lo < 2.0 < hi
    assert no_fixed_point_probability(13) == pytest.approx((25 / 26) ** 13)
