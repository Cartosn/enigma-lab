"""El informe: sus cifras salen de los resultados y sus figuras se dibujan."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from enigma_lab import informe
from enigma_lab.figuras import report_figures, slide_figures

MACRO = re.compile(r"\\(EL[A-Za-z]+)")


def test_every_number_in_the_report_comes_from_a_macro() -> None:
    """Cada \\EL… que usa informe.tex existe en numbers.tex (generado desde los resultados)."""
    used = set(MACRO.findall(informe.SOURCE.read_text(encoding="utf-8")))
    generated = set(informe.macros())
    assert used, "el informe no usa ninguna cifra"
    assert used <= generated, sorted(used - generated)


def test_macros_are_the_presentation_figures() -> None:
    values = informe.macros()
    assert values["ELbarrido"] == "1.054.560"
    assert values["ELbitsSinAnillos"] == "67,11"
    assert values["ELbitsBarrido"] == "20,01"
    assert values["ELfraccionPlugboard"] == "70,2~\\%"
    assert values["ELperiodo"] == "16.900" and values["ELfueraCiclo"] == "676"
    assert values["ELwaldProfundidad"] == "929" and values["ELwaldAzar"] == "1.062"
    assert values["ELturingCero"] == "820" and values["ELturingTres"] == "0,04"


def test_macros_of_the_course_connections() -> None:
    """Las cifras nuevas del contexto en el curso salen del código, como en las diapositivas."""
    values = informe.macros()
    assert values["ELcolaUno"] == "650" and values["ELcolaDos"] == "26"
    assert values["ELcolisiones"] == "650"
    assert values["ELcumpleanos"] == "157" and values["ELcumpleanosP"] == "50,28~\\%"
    assert values["ELanosMilMaquinas"] == "5,04" and values["ELporLazo"] == "26"
    assert values["ELinvoluciones"] == "$\\mathrm{7{,}9}\\times10^{12}$"
    assert values["ELpermutaciones"] == "$\\mathrm{4}\\times10^{26}$"


def test_tex_escapes_spanish_number_format() -> None:
    assert informe.tex("60,1 %") == "60,1~\\%"
    assert informe.tex("−0,093") == "\\ensuremath{-}0,093"
    assert informe.sci("158962555217826360000") == "$\\mathrm{1{,}59}\\times10^{20}$"


def test_numbers_tex_defines_one_command_per_figure() -> None:
    text = informe.numbers_tex({"ELuno": "1", "ELdos": "2,5~\\%"})
    assert "\\newcommand{\\ELuno}{1}" in text
    assert "\\newcommand{\\ELdos}{2,5~\\%}" in text
    assert text.startswith("% Generado por")


def test_page_count_reads_the_tex_log(tmp_path: Path) -> None:
    log = tmp_path / "informe.log"
    assert informe.page_count(log) is None
    log.write_text("Output written on informe.xdv (3 pages, 97736 bytes).", encoding="utf-8")
    assert informe.page_count(log) == 3


def test_report_figures_are_vector_pdfs(tmp_path: Path) -> None:
    saved = report_figures(out_dir=tmp_path)
    assert sorted(p.name for p in saved) == sorted(
        f"{name}.{ext}" for name in ("e4_cribs", "e5_bombe", "e6_sprt") for ext in ("pdf", "png")
    )
    for path in saved:
        head = path.read_bytes()[:8]
        assert head.startswith(b"%PDF" if path.suffix == ".pdf" else b"\x89PNG")


@pytest.mark.lento
def test_slide_figures_are_16_9(tmp_path: Path) -> None:
    from PIL import Image

    from enigma_lab import paths

    saved = slide_figures(out_dir=tmp_path)
    pngs = [p for p in saved if p.suffix == ".png"]
    phase5 = sum(
        (paths.RESULTS / name).is_file()
        for name in ("e7_rejewski_trafico.parquet", "e8_coa_mensajes.parquet")
    )
    assert len(pngs) == 5 + phase5
    for path in pngs:
        width, height = Image.open(path).size
        assert 1.6 < width / height < 2.0, path.name
