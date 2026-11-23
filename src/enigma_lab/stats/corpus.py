"""Corpus de dominio público y normalización al alfabeto de Enigma.

**Fuentes** (Project Gutenberg, descargadas por ``scripts/fetch_corpora.py``):
- alemán: *Effi Briest* (Fontane, 1895) y *Die Verwandlung* (Kafka, 1915);
- español: *El ingenioso hidalgo don Quijote de la Mancha* (Cervantes, 1605).

En el repositorio va una muestra de unos 200 KB por idioma (``data/corpora/muestras``)
para que la app funcione sin internet. El corpus completo (``data/corpora/completo``) se
descarga aparte y no se versiona.

**Normalización.** Enigma solo tiene A–Z.
- Alemán: Ä → AE, Ö → OE, Ü → UE y ß → SS, como escribían los operadores.
- Español: se quitan las tildes y Ñ → N.
- Las demás marcas diacríticas se quitan.
- Hay dos modos:
  - ``"letras"``: solo letras;
  - ``"x"``: cada tramo de espacios y signos se vuelve una X, al estilo militar
    (WETTERBERICHTXFUERXDIEXNACHT).
"""

from __future__ import annotations

import re
import unicodedata
from functools import cache
from pathlib import Path
from typing import Literal

import numpy as np

from enigma_lab import paths

Language = Literal["aleman", "espanol"]
Mode = Literal["letras", "x"]
Source = Literal["muestra", "completo"]

ALL_LANGUAGES: tuple[Language, ...] = ("aleman", "espanol")
LANGUAGES: dict[str, str] = {"aleman": "Alemán", "espanol": "Español"}
MODES: dict[str, str] = {"letras": "Solo letras", "x": "X como separador"}

SAMPLES_DIR = paths.CORPORA / "muestras"
FULL_DIR = paths.CORPORA / "completo"

_GERMAN = {"Ä": "AE", "Ö": "OE", "Ü": "UE", "ẞ": "SS"}


def normalize(text: str, language: Language, mode: Mode = "letras") -> str:
    """Texto a letras A–Z según el idioma y el modo (ver el docstring del módulo).

    >>> normalize("Grüße aus Köln", "aleman", "x")
    'GRUESSEXAUSXKOELN'
    >>> normalize("Señor, ¿dónde está?", "espanol")
    'SENORDONDEESTA'
    """
    upper = text.upper()  # en Python, "ß".upper() ya es "SS"
    if language == "aleman":
        for letter, replacement in _GERMAN.items():
            upper = upper.replace(letter, replacement)
    elif language == "espanol":
        upper = upper.replace("Ñ", "N")
    decomposed = unicodedata.normalize("NFD", upper)
    plain = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
    if mode == "letras":
        return re.sub(r"[^A-Z]", "", plain)
    # Las palabras se unen con una X; las X propias de las palabras se quedan, también al
    # principio y al final del texto («Fax» sigue siendo FAX).
    return "X".join(re.findall(r"[A-Z]+", plain))


def corpus_path(language: Language, source: Source = "muestra") -> Path:
    """Ruta del texto de un idioma: la muestra versionada o el corpus completo."""
    folder = SAMPLES_DIR if source == "muestra" else FULL_DIR
    return folder / f"{language}.txt"


def has_full_corpus() -> bool:
    """¿Se descargó el corpus completo (``make corpus``)?"""
    return all(corpus_path(lang, "completo").is_file() for lang in ALL_LANGUAGES)


@cache
def load_text(language: Language, source: Source = "muestra") -> str:
    """El texto original (con tildes y signos) de un idioma."""
    path = corpus_path(language, source)
    if not path.is_file():
        hint = "corre  make corpus" if source == "completo" else "falta la muestra del repositorio"
        raise FileNotFoundError(f"no está {path} ({hint})")
    return path.read_text(encoding="utf-8")


@cache
def load_letters(language: Language, source: Source = "muestra", mode: Mode = "letras") -> str:
    """El corpus normalizado a A–Z (en caché: se calcula una vez por proceso)."""
    return normalize(load_text(language, source), language, mode)


@cache
def load_codes(language: Language, source: Source = "muestra", mode: Mode = "letras") -> np.ndarray:
    """El corpus normalizado como arreglo de enteros 0–25."""
    letters = load_letters(language, source, mode)
    return np.frombuffer(letters.encode("ascii"), dtype=np.uint8) - ord("A")


def random_excerpts(
    rng: np.random.Generator,
    language: Language,
    n: int,
    length: int,
    source: Source = "muestra",
    mode: Mode = "letras",
) -> np.ndarray:
    """N fragmentos de ``length`` letras tomados de posiciones al azar del corpus: (N, L)."""
    codes = load_codes(language, source, mode)
    if length > len(codes):
        raise ValueError(f"el corpus tiene {len(codes)} letras; no alcanza para {length}")
    starts = rng.integers(0, len(codes) - length + 1, size=n)
    return codes[starts[:, None] + np.arange(length)]
