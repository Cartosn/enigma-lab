"""Página Máquina y su animación: preajustes de la demo 1 y la regla de la traza."""

from __future__ import annotations

import json
import re

from streamlit.testing.v1 import AppTest

from enigma_lab import paths
from enigma_lab.core.machine import Enigma, EnigmaConfig
from enigma_lab.core.wiring import REFLECTORS, ROTORS
from ui.machine_view import COMPONENT, MAX_ANIMATED, machine_html, machine_payload

PAGE = paths.APP / "pages" / "maquina.py"


def _page() -> AppTest:
    return AppTest.from_file(str(PAGE), default_timeout=60).run()


def _output(app: AppTest) -> str:
    """El texto de salida: el bloque grande «el-result» (sin la lectura con la X como espacio)."""
    blocks = [m.value for m in app.markdown if 'class="el-result' in m.value]
    found = re.search(r'<div class="el-result[^"]*"[^>]*>(.*?)</div>', blocks[0])
    assert found is not None
    return found.group(1).strip()


def _click(app: AppTest, label: str) -> AppTest:
    button = next(b for b in app.button if b.label == label)
    return button.click().run()


def test_default_is_vector_bdzgo() -> None:
    app = _page()
    assert not app.exception
    assert _output(app) == "BDZGO"


def test_cover_preset_decrypts_slide_1() -> None:
    """Demo 1: «Portada» descifra en un clic el mensaje de la diapositiva 1."""
    app = _click(_page(), "Portada")
    assert not app.exception
    assert _output(app).replace(" ", "") == "ROMPERXENIGMAXCRIPTOGRAFIAXUNAL"


def test_historical_preset_decrypts_u264() -> None:
    app = _click(_page(), "Ejemplo histórico")
    assert not app.exception
    assert _output(app).replace(" ", "").startswith("VONVONJLOOKS")


def test_payload_is_the_python_trace() -> None:
    """La animación recibe exactamente la traza de Enigma.trace (spec, fase 1)."""
    config = EnigmaConfig.from_strings("I II III", positions="ADU")
    traces = Enigma(config).trace("AAAA")
    payload = machine_payload(config, traces)
    assert payload["letters"] == [t.to_dict() for t in traces]
    assert payload["start"] == "ADU"
    assert [letter["double_step"] for letter in payload["letters"]] == [False, False, True, False]
    html = machine_html(payload)
    embedded = html.split('<script id="payload" type="application/json">')[1].split("</script>")[0]
    assert json.loads(embedded) == json.loads(json.dumps(payload))


def test_long_texts_are_truncated_for_the_animation() -> None:
    config = EnigmaConfig.from_strings("I II III")
    traces = Enigma(config).trace("A" * (MAX_ANIMATED + 10))
    payload = machine_payload(config, traces)
    assert len(payload["letters"]) == MAX_ANIMATED
    assert payload["truncated"] and payload["total"] == MAX_ANIMATED + 10


def test_component_does_not_reimplement_enigma() -> None:
    """Regla clave (spec 3): el JavaScript no trae cableados; solo anima la traza."""
    template = COMPONENT.read_text(encoding="utf-8")
    for spec in ROTORS.values():
        assert spec.wiring not in template
    for wiring in REFLECTORS.values():
        assert wiring not in template


def test_random_key_respects_allowed_rotors() -> None:
    """Demo 2: si se acuerdan los rotores I, II y III, «Clave aleatoria» solo usa esos."""
    for _ in range(5):
        app = AppTest.from_file(str(PAGE), default_timeout=60)
        app.session_state["maq_allowed"] = ["I", "II", "III"]
        app.run()
        app = _click(app, "Clave aleatoria")
        assert not app.exception
        rotors = {app.session_state[f"maq_rotor_{i}"] for i in range(3)}
        assert rotors == {"I", "II", "III"}


def test_demo_mode_keeps_only_the_demo_presets() -> None:
    """Modo demo: los preajustes de la demo 1 con su nombre completo y la clave oculta."""
    app = AppTest.from_file(str(PAGE), default_timeout=60)
    app.session_state["demo_mode"] = True
    app.run()
    assert not app.exception
    assert [b.label for b in app.button] == ["Vector BDZGO", "Portada"]
    assert not [e for e in app.expander if e.label == "¿Qué estoy viendo?"]
    app = _click(app, "Portada")
    assert _output(app).replace(" ", "") == "ROMPERXENIGMAXCRIPTOGRAFIAXUNAL"
    text = " ".join(m.value for m in app.markdown)
    assert "ROMPER ENIGMA CRIPTOGRAFIA UNAL" in text


def test_trace_table_has_one_row_per_letter() -> None:
    from ui.machine_view import trace_table

    config = EnigmaConfig.from_strings("I II III")
    table = trace_table(Enigma(config).trace("AAAAA"))
    assert list(table["lampara"]) == list("BDZGO")
    assert table["camino"].iloc[0] == "A → A → C → D → F → S → S → E → B → B → B"
