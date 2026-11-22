"""Página Rejewski: el indicador doble, los ciclos de AD, BE y CF y el catálogo (spec 8.2, punto 9).

Un día de tráfico de 1932 (rotores I–III, reflector A, 6 cables), cifrado con la máquina real.
Con los mensajes interceptados se reconstruyen AD, BE y CF, se dibujan como ciclos y, cuando
su estructura ya no puede cambiar, se busca en el catálogo de las 105.456 configuraciones.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from enigma_lab import SEED
from enigma_lab.bombe.scrambler import order_label, position_letters
from enigma_lab.core.wiring import ALPHABET
from enigma_lab.experiments.e7_rejewski import kuhl
from enigma_lab.rejewski.catalog import Catalog, build_catalog
from enigma_lab.rejewski.characteristic import (
    DOUBLED_TYPES,
    PRODUCTS,
    characteristic_code,
    format_characteristic,
    middle_moves,
    parse_characteristic,
)
from enigma_lab.rejewski.traffic import Day, core_position, known_after, simulate_day
from enigma_lab.viz import plotly_figs
from enigma_lab.viz.numfmt import fmt_int, fmt_pct
from ui.charts import chart, csv_button
from ui.layout import big_result, is_demo, what_am_i_seeing
from ui.rejewski_view import cycles_payload, indicators_table, product_state, render_cycles

K = "rej_"
MAX_MESSAGES = 250
SHOWN_CANDIDATES = 24
state = st.session_state


# ---------------------------------------------------------------- cálculos (en caché)


@st.cache_resource(show_spinner="Construyendo el catálogo: 105.456 configuraciones…")
def _catalog() -> Catalog:
    return build_catalog()


@st.cache_data(show_spinner=False)
def _day(seed: int) -> Day:
    """Un día de tráfico con ``MAX_MESSAGES`` mensajes; el control elige cuántos se ven."""
    return simulate_day(np.random.default_rng(seed), MAX_MESSAGES)


@st.cache_data(show_spinner=False)
def _distribution() -> pd.DataFrame:
    from enigma_lab.experiments.e7_rejewski import run

    return run()


def _known_table(known: list[np.ndarray]) -> pd.DataFrame:
    """Las parejas conocidas de cada producto: los datos del dibujo, para descargarlos."""
    rows = [
        {"producto": name, "letra": ALPHABET[x], "imagen": ALPHABET[int(y)]}
        for name, part in zip(PRODUCTS, known, strict=True)
        for x, y in enumerate(part)
        if y >= 0
    ]
    return pd.DataFrame(rows)


def _candidates_table(
    catalog: Catalog, code: int, truth: tuple[tuple[str, ...], int], reveal: bool
) -> pd.DataFrame:
    """Las configuraciones candidatas; con la clave revelada, cuál es la verdadera."""
    rows = []
    for order, position in catalog.matches(code)[:SHOWN_CANDIDATES]:
        row: dict[str, object] = {
            "orden": order_label(order),
            "posicion_nucleo": position_letters(position),
        }
        if reveal:
            row["verdadera"] = (tuple(order), position) == truth
        rows.append(row)
    return pd.DataFrame(rows)


def _indicator_line(indicators: np.ndarray, count: int = 16) -> str:
    groups = ["".join(ALPHABET[int(v)] for v in row) for row in indicators[:count]]
    return " · ".join(f"{g[:3]} {g[3:]}" for g in groups)


# ---------------------------------------------------------------- página

demo = is_demo()
st.title("Rejewski")
st.caption("Enigma Lab › Rejewski")
what_am_i_seeing(
    "Hasta 1940, cada mensaje empezaba con su clave de tres letras cifrada dos veces en la "
    "posición del día: seis letras, cifradas por seis permutaciones A, B, C, D, E y F.",
    "Cada indicador da una pareja de AD (de la primera letra a la cuarta), una de BE y una de CF. "
    "Con suficientes mensajes del mismo día se reconstruyen las tres.",
    "Sus ciclos van en parejas de igual longitud, y su estructura (la característica) no depende "
    "del plugboard: conjugar no cambia los ciclos. Solo depende de los rotores.",
    "El catálogo dice qué configuraciones de los rotores dan cada característica: casi siempre "
    "quedan pocas para probar a mano.",
)

catalog = _catalog()
state.setdefault(K + "seed", SEED)
controls = st.columns([2.4, 1.2, 1.5])
n_messages = controls[0].slider(
    "Mensajes interceptados del día", 5, MAX_MESSAGES, 60, 5, key=K + "messages"
)
if controls[1].button("Otro día", icon=":material/casino:", width="stretch"):
    state[K + "seed"] += 1
    state[K + "reveal"] = False
reveal = controls[2].toggle("Revelar la clave", key=K + "reveal")

day = _day(state[K + "seed"])
shown = day.indicators[:n_messages]
known = [known_after(shown, p) for p in range(len(PRODUCTS))]
states = [product_state(k) for k in known]
determined = all(s["characteristic"] for s in states)

metrics = st.columns(4)
metrics[0].metric("Mensajes", fmt_int(n_messages))
for column, name, s in zip(metrics[1:], PRODUCTS, states, strict=True):
    verdict = (
        "completa" if s["permutation"] else "estructura" if s["characteristic"] else "faltan letras"
    )
    column.metric(
        f"Letras de {name}",
        f"{fmt_int(s['letters'])} de 26",
        verdict,
        delta_color="off",
        delta_arrow="off",
        help="Con el teorema de los ciclos en parejas, la estructura (o la permutación entera) "
        "puede quedar determinada antes de ver las 26 letras.",
    )

# ---------------------------------------------------------------- el tráfico

st.subheader("Tráfico de un día con el indicador doble")
st.markdown(
    f'<span class="el-cipher">{_indicator_line(shown)}</span>' + (" …" if n_messages > 16 else ""),
    unsafe_allow_html=True,
)
st.caption(
    "Cada grupo es el indicador de un mensaje: la clave de mensaje tecleada dos veces en la "
    "posición del día. La primera y la cuarta letra son una pareja de AD; la segunda y la "
    "quinta, de BE; la tercera y la sexta, de CF."
)
if not demo:
    with st.expander("Las parejas de los primeros mensajes", icon=":material/table:"):
        st.dataframe(indicators_table(shown), hide_index=True, width="stretch")
if reveal:
    config = day.config
    moved = middle_moves(config)
    st.info(
        f"Clave del día: {config.describe()}. Posición del núcleo al empezar el indicador: "
        f"{position_letters(core_position(config))}."
        + (
            " Este día el rotor central se mueve durante el indicador: la característica no "
            "es la que el catálogo guarda para esa posición."
            if moved
            else " El rotor central no se mueve durante el indicador."
        ),
        icon=":material/key:",
    )

# ---------------------------------------------------------------- los ciclos

st.subheader("AD, BE y CF como ciclos")
render_cycles(cycles_payload(known, demo))
if not demo:
    csv_button("Datos (CSV)", lambda: _known_table(known), "parejas_ad_be_cf")

# ---------------------------------------------------------------- el catálogo

st.subheader("Búsqueda en el catálogo")
truth = (tuple(day.config.rotors), core_position(day.config))
if determined:
    characteristic = tuple(DOUBLED_TYPES[s["types"][0]] for s in states)
    code = characteristic_code(characteristic)  # type: ignore[arg-type]
    size = catalog.size(code)
    found = catalog.code_at(*truth) == code
    big_result(
        format_characteristic(characteristic),  # type: ignore[arg-type]
        f"{fmt_int(size)} configuraciones del catálogo tienen esta característica"
        if size
        else "ninguna configuración del catálogo tiene esta característica",
        ok=size > 0,
        demo=demo,
    )
    if reveal:
        if found:
            st.success(
                "La configuración verdadera está entre ellas: queda probarlas a mano.",
                icon=":material/check_circle:",
            )
        else:
            st.warning(
                "La configuración verdadera no está entre ellas: el rotor central se movió "
                "durante el indicador, y el catálogo supone que no.",
                icon=":material/warning:",
            )
    if size and not demo:
        st.dataframe(
            _candidates_table(catalog, code, truth, reveal), hide_index=True, width="stretch"
        )
        if size > SHOWN_CANDIDATES:
            st.caption(f"Las primeras {SHOWN_CANDIDATES} de {fmt_int(size)}.")
else:
    st.info(
        "Faltan mensajes: la característica de los tres productos todavía puede cambiar. "
        "Sube el número de mensajes interceptados.",
        icon=":material/hourglass:",
    )

if not demo:
    with st.expander("Buscar otra característica", icon=":material/search:"):
        typed = st.text_input(
            "Característica, con la notación de Kuhl",
            "(13 13)(13 13)(13 13)",
            key=K + "query",
            help="Las longitudes de los ciclos de AD, BE y CF, cada producto entre paréntesis.",
        )
        try:
            query = parse_characteristic(typed)
        except ValueError as error:
            st.error(str(error))
        else:
            query_size = catalog.size(characteristic_code(query))
            share = query_size / catalog.n_configurations
            st.markdown(
                f"**{fmt_int(query_size)} configuraciones** ({fmt_pct(share, 2)} del catálogo)."
            )

# ---------------------------------------------------------------- tamaños de clase

st.subheader("Tamaños de clase frente a Kuhl")
reference = kuhl()
distribution = _distribution()
largest = reference["mayor_clase"]
chart(
    plotly_figs.rejewski_class_sizes(
        distribution, (largest["caracteristica"], largest["configuraciones"]), demo
    ),
    "tamanos_de_clase",
    demo,
    data=distribution,
)
sizes = catalog.class_sizes()
st.caption(
    "El catálogo de los rotores I–III con el reflector A tiene "
    f"{fmt_int(catalog.n_configurations)} "
    f"configuraciones y {fmt_int(len(sizes))} características distintas; "
    f"{fmt_int(int((sizes == 1).sum()))} señalan una sola y la más frecuente, "
    f"(13 13)(13 13)(13 13), {fmt_int(int(sizes.max()))}. Kuhl (2007) da "
    f"{fmt_int(reference['caracteristicas_distintas'])}, "
    f"{fmt_int(reference['caracteristicas_unicas'])} y {fmt_int(largest['configuraciones'])}: "
    "la forma coincide, las cifras no del todo (Experimentos › E7)."
)
