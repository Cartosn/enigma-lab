"""Página Estadística del cifrado: qué se filtra y qué no (spec 8.2, punto 4)."""

from __future__ import annotations

import numpy as np
import streamlit as st

from enigma_lab.core.batch import encrypt_batch, random_key_batch, to_texts
from enigma_lab.core.machine import groups_of_five
from enigma_lab.stats.corpus import LANGUAGES, MODES, random_excerpts
from enigma_lab.stats.frequencies import (
    GERMAN_IC_REFERENCE,
    RANDOM_IC,
    chi2_uniform,
    frequencies,
    index_of_coincidence,
    pair_matrix,
)
from enigma_lab.stats.inference import no_fixed_point_probability
from enigma_lab.viz import plotly_figs
from enigma_lab.viz.numfmt import fmt_dec, fmt_int, fmt_pct
from ui.charts import chart
from ui.layout import is_demo, what_am_i_seeing

K = "est_"

demo = is_demo()
st.title("Estadística del cifrado")
st.caption("Enigma Lab › Estadística del cifrado")
what_am_i_seeing(
    "Un fragmento real del corpus (alemán o español) cifrado con una clave aleatoria de "
    "Enigma I con 10 cables.",
    "Las frecuencias del idioma desaparecen: el IC cae de ≈ 0,076 a 1/26 y la prueba χ² ya "
    "no rechaza la uniformidad.",
    "Lo que sí se filtra: ninguna letra se cifra a sí misma. La diagonal de la matriz plano "
    "× cifrado es cero.",
    "La calculadora del final dice qué tan improbable sería eso con una sustitución al azar.",
)

if K + "seed" not in st.session_state:
    st.session_state[K + "seed"] = 2026

controls = st.columns([1, 1, 2, 1])
language = controls[0].selectbox("Idioma", list(LANGUAGES), format_func=LANGUAGES.get)
mode = controls[1].selectbox("Normalización", list(MODES), format_func=MODES.get)
length = controls[2].slider("Longitud del mensaje (letras)", 26, 2000, 500, step=2)
if controls[3].button("Otro fragmento y otra clave", icon=":material/casino:", width="stretch"):
    st.session_state[K + "seed"] += 1

rng = np.random.default_rng(st.session_state[K + "seed"])
plain = random_excerpts(rng, language, 1, length, mode=mode)  # type: ignore[arg-type]
keys, configs = random_key_batch(rng, 1, cables=10)
cipher = encrypt_batch(keys, plain)
plain_text, cipher_text = to_texts(plain)[0], to_texts(cipher)[0]

with st.expander("Texto y clave", icon=":material/description:", expanded=not demo):
    st.caption(configs[0].describe())
    st.markdown(f"**Plano:** `{groups_of_five(plain_text[:150])}`" + (" …" if length > 150 else ""))
    st.markdown(
        f"**Cifrado:** `{groups_of_five(cipher_text[:150])}`" + (" …" if length > 150 else "")
    )

ic_plain = index_of_coincidence(plain[0])
ic_cipher = index_of_coincidence(cipher[0])
chi_plain, p_plain = chi2_uniform(plain[0])
chi_cipher, p_cipher = chi2_uniform(cipher[0])
fixed = int((plain == cipher).sum())

metrics = st.columns(4)
metrics[0].metric(
    "IC del texto plano",
    fmt_dec(float(ic_plain), 4),
    f"alemán: {fmt_dec(GERMAN_IC_REFERENCE, 4)}",
    delta_color="off",
    delta_arrow="off",
)
metrics[1].metric(
    "IC del cifrado",
    fmt_dec(float(ic_cipher), 4),
    f"al azar: 1/26 ≈ {fmt_dec(RANDOM_IC, 4)}",
    delta_color="off",
    delta_arrow="off",
)
metrics[2].metric(
    "χ² del plano (valor p)",
    fmt_dec(float(chi_plain), 1),
    f"p = {fmt_dec(float(p_plain), 4)}",
    delta_color="off",
    delta_arrow="off",
)
metrics[3].metric(
    "χ² del cifrado (valor p)",
    fmt_dec(float(chi_cipher), 1),
    f"p = {fmt_dec(float(p_cipher), 4)}",
    delta_color="off",
    delta_arrow="off",
)
verdict = "rechaza" if p_plain < 0.05 else "no rechaza"
verdict_c = "rechaza" if p_cipher < 0.05 else "no rechaza"
st.caption(
    f"Con α = 0,05, la prueba χ² {verdict} la uniformidad del plano y {verdict_c} la del "
    f"cifrado (25 grados de libertad). Puntos fijos: {fmt_int(fixed)} de {fmt_int(length)}."
)

chart(
    plotly_figs.frequency_comparison(frequencies(plain[0]), frequencies(cipher[0]), demo),
    "frecuencias_plano_cifrado",
    demo,
)

st.subheader("La diagonal en cero")
n_messages = st.slider("Mensajes de 200 letras, cada uno con su propia clave", 50, 1000, 300, 50)
rng_heat = np.random.default_rng(st.session_state[K + "seed"] + 10_000)
with st.spinner(f"Cifrando {fmt_int(n_messages)} mensajes, cada uno con su clave…"):
    plain_many = random_excerpts(rng_heat, language, n_messages, 200, mode=mode)  # type: ignore[arg-type]
    keys_many, _ = random_key_batch(rng_heat, n_messages, cables=10)
    cipher_many = encrypt_batch(keys_many, plain_many)
chart(
    plotly_figs.pair_heatmap(pair_matrix(plain_many, cipher_many), demo),
    "matriz_plano_cifrado",
    demo,
)
st.caption(
    f"{fmt_int(n_messages * 200)} letras cifradas. Las filas oscuras son las letras más "
    "frecuentes del idioma; la diagonal queda vacía."
)

st.subheader("Calculadora del distinguidor")
letters = st.slider("Letras conocidas", 1, 300, 100)
probability = no_fixed_point_probability(letters)
st.markdown(
    f"Si cada letra se cifrara con una sustitución al azar, que ninguna de {fmt_int(letters)} "
    f"coincida con su original pasaría con probabilidad (25/26)^{letters} = "
    f"**{fmt_pct(probability, 2)}**. En Enigma pasa siempre: es un distinguidor perfecto."
)
