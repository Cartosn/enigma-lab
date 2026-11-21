"""Página La Bombe: el barrido de los rotores, las paradas y el verificador (spec 8.2, punto 6).

Demo 2 del guion (diapositiva 12): el cifrado de un compañero con el crib WETTERBERICHT.
Plan B: el botón «Caso de respaldo», que carga el caso de 6.1 (modo Bletchley, 3 lazos).
"""

from __future__ import annotations

import json
import time
from typing import Any

import streamlit as st

from enigma_lab import paths
from enigma_lab.bombe import checker
from enigma_lab.bombe.scrambler import (
    ENIGMA_I_ROTORS,
    Order,
    order_label,
    position_letters,
    rotor_orders,
)
from enigma_lab.bombe.sweep import MODES, BombeRun, BombeSettings, OrderRun, run_bombe, true_stop
from enigma_lab.bombe.wiring import wiring_from_menu
from enigma_lab.core.machine import EnigmaConfig, clean, groups_of_five
from enigma_lab.cribs.dragging import alignments
from enigma_lab.cribs.menu import menu_at, menu_stats
from enigma_lab.viz.numfmt import fmt_dec, fmt_int
from ui.bombe_view import drums_payload, render_drums, stops_frame
from ui.cribs_view import menu_payload, render_menu
from ui.layout import is_demo, what_am_i_seeing

K = "bombe_"
ORDER_SETS: dict[str, tuple[str, tuple[str, ...]]] = {
    "todos": ("Rotores I a V (60 órdenes)", ENIGMA_I_ROTORS),
    "i_iii": ("Rotores I, II y III (6 órdenes)", ("I", "II", "III")),
    "uno": ("Un solo orden", ()),
}
ALL_ORDERS = rotor_orders()
RESULTS = ("run", "hypotheses", "verification", "compare", "signature")
state = st.session_state


# ---------------------------------------------------------------- estado


def _clear_results() -> None:
    for name in RESULTS:
        state.pop(K + name, None)


def _load(
    cipher: str,
    crib: str,
    position: int,
    key: dict[str, str] | None = None,
    plaintext: str | None = None,
) -> None:
    state[K + "cipher"] = groups_of_five(clean(cipher))
    state[K + "crib"] = clean(crib)
    state[K + "position"] = position
    state[K + "key"] = key
    state[K + "plaintext"] = plaintext
    state.pop(K + "test", None)
    _clear_results()


def _backup_case() -> None:
    data = json.loads((paths.DEMO / "respaldo_bombe.json").read_text(encoding="utf-8"))
    _load(data["ciphertext"], data["crib"], data["crib_position"], data["key"], data["plaintext"])
    state[K + "mode"] = "bletchley"
    state[K + "orders"] = "todos"
    state[K + "diagonal"] = True


def _from_cribs() -> None:
    data = state["bombe_input"]
    _load(data["cipher"], data["crib"], int(data["position"]))


if K + "cipher" not in state:
    if "bombe_input" in state:
        _from_cribs()
    else:
        _backup_case()


# ---------------------------------------------------------------- página

demo = is_demo()
st.title("La Bombe")
st.caption("Enigma Lab › La Bombe")
what_am_i_seeing(
    "La Bombe no prueba claves: prueba hipótesis. En cada orden de rotores y cada una de "
    "sus 17.576 posiciones supone que la letra de prueba va con una letra x del plugboard.",
    "La corriente propaga esa hipótesis por el menú. Si los 26 hilos del cable de prueba se "
    "encienden, toda hipótesis se contradice; si no, la Bombe se detiene: es una parada.",
    "El diagonal board impone la simetría del plugboard (si A va con B, B va con A) y "
    "elimina muchas paradas falsas.",
    "«Verificar» hace lo que seguía en Bletchley: deduce los steckers, completa el plugboard, "
    "busca los anillos y descifra el mensaje.",
)

