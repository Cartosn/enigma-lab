"""La conexión de cada página con el curso: la línea «En clase» debajo del título.

Son las etiquetas «EN CLASE» de las diapositivas, tal cual. Una página que corresponde a
dos diapositivas lleva las dos; una página sin diapositiva, una frase de la tabla
«Conexiones con el curso» de la guía de estudio. En Experimentos, la línea va en cada
pestaña, con la diapositiva de su experimento.
"""

from __future__ import annotations

SLIDES: dict[int, str] = {
    4: "Semana 1 · un Vigenère que cambia de alfabeto en cada letra",
    5: "Semanas 4 y 6 · contador como en CTR; recorrido en ρ",
    6: "Semanas 3 y 4 · indistinguibilidad y conteo de permutaciones",
    7: "Semana 3 · ataque paralelo: con 1.000 máquinas, 5 años",
    9: "Semana 13 · clave de sesión cifrada, como el PMS en TLS",
    10: "Semana 5 · A5/1 también se ataca con texto conocido",
    11: "Semana 2 · probabilidad, como en la prueba de esfuerzo",
    12: "Semanas 3 y 5 · fuerza bruta sobre 20 bits, como en A5/1",
    13: "Semanas 1, 5 y 8 · two-time pad, WEP y nonce reuse",
    15: "Semana 1 · análisis de frecuencias e índice de coincidencia",
    16: "Semana 3 · la seguridad la fija el mejor ataque",
    17: "Semana 1 · el índice de coincidencia de Vigenère",
}
"""Las etiquetas «EN CLASE» de las diapositivas, por número de diapositiva."""

PAGES: dict[str, tuple[str, ...]] = {
    "inicio": (
        "Semana 3 · 67 bits nominales y 20 efectivos: la seguridad la fija el mejor ataque",
    ),
    "maquina": (SLIDES[4], SLIDES[5]),
    "espacio": (SLIDES[7],),
    "estadistica": (SLIDES[6],),
    "cribs": (SLIDES[10], SLIDES[11]),
    "bombe": (SLIDES[12],),
    "banburismus": (SLIDES[13],),
    "rejewski": (SLIDES[9],),
    "ataque": (SLIDES[16],),
}
"""La línea de cada página, por el nombre de su archivo en ``app/paginas/``."""

EXPERIMENTS: dict[str, str] = {
    "e1": "Semana 1 · Kerckhoffs: los ataques suponen conocido el cableado",
    "e2": SLIDES[7],
    "e3": SLIDES[6],
    "e4": SLIDES[15],
    "e5": SLIDES[16],
    "e6": SLIDES[17],
    "e7": SLIDES[9],
    "e8": SLIDES[16],
}
"""La línea de cada pestaña de Experimentos."""
