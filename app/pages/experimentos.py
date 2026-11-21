"""Página Experimentos: una pestaña por experimento (spec 8.2, punto 7).

Por defecto muestra los resultados guardados en ``results/`` (modo completo, los mismos
de ``RESUMEN.md``). «Correr ahora» repite el experimento en modo rápido dentro de la
sesión, sin tocar los resultados guardados.
"""

from __future__ import annotations

import io
from typing import Any

import pandas as pd
import streamlit as st

from enigma_lab import SEED, paths
from enigma_lab.banburismus.sprt import exact_turing
from enigma_lab.experiments import (
    e1_validation,
    e2_keyspace,
    e3_statistics,
    e4_cribs,
    e5_bombe,
    e6_banburismus,
)
from enigma_lab.experiments.common import read_summary
from enigma_lab.viz import plotly_figs
from enigma_lab.viz.numfmt import fmt_dec, fmt_int, fmt_pct
from ui.layout import is_demo, what_am_i_seeing

INFO: dict[str, dict[str, str]] = {
    "e1": {
        "tab": "E1 · Validación",
        "pregunta": "¿El simulador es correcto?",
        "metodo": "Los vectores publicados de la sección 6.1, 10.000 claves y mensajes "
        "aleatorios comparados con py-enigma, y 2.000 claves para las propiedades "
        "(involución, sin puntos fijos, lotes = escalar).",
        "referencia": "Meta del spec: 100 % de coincidencia con py-enigma.",
    },
    "e2": {
        "tab": "E2 · Espacio de claves",
        "pregunta": "¿Cuánto aporta cada componente de la clave?",
        "metodo": "Conteo exacto con enteros de Python: órdenes, posiciones, anillos y "
        "plugboard N(k) para 0 a 13 cables.",
        "referencia": "Spec 5.2: 67,11 bits sin anillos; máximo de N(k) en 11 cables.",
    },
    "e3": {
        "tab": "E3 · Estadística",
        "pregunta": "¿Qué estadística se filtra y cuál no?",
        "metodo": "Fragmentos reales en alemán y español, de varias longitudes, cada uno con su "
        "clave aleatoria: IC, prueba χ² y matriz plano × cifrado.",
        "referencia": "IC del alemán ≈ 0,0758 (Pommerening) frente a 1/26 ≈ 0,0385.",
    },
    "e4": {
        "tab": "E4 · Cribs",
        "pregunta": "¿Cuántas posiciones descarta un crib?",
        "metodo": "Mensajes de 250 letras (aleatorios o alemán real), crib de L letras en una "
        "posición al azar: qué fracción de las alineaciones falsas sobrevive.",
        "referencia": "Teoría (25/26)^L; piloto: 60,0 % con L = 13.",
    },
    "e5": {
        "tab": "E5 · Bombe",
        "pregunta": "¿Cuántas paradas falsas deja la Bombe?",
        "metodo": "Menús conexos de cribs alemanes reales, por letras (vértices) y lazos, con "
        "clave aleatoria: se barre el orden verdadero en modo Bletchley con y sin diagonal "
        "board, y en modo robusto un subconjunto. Paradas falsas, éxito y tiempo por orden.",
        "referencia": "Tabla de Turing (Wikipedia «Bombe»): con 12 letras, 820, 31, 1,2 y 0,04 "
        "paradas por orden con 0, 1, 2 y 3 lazos.",
    },
    "e6": {
        "tab": "E6 · Banburismus",
        "pregunta": "¿Cuánto solapamiento necesita el Banburismus?",
        "metodo": "Pares de mensajes en profundidad cifrados con la máquina real (misma clave "
        "diaria, claves de mensaje que solo difieren en el rotor derecho), con texto de tasa 1/17 "
        "o alemán del corpus. El SPRT de Wald con letras sueltas o multigramas, en el "
        "desplazamiento verdadero y en uno falso: aciertos, letras hasta decidir y curva ROC.",
        "referencia": "Aproximación de Wald con letras sueltas y tasas 1/17 y 1/26 (Wikipedia "
        "«Banburismus»): 929 letras en profundidad y 1.062 al azar.",
    },
}
PENDING = {
    "e7": ("E7 · Rejewski", 5),
    "e8": ("E8 · Ataque moderno", 5),
}


def _saved(name: str) -> pd.DataFrame | None:
    path = paths.RESULTS / f"{name}.parquet"
    return pd.read_parquet(path) if path.is_file() else None


