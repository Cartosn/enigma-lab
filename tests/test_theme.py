"""Tema «Bletchley nocturno»: colores del spec, contraste y plantillas."""

from __future__ import annotations

import io

import pytest

from enigma_lab.viz import theme


def test_tokens_match_spec() -> None:
    """Los colores de la sección 8.1 del spec, tal cual."""
    d = theme.DARK
    assert (d.background, d.surface, d.border) == ("#0F1216", "#171B21", "#2A3038")
    assert (d.text, d.text_muted) == ("#E8E6E3", "#9AA3AD")
    assert (d.accent, d.accent_2, d.error, d.success) == (
        "#F2B134",
        "#4FB3BF",
        "#E5534B",
        "#57AB5A",
    )


def test_categorical_is_okabe_ito() -> None:
    okabe_ito = {"#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7"}
    assert set(theme.CATEGORICAL) == okabe_ito
    assert len(theme.CATEGORICAL) == len(okabe_ito)


@pytest.mark.parametrize("tokens", [theme.DARK, theme.PRINT], ids=["oscuro", "impreso"])
def test_first_three_series_contrast(tokens: theme.Tokens) -> None:
    """Las tres primeras series se distinguen del fondo con al menos 3:1 en ambos temas."""
    for color in theme.CATEGORICAL[:3]:
        assert theme.contrast_ratio(color, tokens.background) >= 3


@pytest.mark.parametrize(
    "ramp", [theme.SEQUENTIAL_DARK, theme.SEQUENTIAL_PRINT], ids=["oscura", "impresa"]
)
def test_sequential_ramps_are_monotone(ramp: tuple[str, ...]) -> None:
    lum = [theme.relative_luminance(c) for c in ramp]
    assert lum == sorted(lum) or lum == sorted(lum, reverse=True)


def test_text_contrast() -> None:
    """Texto principal y secundario legibles (WCAG AA, 4,5:1) sobre fondo y superficie."""
    for tokens in (theme.DARK, theme.PRINT):
        for bg in (tokens.background, tokens.surface):
            assert theme.contrast_ratio(tokens.text, bg) >= 4.5
            assert theme.contrast_ratio(tokens.text_muted, bg) >= 4.5


def test_ink_on_fill() -> None:
    assert theme.ink_on("#0072B2") == "#FFFFFF"
    assert theme.ink_on("#F0E442") == "#111418"


def test_plotly_templates_registered() -> None:
    import plotly.graph_objects as go
    import plotly.io as pio

    theme.register_plotly_templates()
    assert {"enigma_dark", "enigma_dark_demo"} <= set(pio.templates)
    fig = go.Figure(go.Scatter(x=[1, 2], y=[3, 4]), layout={"template": "enigma_dark"})
    assert list(fig.layout.template.layout.colorway) == list(theme.CATEGORICAL)
    assert fig.layout.template.layout.separators == ",."
    demo = pio.templates["enigma_dark_demo"].layout
    assert demo.font.size == 22
    assert demo.xaxis.tickfont.size == 20  # nada bajo 20 px en el modo demo (spec 8.1)


@pytest.mark.parametrize("style", ["enigma_print", "enigma_slides"])
def test_matplotlib_styles_render(style: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib import font_manager

    with theme.mpl_style_context(style):
        fig, ax = plt.subplots()
        ax.plot([5, 10, 13], [0.82, 0.68, 0.60], marker="o")
        ax.set_title("Prueba del estilo: 60,1 % con 13 letras")
        for fmt in ("png", "svg", "pdf"):
            fig.savefig(io.BytesIO(), format=fmt)
        plt.close(fig)
    inter = font_manager.findfont(
        font_manager.FontProperties(family="Inter"), fallback_to_default=False
    )
    assert inter.endswith("Inter-Regular.ttf")


def test_unknown_style() -> None:
    with pytest.raises(ValueError):
        theme.mpl_style("comic_sans")
