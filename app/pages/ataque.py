"""Página Ataque moderno: el ataque de Gillogly solo con texto cifrado (spec 8.2, punto 10).

Un mensaje alemán cifrado con una clave al azar; el ataque no conoce nada más. La fase 1 mide el
índice de coincidencia de cada ubicación sin plugboard, la fase 2 ajusta los anillos y la fase 3
sube el plugboard por hill climbing. Abajo, la curva de éxito de E8 según la longitud.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import streamlit as st

from enigma_lab import SEED, paths
from enigma_lab.attacks import gillogly, hillclimb
from enigma_lab.bombe.scrambler import order_label, rotor_orders
from enigma_lab.core.machine import encrypt, groups_of_five
from enigma_lab.core.random_keys import random_config
from enigma_lab.core.wiring import ALPHABET
from enigma_lab.experiments import e8_coa
from enigma_lab.stats.corpus import random_excerpts
from enigma_lab.viz import plotly_figs
from enigma_lab.viz.numfmt import fmt_dec, fmt_int, fmt_pct
from enigma_lab.viz.theme import DARK
from ui.charts import chart
from ui.layout import big_result, is_demo, what_am_i_seeing, x_as_space

K = "att_"
ORDER_SETS = {
    "I-V": ("Rotores I a V: 60 órdenes", ("I", "II", "III", "IV", "V")),
    "I-III": ("Rotores I a III: 6 órdenes", ("I", "II", "III")),
}
state = st.session_state


def _letters(codes: np.ndarray) -> str:
    return "".join(ALPHABET[int(c)] for c in codes)


@st.cache_data(show_spinner=False)
def _german_ic() -> float:
    """El IC de la muestra alemana con la X como separador: el del texto plano del ataque."""
    from enigma_lab.stats.corpus import load_codes
    from enigma_lab.stats.frequencies import index_of_coincidence

    return float(index_of_coincidence(load_codes("aleman", "muestra", "x")))


@st.cache_data(show_spinner=False)
def _message(seed: int, length: int, cables: int, rotors: tuple[str, ...]) -> dict[str, Any]:
    """Un mensaje alemán de la muestra, cifrado con una clave al azar."""
    rng = np.random.default_rng(seed)
    config = random_config(rng, cables=cables, rotors=rotors)
    plain = random_excerpts(rng, "aleman", 1, length, "muestra", "x")[0].astype(np.int64)
    cipher = encrypt(config, _letters(plain))
    return {"config": config, "plain": plain, "cipher": cipher}


def _run(message: dict[str, Any], rotors: tuple[str, ...]) -> dict[str, Any]:
    """Las tres fases; se guarda lo que dibuja la página (no los 1.054.560 IC)."""
    cipher = e8_coa.to_codes(message["cipher"])
    orders = tuple(rotor_orders(rotors))
    result = gillogly.attack(cipher, orders, top1=200, top2=20)
    flat = np.concatenate([result.scores[o] for o in orders])
    edges = np.linspace(flat.min(), flat.max(), 120)
    counts, edges = np.histogram(flat, bins=edges)
    best = result.best.candidate
    paths_best = gillogly.paths_for(best.order, best.start, best.ring_m, best.ring_r, len(cipher))
    _, _, trace, n_trace = hillclimb.climb_plugboard(
        paths_best, cipher, np.arange(26), hillclimb.trigram_table(), True
    )
    truth = e8_coa.true_location(message["config"])
    return {
        "counts": counts,
        "edges": edges,
        "best_ic": result.phase1[0].ic,
        "true_ic": max(
            float(result.scores[truth.order][s])
            for s in gillogly.neighbours(truth.start, both=True)
        ),
        "rank": result.rank_of(truth.order, truth.start),
        "locations": len(flat),
        "trace": trace[:n_trace].copy(),
        "text": result.best.plaintext,
        "config": result.config,
        "seconds": result.seconds,
        "phase2": result.phase2[:5],
    }


@st.cache_data(show_spinner=False)
def _saved_e8() -> pd.DataFrame | None:
    path = paths.RESULTS / "e8_coa_mensajes.parquet"
    return pd.read_parquet(path) if path.is_file() else None


def _logistic_curves(df: pd.DataFrame) -> dict[int, tuple[np.ndarray, np.ndarray]]:
    fit = e8_coa.logistic(df)
    if fit is None:
        return {}
    grid = np.geomspace(df["L"].min(), df["L"].max(), 120)
    return {
        int(c): (grid, e8_coa.predicted(fit, grid, int(c))) for c in sorted(df["cables"].unique())
    }


def _references() -> list[tuple[float, str]]:
    ref = e8_coa.references()
    return [
        (ref["unicidad"]["letras"], "unicidad ≈ 23"),
        (ref["limite_reglamentario_letras"], "límite real: 250"),
        (ref["gillogly_1995"]["letras_hasta_6_cables"], "Gillogly, ≤ 6 cables: ~300"),
        (ref["gillogly_1995"]["letras_unico_exito_10_cables"], "Gillogly, 10 cables: 1.463"),
    ]


# ---------------------------------------------------------------- página

demo = is_demo()
st.title("Ataque moderno")
st.caption("Enigma Lab › Ataque moderno")
what_am_i_seeing(
    "Solo con el texto cifrado: sin crib, sin indicador y sin saber nada de la clave "
    "(Gillogly 1995).",
    "Fase 1: se descifra en cada orden y posición con anillos AAA y sin plugboard, y se mide el "
    "índice de coincidencia. En la ubicación correcta parte del texto sale bien y el IC sube.",
    "Fase 2: para las mejores ubicaciones se prueban los 676 anillos del central y del derecho.",
    "Fase 3: el plugboard por hill climbing, primero con el IC y luego con trigramas del alemán.",
    "Abajo, cuánto texto necesita el ataque (E8), frente a Gillogly y a la distancia de unicidad.",
)

state.setdefault(K + "seed", SEED)
controls = st.columns([2.0, 1.0, 1.8, 1.4])
length = controls[0].slider("Letras del mensaje", 50, 1_500, 600, 50, key=K + "length")
cables = controls[1].selectbox("Cables", [6, 8, 10], key=K + "cables")
order_key = controls[2].radio(
    "Órdenes que se prueban",
    list(ORDER_SETS),
    format_func=lambda k: ORDER_SETS[k][0],
    key=K + "orders",
    help="Con los rotores I a III el ataque prueba 105.456 ubicaciones en la fase 1; con I a V, "
    "1.054.560 (las de la Bombe).",
)
if controls[3].button("Otro mensaje", icon=":material/casino:", width="stretch"):
    state[K + "seed"] += 1
    state.pop(K + "result", None)
rotors = ORDER_SETS[order_key][1]
message = _message(state[K + "seed"], length, cables, rotors)
signature = (state[K + "seed"], length, cables, order_key)

st.subheader("El texto cifrado")
st.markdown(
    f'<span class="el-cipher">{groups_of_five(message["cipher"][:200])}'
    f"{' …' if length > 200 else ''}</span>",
    unsafe_allow_html=True,
)
reveal = st.toggle("Revelar la clave", key=K + "reveal")
if reveal:
    st.info(f"Clave verdadera: {message['config'].describe()}.", icon=":material/key:")

if st.button("Atacar", type="primary", icon=":material/bolt:"):
    locations = len(rotor_orders(rotors)) * 17_576
    with st.spinner(f"Probando {fmt_int(locations)} ubicaciones y subiendo el plugboard…"):
        state[K + "result"] = (signature, _run(message, rotors))

stored = state.get(K + "result")
if stored is None or stored[0] != signature:
    st.info("Pulsa «Atacar» para correr las tres fases sobre este cifrado.", icon=":material/bolt:")
    result = None
else:
    result = stored[1]

if result is not None:
    plain = message["plain"]
    accuracy = float((result["text"] == plain).mean())
    metrics = st.columns(4)
    metrics[0].metric("Ubicaciones de la fase 1", fmt_int(result["locations"]))
    metrics[1].metric(
        "Puesto de la verdadera en la fase 1",
        fmt_int(result["rank"] + 1) if reveal else "—",
        help="Cuántas ubicaciones falsas tienen más IC que la verdadera, más uno. Se ve al "
        "revelar la clave.",
    )
    metrics[2].metric("Letras correctas", fmt_pct(accuracy) if reveal else "—")
    metrics[3].metric("Tiempo", f"{fmt_dec(sum(result['seconds'].values()), 1)} s")

    st.subheader("Fase 1: la curva del IC en la búsqueda")
    marks = [
        ("1/26", 1 / 26, DARK.text_muted),
        ("la mejor", result["best_ic"], DARK.accent),
    ]
    if reveal:
        marks.append(("la verdadera", result["true_ic"], DARK.success))
    chart(
        plotly_figs.attack_ic_histogram(result["counts"], result["edges"], marks, demo),
        "ic_fase1",
        demo,
        data=pd.DataFrame(
            {
                "ic_desde": result["edges"][:-1],
                "ic_hasta": result["edges"][1:],
                "ubicaciones": result["counts"],
            }
        ),
    )
    st.caption(
        "Sin plugboard y con los anillos supuestos, el IC de casi todas las ubicaciones queda "
        f"cerca de 1/26 = {fmt_dec(1 / 26, 4)}; el del texto plano alemán es "
        f"{fmt_dec(_german_ic(), 4)}. "
        "La ubicación correcta sobresale solo si el mensaje es largo y tiene pocos cables: los "
        "anillos supuestos hacen girar el central y el izquierdo en otra letra y corren parte del "
        "texto."
    )

    st.subheader("Fase 3: el hill climbing del plugboard")
    if len(result["trace"]):
        chart(plotly_figs.attack_climb(result["trace"], demo), "hill_climbing", demo)
    config = result["config"]
    st.caption(
        f"En la mejor ubicación: {order_label(tuple(config.rotors))}, anillos "
        f"{config.ring_letters}, posición {config.position_letters} y "
        f"{len(config.plugboard)} cables ({config.plugboard_string or 'ninguno'})."
    )
    text = _letters(result["text"])
    big_result(
        groups_of_five(text[:150]),
        x_as_space(text[:300]),
        ok=accuracy >= 0.9 or not reveal,
        demo=demo,
    )
    if reveal:
        if accuracy >= e8_coa.SUCCESS:
            st.success(
                f"Mensaje leído: {fmt_pct(accuracy)} de las letras.", icon=":material/check_circle:"
            )
        else:
            st.warning(
                f"El ataque no lo leyó ({fmt_pct(accuracy)} de las letras). La ubicación "
                f"verdadera quedó en el puesto {fmt_int(result['rank'] + 1)} de la fase 1.",
                icon=":material/warning:",
            )

st.subheader("Curva de éxito según la longitud (E8)")
saved = _saved_e8()
if saved is None:
    st.info("Aún no hay resultados de E8: corre  make reproduce.")
else:
    table = e8_coa.aggregate(saved)
    chart(
        plotly_figs.e8_success(table, _logistic_curves(saved), _references(), demo),
        "e8_exito",
        demo,
        data=table,
    )
    n_cell = int(table["n"].min())
    st.caption(
        f"{fmt_int(len(saved))} mensajes ({n_cell} por punto), con IC de Wilson; las líneas son "
        "la regresión logística y el punteado, el hill climbing con la ubicación dada: lo que "
        "lograría el ataque si la fase 1 no fallara. Detalle en Experimentos › E8."
    )
