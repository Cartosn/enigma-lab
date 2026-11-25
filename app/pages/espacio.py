"""Página Espacio de claves: cuántos bits aporta cada componente."""

from __future__ import annotations

import math

import streamlit as st

from enigma_lab.core import keyspace as ks
from enigma_lab.experiments.e2_keyspace import run as e2_table
from enigma_lab.viz import plotly_figs
from enigma_lab.viz.numfmt import fmt_dec, fmt_int, fmt_pct, fmt_sci
from enigma_lab.viz.theme import DARK
from ui.charts import chart, csv_button
from ui.course import PAGES as IN_CLASS
from ui.layout import in_class, is_demo, segmented_bar, what_am_i_seeing

MODELS = {"Enigma I (5 rotores)": ks.ENIGMA_I, "Enigma M3 (8 rotores)": ks.M3}
# Máquinas en paralelo de la calculadora de fuerza bruta (ataque paralelo). Va como comentario:
# en una página, Streamlit dibujaría un texto suelto.
MACHINES = [1, 10, 100, 1_000, 10_000, 100_000, 1_000_000]


def _duration(years: float) -> str:
    """Un tiempo legible: en años si pasa de uno, y si no en días, horas, segundos o ms."""
    if years >= 1e4:
        return f"{fmt_sci(years, 3)} años"
    if years >= 1:
        return f"{fmt_dec(years, 2 if years < 10 else 1)} años"
    seconds = years * ks.SECONDS_PER_YEAR
    for unit, size in (("días", 86_400), ("horas", 3_600), ("min", 60), ("s", 1)):
        if seconds >= size:
            return f"{fmt_dec(seconds / size, 1)} {unit}"
    return f"{fmt_dec(seconds * 1000, 3)} ms"


demo = is_demo()
st.title("Espacio de claves")
st.caption("Enigma Lab › Espacio de claves")
in_class(*IN_CLASS["espacio"])
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
speed = st.columns(2)
exponent = speed[0].slider(
    "Pruebas por segundo en cada máquina (potencia de 10)",
    3,
    18,
    9,
    help="10⁹ = mil millones de claves por segundo.",
)
machines = speed[1].select_slider(
    "Máquinas en paralelo",
    options=MACHINES,
    value=1,
    format_func=fmt_int,
    help="Ataque paralelo: las máquinas se reparten las claves y tardan tantas veces menos.",
)
rate = 10.0**exponent
years_all = ks.brute_force_years(space.total_without_rings, rate, machines)
seconds_bombe = space.bombe_sweep / (rate * machines)
calc = st.columns(2)
calc[0].metric(f"Probar las {fmt_sci(space.total_without_rings)} claves", _duration(years_all))
calc[1].metric(
    f"Barrer las {fmt_int(space.bombe_sweep)} de la Bombe",
    _duration(seconds_bombe / ks.SECONDS_PER_YEAR),
)
where = "una máquina" if machines == 1 else f"cada una de {fmt_int(machines)} máquinas"
st.caption(
    f"A 10^{exponent} pruebas por segundo en {where}. Años de 365,25 días. Probar las claves "
    f"una por una cuesta {fmt_sci(space.total_without_rings / space.bombe_sweep)} veces más "
    f"que el barrido de la Bombe (2^{fmt_dec(math.log2(space.plugboard), 1)}, los bits del "
    "plugboard). Repartir el trabajo entre máquinas divide el tiempo, pero no quita ningún bit."
)

if not demo:
    csv_button(
        "Todas las cifras de E2 (CSV)",
        e2_table,
        "e2_espacio_de_claves",
        icon=":material/download:",
    )
