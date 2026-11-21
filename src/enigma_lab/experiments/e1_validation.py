"""E1 · ¿El simulador es correcto? (spec 7, con la validación de 6.1 a 6.3).

Tres partes:

1. **Vectores de 6.1:** la tabla de la diapositiva 14.
2. **py-enigma:** N claves y mensajes aleatorios (10.000 en modo completo), cifrados
   por el simulador y por py-enigma, una implementación independiente. La meta es
   100 % de coincidencia. Las claves mezclan Enigma I (la mitad), M3 y M4, con 0 a 10
   cables, y los mensajes tienen de 1 a 200 letras. py-enigma no trae el reflector A
   ni admite más de 10 cables, así que aquí se usan B y C (B y C delgados en la M4);
   las pruebas con hypothesis cubren de 0 a 13 cables y el reflector A.
3. **Propiedades:** 2.000 claves de Enigma I con 10 cables y mensajes de 100 letras
   (200.000 letras), como el piloto de las diapositivas 6 y 14. Se cuentan los puntos
   fijos (deben ser 0) y se comprueban la involución (cifrar dos veces devuelve el
   original) y que el cifrado por lotes dé lo mismo que el escalar.
"""

from __future__ import annotations

import time
from typing import Any

import numpy as np
import pandas as pd

from enigma_lab import SEED
from enigma_lab.core.batch import encrypt_batch, random_key_batch, to_texts
from enigma_lab.core.machine import EnigmaConfig, encrypt
from enigma_lab.core.random_keys import random_config, random_text
from enigma_lab.core.vectors import check_all
from enigma_lab.experiments.common import (
    Mode,
    RunInfo,
    save_figure,
    save_table,
    update_summary,
)
from enigma_lab.stats.inference import wilson_interval

PARAMS: dict[str, dict[str, int]] = {
    "rapido": {"n_pyenigma": 1_000, "n_properties": 2_000, "length": 100},
    "completo": {"n_pyenigma": 10_000, "n_properties": 2_000, "length": 100},
}
MODELS = ("I", "M3", "M4")
MODEL_WEIGHTS = (0.5, 0.25, 0.25)
PYENIGMA_REFLECTORS = {"I": ("B", "C"), "M3": ("B", "C"), "M4": ("B-Thin", "C-Thin")}
PYENIGMA_MAX_CABLES = 10
"""py-enigma rechaza más de 10 cables («Please specify 10 or less pairs»)."""


def pyenigma_encrypt(config: EnigmaConfig, text: str) -> str:
    """Cifra con py-enigma (la implementación de referencia) la misma clave y texto."""
    from enigma.machine import EnigmaMachine

    machine = EnigmaMachine.from_key_sheet(
        rotors=list(config.rotors),
        ring_settings=list(config.rings),
        reflector=config.reflector,
        plugboard_settings=config.plugboard_string or None,
    )
    machine.set_display(config.position_letters)
    result: str = machine.process_text(text)
    return result


def _random_case(rng: np.random.Generator) -> tuple[EnigmaConfig, str]:
    model = str(rng.choice(MODELS, p=MODEL_WEIGHTS))
    cables = int(rng.integers(0, PYENIGMA_MAX_CABLES + 1))
    config = random_config(rng, model=model, cables=cables, reflectors=PYENIGMA_REFLECTORS[model])
    return config, random_text(rng, int(rng.integers(1, 201)))


def compare_with_pyenigma(n: int, rng: np.random.Generator) -> pd.DataFrame:
    """N casos aleatorios cifrados por el simulador y por py-enigma."""
    rows = []
    for case in range(n):
        config, text = _random_case(rng)
        ours = encrypt(config, text)
        rows.append(
            {
                "parte": "py-enigma",
                "caso": case,
                "modelo": config.model,
                "rotores": " ".join(config.rotors),
                "reflector": config.reflector,
                "anillos": config.ring_letters,
                "posiciones": config.position_letters,
                "plugboard": config.plugboard_string,
                "cables": len(config.plugboard),
                "letras": len(text),
                "coincide": ours == pyenigma_encrypt(config, text),
                "puntos_fijos": sum(a == b for a, b in zip(text, ours, strict=True)),
                "involucion": encrypt(config, ours) == text,
            }
        )
    return pd.DataFrame(rows)


def check_properties(n_keys: int, length: int, rng: np.random.Generator) -> pd.DataFrame:
    """Puntos fijos, involución y lotes = escalar en n_keys claves de Enigma I (10 cables)."""
    keys, configs = random_key_batch(rng, n_keys, model="I", cables=10)
    plain = rng.integers(0, 26, size=(n_keys, length), dtype=np.uint8)
    cipher = encrypt_batch(keys, plain)
    back = encrypt_batch(keys, cipher)
    plain_texts, cipher_texts = to_texts(plain), to_texts(cipher)
    rows = []
    for i, config in enumerate(configs):
        rows.append(
            {
                "parte": "propiedades",
                "caso": i,
                "modelo": config.model,
                "rotores": " ".join(config.rotors),
                "reflector": config.reflector,
                "anillos": config.ring_letters,
                "posiciones": config.position_letters,
                "plugboard": config.plugboard_string,
                "cables": len(config.plugboard),
                "letras": length,
                "coincide": encrypt(config, plain_texts[i]) == cipher_texts[i],
                "puntos_fijos": int((plain[i] == cipher[i]).sum()),
                "involucion": bool((back[i] == plain[i]).all()),
            }
        )
    return pd.DataFrame(rows)


