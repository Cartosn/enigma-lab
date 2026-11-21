"""Experimentos E2 a E4 (con pocos casos) y el resumen para la presentación."""

from __future__ import annotations

import json
import shutil

import pytest

from enigma_lab import SEED, paths, resumen
from enigma_lab.experiments import e2_keyspace, e3_statistics, e4_cribs, e5_bombe

SMALL_E3 = {"n": 60, "lengths": [100, 300], "source": "muestra"}
SMALL_E4 = {"n": 300, "lengths": [5, 13, 30], "message_length": 250, "source": "muestra"}
SMALL_E5 = {
    "letters": [12],
    "loops": [2, 3],
    "n": 4,
    "robust_letters": [12],
    "robust_n": 2,
    "batch": 100_000,
    "max_candidates": 2_000_000,
    "source": "muestra",
}


def test_e2_matches_section_52() -> None:
    df = e2_keyspace.run()
    plug = df[df["tabla"] == "plugboard"]
    assert plug.loc[plug["opciones"].map(int).idxmax(), "cables"] == 11
    figures = e2_keyspace.summary(df)
    assert figures["total_sin_anillos"] == "158962555217826360000"
    assert round(figures["bits_barrido"], 2) == 20.01


def test_e3_cipher_ic_falls_to_one_over_26() -> None:
    df, pairs = e3_statistics.run_with_pairs(SMALL_E3, SEED)
    table = e3_statistics.by_condition(df)
    german = table[table["idioma"] == "aleman"]
    assert (german["ic_plano"] > 0.065).all()
    assert (abs(german["ic_cifrado"] - 1 / 26) < 0.003).all()
    assert df["puntos_fijos"].sum() == 0
    assert pairs.trace() == 0


def test_e4_random_text_follows_theory() -> None:
    df = e4_cribs.run(SMALL_E4, SEED)
    assert df["verdadera_sobrevive"].all()
    table = e4_cribs.aggregate(df, "muestra")
    random_text = table[table["texto"] == "aleatorio"]
    assert (abs(random_text["p"] - random_text["teorico"]) < 0.01).all()
    german = table[table["texto"] == "aleman"]
    assert (german["teorico_kappa"] >= german["teorico"]).all()


def test_e5_bombe_small() -> None:
    df = e5_bombe.run(SMALL_E5, SEED)
    bletchley = df[df["modo"] == "bletchley"]
    # Sin vuelta del central en el tramo, el modo Bletchley siempre da la parada verdadera.
    assert bletchley.loc[~bletchley["vuelta"], "verdadera"].all()
    # El diagonal board nunca agrega paradas: mismo menú, mismas uniones y algunas más.
    on = bletchley[bletchley["diagonal"]].reset_index(drop=True)
    off = bletchley[~bletchley["diagonal"]].reset_index(drop=True)
    assert (off["paradas"] >= on["paradas"]).all()
    table = e5_bombe.aggregate(df)
    expected = {"letras", "lazos", "diagonal", "modo", "n_menus", "paradas_media", "ic_bajo"}
    assert expected | {"ic_alto", "exito", "s_por_orden"} <= set(table.columns)
    assert e5_bombe.turing_value(12, 3) == (0.04, "")


def test_turing_table_is_complete() -> None:
    table = e5_bombe.turing_table()
    assert len(table) == 36 and set(table["letras"]) == set(range(8, 17))
    assert e5_bombe.turing_value(12, 0) == (820.0, "")
    assert e5_bombe.turing_value(16, 3) == (0.01, "<")


@pytest.mark.skipif(not (paths.RESULTS / "summary.json").is_file(), reason="sin resultados")
def test_resumen_builds_from_saved_results(tmp_path) -> None:  # type: ignore[no-untyped-def]
    for item in paths.RESULTS.glob("*.parquet"):
        shutil.copy(item, tmp_path / item.name)
    shutil.copy(paths.RESULTS / "summary.json", tmp_path / "summary.json")
    out = resumen.main(tmp_path)
    text = (out / "RESUMEN.md").read_text(encoding="utf-8")
    assert "## 1. Por diapositiva de resultados" in text and "## 4. Discrepancias" in text
    data = json.loads((out / "cifras.json").read_text(encoding="utf-8"))
    computed = [c for c in data["cifras"] if c["obtenido"] is not None]
    assert computed and all(c["coincide"] for c in computed)
    if (tmp_path / "e4_cribs.parquet").is_file():
        header = (out / "r2_cribs.csv").read_text(encoding="utf-8").splitlines()[0]
        assert header.startswith("L,texto,n,sobreviven,p,ic_bajo,ic_alto,teorico")
    if (tmp_path / "e5_bombe.parquet").is_file():
        header = (out / "r3_bombe.csv").read_text(encoding="utf-8").splitlines()[0]
        assert header.startswith(
            "letras,lazos,diagonal,modo,n_menus,paradas_media,ic_bajo,ic_alto,exito,s_por_orden"
        )
        assert "### Diapositiva 16 · Bombe (E5)" in text
