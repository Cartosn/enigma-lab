"""Página Máquina: configurar Enigma, cifrar y ver el camino de cada letra.

Demo 1 del guion (diapositiva 4): el preajuste «Vector BDZGO» y luego «Portada», que
descifra en un clic el mensaje de la diapositiva 1.
"""

from __future__ import annotations

import numpy as np
import streamlit as st

from enigma_lab.core.machine import Enigma, EnigmaConfig, groups_of_five, to_machine_letters
from enigma_lab.core.random_keys import random_config
from enigma_lab.core.vectors import vector
from enigma_lab.core.wiring import ALPHABET, MODELS
from enigma_lab.viz.numfmt import fmt_int
from ui.charts import csv_button
from ui.course import PAGES as IN_CLASS
from ui.layout import big_result, hidden_in_demo, in_class, is_demo, what_am_i_seeing, x_as_space
from ui.machine_view import render_machine, trace_table

K = "maq_"  # prefijo de las claves de st.session_state de esta página
LETTERS = list(ALPHABET)
MAX_SLOTS = 4  # la M4 lleva cuatro rotores


# ---------------------------------------------------------------- estado


def _load(config: EnigmaConfig, text: str) -> None:
    """Pone una clave y un texto en los controles (lo llaman los botones)."""
    state = st.session_state
    state[K + "model"] = config.model
    names = list(config.rotors)
    if MODELS[config.model].greek:
        state[K + "greek"] = names.pop(0)
    for i, name in enumerate(names):
        state[f"{K}rotor_{i}"] = name
    state[K + "reflector"] = config.reflector
    for i in range(MAX_SLOTS):
        state[f"{K}ring_{i}"] = config.ring_letters[i] if i < len(config.rotors) else "A"
        state[f"{K}pos_{i}"] = config.position_letters[i] if i < len(config.rotors) else "A"
    state[K + "plugboard"] = config.plugboard_string
    state[K + "text"] = text
    state[K + "start"] = config.position_letters


def _preset_bdzgo() -> None:
    _load(EnigmaConfig.from_strings("I II III"), "AAAAA")


def _preset_cover() -> None:
    v = vector("portada")
    _load(EnigmaConfig.from_dict(v["key"]), v["output"])  # el cifrado de la portada


def _preset_historical() -> None:
    v = vector("m4_u264")
    _load(EnigmaConfig.from_dict(v["key"]), v["input"])


def _random_key() -> None:
    """Clave al azar de verdad (sin semilla fija): la usa el compañero de la demo 2.

    Si se marcaron rotores permitidos (por ejemplo I, II y III, lo que se acuerde para la
    demo 2), los tres rotores salen de ellos.
    """
    model = st.session_state.get(K + "model", "I")
    text = st.session_state.get(K + "text", "") or "WETTERBERICHT"
    allowed = [r for r in st.session_state.get(K + "allowed", []) if r in MODELS[model].rotors]
    config = random_config(
        np.random.default_rng(),
        model=model,
        cables=10,
        rotors=allowed if len(allowed) >= 3 else None,
    )
    _load(config, text)


def _reset_positions() -> None:
    start = st.session_state.get(K + "start", "AAAA")
    for i, letter in enumerate(start):
        st.session_state[f"{K}pos_{i}"] = letter


def _keep_valid(key: str, options: list[str]) -> None:
    """Si el valor guardado no existe entre las opciones (cambió el modelo), usa la primera."""
    if st.session_state.get(key) not in options:
        st.session_state[key] = options[0]


if K + "model" not in st.session_state:
    _preset_bdzgo()

# ---------------------------------------------------------------- página

demo = is_demo()
st.title("Máquina")
st.caption("Enigma Lab › Máquina")
in_class(*IN_CLASS["maquina"])
what_am_i_seeing(
    "Una Enigma simulada en Python: modelo, rotores, anillos, posición inicial y cables.",
    "La animación muestra el paso de los rotores (el doble paso en ámbar) y la letra que "
    "sale de cada etapa: en turquesa la ida, en ámbar la vuelta.",
    "Cifrar y descifrar son la misma operación: si escribes la salida como entrada, con la "
    "misma clave, vuelve el texto original.",
    "La lámpara de la tecla pulsada (contorno punteado) nunca se enciende: ninguna letra se "
    "cifra a sí misma.",
)

PRESETS = (
    (
        "Vector BDZGO",
        _preset_bdzgo,
        ":material/science:",
        "I-II-III, reflector B, anillos y posición AAA, sin cables: AAAAA sale BDZGO.",
    ),
    (
        "Portada",
        _preset_cover,
        ":material/mail:",
        "La clave de la diapositiva 1, con su cifrado ya escrito.",
    ),
    (
        "Ejemplo histórico",
        _preset_historical,
        ":material/history_edu:",
        "Mensaje real del U-264 (Enigma M4, 1942).",
    ),
    (
        "Clave aleatoria",
        _random_key,
        ":material/casino:",
        "Rotores, anillos, posición y 10 cables al azar.",
    ),
    (
        "Reiniciar posición",
        _reset_positions,
        ":material/restart_alt:",
        "Vuelve a la posición inicial de la clave cargada.",
    ),
)
# En modo demo solo quedan los dos preajustes de la demo 1, con su nombre completo.
shown_presets = PRESETS[:2] if demo else PRESETS
for column, (label, action, icon, tip) in zip(
    st.columns(len(shown_presets)), shown_presets, strict=True
):
    column.button(label, on_click=action, icon=icon, help=tip, width="stretch", wrap=True)

