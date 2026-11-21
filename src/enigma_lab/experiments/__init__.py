"""Experimentos E1 a E8 (spec, sección 7).

Cada experimento es un módulo ``eN_*.py`` con ``run(params, seed) -> DataFrame``,
``summary(df) -> dict`` y ``figure(df, theme)``. Se corren con

    python -m enigma_lab.experiments e1 --mode completo --seed 2026

y guardan ``results/eN_*.parquet``, sus figuras y sus cifras en ``results/summary.json``.
"""

EXPERIMENTS = {
    "e1": "enigma_lab.experiments.e1_validation",
}
"""Experimentos disponibles, por identificador (crecen con cada fase)."""
