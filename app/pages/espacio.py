"""Página Espacio de claves: cuántos bits aporta cada componente (spec 8.2, punto 3)."""

from __future__ import annotations

import math

import streamlit as st

from enigma_lab.core import keyspace as ks
from enigma_lab.experiments.e2_keyspace import run as e2_table
from enigma_lab.viz import plotly_figs
from enigma_lab.viz.numfmt import fmt_dec, fmt_int, fmt_pct, fmt_sci
from enigma_lab.viz.theme import DARK
from ui.charts import chart, csv_button
from ui.layout import is_demo, segmented_bar, what_am_i_seeing

MODELS = {"Enigma I (5 rotores)": ks.ENIGMA_I, "Enigma M3 (8 rotores)": ks.M3}

demo = is_demo()
st.title("Espacio de claves")
st.caption("Enigma Lab › Espacio de claves")
what_am_i_seeing(
    "Cuántas claves tiene Enigma y cuántos bits aporta cada componente: orden de rotores, "
    "posiciones, anillos y plugboard. Los conteos son exactos (`core/keyspace.py`).",
    "El plugboard domina: con 10 cables aporta unos 47 de los 67 bits sin anillos.",
    "La Bombe aparta el plugboard y solo barre órdenes × posiciones: de 67 bits a 20.",
    "Más cables no siempre es más seguro: N(k) llega a su máximo con 11 cables.",
)

controls = st.columns([1.2, 2])
model_name = controls[0].selectbox("Modelo", list(MODELS))
cables = controls[1].slider("Cables en el plugboard", 0, ks.max_cables(), ks.DEFAULT_CABLES)
space = ks.keyspace(MODELS[model_name], cables=cables)
bits = space.component_bits()
total_bits = ks.bits(space.total_without_rings)
sweep_bits = ks.bits(space.bombe_sweep)

metrics = st.columns(4)
metrics[0].metric(
    "Claves sin anillos",
    fmt_sci(space.total_without_rings, 3),
    f"{fmt_dec(total_bits)} bits",
    delta_color="off",
    delta_arrow="off",
)
metrics[1].metric(
    "Con anillos",
    fmt_sci(space.total_with_rings, 3),
    f"{fmt_dec(ks.bits(space.total_with_rings))} bits",
    delta_color="off",
    delta_arrow="off",
)
metrics[2].metric(
    "Barrido de la Bombe",
    fmt_int(space.bombe_sweep),
    f"{fmt_dec(sweep_bits)} bits",
    delta_color="off",
    delta_arrow="off",
)
metrics[3].metric(
    "Parte del plugboard",
    fmt_pct(space.plugboard_share),
    f"{fmt_dec(bits['plugboard'])} bits",
    delta_color="off",
    delta_arrow="off",
)

st.markdown(
    segmented_bar(
        [
            (
                f"Orden: {fmt_dec(bits['orders'])} bits",
                bits["orders"],
                fmt_dec(bits["orders"]),
                DARK.accent,
            ),
            (
                f"Posiciones: {fmt_dec(bits['positions'])} bits",
                bits["positions"],
                fmt_dec(bits["positions"]),
                DARK.accent,
            ),
            (
                f"Plugboard: {fmt_dec(bits['plugboard'])} bits (la Bombe lo aparta)",
                max(bits["plugboard"], 0.0001),
                fmt_dec(bits["plugboard"]),
                DARK.border,
            ),
        ],
        label=f"De {fmt_dec(total_bits)} bits, la Bombe barre {fmt_dec(sweep_bits)}",
    ),
    unsafe_allow_html=True,
)
st.caption(
    f"De {fmt_dec(total_bits)} bits a {fmt_dec(sweep_bits)}: en ámbar, lo que recorre la Bombe."
)

charts = st.columns(2)
chart(plotly_figs.keyspace_bits(space, model_name, demo), "bits_por_componente", demo, charts[0])
chart(plotly_figs.plugboard_curve(cables, demo), "plugboard_nk", demo, charts[1])

st.subheader("Calculadora de fuerza bruta")
exponent = st.slider(
    "Pruebas por segundo (potencia de 10)",
    3,
    18,
    9,
    help="10⁹ = mil millones de claves por segundo.",
)
rate = 10.0**exponent
years_all = ks.brute_force_years(space.total_without_rings, rate)
seconds_bombe = space.bombe_sweep / rate
calc = st.columns(2)
calc[0].metric(
    f"Probar las {fmt_sci(space.total_without_rings)} claves",
    f"{fmt_sci(years_all, 3) if years_all >= 1e4 else fmt_dec(years_all, 1)} años",
)
bombe_text = (
    f"{fmt_dec(seconds_bombe * 1000, 3)} ms"
    if seconds_bombe < 1
    else f"{fmt_dec(seconds_bombe, 1)} s"
)
calc[1].metric(f"Barrer las {fmt_int(space.bombe_sweep)} de la Bombe", bombe_text)
st.caption(
    f"A 10^{exponent} pruebas por segundo. Años de 365,25 días. Probar las claves una por una "
    f"cuesta {fmt_sci(space.total_without_rings / space.bombe_sweep)} veces más que el "
    f"barrido de la Bombe (2^{fmt_dec(math.log2(space.plugboard), 1)}, los bits del plugboard)."
)

if not demo:
    csv_button(
        "Todas las cifras de E2 (CSV)",
        e2_table,
        "e2_espacio_de_claves",
        icon=":material/download:",
    )
