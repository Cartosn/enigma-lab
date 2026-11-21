"""Enlaces de CyberChef para validar el simulador a mano (spec 6.2).

CyberChef (GCHQ) es una implementación independiente de Enigma que corre en el
navegador. Este script arma, para varios casos, la URL de CyberChef con la receta
«Enigma» y el texto de entrada ya puestos: al abrirla, CyberChef muestra su salida, que
se compara con la del simulador. Los resultados se anotan en ``docs/VALIDACION.md``.

Formato de CyberChef:
- Rotores: cableado + «<» + letras de arrastre. CyberChef nombra la letra a la que llega
  el rotor al arrastrar (R para el rotor I), una más que nuestra muesca (Q).
- Reflector: parejas de letras («AY BR CU…»).

Uso:  uv run python scripts/cyberchef_urls.py
"""

from __future__ import annotations

import base64
import sys
from urllib.parse import quote

import numpy as np

from enigma_lab.core.machine import EnigmaConfig, encrypt
from enigma_lab.core.random_keys import random_config, random_text
from enigma_lab.core.vectors import vector
from enigma_lab.core.wiring import ALPHABET, REFLECTORS, ROTORS

BASE = "https://gchq.github.io/CyberChef/"


def rotor_arg(name: str) -> str:
    """Rotor en el formato de CyberChef: «EKMFLGDQVZNTOWYHXUSPAIBRCJ<R»."""
    spec = ROTORS[name]
    steps = "".join(ALPHABET[(ALPHABET.index(n) + 1) % 26] for n in spec.notches)
    return spec.wiring + (f"<{steps}" if steps else "")


def reflector_arg(name: str) -> str:
    """Reflector como parejas: «AY BR CU DH…»."""
    wiring = REFLECTORS[name]
    pairs = sorted({"".join(sorted((ALPHABET[i], c))) for i, c in enumerate(wiring)})
    return " ".join(pairs)


def recipe(config: EnigmaConfig) -> str:
    """La operación Enigma de CyberChef con los argumentos de la clave."""
    rotors = list(config.rotors)
    rings, positions = config.ring_letters, config.position_letters
    if len(rotors) == 4:
        model, fourth = "4-rotor", (rotor_arg(rotors[0]), rings[0], positions[0])
        rotors, rings, positions = rotors[1:], rings[1:], positions[1:]
    else:
        model, fourth = "3-rotor", (rotor_arg("Beta"), "A", "A")
    args = [model, *fourth]
    for name, ring, position in zip(rotors, rings, positions, strict=True):
        args += [rotor_arg(name), ring, position]
    args += [reflector_arg(config.reflector), config.plugboard_string]
    quoted = ",".join(f"'{a}'" for a in args)
    return f"Enigma({quoted},false)"


def url(config: EnigmaConfig, text: str) -> str:
    """URL de CyberChef con la receta y la entrada (en base64, como la guarda CyberChef)."""
    data = base64.b64encode(text.encode("ascii")).decode("ascii").rstrip("=")
    return f"{BASE}#recipe={quote(recipe(config), safe='')}&input={data}"


def cases() -> list[tuple[str, EnigmaConfig, str]]:
    """Los casos: cuatro vectores de 6.1, el mensaje del U-264 y una clave M3 al azar."""
    chosen = []
    for vid in ("bdzgo", "ewtyx", "portada", "m4_u264"):
        v = vector(vid)
        chosen.append((v["label"], EnigmaConfig.from_dict(v["key"]), v["input"]))
    v = vector("py_enigma")
    chosen.append(
        (v["label"], EnigmaConfig.from_dict(v["key"]).with_positions(v["message_key"]), v["input"])
    )
    rng = np.random.default_rng(2026)
    config = random_config(rng, model="M3", cables=10, reflectors=("C",))
    chosen.append(("Clave M3 al azar (semilla 2026), 120 letras", config, random_text(rng, 120)))
    return chosen


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    for label, config, text in cases():
        print(f"## {label}\n{config.describe()}")
        print(f"Esperado: {encrypt(config, text)}")
        print(f"{url(config, text)}\n")


if __name__ == "__main__":
    main()