@st.cache_data(show_spinner=False)
def _run_quick(experiment: str) -> dict[str, Any]:
    """Corre un experimento en modo rápido, en memoria."""
    if experiment == "e1":
        return {
            "df": e1_validation.run(e1_validation.PARAMS["rapido"], SEED),
            "vectores": e1_validation.vectors_table(),
        }
    if experiment == "e3":
        df, pairs = e3_statistics.run_with_pairs(e3_statistics.PARAMS["rapido"], SEED)
        return {"df": df, "pares": pairs}
    if experiment == "e4":
        return {"df": e4_cribs.run(e4_cribs.PARAMS["rapido"], SEED)}
    if experiment == "e5":
        return {"df": e5_bombe.run(e5_bombe.PARAMS["rapido"], SEED)}
    if experiment == "e6":
        df, paths = e6_banburismus.run_with_trajectories(e6_banburismus.PARAMS["rapido"], SEED)
        return {"df": df, "trayectorias": paths}
    return {"df": e2_keyspace.run()}


def _figure_bytes(fig: Any) -> tuple[bytes, bytes]:
    import matplotlib.pyplot as plt

    out = []
    for fmt in ("png", "svg"):
        buffer = io.BytesIO()
        fig.savefig(buffer, format=fmt)
        out.append(buffer.getvalue())
    plt.close(fig)
    return out[0], out[1]


def _downloads(name: str, table: pd.DataFrame, fig: Any) -> None:
    png, svg = _figure_bytes(fig)
    cols = st.columns(3)
    cols[0].download_button(
        "Datos (CSV)",
        table.to_csv(index=False).encode("utf-8"),
        f"{name}.csv",
        "text/csv",
        icon=":material/table:",
        key=f"{name}_csv",
    )
    cols[1].download_button(
        "Figura (PNG)", png, f"{name}.png", "image/png", icon=":material/image:", key=f"{name}_png"
    )
    cols[2].download_button(
        "Figura (SVG)",
        svg,
        f"{name}.svg",
        "image/svg+xml",
        icon=":material/draw:",
        key=f"{name}_svg",
    )


def _source(experiment: str) -> bool:
    """¿Correr ahora en modo rápido? (si no, resultados guardados)."""
    choice = st.radio(
        "Resultados",
        ["Guardados (modo completo)", "Correr ahora (modo rápido)"],
        horizontal=True,
        key=f"{experiment}_source",
    )
    return choice.startswith("Correr")


demo = is_demo()
st.title("Experimentos")
st.caption("Enigma Lab › Experimentos")
what_am_i_seeing(
    "Cada pestaña es un experimento: su pregunta, su método y su referencia publicada.",
    "Por defecto se muestran los resultados guardados (modo completo, semilla 2026), los "
    "mismos que alimentan el resumen para las diapositivas.",
    "«Correr ahora» repite el experimento en modo rápido dentro de la app, sin tocar lo guardado.",
    "Cada gráfico se puede descargar (PNG o SVG) junto con sus datos (CSV).",
)
summary = read_summary()
tabs = st.tabs([info["tab"] for info in INFO.values()] + [t for t, _ in PENDING.values()])

