"""La Bombe rápida: el modelo eléctrico con union-find en Numba.

**Qué hace la corriente.** En el modelo de 26 cables × 26 hilos (ver
:mod:`enigma_lab.bombe.wiring`), energizar un hilo enciende todos los hilos conectados
con él: su componente conexa. Union-find calcula todas las componentes a la vez: cada
conexión (arista del menú o par del diagonal board) une dos conjuntos, y al final cada
hilo apunta a la raíz de su componente.

**Union-find con compresión de caminos.** ``parent[v]`` es el «padre» de v; la raíz es
el que es su propio padre. ``_find`` sube hasta la raíz y, de paso, hace que cada nodo
del camino salte a su abuelo (compresión por mitades), así los caminos quedan cortos.
``_union`` cuelga una raíz de la otra (la de índice menor queda como raíz).

**La parada.** Se energiza el hilo x del cable de prueba T y se cuentan los hilos
encendidos en T. Los hilos de T quedan repartidos en bloques (las componentes que los
contienen):

- Si los 26 están en un solo bloque, toda hipótesis T↔u lleva a una contradicción: no
  hay parada.
- Si hay dos bloques o más, la Bombe se detiene. Da igual qué hilo x se energice: el
  bloque de x no tiene los 26 hilos.

**El stecker candidato.** La hipótesis verdadera, en la posición verdadera, solo
enciende hipótesis verdaderas: un hilo por cable. Por eso el candidato es un hilo que
queda **solo en su bloque** (un bloque de tamaño 1). Con 1 hilo encendido es T↔x; con
25, el hilo apagado; con otros conteos, cada hilo aislado es un candidato y el
verificador los prueba todos. Si no hay ninguno aislado, la parada no tiene candidato
y el verificador la descarta (decisión D-033).

**Desfase.** Los rotores avanzan antes de cifrar cada letra. La posición candidata C es
la de las ventanas antes de la primera letra del crib, así que el paso i del menú usa el
rotor derecho en C + i + 1.

**Vueltas del rotor central.** ``turn = 0`` es el modo Bletchley: dentro del tramo solo
gira el rotor derecho. ``turn = k ≥ 1`` es la variante del modo robusto en la que el
central avanza al cifrar la letra k del crib: las aristas con paso i ≥ k usan el
central en C + 1.
"""

from __future__ import annotations

import numpy as np
from numba import njit, prange

N_POSITIONS = 26**3


@njit(cache=True)
def _find(parent: np.ndarray, x: int) -> int:  # pragma: no cover - Numba
    """Raíz de la componente de x; cada nodo del camino salta a su abuelo."""
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x


@njit(cache=True)
def _union(parent: np.ndarray, a: int, b: int) -> None:  # pragma: no cover - Numba
    """Une las componentes de a y b; la raíz de índice menor queda como raíz."""
    ra = _find(parent, a)
    rb = _find(parent, b)
    if ra < rb:
        parent[rb] = ra
    elif rb < ra:
        parent[ra] = rb


@njit(cache=True)
def _wire_up(
    parent: np.ndarray,
    table: np.ndarray,
    left: int,
    middle: int,
    right: int,
    turn: int,
    edge_a: np.ndarray,
    edge_b: np.ndarray,
    edge_offset: np.ndarray,
    diag_a: np.ndarray,
    diag_b: np.ndarray,
) -> None:  # pragma: no cover - Numba
    """Conecta los hilos de la Bombe en la posición candidata (left, middle, right).

    La arista (a, b, i) une el hilo u del cable a con el hilo Sᵢ(u) del cable b, con
    Sᵢ el aleatorizador en (left, middle', right + i + 1); middle' = middle + 1 si la
    variante ``turn`` dice que el central ya avanzó (i ≥ turn ≥ 1).
    """
    for v in range(parent.shape[0]):
        parent[v] = v
    for e in range(edge_a.shape[0]):
        i = edge_offset[e]
        m = middle
        if turn > 0 and i >= turn:
            m = middle + 1
        row = left * 676 + (m % 26) * 26 + (right + i + 1) % 26
        a = edge_a[e] * 26
        b = edge_b[e] * 26
        for u in range(26):
            _union(parent, a + u, b + table[row, u])
    for d in range(diag_a.shape[0]):
        _union(parent, diag_a[d], diag_b[d])


@njit(cache=True)
def _union_counting(
    parent: np.ndarray, t_count: np.ndarray, a: int, b: int
) -> int:  # pragma: no cover - Numba
    """Une como ``_union`` y devuelve cuántos hilos del cable de prueba tiene la componente."""
    ra = _find(parent, a)
    rb = _find(parent, b)
    if ra == rb:
        return t_count[ra]
    if rb < ra:
        ra, rb = rb, ra
    parent[rb] = ra
    t_count[ra] += t_count[rb]
    return t_count[ra]


