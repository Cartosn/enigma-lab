"""Catálogo de los módulos de Enigma Lab.

Lo usan la navegación (``Inicio.py``) y las tarjetas de la página Inicio, para que
las dos digan lo mismo. ``page`` vale ``None`` si el módulo no tiene página.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Module:
    """Un módulo de la app: cómo se llama, qué hace, en qué fase llega y su página."""

    key: str
    title: str
    summary: str
    phase: str
    icon: str
    page: str | None = None  # ruta relativa a app/, p. ej. "paginas/maquina.py"


MODULES: tuple[Module, ...] = (
    Module(
        "maquina",
        "Máquina",
        "Configura una Enigma I, M3 o M4, cifra y sigue el camino de cada letra.",
        "Fase 1",
        ":material/keyboard:",
        page="paginas/maquina.py",
    ),
    Module(
        "espacio",
        "Espacio de claves",
        "Cuántos bits aporta cada componente y por qué domina el plugboard.",
        "Fase 2",
        ":material/key:",
        page="paginas/espacio.py",
    ),
    Module(
        "estadistica",
        "Estadística del cifrado",
        "Qué estadística del idioma deja pasar el cifrado y cuál no.",
        "Fase 2",
        ":material/bar_chart:",
        page="paginas/estadistica.py",
    ),
    Module(
        "cribs",
        "Cribs y menús",
        "El crib deslizándose sobre el cifrado y el menú que alimenta a la Bombe.",
        "Fase 2",
        ":material/hub:",
        page="paginas/cribs.py",
    ),
    Module(
        "bombe",
        "La Bombe",
        "Barrido de los rotores, paradas y verificación de la clave.",
        "Fase 3",
        ":material/settings:",
        page="paginas/bombe.py",
    ),
    Module(
        "experimentos",
        "Experimentos",
        "E1 a E8: pregunta, método, resultados con intervalos y la referencia publicada.",
        "Fases 2 a 5",
        ":material/science:",
        page="paginas/experimentos.py",
    ),
    Module(
        "banburismus",
        "Banburismus",
        "Decibanes y la prueba secuencial de Wald con dos mensajes en profundidad.",
        "Fase 4",
        ":material/stacked_line_chart:",
        page="paginas/banburismus.py",
    ),
    Module(
        "rejewski",
        "Rejewski",
        "Ciclos de AD, BE y CF y el catálogo de características.",
        "Fase 5",
        ":material/cycle:",
        page="paginas/rejewski.py",
    ),
    Module(
        "ataque",
        "Ataque moderno",
        "Índice de coincidencia y hill climbing solo con texto cifrado.",
        "Fase 5",
        ":material/bolt:",
        page="paginas/ataque.py",
    ),
)
