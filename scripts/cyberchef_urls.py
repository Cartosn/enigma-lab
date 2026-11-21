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
import json
import sys
from urllib.parse import quote

import numpy as np

from enigma_lab import paths
from enigma_lab.bombe.cases import BombeCase, random_case
from enigma_lab.bombe.sweep import BombeSettings, run_order
from enigma_lab.bombe.wiring import wiring_from_menu
from enigma_lab.core.machine import EnigmaConfig, encrypt
from enigma_lab.core.random_keys import random_config, random_text
from enigma_lab.core.vectors import vector
from enigma_lab.core.wiring import ALPHABET, REFLECTORS, ROTORS
from enigma_lab.cribs.menu import build_menu, menu_stats

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


# ---------------------------------------------------------------- Bombe (fase 3)
#
# La operación Bombe de CyberChef recibe el cifrado como entrada y, como argumentos, el
# modelo, el 4.º rotor (ignorado con 3 rotores), los rotores de izquierda a derecha, el
# reflector, el crib, su desfase y si usar la máquina de verificación. Supone anillos AAA y
# que solo gira el rotor derecho, como nuestro modo Bletchley. Usa solo la componente del
# menú con más lazos; por eso los casos tienen menús conexos, donde las dos reglas coinciden.


def bombe_recipe(order: tuple[str, ...], crib: str, offset: int, checking: bool = False) -> str:
    """La operación Bombe de CyberChef para un orden de rotores (reflector B)."""
    args = ["3-rotor", rotor_arg("Beta"), *(rotor_arg(r) for r in order), reflector_arg("B"), crib]
    quoted = ",".join(f"'{a}'" for a in args)
    return f"Bombe({quoted},{offset},{'true' if checking else 'false'})"


def bombe_url(
    order: tuple[str, ...], ciphertext: str, crib: str, offset: int, checking: bool
) -> str:
    """URL de CyberChef con la receta Bombe y el cifrado como entrada."""
    data = base64.b64encode(ciphertext.encode("ascii")).decode("ascii").rstrip("=")
    recipe_text = quote(bombe_recipe(order, crib, offset, checking), safe="")
    return f"{BASE}#recipe={recipe_text}&input={data}"


def bombe_cases() -> list[tuple[str, BombeCase]]:
    """Tres casos con menú conexo: el de respaldo (3 lazos) y dos al azar (2 y 1 lazos).

    Los cribs al azar son cortos (12 y 11 letras) para que haya paradas falsas que
    comparar; el tercero lleva el crib en la posición 3, para comprobar también el desfase.
    """
    data = json.loads((paths.DEMO / "respaldo_bombe.json").read_text(encoding="utf-8"))
    backup = BombeCase(
        EnigmaConfig.from_dict(data["key"]), data["plaintext"], data["ciphertext"], 0, 13
    )
    chosen = [("Caso de respaldo (6.1): 3 lazos", backup)]
    rng = np.random.default_rng(2026)
    for loops, position, length in ((2, 0, 12), (1, 3, 11)):
        while True:
            case = random_case(rng, crib_length=length, message_length=60, crib_position=position)
            stats = menu_stats(build_menu(case.crib, case.cipher_segment))
            if stats.components == 1 and stats.loops == loops:
                break
        chosen.append((f"Clave al azar (semilla 2026): {loops} lazo(s), crib en {position}", case))
    return chosen


def expected_stops(case: BombeCase, test_letter: str) -> list[str]:
    """Las paradas de nuestra Bombe en el orden verdadero: «HEC T↔Q», ordenadas por posición."""
    wiring = wiring_from_menu(case.crib, case.cipher_segment, test_letter=test_letter)
    order = case.config.rotors
    run = run_order(wiring, order, BombeSettings(orders=(order,)))
    return [f"{s.position_letters} {s.stecker_label(test_letter)}" for s in run.stops]


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    for label, config, text in cases():
        print(f"## {label}\n{config.describe()}")
        print(f"Esperado: {encrypt(config, text)}")
        print(f"{url(config, text)}\n")
    print("# Bombe\n")
    for label, case in bombe_cases():
        graph = build_menu(case.crib, case.cipher_segment)
        top = max(d for _, d in graph.degree())
        print(f"## {label}\n{case.config.describe()} · crib {case.crib} en {case.crib_position}")
        for letter in sorted(n for n, d in graph.degree() if d == top):
            print(f"Esperado con letra de prueba {letter}: {expected_stops(case, letter)}")
        order = case.config.rotors
        for checking in (False, True):
            print(bombe_url(order, case.ciphertext, case.crib, case.crib_position, checking))
        print()


if __name__ == "__main__":
    main()