def vectors_table() -> pd.DataFrame:
    """Tabla de los vectores de 6.1 con las columnas de ``r1_validacion.csv``."""
    return pd.DataFrame(
        [
            {"prueba": r.label, "esperado": r.expected, "obtenido": r.obtained, "coincide": r.ok}
            for r in check_all()
        ]
    )


def run(params: dict[str, int], seed: int = SEED) -> pd.DataFrame:
    """Corre las partes 2 y 3 (la 1 es ``vectors_table``) con generadores independientes."""
    rng_pyenigma, rng_properties = np.random.default_rng(seed).spawn(2)
    return pd.concat(
        [
            compare_with_pyenigma(params["n_pyenigma"], rng_pyenigma),
            check_properties(params["n_properties"], params["length"], rng_properties),
        ],
        ignore_index=True,
    )


def summary(df: pd.DataFrame, vectors: pd.DataFrame) -> dict[str, Any]:
    """Cifras clave de E1 para ``results/summary.json``."""
    ref = df[df["parte"] == "py-enigma"]
    props = df[df["parte"] == "propiedades"]
    matches = int(ref["coincide"].sum())
    low, high = wilson_interval(matches, len(ref))
    return {
        "vectores_ok": int(vectors["coincide"].sum()),
        "vectores_total": len(vectors),
        "pyenigma_casos": len(ref),
        "pyenigma_coincidencias": matches,
        "pyenigma_tasa": matches / len(ref),
        "pyenigma_ic95": [low, high],
        "pyenigma_por_modelo": {
            m: {"casos": len(g), "coincidencias": int(g["coincide"].sum())}
            for m, g in ref.groupby("modelo")
        },
        "pyenigma_letras": int(ref["letras"].sum()),
        "propiedades_claves": len(props),
        "propiedades_letras": int(props["letras"].sum()),
        "puntos_fijos": int(df["puntos_fijos"].sum()),
        "involucion_ok": int(props["involucion"].sum()),
        "lotes_igual_escalar": int(props["coincide"].sum()),
    }


def _shorten(text: str, width: int) -> str:
    return text if len(text) <= width else text[: width - 1] + "…"


def figure(vectors: pd.DataFrame, theme: str = "enigma_print") -> Any:
    """La tabla de vectores como figura: prueba, resultado esperado y si coincide."""
    import matplotlib.pyplot as plt

    from enigma_lab.viz.theme import DARK, PRINT, mpl_style_context

    tokens = PRINT if theme == "enigma_print" else DARK
    ok = int(vectors["coincide"].sum())
    with mpl_style_context(theme):
        size = plt.rcParams["font.size"]
        fig, ax = plt.subplots(figsize=(6.3, 0.75 + 0.27 * len(vectors)))
        ax.axis("off")
        ax.set_xlim(0, 1)
        ax.set_ylim(len(vectors) + 0.6, -0.8)
        header = {"fontsize": size - 1, "color": tokens.text_muted}
        ax.text(0.0, -0.4, "Prueba", **header)
        ax.text(0.47, -0.4, "Esperado (y obtenido)", **header)
        ax.text(0.86, -0.4, "Resultado", **header)
        for i, row in enumerate(vectors.itertuples()):
            ax.text(0.0, i + 0.5, _shorten(row.prueba, 33), fontsize=size - 1.5, va="center")
            ax.text(
                0.47,
                i + 0.5,
                _shorten(row.esperado, 30),
                fontsize=size - 2.5,
                va="center",
                family="JetBrains Mono",
            )
            status, color = (
                ("✓ coincide", tokens.success) if row.coincide else ("✗ no", tokens.error)
            )
            ax.text(0.86, i + 0.5, status, fontsize=size - 1.5, va="center", color=color)
            ax.axhline(i + 1, color=tokens.grid, linewidth=0.5)
        ax.axhline(0, color=tokens.border, linewidth=0.8)
        ax.set_title(f"E1 · Los {len(vectors)} vectores de la sección 6.1: {ok} coinciden")
    return fig


def main(mode: Mode = "completo", seed: int = SEED) -> dict[str, Any]:
    """Corre E1, guarda sus resultados y devuelve sus cifras clave."""
    started = time.perf_counter()
    vectors = vectors_table()
    df = run(PARAMS[mode], seed)
    figures = summary(df, vectors) | {"segundos": round(time.perf_counter() - started, 1)}
    save_table(df, "e1_validacion")
    save_table(vectors, "e1_vectores")
    update_summary("e1", figures, RunInfo("e1", mode, seed))

    import matplotlib.pyplot as plt

    fig = figure(vectors)
    save_figure(fig, "e1_vectores")
    plt.close(fig)
    return figures
