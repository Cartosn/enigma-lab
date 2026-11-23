"""Exploración inicial: el riesgo de la demo 2, medido con el piloto.

No es código del proyecto ni un resultado para las diapositivas: la fase 3 repite la
medición con ``enigma_lab`` (E5 y ``make bench-demo``). Se conserva para que las cifras
citadas en ``docs/PROGRESS.md`` sean reproducibles.

Para claves aleatorias de Enigma I (rotores I–V, 10 cables) y un mensaje que empieza
por WETTERBERICHT, mide:

- con qué frecuencia el rotor central (o el izquierdo) se mueve dentro de las 13 letras;
- la estructura del menú en la alineación 0: letras y lazos (E − V + 1) de la
  componente con más lazos.

Uso:  uv run python scripts/exploracion_demo2.py [N]   (por defecto N = 5000, semilla 2026)
"""

from __future__ import annotations

import importlib.util
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path
from types import ModuleType

CRIB = "WETTERBERICHT"
PILOT = Path(__file__).resolve().parent / "piloto_enigma.py"


def load_pilot() -> ModuleType:
    """Carga el piloto como módulo, sin ejecutar su ``main``."""
    spec = importlib.util.spec_from_file_location("piloto_enigma", PILOT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def best_component(crib: str, cipher: str) -> tuple[int, int]:
    """(lazos, letras) de la componente del menú con más lazos."""
    graph: defaultdict[str, list[str]] = defaultdict(list)
    for plain, enc in zip(crib, cipher, strict=True):
        graph[plain].append(enc)
        graph[enc].append(plain)
    seen: set[str] = set()
    best = (-1, 0)
    for start in graph:
        if start in seen:
            continue
        stack, component = [start], set()
        while stack:
            node = stack.pop()
            if node not in component:
                component.add(node)
                stack.extend(graph[node])
        seen |= component
        edges = sum(len(graph[node]) for node in component) // 2
        best = max(best, (edges - len(component) + 1, len(component)))
    return best


def main(n: int = 5000) -> None:
    pilot = load_pilot()
    rng = random.Random(2026)
    moved, loops, letters = 0, Counter[int](), []
    for _ in range(n):
        key = pilot.random_key(rng, 10)
        machine = pilot.Enigma(**key)
        windows = []
        for _letter in CRIB:
            machine.step()
            windows.append(tuple(machine.pos[:2]))
        moved += windows[0] != windows[-1]
        cipher = pilot.Enigma(**key).encrypt(CRIB)
        n_loops, _ = best_component(CRIB, cipher)
        loops[min(n_loops, 4)] += 1
        letters.append(len(set(CRIB) | set(cipher)))
    print(f"N = {n} claves, semilla 2026")
    print(
        f"El central o el izquierdo se mueve dentro del tramo: {moved / n:.3f}"
        f"  (12/26 = {12 / 26:.3f})"
    )
    print(
        f"Letras del menú: media {sum(letters) / n:.2f}, mín. {min(letters)}, máx. {max(letters)}"
    )
    for k in sorted(loops):
        label = "4 o más" if k == 4 else str(k)
        print(f"Lazos en la mejor componente = {label}: {loops[k] / n:.3f}")


if __name__ == "__main__":
    main(*(int(a) for a in sys.argv[1:]))
