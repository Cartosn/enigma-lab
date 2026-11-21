"""Página Inicio: la pregunta del proyecto y la cifra «67 → 20 bits» (spec 8.2, punto 1).

Todas las cifras salen de ``enigma_lab.core.keyspace``; ninguna está escrita a mano.
"""

from __future__ import annotations

import streamlit as st

from enigma_lab import paths
from enigma_lab.core import keyspace as ks
from enigma_lab.viz.numfmt import fmt_dec, fmt_int, fmt_pct, fmt_sci
from enigma_lab.viz.theme import DARK
from ui.catalog import MODULES
from ui.layout import segmented_bar, what_am_i_seeing

space = ks.keyspace(ks.ENIGMA_I, cables=ks.DEFAULT_CABLES)
parts = space.component_bits()
total_bits = ks.bits(space.total_without_rings)
sweep_bits = ks.bits(space.bombe_sweep)

st.title("Enigma Lab")
st.caption(
    "Simulación y criptoanálisis estadístico de Enigma y la Bombe de Turing-Welchman · "
    "Proyecto final de Criptografía · Universidad Nacional de Colombia · 2026"
)

what_am_i_seeing(
    "La pregunta del proyecto y su hipótesis: la estructura de Enigma permite apartar "
    "el plugboard y buscar solo en los rotores.",
    "«67 → 20 bits» compara las claves de Enigma I sin anillos con lo que de verdad "
    "recorre la Bombe. Lo calcula `core/keyspace.py`.",
    "La barra reparte los bits entre los componentes de la clave; en ámbar, lo que barre la Bombe.",
    "Las tarjetas llevan a cada módulo; los que aún no existen dicen en qué fase llegan.",
)

st.markdown(
    f"""
<div class="el-hero">
  <p class="el-question">¿Por qué se rompió un cifrado con {fmt_sci(space.total_without_rings)}
  claves, y cuánta información necesita cada ataque?</p>
  <div class="el-figure" role="img"
       aria-label="De {round(total_bits)} bits a {round(sweep_bits)} bits">
    <span class="num">{round(total_bits)}</span><span class="unit">bits</span>
    <span class="arrow">→</span>
    <span class="num el-amber">{round(sweep_bits)}</span><span class="unit">bits</span>
  </div>
  <p class="el-sub">Enigma I con {ks.DEFAULT_CABLES} cables tiene
  {fmt_int(space.total_without_rings)} claves sin contar anillos ({fmt_dec(total_bits)} bits).
  La Bombe aparta el plugboard, que aporta {fmt_dec(parts["plugboard"])} bits
  ({fmt_pct(space.plugboard_share)}), y solo recorre {fmt_int(space.orders)} órdenes de rotores
  × {fmt_int(space.positions)} posiciones = {fmt_int(space.bombe_sweep)} configuraciones:
  {fmt_dec(sweep_bits)} bits.</p>
</div>
""",
    unsafe_allow_html=True,
)

bar = segmented_bar(
    [
        (
            f"Orden de rotores: {fmt_dec(parts['orders'])} bits",
            parts["orders"],
            fmt_dec(parts["orders"]),
            DARK.accent,
        ),
        (
            f"Posiciones: {fmt_dec(parts['positions'])} bits",
            parts["positions"],
            fmt_dec(parts["positions"]),
            DARK.accent,
        ),
        (
            f"Plugboard: {fmt_dec(parts['plugboard'])} bits (la Bombe lo aparta)",
            parts["plugboard"],
            fmt_dec(parts["plugboard"]),
            DARK.border,
        ),
    ],
    label=(
        f"Bits por componente: orden {fmt_dec(parts['orders'])}, posiciones "
        f"{fmt_dec(parts['positions'])} y plugboard {fmt_dec(parts['plugboard'])}, "
        f"de {fmt_dec(total_bits)} bits"
    ),
)
st.markdown(bar, unsafe_allow_html=True)
st.caption(
    f"En ámbar, los {fmt_dec(sweep_bits)} bits que recorre la Bombe. Los anillos añaden "
    f"{fmt_dec(parts['rings'])} bits más ({fmt_sci(space.total_with_rings, 3)} claves); "
    "la Bombe no los busca porque supone anillos AAA y el verificador los recupera."
)

st.subheader("Módulos")
columns = st.columns(3)
for index, module in enumerate(MODULES):
    with columns[index % 3].container(border=True):
        st.markdown(f"**{module.icon} {module.title}**")
        st.caption(module.summary)
        if module.page:
            st.page_link(module.page, label="Abrir", icon=":material/arrow_forward:")
        else:
            st.badge(f"{module.phase} · pendiente", color="gray")

st.subheader("Estado de la validación")
st.markdown(
    ":material/pending: **Pendiente (fase 1).** Aquí aparecerán, comprobados en vivo, los "
    "vectores de prueba de la sección 6.1 del spec: BDZGO, EWTYX, el doble paso, el "
    "ejemplo de py-enigma, el mensaje de la portada y la traza de la letra A."
)

with st.expander("Fuentes", icon=":material/menu_book:"):
    sources = paths.DOCS / "FUENTES.md"
    if sources.is_file():
        # Sin el título «# Fuentes» del archivo (el panel ya se llama así); las secciones
        # bajan un nivel para no competir con los títulos de la página.
        body = sources.read_text(encoding="utf-8").split("\n", 1)[1]
        st.markdown(body.replace("\n## ", "\n#### "))
    else:
        st.caption("Falta docs/FUENTES.md.")
