"""El menú: el crib convertido en un grafo.

Con el crib en una alineación, cada columna (letra plana p, letra cifrada c, paso i)
dice que en el paso i la máquina, sin contar el plugboard, lleva S(p) a S(c), donde S es
el plugboard. Las dos letras pasan por la misma posición del aleatorizador. Eso se
dibuja como una arista p — c etiquetada con i.

- **Grafo:** no dirigido y con aristas múltiples (``networkx.MultiGraph``); la misma
  pareja puede salir en dos pasos.
- **Lazos:** número ciclomático E − V + 1 de la componente usada. Un lazo es una cadena
  de hipótesis que debe cerrar: con la hipótesis falsa casi nunca cierra, así que cada
  lazo divide las paradas falsas de la Bombe por unas 26.
- **Letra de prueba:** la de mayor grado en la componente con más lazos. Es donde la
  Bombe conecta su registro de prueba.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import networkx as nx

from enigma_lab.core.machine import clean


@dataclass(frozen=True)
class MenuEdge:
    """Una arista del menú: letras a (crib) y b (cifrado) en el paso ``offset`` del crib."""

    a: str
    b: str
    offset: int
    in_loop: bool = False


@dataclass(frozen=True)
class MenuStats:
    """Las métricas del menú que usa la Bombe."""

    letters: int
    edges: int
    components: int
    loops: int  # número ciclomático de la componente usada
    total_loops: int  # E − V + C de todo el menú
    test_letter: str
    test_degree: int
    used_component: frozenset[str]


def build_menu(crib: str, cipher_segment: str) -> nx.MultiGraph:
    """El menú de un crib alineado: aristas crib[i] — cifrado[i] con ``offset=i``."""
    word, cipher = clean(crib), clean(cipher_segment)
    if len(word) != len(cipher):
        raise ValueError("el crib y el tramo de cifrado deben tener la misma longitud")
    graph = nx.MultiGraph()
    for i, (plain, enc) in enumerate(zip(word, cipher, strict=True)):
        graph.add_edge(plain, enc, offset=i)
    return graph


def menu_at(ciphertext: str, crib: str, position: int) -> nx.MultiGraph:
    """El menú con el crib en la posición ``position`` del cifrado."""
    cipher = clean(ciphertext)
    return build_menu(crib, cipher[position : position + len(clean(crib))])


def _component_loops(graph: nx.MultiGraph, nodes: set[str]) -> int:
    sub = graph.subgraph(nodes)
    return int(sub.number_of_edges() - sub.number_of_nodes() + 1)


def menu_stats(graph: nx.MultiGraph) -> MenuStats:
    """Letras, aristas, componentes, lazos y letra de prueba.

    La componente usada es la de más lazos (si empatan, la de más letras). La letra de
    prueba es la de mayor grado en ella (si empatan, la primera en orden alfabético).
    """
    components = [set(c) for c in nx.connected_components(graph)]
    used = max(components, key=lambda c: (_component_loops(graph, c), len(c)))
    test = min(used, key=lambda n: (-graph.degree(n), n))
    return MenuStats(
        letters=graph.number_of_nodes(),
        edges=graph.number_of_edges(),
        components=len(components),
        loops=_component_loops(graph, used),
        total_loops=graph.number_of_edges() - graph.number_of_nodes() + len(components),
        test_letter=test,
        test_degree=int(graph.degree(test)),
        used_component=frozenset(used),
    )


def menu_edges(graph: nx.MultiGraph) -> list[MenuEdge]:
    """Las aristas del menú, marcando las que forman parte de algún lazo.

    Una arista está en un lazo si no es un puente: al quitarla, sus dos letras siguen
    conectadas. Dos aristas paralelas (la misma pareja en dos pasos) forman un lazo.
    """
    simple = nx.Graph(graph)
    bridges = {frozenset(e) for e in nx.bridges(simple)}
    edges = []
    for a, b, data in graph.edges(data=True):
        parallel = graph.number_of_edges(a, b) > 1
        is_bridge = frozenset((a, b)) in bridges and not parallel
        edges.append(MenuEdge(a, b, int(data["offset"]), in_loop=not is_bridge and a != b))
    return sorted(edges, key=lambda e: e.offset)


def _unit_box(raw: dict[Any, Any]) -> dict[str, tuple[float, float]]:
    """Lleva unas posiciones al cuadrado [0, 1] × [0, 1]; un eje sin extensión queda en 0,5."""
    xs = [float(p[0]) for p in raw.values()]
    ys = [float(p[1]) for p in raw.values()]
    span_x, span_y = max(xs) - min(xs), max(ys) - min(ys)
    return {
        str(node): (
            (float(x) - min(xs)) / span_x if span_x else 0.5,
            (float(y) - min(ys)) / span_y if span_y else 0.5,
        )
        for node, (x, y) in raw.items()
    }


def layout(graph: nx.MultiGraph) -> dict[str, tuple[float, float]]:
    """Posiciones de las letras para dibujar el menú, en [0, 1] y deterministas.

    Cada componente conexa se dibuja aparte con Kamada-Kawai, y las componentes van una
    al lado de la otra, de la más grande a la más pequeña, con un ancho proporcional a
    sus letras. Con una sola componente es Kamada-Kawai sobre todo el menú.
    """
    simple = nx.Graph(graph)
    if simple.number_of_nodes() == 1:
        return {str(next(iter(simple.nodes))): (0.5, 0.5)}
    components = sorted(
        (sorted(c) for c in nx.connected_components(simple)), key=lambda c: (-len(c), c)
    )
    if len(components) == 1:
        return _unit_box(nx.kamada_kawai_layout(simple))
    gap = 0.6  # espacio entre componentes, en «letras»
    total = sum(len(c) for c in components) + gap * (len(components) - 1)
    positions: dict[str, tuple[float, float]] = {}
    start = 0.0
    for nodes in components:
        sub = simple.subgraph(nodes)
        box = (
            _unit_box(nx.kamada_kawai_layout(sub))
            if len(nodes) > 2
            else _unit_box({n: (k, 0.0) for k, n in enumerate(nodes)})
        )
        width = len(nodes) / total
        margin = 0.12 * width if len(nodes) > 1 else 0.0
        for node, (x, y) in box.items():
            positions[node] = (start + margin + x * (width - 2 * margin), y)
        start += width + gap / total
    return positions
