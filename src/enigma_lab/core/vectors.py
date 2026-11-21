"""Vectores de prueba de la sección 6.1 (``data/reference/test_vectors.json``).

Un solo lugar para comprobarlos. Los usan las pruebas, el experimento E1 (tabla de la
diapositiva 14) y la página Inicio (estado de la validación en vivo).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import cache
from typing import Any

from enigma_lab import paths
from enigma_lab.core.machine import Enigma, EnigmaConfig, encrypt
from enigma_lab.core.stepping import cycle_structure, notch_sets
from enigma_lab.core.wiring import ROTORS
from enigma_lab.viz.numfmt import fmt_int

VECTORS_FILE = paths.REFERENCE / "test_vectors.json"


@dataclass(frozen=True)
class VectorResult:
    """Un vector comprobado: lo esperado, lo obtenido y si coinciden."""

    id: str
    label: str
    expected: str
    obtained: str

    @property
    def ok(self) -> bool:
        return self.expected == self.obtained


@cache
def load_vectors() -> tuple[dict[str, Any], ...]:
    """Los vectores del archivo JSON, en orden."""
    data = json.loads(VECTORS_FILE.read_text(encoding="utf-8"))
    return tuple(data["vectors"])


def vector(vector_id: str) -> dict[str, Any]:
    """Un vector por su identificador (p. ej. "portada")."""
    for v in load_vectors():
        if v["id"] == vector_id:
            return v
    raise KeyError(vector_id)


def check(v: dict[str, Any]) -> VectorResult:
    """Comprueba un vector con el simulador."""
    kind = v["kind"]
    if kind == "encrypt":
        expected, obtained = v["output"], encrypt(EnigmaConfig.from_dict(v["key"]), v["input"])
    elif kind == "stepping":
        machine = Enigma(EnigmaConfig.from_dict(v["key"]))
        windows = [machine.window]
        for _ in range(v["presses"]):
            machine.step()
            windows.append(machine.window)
        expected, obtained = " → ".join(v["windows"]), " → ".join(windows)
    elif kind == "message_key":
        config = EnigmaConfig.from_dict(v["key"])
        message_key = encrypt(config, v["indicator"])
        plaintext = encrypt(config.with_positions(message_key), v["input"])
        expected = f"{v['message_key']} → {v['output']}"
        obtained = f"{message_key} → {plaintext}"
    elif kind == "period":
        names = v["rotors"].split()
        lengths, off_cycle = cycle_structure(notch_sets([ROTORS[n].notches for n in names]))
        expected = f"periodo {fmt_int(v['period'])}; {fmt_int(v['off_cycle'])} fuera del ciclo"
        obtained = f"periodo {' + '.join(fmt_int(n) for n in lengths)}; "
        obtained += f"{fmt_int(off_cycle)} fuera del ciclo"
    elif kind == "trace":
        trace = Enigma(EnigmaConfig.from_dict(v["key"])).trace(v["input"])[0]
        expected, obtained = " → ".join(v["letters"]), trace.path()
    else:
        raise ValueError(f"tipo de vector desconocido: {kind!r}")
    return VectorResult(v["id"], v["label"], expected, obtained)


def check_all() -> list[VectorResult]:
    """Comprueba todos los vectores del archivo."""
    return [check(v) for v in load_vectors()]
