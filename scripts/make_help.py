"""Imprime los objetivos del Makefile con su descripción (los comentarios «##»).

Lo usa ``make help``. Solo usa la biblioteca estándar, para que funcione aunque el
entorno del proyecto todavía no esté instalado.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

TARGET = re.compile(r"^([A-Za-z0-9_-]+):.*?##\s*(.+)$")


def targets(makefile: Path) -> list[tuple[str, str]]:
    """Pares (objetivo, descripción) en el orden del Makefile."""
    lines = makefile.read_text(encoding="utf-8").splitlines()
    return [(m.group(1), m.group(2)) for line in lines if (m := TARGET.match(line))]


def main(path: str = "Makefile") -> None:
    found = targets(Path(path))
    width = max(len(name) for name, _ in found)
    print("Objetivos de make:")
    for name, description in found:
        print(f"  make {name:<{width}}  {description}")


if __name__ == "__main__":
    main(*sys.argv[1:])
