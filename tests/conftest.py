"""Configuración común de las pruebas.

Hypothesis corre en modo determinista (``derandomize``): los mismos ejemplos en cada
ejecución, en el espíritu de la semilla global 2026. Sin límite de tiempo por ejemplo,
porque la primera llamada a una función de Numba incluye su compilación.
"""

from __future__ import annotations

import sys
from pathlib import Path

from hypothesis import settings

ROOT = Path(__file__).resolve().parents[1]

settings.register_profile("enigma", derandomize=True, deadline=None)
settings.load_profile("enigma")

# La app importa sus utilidades (``app/ui``) como lo hace Streamlit al correr
# ``streamlit run app/Inicio.py``: con la carpeta de la app en sys.path.
APP_DIR = str(ROOT / "app")
if APP_DIR not in sys.path:
    sys.path.insert(0, APP_DIR)
