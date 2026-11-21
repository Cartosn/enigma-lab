"""Propiedades de la sección 6.3, con hypothesis.

- Cifrar dos veces devuelve el original (la máquina es una involución).
- Ninguna letra se cifra a sí misma.
- La API por lotes coincide con la escalar.
"""

from __future__ import annotations

import numpy as np
from hypothesis import given
from hypothesis import strategies as st

from enigma_lab import SEED
from enigma_lab.core.batch import KeyBatch, encrypt_batch, to_codes, to_texts
from enigma_lab.core.machine import EnigmaConfig, encrypt
from enigma_lab.core.wiring import ALPHABET, MODELS
from enigma_lab.experiments.e1_validation import check_properties

letters = st.text(alphabet=ALPHABET, min_size=1, max_size=120)


@st.composite
def configs(draw: st.DrawFn, models: tuple[str, ...] = ("I", "M3", "M4")) -> EnigmaConfig:
    """Una clave cualquiera: modelo, rotores, reflector, anillos, posiciones y 0–13 cables."""
    model = draw(st.sampled_from(models))
    spec = MODELS[model]
    rotors = tuple(draw(st.permutations(spec.rotors))[:3])
    if spec.greek:
        rotors = (draw(st.sampled_from(spec.greek)), *rotors)
    n = spec.n_rotors
    settings = st.lists(st.integers(0, 25), min_size=n, max_size=n).map(tuple)
    cables = draw(st.integers(0, 13))
    shuffled = draw(st.permutations(ALPHABET))
    pairs = tuple(
        sorted(tuple(sorted(shuffled[2 * i : 2 * i + 2])) for i in range(cables))  # type: ignore[misc]
    )
    return EnigmaConfig(
        rotors=rotors,
        reflector=draw(st.sampled_from(spec.reflectors)),
        rings=draw(settings),
        positions=draw(settings),
        plugboard=pairs,
        model=model,
    )


@given(configs(), letters)
def test_encrypting_twice_returns_the_original(config: EnigmaConfig, text: str) -> None:
    assert encrypt(config, encrypt(config, text)) == text


@given(configs(), letters)
def test_no_letter_encrypts_to_itself(config: EnigmaConfig, text: str) -> None:
    assert all(p != c for p, c in zip(text, encrypt(config, text), strict=True))


@given(st.lists(configs(models=("I", "M3")), min_size=1, max_size=8), st.data())
def test_batch_matches_scalar(keys: list[EnigmaConfig], data: st.DataObject) -> None:
    length = data.draw(st.integers(1, 80))
    texts = [data.draw(st.text(alphabet=ALPHABET, min_size=length, max_size=length)) for _ in keys]
    batch = to_texts(encrypt_batch(KeyBatch.from_configs(keys), to_codes(texts)))
    assert batch == [encrypt(c, t) for c, t in zip(keys, texts, strict=True)]


def test_pilot_properties_2000_keys() -> None:
    """Diapositivas 6 y 14: 2.000 claves y 200.000 letras, 0 puntos fijos, involución."""
    df = check_properties(2_000, 100, np.random.default_rng(SEED))
    assert len(df) == 2_000 and df["letras"].sum() == 200_000
    assert df["puntos_fijos"].sum() == 0
    assert df["involucion"].all()
    assert df["coincide"].all()  # lotes = escalar