buttons = st.columns(2)
buttons[0].button(
    "Caso de respaldo",
    on_click=_backup_case,
    icon=":material/support:",
    width="stretch",
    help="El caso de 6.1: rotores II-III-I, WETTERBERICHT en la posición 0, 3 lazos.",
)
buttons[1].button(
    "Traer de Cribs y menús",
    on_click=_from_cribs,
    icon=":material/hub:",
    width="stretch",
    disabled="bombe_input" not in state,
    help="El cifrado, el crib y la alineación elegidos en la página Cribs y menús.",
)

inputs = st.columns([3, 2])
cipher = clean(inputs[0].text_area("Texto cifrado", key=K + "cipher", height=90))
crib = clean(inputs[1].text_input("Crib", key=K + "crib"))
if not crib or len(crib) > len(cipher) or len(crib) < 2:
    st.warning(
        "Escribe un cifrado y un crib de 2 letras o más, más corto que él.",
        icon=":material/warning:",
    )
    st.stop()
if len(crib) > 26:
    st.warning(
        "Con más de 26 letras el central avanza siempre dentro del tramo; usa un crib más corto."
    )
    st.stop()
valid = [a.position for a in alignments(cipher, crib) if a.valid]
if not valid:
    st.error("Ninguna alineación es posible: el crib no cabe sin conflictos en este cifrado.")
    st.stop()
if state.get(K + "position") not in valid:
    state[K + "position"] = valid[0]
position = inputs[1].selectbox(
    "Posición del crib",
    valid,
    key=K + "position",
    help="Solo las alineaciones sin conflictos (ninguna letra del crib sobre sí misma).",
)

# ---------------------------------------------------------------- el menú

menu = menu_at(cipher, crib, position)
stats = menu_stats(menu)
st.subheader("El menú")
metrics = st.columns(5)
metrics[0].metric("Letras", stats.letters)
metrics[1].metric("Aristas", stats.edges)
metrics[2].metric("Componentes", stats.components)
metrics[3].metric("Lazos", stats.loops, help="Número ciclomático E − V + 1 de la componente usada")
metrics[4].metric(
    "Letra de prueba",
    stats.test_letter,
    f"grado {stats.test_degree}",
    delta_color="off",
    delta_arrow="off",
)
if not demo:
    render_menu(menu_payload(menu))
if stats.loops < 3:
    st.warning(
        f"Este menú tiene {stats.loops} lazo{'s' if stats.loops != 1 else ''}. Con menos de 3 "
        "habrá muchas paradas falsas: cada lazo divide las paradas por unas 26. El verificador "
        "las revisa todas, pero tarda más.",
        icon=":material/warning:",
    )

# ---------------------------------------------------------------- configuración

st.subheader("Configuración")
config_cols = st.columns([2.2, 1.2, 1.4, 1.2])
state.setdefault(K + "orders", "todos")
choice = config_cols[0].radio(
    "Órdenes a probar",
    list(ORDER_SETS),
    format_func=lambda k: ORDER_SETS[k][0],
    key=K + "orders",
)
if choice == "uno":
    default_order: Order = ("II", "III", "I")
    single = config_cols[0].selectbox(
        "Orden",
        ALL_ORDERS,
        index=ALL_ORDERS.index(default_order),
        format_func=order_label,
        key=K + "single",
    )
    orders: tuple[Order, ...] = (single,)
else:
    orders = tuple(rotor_orders(ORDER_SETS[choice][1]))
state.setdefault(K + "diagonal", True)
diagonal = config_cols[1].toggle("Diagonal board", key=K + "diagonal")
state.setdefault(K + "mode", "bletchley")
mode = config_cols[2].radio(
    "Modo",
    list(MODES),
    format_func=lambda k: MODES[k],
    key=K + "mode",
    help="Bletchley: dentro del tramo solo gira el rotor derecho. Robusto: prueba además "
    "una vuelta del central en cada letra del crib (unas L veces más tiempo y paradas).",
)
letters = sorted(set(crib) | set(cipher[position : position + len(crib)]))
state.setdefault(K + "test", stats.test_letter)
if state[K + "test"] not in letters:
    state[K + "test"] = stats.test_letter
test_letter = config_cols[3].selectbox("Letra de prueba", letters, key=K + "test")