@njit(cache=True)
def _wire_up_until_full(
    parent: np.ndarray,
    t_count: np.ndarray,
    table: np.ndarray,
    left: int,
    middle: int,
    right: int,
    turn: int,
    edge_a: np.ndarray,
    edge_b: np.ndarray,
    edge_offset: np.ndarray,
    diag_a: np.ndarray,
    diag_b: np.ndarray,
    test_node: int,
) -> bool:  # pragma: no cover - Numba
    """Como ``_wire_up``, pero se detiene si los 26 hilos de T quedan en una componente.

    Desde ese momento ya no puede haber parada: las uniones solo juntan componentes, nunca
    las separan. Cada componente lleva la cuenta de sus hilos del cable de prueba. Es la
    gran mayoría de las posiciones, así que ahorra buena parte del barrido. Devuelve
    verdadero si se llenó el cable de prueba (sin parada).
    """
    for v in range(parent.shape[0]):
        parent[v] = v
        t_count[v] = 0
    for u in range(26):
        t_count[test_node + u] = 1
    for e in range(edge_a.shape[0]):
        i = edge_offset[e]
        m = middle
        if turn > 0 and i >= turn:
            m = middle + 1
        row = left * 676 + (m % 26) * 26 + (right + i + 1) % 26
        a = edge_a[e] * 26
        b = edge_b[e] * 26
        for u in range(26):
            if _union_counting(parent, t_count, a + u, b + table[row, u]) == 26:
                return True
    for d in range(diag_a.shape[0]):
        if _union_counting(parent, t_count, diag_a[d], diag_b[d]) == 26:
            return True
    return False


@njit(cache=True)
def _test_register(
    parent: np.ndarray, test_node: int, test_wire: int, roots: np.ndarray
) -> tuple[int, int]:  # pragma: no cover - Numba
    """(hilos encendidos en T al energizar x, máscara de bits de los hilos aislados de T)."""
    for u in range(26):
        roots[u] = _find(parent, test_node + u)
    target = roots[test_wire]
    lit = 0
    for u in range(26):
        if roots[u] == target:
            lit += 1
    singles = 0
    if lit < 26:
        for u in range(26):
            size = 0
            for w in range(26):
                if roots[w] == roots[u]:
                    size += 1
            if size == 1:
                singles |= 1 << u
    return lit, singles


