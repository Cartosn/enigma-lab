"""Rutas del proyecto, siempre con ``pathlib`` (deben funcionar en Windows y Linux).

La raíz se deduce de la ubicación de este archivo (``src/enigma_lab/paths.py``), lo
que vale para la instalación editable que crea ``uv sync``. Si el paquete se instala
en otro lugar (por ejemplo, una imagen de Docker), la variable de entorno
``ENIGMA_LAB_ROOT`` permite indicar la raíz del repositorio.
"""

from __future__ import annotations

import os
from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent
ROOT = Path(os.environ.get("ENIGMA_LAB_ROOT", PACKAGE_DIR.parents[1])).resolve()

DATA = ROOT / "data"
REFERENCE = DATA / "reference"
DEMO = DATA / "demo"
CORPORA = DATA / "corpora"

RESULTS = ROOT / "results"
FIGURES = RESULTS / "figures"
SLIDE_FIGURES = FIGURES / "slides"
PRESENTATION = RESULTS / "presentacion"

DOCS = ROOT / "docs"
APP = ROOT / "app"