wiring = wiring_from_menu(
    crib, cipher[position : position + len(crib)], test_letter=test_letter, diagonal=diagonal
)
settings = BombeSettings(orders=orders, mode=mode)  # type: ignore[arg-type]
signature = (cipher, crib, position, orders, diagonal, mode, test_letter)
if state.get(K + "signature") != signature:
    for name in RESULTS:
        state.pop(K + name, None)
variants = len(settings.turns(len(crib)))
st.caption(
    f"{fmt_int(len(orders))} orden{'es' if len(orders) != 1 else ''} × 17.576 posiciones"
    + (f" × {variants} variantes" if variants > 1 else "")
    + f" = {fmt_int(len(orders) * 17576 * variants)} pruebas."
)

key_data = state.get(K + "key")
known_key = EnigmaConfig.from_dict(key_data) if key_data else None


def _run_sweep() -> None:
    """El barrido con la barra por orden, el contador de paradas y el cronómetro."""
    bar = st.progress(0.0, text="Preparando la Bombe…")
    live = st.empty()
    drums = st.empty()
    with drums.container():
        render_drums(
            drums_payload(
                wiring, "running", "Barriendo", f"{fmt_int(len(orders))} órdenes", demo=demo
            )
        )
    start = time.perf_counter()
    found = 0

    def update(k: int, order_run: OrderRun) -> None:
        nonlocal found
        found += len(order_run)
        elapsed = time.perf_counter() - start
        bar.progress(
            (k + 1) / len(orders),
            text=f"Orden {k + 1} de {len(orders)}: {order_label(order_run.order)}",
        )
        live.markdown(f"**Paradas:** {fmt_int(found)} · **Cronómetro:** {fmt_dec(elapsed, 1)} s")

    run = run_bombe(wiring, settings, progress=update)
    bar.progress(1.0, text="Máquina de verificación: descartando contradicciones…")
    hypotheses = checker.consistent_stops(wiring, run.runs, settings.reflector)
    bar.empty()
    drums.empty()
    state[K + "run"] = run
    state[K + "hypotheses"] = hypotheses
    state[K + "signature"] = signature
    state[K + "elapsed"] = time.perf_counter() - start


if st.button("Correr la Bombe", type="primary", icon=":material/play_arrow:", width="stretch"):
    _run_sweep()

run: BombeRun | None = state.get(K + "run")
if run is None:
    st.stop()

# ---------------------------------------------------------------- resultados

hypotheses: checker.Hypotheses = state[K + "hypotheses"]
st.subheader("Paradas")
cols = st.columns(4)
cols[0].metric("Paradas", fmt_int(run.n_stops))
cols[1].metric(
    "Consistentes", fmt_int(len(hypotheses)), help="Hipótesis que pasan la máquina de verificación"
)
cols[2].metric("Tiempo del barrido", f"{fmt_dec(run.seconds, 1)} s")
cols[3].metric("Por orden", f"{fmt_dec(run.seconds / max(1, len(run.runs)), 2)} s")

expected = true_stop(known_key, position, len(crib)) if known_key else None
verification: checker.Verification | None = state.get(K + "verification")
shown = verification.best.hypothesis.stop if verification and verification.best else None
if shown is None and len(hypotheses):
    shown = hypotheses.get(0).stop
if shown is not None:
    render_drums(
        drums_payload(
            wiring,
            "done",
            "Parada",
            f"orden {order_label(shown.order)}"
            + (f" · vuelta en la letra {shown.turn}" if shown.turn else ""),
            shown,
            demo=demo,
        )
    )

table = stops_frame(run, hypotheses)
if known_key is not None and expected is not None and not table.empty:
    true_order, true_pos = order_label(known_key.rotors), position_letters(expected[0])
    table.insert(
        0,
        "Verdadera",
        [
            "✔" if (o == true_order and p == true_pos) else ""
            for o, p in zip(table["Orden"], table["Posición"], strict=True)
        ],
    )
if run.n_stops == 0:
    st.info(
        "Ninguna parada: con este crib y estos órdenes no hay posición posible.",
        icon=":material/info:",
    )
