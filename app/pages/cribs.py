"""Página Cribs y menús: el arrastre del crib y el menú de la Bombe (spec 8.2, punto 5)."""

from __future__ import annotations

import json

import numpy as np
import streamlit as st

from enigma_lab import paths
from enigma_lab.core.batch import encrypt_batch, random_key_batch, to_texts
from enigma_lab.core.machine import clean, groups_of_five
from enigma_lab.cribs.dragging import alignments, survival_probability
from enigma_lab.cribs.menu import menu_at, menu_stats
from enigma_lab.stats.corpus import random_excerpts
from enigma_lab.viz.numfmt import fmt_int, fmt_pct
from ui.cribs_view import drag_payload, menu_payload, render_drag, render_menu
from ui.layout import is_demo, what_am_i_seeing

K = "crib_"
SLIDE_10 = ("BBGCCKITCTTEZZZLCZ", "WETTERBERICHT")


def _load(cipher: str, crib: str, truth: int | None = None) -> None:
    st.session_state[K + "cipher"] = groups_of_five(clean(cipher))
    st.session_state[K + "crib"] = clean(crib)
    st.session_state[K + "truth"] = truth
    st.session_state.pop(K + "position", None)


def _slide_example() -> None:
    _load(*SLIDE_10, truth=0)


def _backup_case() -> None:
    data = json.loads((paths.DEMO / "respaldo_bombe.json").read_text(encoding="utf-8"))
    _load(data["ciphertext"], data["crib"], truth=data["crib_position"])


def _generate() -> None:
    """Un mensaje alemán real de 80 letras con clave aleatoria; el crib son 13 de sus letras."""
    rng = np.random.default_rng()
    plain = random_excerpts(rng, "aleman", 1, 80, mode="x")
    keys, _ = random_key_batch(rng, 1, cables=10)
    cipher = to_texts(encrypt_batch(keys, plain))[0]
    start = int(rng.integers(0, 80 - 13 + 1))
    _load(cipher, to_texts(plain)[0][start : start + 13], truth=start)


if K + "cipher" not in st.session_state:
    _slide_example()

demo = is_demo()
st.title("Cribs y menús")
st.caption("Enigma Lab › Cribs y menús")
what_am_i_seeing(
    "El crib (una palabra que se adivina) se desliza sobre el cifrado. Si una letra cae "
    "sobre la misma letra cifrada, esa alineación es imposible: Enigma nunca cifra una "
    "letra en sí misma.",
    "El filtro descarta algunas posiciones, no todas: con L letras, una alineación falsa "
    "sobrevive con probabilidad (25/26)^L.",
    "Con una alineación elegida, el crib se vuelve un grafo: el menú. Los lazos (en ámbar) "
    "son lo que hace eficaz a la Bombe.",
)

buttons = st.columns(3)
buttons[0].button(
    "Ejemplo de la diapositiva 10",
    on_click=_slide_example,
    icon=":material/slideshow:",
    width="stretch",
)
buttons[1].button(
    "Caso de respaldo", on_click=_backup_case, icon=":material/support:", width="stretch"
)
buttons[2].button(
    "Generar un caso",
    on_click=_generate,
    icon=":material/casino:",
    width="stretch",
    help="Mensaje alemán real de 80 letras con clave al azar.",
)

inputs = st.columns([3, 2])
cipher_raw = inputs[0].text_area("Texto cifrado", key=K + "cipher", height=80)
crib_raw = inputs[1].text_input("Crib", key=K + "crib")
cipher, crib = clean(cipher_raw), clean(crib_raw)
if not crib or len(crib) > len(cipher):
    st.warning("Escribe un cifrado y un crib más corto que él.", icon=":material/warning:")
    st.stop()

aligned = alignments(cipher, crib)
valid = [a.position for a in aligned if a.valid]
truth = st.session_state.get(K + "truth")

st.subheader("El crib deslizándose")
render_drag(drag_payload(cipher, crib, aligned, start=truth or 0, demo=demo))
expected = (len(aligned) - 1) * survival_probability(len(crib))
st.caption(
    f"{fmt_int(len(aligned))} alineaciones; {fmt_int(len(valid))} posibles. Con {len(crib)} "
    f"letras, una alineación falsa sobrevive con probabilidad (25/26)^{len(crib)} = "
    f"{fmt_pct(survival_probability(len(crib)))}: se esperarían unas "
    f"{fmt_int(round(expected))} falsas posibles."
    + (f" La verdadera es la {truth}." if truth is not None else "")
)

if not valid:
    st.error("Ninguna alineación es posible: el crib no está en este cifrado.")
    st.stop()

st.subheader("El menú")
default = valid.index(truth) if truth in valid else 0
position = st.selectbox(
    "Alineación para el menú",
    valid,
    index=default,
    key=K + "position",
    format_func=lambda p: f"Posición {p}" + (" (la verdadera)" if p == truth else ""),
)
menu = menu_at(cipher, crib, position)
stats = menu_stats(menu)
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
render_menu(menu_payload(menu))
if stats.loops < 3:
    st.warning(
        f"Este menú tiene {stats.loops} lazo{'s' if stats.loops != 1 else ''}. Con menos de 3, "
        "la Bombe dará muchas paradas falsas (página La Bombe, fase 3).",
        icon=":material/warning:",
    )
st.session_state["bombe_input"] = {"cipher": cipher, "crib": crib, "position": position}