# La clave se oculta en modo demo, pero sus controles siguen vivos (conservan su estado).
with (
    hidden_in_demo("maq_clave"),
    st.expander("Clave", expanded=True, icon=":material/tune:"),
):
    top = st.columns([1.3, 1, 1, 1, 1, 1.1])
    model = top[0].selectbox(
        "Modelo", list(MODELS), format_func=lambda k: MODELS[k].name, key=K + "model"
    )
    spec = MODELS[model]
    slot_cols = top[1:5] if spec.greek else top[2:5]
    rotor_names: list[str] = []
    if spec.greek:
        _keep_valid(K + "greek", list(spec.greek))
        rotor_names.append(slot_cols[0].selectbox("Griego", spec.greek, key=K + "greek"))
        slot_cols = slot_cols[1:]
    labels = ("Izquierdo", "Central", "Derecho")
    for i, (column, label) in enumerate(zip(slot_cols, labels, strict=True)):
        _keep_valid(f"{K}rotor_{i}", list(spec.rotors))
        rotor_names.append(column.selectbox(label, spec.rotors, key=f"{K}rotor_{i}"))
    _keep_valid(K + "reflector", list(spec.reflectors))
    reflector = top[5].selectbox("Reflector", spec.reflectors, key=K + "reflector")

    n = spec.n_rotors
    ring_cols, pos_cols = st.columns(2, gap="large")
    ring_cols.markdown("Anillos (Ringstellung), de izquierda a derecha")
    pos_cols.markdown("Posición inicial (ventanas), de izquierda a derecha")
    rings = [
        c.selectbox(f"Anillo {i + 1}", LETTERS, key=f"{K}ring_{i}", label_visibility="collapsed")
        for i, c in enumerate(ring_cols.columns(n))
    ]
    positions = [
        c.selectbox(f"Posición {i + 1}", LETTERS, key=f"{K}pos_{i}", label_visibility="collapsed")
        for i, c in enumerate(pos_cols.columns(n))
    ]
    plugboard = st.text_input(
        "Plugboard",
        key=K + "plugboard",
        placeholder="AV BS CG DL FU HZ IN KM OW RX",
        help="Parejas de letras separadas por espacios; hasta 13 cables.",
    )
    chosen = st.session_state.get(K + "allowed") or []
    if any(r not in spec.rotors for r in chosen):  # cambió el modelo
        st.session_state[K + "allowed"] = [r for r in chosen if r in spec.rotors]
    st.multiselect(
        "Rotores permitidos en «Clave aleatoria»",
        spec.rotors,
        key=K + "allowed",
        placeholder="Todos los del modelo",
        help="Para la demo 2: si se acuerda que el compañero use solo los rotores I, II y III, "
        "márcalos aquí antes de pulsar «Clave aleatoria». Con menos de 3, se usan todos.",
    )

try:
    config = EnigmaConfig.from_strings(
        " ".join(rotor_names), reflector, "".join(rings), "".join(positions), plugboard, model
    )
except ValueError as error:
    st.error(f"Clave inválida: {error}", icon=":material/error:")
    st.stop()

if demo:
    st.caption(config.describe())

raw = st.text_area(
    "Texto de entrada",
    key=K + "text",
    height=90,
    help="Solo existen las teclas A–Z: las tildes se quitan, la Ñ pasa a N y se ignora lo "
    "demás. Para separar palabras se usaba la X.",
)
text = to_machine_letters(raw)
if text != raw.replace(" ", "").upper():
    st.caption(f"Entra a la máquina: `{groups_of_five(text)}`")

machine = Enigma(config)
traces = machine.trace(text)
output = "".join(t.lamp for t in traces)

st.markdown("**Salida**")
# La lectura con la X como espacio solo tiene sentido al descifrar: cuando la salida trae
# más X que la entrada (la X separaba palabras en el texto plano).
reading = x_as_space(output) if output.count("X") > text.count("X") else ""
big_result(groups_of_five(output), reading, demo=demo)
if output and not demo:
    with st.expander("Copiar el resultado", icon=":material/content_copy:"):
        st.code(groups_of_five(output), language=None)
    st.caption(f"Ventanas al terminar: {machine.window} · {fmt_int(len(text))} letras")
if output:
    back = Enigma(config).encrypt(output)
    fixed = sum(a == b for a, b in zip(text, output, strict=True))
    checks = st.columns(2)
    if back == text:
        checks[0].markdown(
            ":green[:material/check_circle:] **Cifrar la salida devuelve la entrada.**"
        )
    else:  # no debería pasar nunca: lo prueban test_properties.py y E1
        checks[0].markdown(":red[:material/cancel:] **Cifrar la salida no devolvió la entrada.**")
    mark = ":green[:material/check_circle:]" if fixed == 0 else ":red[:material/cancel:]"
    checks[1].markdown(
        f"{mark} **Ninguna letra se cifró a sí misma:** {fmt_int(fixed)} de {fmt_int(len(text))}."
    )

signature = (config, text)
autoplay = st.session_state.get(K + "last_signature") != signature
st.session_state[K + "last_signature"] = signature
render_machine(config, traces, demo=demo, autoplay=autoplay)
if traces and not demo:
    csv_button(
        "Traza (CSV)",
        lambda: trace_table(traces),
        "traza_enigma",
        icon=":material/route:",
    )