else:
    st.dataframe(table, hide_index=True, width="stretch", height=260)
    st.caption(
        f"{fmt_int(run.n_stops)} paradas; {fmt_int(len(hypotheses))} hipótesis pasan la máquina de "
        f"verificación. Se muestran hasta {fmt_int(len(table))}, primero las consistentes."
    )

# ---------------------------------------------------------------- verificar

if len(hypotheses) and st.button(
    "Verificar", type="primary", icon=":material/task_alt:", width="stretch"
):
    with st.spinner("Completando el plugboard y buscando los anillos…"):
        state[K + "verification"] = checker.verify(run, cipher, position, hypotheses=hypotheses)
    st.rerun()

if verification is not None:
    best = verification.best
    if best is None:
        st.error("Ninguna parada da un descifrado: revisa el crib o su posición.")
    else:
        size = "2.6rem" if demo else "1.8rem"
        tone = "el-cipher" if best.plausible else "el-sub"
        st.markdown(
            f'<div class="{tone}" style="font-size: {size}; line-height: 1.35; '
            f'word-break: break-all;">{groups_of_five(best.plaintext)}</div>',
            unsafe_allow_html=True,
        )
        if best.plausible:
            st.success(
                f"Descifrado plausible (log₁₀ P por letra {fmt_dec(best.score, 2)}; alemán ≈ "
                f"{fmt_dec(-0.67, 2)}, azar ≈ {fmt_dec(-2.66, 2)}).",
                icon=":material/check_circle:",
            )
        else:
            st.warning(
                "Ninguna parada da un texto que parezca alemán: el crib puede estar mal, o el "
                "central se movió dentro del tramo (prueba el modo robusto).",
                icon=":material/warning:",
            )
        st.caption(f"Leyendo la X como espacio: {best.plaintext.replace('X', ' ').strip()}")
        st.markdown(f"**Clave equivalente:** `{best.config.describe()}`")
        if known_key is not None:
            same = best.plaintext == state.get(K + "plaintext")
            st.caption(
                f"Clave del caso: {known_key.describe()}."
                + (
                    " El descifrado coincide letra por letra con el mensaje original."
                    if same
                    else ""
                )
            )
        with st.expander("Hipótesis examinadas", icon=":material/list:"):
            rows: list[dict[str, Any]] = [
                {
                    "Orden": order_label(s.hypothesis.stop.order),
                    "Posición": s.hypothesis.stop.position_letters,
                    "Stecker": f"{test_letter}↔{chr(65 + s.hypothesis.wire)}",
                    "log₁₀ P por letra": round(s.score, 3),
                    "Descifrado": s.plaintext[:40],
                }
                for s in verification.solutions[:10]
            ]
            st.dataframe(rows, hide_index=True, width="stretch")
            st.caption(
                f"{fmt_int(verification.hypotheses)} hipótesis consistentes; se descifraron las "
                f"{fmt_int(len(verification.solutions))} con mejor puntaje rápido, en "
                f"{fmt_dec(verification.seconds, 1)} s."
            )

# ---------------------------------------------------------------- con y sin diagonal board

st.subheader("Con y sin diagonal board")
compare: dict[str, int] | None = state.get(K + "compare")
if compare is None:
    if st.button("Comparar para este menú", icon=":material/compare_arrows:"):
        other = wiring_from_menu(
            crib,
            cipher[position : position + len(crib)],
            test_letter=test_letter,
            diagonal=not diagonal,
        )
        with st.spinner("Barriendo los mismos órdenes con el otro ajuste…"):
            other_run = run_bombe(other, settings)
        counts = {"con": run.n_stops, "sin": other_run.n_stops}
        if not diagonal:
            counts = {"con": other_run.n_stops, "sin": run.n_stops}
        state[K + "compare"] = counts
        st.rerun()
else:
    pair = st.columns(2)
    pair[0].metric("Paradas con diagonal board", fmt_int(compare["con"]))
    pair[1].metric("Paradas sin diagonal board", fmt_int(compare["sin"]))
    if compare["con"]:
        st.caption(
            f"Sin el diagonal board hay {fmt_dec(compare['sin'] / compare['con'], 1)} veces más "
            "paradas en estos órdenes."
        )
