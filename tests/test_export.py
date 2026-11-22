"""Spec 8.3: todo gráfico se puede exportar; los datos salen de la propia figura."""

from __future__ import annotations

import numpy as np
import plotly.graph_objects as go

from enigma_lab.viz.plotly_figs import figure_table, pair_heatmap, plugboard_curve


def test_scatter_and_bars_become_long_rows() -> None:
    fig = go.Figure()
    fig.add_scatter(x=[1, 2, 3], y=[0.5, 0.25, 0.125], name="medido")
    fig.add_bar(x=["A", "B"], y=[3, 4])
    table = figure_table(fig)
    assert list(table.columns) == ["serie", "x", "y"]
    assert len(table) == 5
    assert table.loc[table["serie"] == "medido", "y"].tolist() == [0.5, 0.25, 0.125]
    assert set(table["serie"]) == {"medido", "serie 2"}


def test_error_bars_are_exported() -> None:
    fig = go.Figure(go.Scatter(x=[8, 12], y=[700.0, 26.0], error_y={"array": [5.0, 1.2]}))
    table = figure_table(fig)
    assert table["error_y"].tolist() == [5.0, 1.2]


def test_heatmap_gives_one_row_per_cell() -> None:
    matrix = np.arange(26 * 26).reshape(26, 26)
    table = figure_table(pair_heatmap(matrix))
    assert len(table) == 26 * 26
    cell = table[(table["y"] == "B") & (table["x"] == "C")]
    assert cell["z"].item() == matrix[1, 2]


def test_app_chart_exports_its_numbers() -> None:
    """La curva N(k) de la página Espacio de claves: 14 puntos, con N(11) como máximo."""
    table = figure_table(plugboard_curve(10))
    assert len(table) == 14
    assert table.loc[table["y"].idxmax(), "x"] == 11


def test_figure_downloads_are_valid_png_and_svg() -> None:
    """Lo que entrega una descarga diferida de la página Experimentos (figura de E2)."""
    from enigma_lab.experiments import e2_keyspace
    from ui.charts import csv_bytes, figure_bytes

    table = e2_keyspace.run()
    png = figure_bytes(lambda: e2_keyspace.figure(table), "png")
    svg = figure_bytes(lambda: e2_keyspace.figure(table), "svg")
    assert png.startswith(b"\x89PNG")
    assert b"<svg" in svg[:500]
    assert csv_bytes(table).decode("utf-8").startswith("tabla,modelo,componente")


def test_saved_results_download_the_saved_figure(tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Con los resultados guardados se baja la figura de ``results/figures/`` sin dibujarla.

    Dibujar la de E4 pediría el corpus completo, que no está en Docker ni en un clon sin
    ``make corpus`` (D-071). Si el archivo guardado no existe, la figura se dibuja.
    """
    from enigma_lab import paths
    from enigma_lab.experiments import e2_keyspace
    from ui.charts import figure_data

    def never() -> None:
        raise AssertionError("con la figura guardada no se dibuja nada")

    saved = paths.FIGURES / "e4_cribs"
    png = figure_data(never, "png", saved)
    assert png == (paths.FIGURES / "e4_cribs.png").read_bytes()
    assert png.startswith(b"\x89PNG")
    assert b"<svg" in figure_data(never, "svg", saved)[:500]
    table = e2_keyspace.run()
    drawn = figure_data(lambda: e2_keyspace.figure(table), "png", tmp_path / "no_existe")
    assert drawn.startswith(b"\x89PNG")