for tab, (experiment, info) in zip(tabs, INFO.items(), strict=False):
    with tab:
        st.markdown(
            f"**Pregunta.** {info['pregunta']}  \n**Método.** {info['metodo']}  \n"
            f"**Referencia.** {info['referencia']}"
        )
        run_now = _source(experiment)
        run_info = summary.get(experiment, {}).get("corrida")
        if not run_now and run_info:
            st.caption(
                f"Corrida guardada: modo {run_info['modo']}, semilla {run_info['semilla']}, "
                f"{run_info['fecha']}, commit {run_info['commit']}."
            )
        quick = _run_quick(experiment) if run_now else None

        if experiment == "e1":
            df = quick["df"] if quick else _saved("e1_validacion")
            vectors = quick["vectores"] if quick else _saved("e1_vectores")
            if df is None or vectors is None:
                st.info("Aún no hay resultados guardados: corre  make reproduce.")
                continue
            figures = e1_validation.summary(df, vectors)
            low, high = figures["pyenigma_ic95"]
            cols = st.columns(3)
            cols[0].metric(
                "Coinciden con py-enigma",
                f"{fmt_int(figures['pyenigma_coincidencias'])} de "
                f"{fmt_int(figures['pyenigma_casos'])}",
                f"IC 95 %: {fmt_pct(low, 2)}–{fmt_pct(high, 2)}",
                delta_color="off",
                delta_arrow="off",
            )
            cols[1].metric(
                "Puntos fijos",
                fmt_int(figures["puntos_fijos"]),
                f"en {fmt_int(figures['propiedades_letras'] + figures['pyenigma_letras'])} letras",
                delta_color="off",
                delta_arrow="off",
            )
            cols[2].metric(
                "Vectores de 6.1", f"{figures['vectores_ok']} de {figures['vectores_total']}"
            )
            st.dataframe(vectors, hide_index=True, width="stretch")
            _downloads("e1_vectores", vectors, e1_validation.figure(vectors))

        elif experiment == "e2":
            df = quick["df"] if quick else _saved("e2_espacio_de_claves")
            if df is None:
                st.info("Aún no hay resultados guardados: corre  make reproduce.")
                continue
            from enigma_lab.core import keyspace as ks

            cols = st.columns(2)
            cols[0].plotly_chart(
                plotly_figs.keyspace_bits(ks.keyspace(ks.ENIGMA_I), "Enigma I", demo),
                theme=None,
                config=plotly_figs.plotly_config(),
                width="stretch",
            )
            cols[1].plotly_chart(
                plotly_figs.plugboard_curve(ks.DEFAULT_CABLES, demo),
                theme=None,
                config=plotly_figs.plotly_config(),
                width="stretch",
            )
            st.dataframe(df, hide_index=True, width="stretch")
            _downloads("e2_espacio_de_claves", df, e2_keyspace.figure(df))

        elif experiment == "e3":
            df = quick["df"] if quick else _saved("e3_estadistica")
            pairs_df = None if quick else _saved("e3_pares")
            if df is None:
                st.info("Aún no hay resultados guardados: corre  make reproduce.")
                continue
            pairs = (
                quick["pares"]
                if quick
                else (
                    pairs_df.pivot(index="plano", columns="cifrado", values="n").to_numpy()
                    if pairs_df is not None
                    else None
                )
            )
            table = e3_statistics.by_condition(df)
            st.plotly_chart(
                plotly_figs.e3_ic(table, demo),
                theme=None,
                config=plotly_figs.plotly_config(),
                width="stretch",
            )
            if pairs is not None:
                st.plotly_chart(
                    plotly_figs.pair_heatmap(pairs, demo),
                    theme=None,
                    config=plotly_figs.plotly_config(),
                    width="stretch",
                )
            st.dataframe(table, hide_index=True, width="stretch")
            st.caption(
                f"N = {fmt_int(int(table['n'].iloc[0]))} mensajes por condición; "
                f"{fmt_int(int(df['puntos_fijos'].sum()))} puntos fijos en "
                f"{fmt_int(int(df['L'].sum()))} letras."
            )
            _downloads("e3_estadistica", table, e3_statistics.figure(df, pairs=pairs))

        elif experiment == "e4":
            df = quick["df"] if quick else _saved("e4_cribs_mensajes")
            if df is None:
                st.info("Aún no hay resultados guardados: corre  make reproduce.")
                continue
            source = "muestra" if quick else summary.get("e4", {}).get("fuente", "completo")
            table = e4_cribs.aggregate(df, source)
            st.plotly_chart(
                plotly_figs.e4_survival(table, demo),
                theme=None,
                config=plotly_figs.plotly_config(),
                width="stretch",
            )
            row = table[(table["texto"] == "aleman") & (table["L"] == 13)]
            if not row.empty:
                r = row.iloc[0]
                st.caption(
                    f"Alemán real, L = 13: sobrevive el {fmt_pct(r['p'])} (IC 95 % "
                    f"{fmt_pct(r['ic_bajo'])}–{fmt_pct(r['ic_alto'])}); (25/26)^13 = "
                    f"{fmt_pct(r['teorico'])} y la teoría con el IC del alemán da "
                    f"{fmt_pct(r['teorico_kappa'])}."
                )
            st.dataframe(table, hide_index=True, width="stretch")
            _downloads("e4_cribs", table, e4_cribs.figure(df, source=source))

        elif experiment == "e5":
            df = quick["df"] if quick else _saved("e5_bombe_menus")
            if df is None:
                st.info("Aún no hay resultados guardados: corre  make reproduce.")
                continue
            table = e5_bombe.aggregate(df)
            st.plotly_chart(
                plotly_figs.e5_vs_turing(table, demo),
                theme=None,
                config=plotly_figs.plotly_config(),
                width="stretch",
            )
            for diagonal in ("si", "no"):
                st.plotly_chart(
                    plotly_figs.e5_heatmap(table, diagonal, demo),
                    theme=None,
                    config=plotly_figs.plotly_config(),
                    width="stretch",
                )
            figures = e5_bombe.summary(df, e5_bombe.PARAMS["rapido" if quick else "completo"])
            robust = figures.get("robusto_tiempo_relativo")
            st.caption(
                f"Éxito del modo Bletchley: {fmt_pct(figures['exito_bletchley'])} (el central se "
                f"movió dentro del tramo en el {fmt_pct(figures['vuelta_frac'])} de los menús); "
                f"sin esa vuelta, {fmt_pct(figures['exito_bletchley_sin_vuelta'])}."
                + (
                    f" Modo robusto: éxito {fmt_pct(figures['exito_robusto'])}, "
                    f"{fmt_dec(robust, 1)} veces el tiempo y "
                    f"{fmt_dec(figures['robusto_paradas_relativas'], 1)} veces las paradas."
                    if robust
                    else ""
                )
            )
            st.dataframe(table, hide_index=True, width="stretch")
            _downloads("e5_bombe", table, e5_bombe.figure(df))

        elif experiment == "e6":
            df = quick["df"] if quick else _saved("e6_banburismus_pruebas")
            if df is None:
                st.info("Aún no hay resultados guardados: corre  make reproduce.")
                continue
            trajectories = quick["trayectorias"] if quick else _saved("e6_banburismus_trayectorias")
            corpus = "muestra" if quick else summary.get("e6", {}).get("corpus", "completo")
            saved_table = None if quick else _saved("e6_banburismus")
            table = saved_table if saved_table is not None else e6_banburismus.aggregate(df, corpus)
            st.plotly_chart(
                plotly_figs.e6_letters(table, demo),
                theme=None,
                config=plotly_figs.plotly_config(),
                width="stretch",
            )
            exact = {h: exact_turing(0.01, h == "profundidad") for h in ("profundidad", "azar")}
            st.caption(
                f"Cálculo exacto con tasa 1/17 (sin simulación): "
                f"{fmt_dec(exact['profundidad'].letters, 1)} letras en profundidad y "
                f"{fmt_dec(exact['azar'].letters, 1)} al azar. La diferencia con Wald es el "
                f"sobrepaso: arriba, el puntaje pasa el umbral por "
                f"{fmt_dec(exact['profundidad'].overshoot_upper, 2)} dB en promedio; abajo, por "
                f"{fmt_dec(exact['azar'].overshoot_lower, 3)} dB."
            )
            st.plotly_chart(
                plotly_figs.e6_identification(table, demo),
                theme=None,
                config=plotly_figs.plotly_config(),
                width="stretch",
            )
            mark = e6_banburismus.ROC_OVERLAP
            curves = []
            for text, keys in e6_banburismus.SOURCES.items():
                for key in keys:
                    group = df[(df["fuente"] == text) & (df["puntuacion"] == key)]
                    depth, chance = e6_banburismus.scores_at(group, mark)
                    fpr, tpr = e6_banburismus.roc_points(depth, chance)
                    label = e6_banburismus.SHORT_LABELS[e6_banburismus.combo(text, key)]
                    curves.append((label, fpr, tpr, e6_banburismus.auc(depth, chance)))
            st.plotly_chart(
                plotly_figs.roc_curves(curves, mark, demo),
                theme=None,
                config=plotly_figs.plotly_config(),
                width="stretch",
            )
            st.dataframe(table, hide_index=True, width="stretch")
            _downloads(
                "e6_banburismus",
                table,
                e6_banburismus.figure(df, trajectories=trajectories, corpus=corpus),
            )

for tab, (name, phase) in zip(tabs[len(INFO) :], PENDING.values(), strict=True):
    with tab:
        st.info(f"{name}: llega en la fase {phase}.", icon=":material/schedule:")

st.caption(
    "Las tablas muestran los datos tal como se descargan en CSV (con punto decimal); los "
    f"textos y gráficos usan coma decimal, por ejemplo {fmt_dec(0.0758, 4)}."
)
