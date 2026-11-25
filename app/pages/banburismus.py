"""Página Banburismus: decibanes y la prueba secuencial de Wald.

Dos mensajes en profundidad con un desplazamiento oculto. Se comparan en cada
desplazamiento de −25 a +25 y se suman decibanes; la trayectoria del puntaje decide con
los umbrales de Wald. La puntuación alterna entre letras sueltas y multigramas, y la
curva ROC muestra qué tan bien separa cada una la profundidad del azar.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import streamlit as st

from enigma_lab import SEED
from enigma_lab.banburismus.depth import (
    MAX_OFFSET,
    OFFSETS,
    TEXT_SOURCES,
    DepthPairs,
    false_offsets,
    make_pairs,
    repeats,
)
from enigma_lab.banburismus.scoring import (
    SCORINGS,
    TURING,
    RepeatModel,
    column_weights,
    offset_scores,
    scoring_model,
    trajectory,
)
from enigma_lab.banburismus.sprt import thresholds, wald_letters
from enigma_lab.core.machine import groups_of_five
from enigma_lab.core.wiring import ALPHABET
from enigma_lab.experiments.e6_banburismus import auc, roc_points
from enigma_lab.stats.corpus import Source
from enigma_lab.viz import plotly_figs
from enigma_lab.viz.numfmt import fmt_dec, fmt_int, fmt_pct
from enigma_lab.viz.theme import CATEGORICAL, DARK
from ui.charts import chart
from ui.course import PAGES as IN_CLASS
from ui.layout import in_class, is_demo, what_am_i_seeing

K = "banb_"
CORPUS: Source = "muestra"  # la muestra del repositorio: la app funciona sin internet
ALPHAS = {0.05: "5 %", 0.01: "1 %", 0.001: "0,1 %"}
ROC_PAIRS = 300
ROC_MAX_LETTERS = 800
state = st.session_state


# ---------------------------------------------------------------- cálculos (en caché)


@st.cache_data(show_spinner=False)
def _pair(seed: int, text: str, length: int) -> DepthPairs:
    """Un par de mensajes en profundidad, de ``length`` + 25 letras cada uno."""
    rng = np.random.default_rng(seed)
    return make_pairs(rng, 1, length + MAX_OFFSET, text, CORPUS)  # type: ignore[arg-type]


@st.cache_data(show_spinner=False)
def _roc(text: str, length: int) -> list[tuple[str, np.ndarray, np.ndarray, float]]:
    """Curvas ROC de las cuatro puntuaciones con ``ROC_PAIRS`` pares nuevos (semilla 2026).

    Profundidad: el desplazamiento verdadero de cada par. Azar: otro desplazamiento del
    mismo par, al azar. El puntaje es la suma de decibanes en ``length`` columnas.
    """
    rng = np.random.default_rng(SEED)
    pairs = make_pairs(rng, ROC_PAIRS, length + MAX_OFFSET, text, CORPUS)  # type: ignore[arg-type]
    depth_cols = repeats(pairs.cipher1, pairs.cipher2, pairs.offsets, length)
    chance_cols = repeats(pairs.cipher1, pairs.cipher2, false_offsets(rng, pairs.offsets), length)
    curves = []
    for key in SCORINGS:
        model = scoring_model(key, CORPUS)
        depth = column_weights(depth_cols, model).sum(axis=1)
        chance = column_weights(chance_cols, model).sum(axis=1)
        fpr, tpr = roc_points(depth, chance)
        curves.append((SCORINGS[key], fpr, tpr, auc(depth, chance)))
    return curves


def _signed(value: int) -> str:
    return f"+{value}" if value > 0 else fmt_int(value)


def _letters(codes: np.ndarray, count: int = 60) -> str:
    return groups_of_five("".join(ALPHABET[int(c)] for c in codes[:count])) + " …"


def _weights_table(model: RepeatModel) -> pd.DataFrame:
    """Los pesos de la puntuación elegida, según cuántas columnas seguidas acaban de repetir."""
    rows = []
    for r, (h, plus, minus) in enumerate(zip(model.probs, model.plus, model.minus, strict=True)):
        if model.order == 1:
            before = "cualquiera (letras sueltas)"
        else:
            before = str(r) + (" o más" if r == model.order - 1 else "")
        rows.append(
            {
                "Repeticiones seguidas justo antes": before,
                "P(repite) en profundidad": fmt_pct(h, 2),
                "Si repite": f"+{fmt_dec(float(plus), 3)} dB",
                "Si no repite": f"{fmt_dec(float(minus), 3)} dB",
            }
        )
    return pd.DataFrame(rows)


def _decision(values: np.ndarray, upper: float, lower: float) -> str:
    crossed = np.flatnonzero((values >= upper) | (values <= lower))
    if not len(crossed):
        return f"sin decidir en {fmt_int(len(values))} letras ({fmt_dec(float(values[-1]), 1)} dB)"
    k = int(crossed[0])
    verdict = "acepta profundidad" if values[k] >= upper else "descarta"
    return f"{verdict} en la letra {fmt_int(k + 1)}"


# ---------------------------------------------------------------- página

demo = is_demo()
st.title("Banburismus")
st.caption("Enigma Lab › Banburismus")
in_class(*IN_CLASS["banburismus"])
what_am_i_seeing(
    "Dos mensajes con la misma clave diaria y claves de mensaje que solo difieren en el rotor "
    "derecho quedan en profundidad: corridos d letras, pasan por los mismos estados.",
    "En profundidad, dos letras cifradas coinciden si y solo si coinciden las planas: 1 de cada "
    "17 en el texto naval alemán (Turing) y 1 de cada 26 al azar.",
    "Cada columna suma decibanes (10·log₁₀ del factor de Bayes): +1,845 si repite y −0,093 si "
    "no. El desplazamiento con más decibanes es el candidato.",
    "La prueba de Wald decide al cruzar ±19,96 dB (errores del 1 %). Con letras sueltas hacen "
    "falta unas 929 letras; los bigramas y trigramas aprovechan que las repeticiones vienen en "
    "racimos.",
)

state.setdefault(K + "seed", SEED)
controls = st.columns([1.3, 2.2, 1.2])
text = controls[0].selectbox(
    "Texto plano",
    list(TEXT_SOURCES),
    format_func=lambda k: TEXT_SOURCES[k],
    key=K + "text",
    help="Alemán del corpus, o un texto sintético que en profundidad repite 1 de cada 17 "
    "letras exactas, el modelo de Turing.",
)
length = controls[1].slider(
    "Letras comparadas en cada desplazamiento", 50, 1500, 400, 50, key=K + "length"
)
if controls[2].button("Otro par de mensajes", icon=":material/casino:", width="stretch"):
    state[K + "seed"] += 1
    state[K + "reveal"] = False

options = st.columns([3, 1.4])
scoring_key = options[0].radio(
    "Puntuación",
    list(SCORINGS),
    format_func=SCORINGS.get,
    horizontal=True,
    key=K + "scoring",
    help="Letras sueltas con la tasa 1/17 de Turing o con la del corpus; o multigramas: la "
    "probabilidad de repetir depende de cuántas columnas seguidas acaban de repetir.",
)
alpha = options[1].select_slider(
    "Errores α = β", options=list(ALPHAS), value=0.01, format_func=ALPHAS.get, key=K + "alpha"
)
model = scoring_model(scoring_key, CORPUS)
upper, lower = thresholds(alpha)

metrics = st.columns(4)
metrics[0].metric(
    "Repetición (1/17 frente a 1/26)",
    f"+{fmt_dec(float(TURING.plus[0]), 3)} dB",
    help="10·log₁₀((1/17) / (1/26))",
)
metrics[1].metric(
    "No repetición",
    f"{fmt_dec(float(TURING.minus[0]), 3)} dB",
    help="10·log₁₀((16/17) / (25/26))",
)
metrics[2].metric(
    "Umbrales de Wald",
    f"±{fmt_dec(upper, 2)} dB",
    f"α = β = {ALPHAS[alpha]}",
    delta_color="off",
    delta_arrow="off",
)
metrics[3].metric(
    "Wald con letras sueltas",
    f"{fmt_int(round(wald_letters(TURING.drift(True), True, alpha)))} y "
    f"{fmt_int(round(wald_letters(TURING.drift(False), False, alpha)))}",
    "confirmar y descartar",
    delta_color="off",
    delta_arrow="off",
)
with st.expander("Pesos de esta puntuación", icon=":material/scale:"):
    st.dataframe(_weights_table(model), hide_index=True, width="stretch")
    st.caption(
        f"En promedio, {fmt_dec(model.drift(True), 4)} dB por letra en profundidad y "
        f"{fmt_dec(model.drift(False), 4)} dB al azar, si el texto siguiera este modelo."
    )

# ---------------------------------------------------------------- los dos mensajes

pair = _pair(state[K + "seed"], text, length)
offset = int(pair.offsets[0])
st.subheader("Dos mensajes en profundidad")
reveal = st.toggle("Revelar el desplazamiento verdadero", key=K + "reveal")
keys = [pair.message_key(0, 1), pair.message_key(0, 2)]
shown = [k if reveal else k[:2] + "?" for k in keys]
st.markdown(
    f"**Mensaje 1** · clave de mensaje `{shown[0]}`  \n"
    f'<span class="el-cipher">{_letters(pair.cipher1[0])}</span>  \n'
    f"**Mensaje 2** · clave de mensaje `{shown[1]}`  \n"
    f'<span class="el-cipher">{_letters(pair.cipher2[0])}</span>',
    unsafe_allow_html=True,
)
st.caption(
    "Misma clave diaria (oculta) y el mismo rotor izquierdo y central en las dos claves de "
    "mensaje: las dos máquinas recorren los mismos estados, corridas d letras. "
    + (
        f"Aquí d = {_signed(offset)}: la letra j del mensaje 2 se cifró en el mismo estado que "
        f"la j {'+' if offset > 0 else '−'} {abs(offset)} del 1."
        if reveal
        else "El desplazamiento d está oculto."
    )
)

# ---------------------------------------------------------------- por desplazamiento

st.subheader("Coincidencias y decibanes por desplazamiento")
table = offset_scores(pair.cipher1[0], pair.cipher2[0], length, model, OFFSETS)
best = int(table.loc[table["decibanes"].idxmax(), "desplazamiento"])
chart(
    plotly_figs.banburismus_offsets(table, upper, offset if reveal else None, demo),
    "decibanes_por_desplazamiento",
    demo,
    data=table,
)
best_row = table[table["desplazamiento"] == best].iloc[0]
expected_random = length / 26
st.caption(
    f"{fmt_int(length)} columnas en cada desplazamiento. Al azar se esperan unas "
    f"{fmt_dec(expected_random, 1)} repeticiones; el mejor desplazamiento tiene "
    f"{fmt_int(int(best_row['repeticiones']))}, con {fmt_int(int(best_row['bigramas']))} bigramas "
    f"y {fmt_int(int(best_row['trigramas']))} trigramas repetidos."
)
if reveal:
    if best == offset:
        st.success(
            f"El desplazamiento con más decibanes, {_signed(best)}, es el verdadero.",
            icon=":material/check_circle:",
        )
    else:
        st.warning(
            f"El mejor desplazamiento es {_signed(best)}, pero el verdadero es {_signed(offset)}: "
            "con este solapamiento la evidencia no alcanza. Prueba con más letras.",
            icon=":material/warning:",
        )

# ---------------------------------------------------------------- trayectoria

st.subheader("Trayectoria acumulada con los umbrales de Wald")
rng = np.random.default_rng(state[K + "seed"])
others = [int(d) for d in rng.permutation(OFFSETS) if int(d) not in (best, offset)][:2]
lines: list[tuple[str, int, str]] = [(f"mejor: {_signed(best)}", best, DARK.accent)]
if reveal and offset != best:
    lines.append((f"verdadero: {_signed(offset)}", offset, DARK.success))
lines += [
    (f"otro: {_signed(d)}", d, color)
    for d, color in zip(others, (CATEGORICAL[1], CATEGORICAL[3]), strict=True)
]
paths = [
    (label, trajectory(repeats(pair.cipher1[0], pair.cipher2[0], d, length), model), color)
    for label, d, color in lines
]
chart(
    plotly_figs.banburismus_trajectories(paths, upper, lower, demo),
    "trayectorias_wald",
    demo,
)
st.caption(
    " · ".join(f"{label}: {_decision(values, upper, lower)}" for label, values, _ in paths)
    + f". El puntaje se lee de izquierda a derecha y la prueba se detiene en ±{fmt_dec(upper, 2)} "
    "dB. Wald supone que se detiene justo en el umbral; en realidad lo pasa (el sobrepaso), y "
    "por eso la simulación pide unas letras más que su aproximación (Experimentos › E6)."
)

# ---------------------------------------------------------------- curva ROC

st.subheader("Curva ROC")
roc_length = min(length, ROC_MAX_LETTERS)
with st.spinner(f"Simulando {ROC_PAIRS} pares con {fmt_int(roc_length)} letras…"):
    curves = _roc(text, roc_length)
chart(plotly_figs.roc_curves(curves, roc_length, demo), "curvas_roc", demo)
st.caption(
    f"{ROC_PAIRS} pares nuevos de «{TEXT_SOURCES[text]}» (semilla {SEED}): el puntaje en el "
    "desplazamiento verdadero frente al de otro al azar, tras "
    f"{fmt_int(roc_length)} letras. Con letras sueltas el puntaje solo depende del número de "
    "repeticiones, así que las dos tasas dan la misma curva. Los resultados completos, con 2.000 "
    "pares por condición, están en Experimentos › E6."
)