@njit(cache=True, parallel=True)
def sweep(
    table: np.ndarray,
    edge_a: np.ndarray,
    edge_b: np.ndarray,
    edge_offset: np.ndarray,
    diag_a: np.ndarray,
    diag_b: np.ndarray,
    n_cables: int,
    test_node: int,
    test_wire: int,
    turns: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:  # pragma: no cover - Numba
    """Barre las 17.576 posiciones de un orden, para cada variante de ``turns``.

    Devuelve ``lit`` (17.576, V) uint8, los hilos encendidos en el cable de prueba, y
    ``singles`` (17.576, V) uint32, la máscara de sus hilos aislados. Hay parada donde
    ``lit < 26``. Las posiciones se reparten entre los hilos de la CPU por bloques de
    26 (izquierdo y central fijos).
    """
    n_var = turns.shape[0]
    lit = np.empty((N_POSITIONS, n_var), np.uint8)
    singles = np.zeros((N_POSITIONS, n_var), np.uint32)
    for block in prange(676):
        parent = np.empty(n_cables * 26, np.int32)
        t_count = np.empty(n_cables * 26, np.int32)
        roots = np.empty(26, np.int32)
        left = block // 26
        middle = block % 26
        for right in range(26):
            p = block * 26 + right
            for v in range(n_var):
                full = _wire_up_until_full(
                    parent,
                    t_count,
                    table,
                    left,
                    middle,
                    right,
                    turns[v],
                    edge_a,
                    edge_b,
                    edge_offset,
                    diag_a,
                    diag_b,
                    test_node,
                )
                if full:
                    lit[p, v] = 26
                    continue
                count, mask = _test_register(parent, test_node, test_wire, roots)
                lit[p, v] = count
                singles[p, v] = mask
    return lit, singles


# ---------------------------------------------------------------- máquina de verificación


@njit(cache=True)
def _component_lists(
    parent: np.ndarray, roots: np.ndarray, head: np.ndarray, nxt: np.ndarray
) -> None:  # pragma: no cover - Numba
    """La raíz de cada hilo y, por raíz, la lista enlazada de sus hilos (head → nxt → …)."""
    n = parent.shape[0]
    for v in range(n):
        head[v] = -1
    for v in range(n):
        r = _find(parent, v)
        roots[v] = r
        nxt[v] = head[r]
        head[r] = v


@njit(cache=True)
def _absorb(
    root: int, head: np.ndarray, nxt: np.ndarray, letter_codes: np.ndarray, plug: np.ndarray
) -> bool:  # pragma: no cover - Numba
    """Agrega al plugboard parcial lo que dice cada hilo de la componente ``root``.

    El hilo u del cable a dice P(a) = u y, por simetría, P(u) = a. Devuelve falso si
    alguna letra queda con dos parejas (la hipótesis se contradice).
    """
    good = True
    v = head[root]
    while v >= 0:
        a = letter_codes[v // 26]
        u = v % 26
        if plug[a] == -1:
            plug[a] = u
        elif plug[a] != u:
            good = False
        if plug[u] == -1:
            plug[u] = a
        elif plug[u] != a:
            good = False
        v = nxt[v]
    return good


@njit(cache=True)
def _settle(
    k: int,
    cable_component: np.ndarray,
    letter_codes: np.ndarray,
    roots: np.ndarray,
    head: np.ndarray,
    nxt: np.ndarray,
    plug: np.ndarray,
    trial: np.ndarray,
) -> int:  # pragma: no cover - Numba
    """Revisa otra componente del menú con el plugboard parcial. Devuelve:

    0 si ninguna hipótesis suya es compatible (la parada cae), 1 si quedó decidida (y
    se agregó al plugboard) y 2 si hay varias compatibles (queda pendiente).
    """
    n_cables = cable_component.shape[0]
    first = -1
    for c in range(n_cables):
        if cable_component[c] != k:
            continue
        if first < 0:
            first = c
        partner = plug[letter_codes[c]]
        if partner >= 0:  # una deducción ya fija la hipótesis de esta componente
            return 1 if _absorb(roots[c * 26 + partner], head, nxt, letter_codes, plug) else 0
    found = 0
    chosen = -1
    for u in range(26):
        r = roots[first * 26 + u]
        size = 0
        for w in range(26):
            if roots[first * 26 + w] == r:
                size += 1
        if size != 1:
            continue
        trial[:] = plug
        if _absorb(r, head, nxt, letter_codes, trial):
            found += 1
            chosen = r
            if found > 1:
                return 2
    if found == 0:
        return 0
    _absorb(chosen, head, nxt, letter_codes, plug)
    return 1


@njit(cache=True, parallel=True)
def check_hypotheses(
    table: np.ndarray,
    edge_a: np.ndarray,
    edge_b: np.ndarray,
    edge_offset: np.ndarray,
    diag_a: np.ndarray,
    diag_b: np.ndarray,
    letter_codes: np.ndarray,
    test_node: int,
    cable_component: np.ndarray,
    test_component: int,
    n_components: int,
    positions: np.ndarray,
    turns: np.ndarray,
    row_start: np.ndarray,
    row_wire: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:  # pragma: no cover - Numba
    """La máquina de verificación: qué implica cada hipótesis T↔x de cada parada.

    La parada s tiene las hipótesis ``row_wire[row_start[s]:row_start[s + 1]]``. Para
    cada una se leen los hilos que enciende (los steckers que implica) y se descarta si
    alguna letra queda con dos parejas. Después se revisan las demás componentes del
    menú: cada una necesita al menos una hipótesis compatible (en la posición verdadera
    siempre la hay: la verdadera). Si tiene exactamente una, sus steckers se agregan.

    Devuelve ``plugs`` (H, 26) int8, el plugboard parcial de cada hipótesis (−1 =
    desconocido), y ``ok`` (H,), si sobrevive.
    """
    n_stops = positions.shape[0]
    n_rows = row_wire.shape[0]
    n_nodes = letter_codes.shape[0] * 26
    plugs = np.full((n_rows, 26), -1, np.int8)
    ok = np.zeros(n_rows, np.bool_)
    for s in prange(n_stops):
        parent = np.empty(n_nodes, np.int32)
        roots = np.empty(n_nodes, np.int32)
        head = np.empty(n_nodes, np.int32)
        nxt = np.empty(n_nodes, np.int32)
        plug = np.empty(26, np.int64)
        trial = np.empty(26, np.int64)
        status = np.empty(n_components, np.int64)
        p = positions[s]
        _wire_up(
            parent,
            table,
            p // 676,
            (p // 26) % 26,
            p % 26,
            turns[s],
            edge_a,
            edge_b,
            edge_offset,
            diag_a,
            diag_b,
        )
        _component_lists(parent, roots, head, nxt)
        for row in range(row_start[s], row_start[s + 1]):
            plug[:] = -1
            good = _absorb(roots[test_node + row_wire[row]], head, nxt, letter_codes, plug)
            status[:] = 2
            status[test_component] = 1
            changed = True
            while good and changed:  # una deducción nueva puede decidir otra componente
                changed = False
                for k in range(n_components):
                    if status[k] != 2:
                        continue
                    result = _settle(
                        k, cable_component, letter_codes, roots, head, nxt, plug, trial
                    )
                    if result == 0:
                        good = False
                        break
                    if result == 1:
                        status[k] = 1
                        changed = True
            ok[row] = good
            for a in range(26):
                plugs[row, a] = plug[a]
    return plugs, ok
