"""Experimentos E2 a E6 (con pocos casos) y el resumen para la presentación."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import numpy as np
import pytest

from enigma_lab import SEED, paths, resumen
from enigma_lab.experiments import (
    e2_keyspace,
    e3_statistics,
    e4_cribs,
    e5_bombe,
    e6_banburismus,
    e7_rejewski,
    e8_coa,
)
from enigma_lab.experiments.common import output_dir

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
SMALL_E6 = {
    "n": 60,
    "max_letters": 3_000,
    "overlaps": [50, 200],
    "alphas": [0.05, 0.01],
    "corpus": "muestra",
    "trajectories": 3,
    "trajectory_letters": 500,
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


def test_e6_banburismus_small() -> None:
    df, paths_df = e6_banburismus.run_with_trajectories(SMALL_E6, SEED)
    # 1 puntuación con tasa 1/17 y 4 con alemán, 60 pares y 2 hipótesis.
    assert len(df) == 5 * 60 * 2
    table = e6_banburismus.aggregate(df, "muestra")
    assert list(table.columns[:8]) == resumen.R4_COLUMNS
    assert len(table) == 5 * 2 * 2 * 3  # combinaciones × α × hipótesis × solapamientos
    longest = table[(table["solapamiento"] == 3_000) & np.isclose(table["alfa"], 0.01)]
    assert (longest["sin_decidir"] < 0.05).all()
    german = longest[(longest["fuente"] == "aleman") & (longest["hipotesis"] == "profundidad")]
    assert (german["aciertos"] > 0.9).all() and (german["auc"] > 0.99).all()
    wald = longest[longest["fuente"] == "tasa_1_17"].set_index("hipotesis")["wald"]
    assert round(wald["profundidad"]) == 929 and round(wald["azar"]) == 1062
    roc = e6_banburismus.roc_table(df)
    assert set(roc["solapamiento"]) == {50, 200, 3_000}
    assert ((roc["tpr"] >= 0) & (roc["tpr"] <= 1)).all()
    assert set(paths_df["hipotesis"]) == {"profundidad", "azar"}
    figures = e6_banburismus.summary(df, SMALL_E6)
    assert figures["tasas"]["corpus_x"] > figures["tasas"]["turing"]
    assert set(figures["simulacion"]) == {
        "tasa_1_17/letras_1_17",
        "aleman/letras_1_17",
        "aleman/letras",
        "aleman/trigramas",
        "aleman/tetragramas",
    }


def test_e6_auc_matches_mann_whitney() -> None:
    from scipy.stats import mannwhitneyu

    rng = np.random.default_rng(SEED)
    depth, chance = rng.normal(1, 1, 300), rng.normal(0, 1, 400)
    u = mannwhitneyu(depth, chance).statistic
    assert e6_banburismus.auc(depth, chance) == pytest.approx(u / (300 * 400))
    fpr, tpr = e6_banburismus.roc_points(depth, chance)
    assert fpr[0] == tpr[0] == 0 and fpr[-1] == tpr[-1] == 1
    assert np.trapezoid(tpr, fpr) == pytest.approx(e6_banburismus.auc(depth, chance))


def test_e7_catalog_and_traffic_small() -> None:
    """El catálogo exacto frente a Kuhl y 40 días de tráfico, que concuerdan con la teoría."""
    df = e7_rejewski.run()
    assert df["configuraciones"].sum() == 105_456
    assert df.loc[df["tamano"] == 1, "kuhl"].item() == 11_466
    params = {"days": 40, "messages": 600}
    days = e7_rejewski.run_traffic(params, SEED)
    figures = e7_rejewski.summary(df, days, params)
    catalog = figures["catalogo"]
    assert catalog["kuhl"]["caracteristicas_distintas"]["kuhl"] == 21_230
    assert catalog["kuhl_hasta_10_tabla"] == 19_604
    assert figures["vuelta"]["posiciones"] == 176
    levels = figures["trafico"]["por_nivel"]
    assert levels["caracteristica"]["dia"][0] <= levels["permutacion"]["dia"][0]
    assert levels["permutacion"]["dia"][0] < levels["eliminacion"]["dia"][0]
    assert levels["todas"]["teoria_producto"] == pytest.approx(100.2149, abs=1e-3)
    # El catálogo encuentra el día si y solo si el central no se mueve durante el indicador.
    assert (days["encontrada"] == ~days["vuelta"]).mean() > 0.9


def test_e8_attack_small() -> None:
    params = {
        "lengths": [600],
        "cables": [6],
        "n": 2,
        "rotors": ["I", "II", "III"],
        "top1": 100,
        "top2": 10,
        "source": "muestra",
    }
    df = e8_coa.run(params, SEED)
    assert len(df) == 2 and df["oraculo_exito"].all()
    table = e8_coa.aggregate(df)
    expected = {"L", "cables", "n", "exito", "ic_bajo", "ic_alto", "fase1", "oraculo"}
    assert expected <= set(table.columns)
    figures = e8_coa.summary(df, params)
    assert figures["ubicaciones_fase1"] == 6 * 17_576
    assert figures["referencias"]["unicidad_letras"] == 23


def test_e8_figure_with_cells_without_success() -> None:
    """La figura de E8 se dibuja aunque una celda no tenga éxitos (bigotes de Wilson de 0)."""
    import matplotlib.pyplot as plt
    import pandas as pd

    rows = []
    for length, hits in ((50, 0), (200, 3), (800, 8)):
        for k in range(8):
            rows.append(
                {
                    "L": length,
                    "cables": 6,
                    "exito": k < hits,
                    "aciertos": 1.0 if k < hits else 0.04,
                    "fase1_encontrada": k < hits,
                    "fase1_puesto": 0 if k < hits else 5_000,
                    "fase1_puesto_anillos_verdaderos": 0,
                    "top1": 200,
                    "oraculo_exito": True,
                    "oraculo_e_exito": True,
                    "segundos": 1.0,
                    "segundos_fase1": 0.5,
                }
            )
    fig = e8_coa.figure(pd.DataFrame(rows))
    plt.close(fig)


def test_e8_logistic_recovers_a_known_curve() -> None:
    """La regresión logística de E8 recupera L₅₀ de datos simulados con una curva conocida."""
    rng = np.random.default_rng(SEED)
    lengths = np.repeat([50, 100, 200, 400, 800], 200)
    true_l50 = 200.0
    p = 1 / (1 + np.exp(-4 * (np.log10(lengths) - np.log10(true_l50))))
    import pandas as pd

    cables = np.where(np.arange(len(lengths)) % 2, 6, 10)  # dos niveles, misma curva: β₂ ≈ 0
    df = pd.DataFrame({"L": lengths, "cables": cables, "exito": rng.random(len(lengths)) < p})
    fit = e8_coa.logistic(df)
    assert fit is not None
    low, high = fit["l50"]["6"]["ic"]
    assert low < true_l50 < high


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
    if (tmp_path / "e6_banburismus.parquet").is_file():
        header = (out / "r4_banburismus.csv").read_text(encoding="utf-8").splitlines()[0]
        assert header.startswith(
            "puntuacion,solapamiento,n,aciertos,letras_media,ic_bajo,ic_alto,auc"
        )
        assert (out / "r4_roc.csv").is_file() and (out / "r4_trayectorias.csv").is_file()
        assert "La diferencia con Wald es el sobrepaso" in text


def test_rapid_mode_saves_apart(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """El modo rápido guarda en results/rapido/ y no pisa la corrida completa (D-075)."""
    monkeypatch.setattr(paths, "RESULTS", tmp_path)
    assert output_dir("completo") == tmp_path
    assert output_dir("rapido") == tmp_path / "rapido"
    e2_keyspace.main("rapido")
    assert (tmp_path / "rapido" / "e2_espacio_de_claves.parquet").is_file()
    assert json.loads((tmp_path / "rapido" / "summary.json").read_text("utf-8"))["e2"]
    assert not (tmp_path / "summary.json").exists()
