"""El informe final (spec, sección 10): cifras, figuras y compilación del PDF.

``make report`` corre este módulo, que:

1. escribe ``report/numbers.tex``: una macro de LaTeX por cifra (``\\ELbarrido`` →
   1.054.560), tomada de ``results/summary.json`` y de los resultados guardados, con el
   formato español de la app. El informe no lleva ningún número escrito a mano;
2. dibuja las tres figuras del informe en ``report/figuras/`` (``enigma_lab.figuras``);
3. compila ``report/informe.tex`` con latexmk o Tectonic si están instalados, y comprueba
   que el PDF no pase de 3 páginas. Si no hay LaTeX, lo avisa: la carpeta ``report/``
   sirve tal cual para Overleaf.

Tectonic se busca en el PATH, en la variable de entorno ``TECTONIC`` y, en Windows, en la
carpeta de usuario ``%LOCALAPPDATA%\\Programs\\tectonic`` (D-053).
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from enigma_lab import paths
from enigma_lab.core import keyspace as ks
from enigma_lab.core.stepping import cycle_structure, notch_sets
from enigma_lab.experiments.common import read_summary
from enigma_lab.experiments.e5_bombe import turing_agreement
from enigma_lab.viz.numfmt import NBSP, fmt_dec, fmt_int, fmt_pct

REPORT = paths.ROOT / "report"
NUMBERS = REPORT / "numbers.tex"
SOURCE = REPORT / "informe.tex"
MAX_PAGES = 3

_TEX = {
    "%": r"\%",
    NBSP: "~",
    "−": r"\ensuremath{-}",
    "×": r"\ensuremath{\times}",
    "±": r"\ensuremath{\pm}",
    "≈": r"\ensuremath{\approx}",
}


def tex(text: str) -> str:
    """Un texto con formato español, seguro para LaTeX: «60,1 %» → «60,1~\\%»."""
    return "".join(_TEX.get(char, char) for char in text)


def sci(value: float | int | str, digits: int = 3) -> str:
    """Notación científica para LaTeX: 1,5896e20 → «$1{,}59\\times10^{20}$».

    Acepta el número como texto: ``summary.json`` guarda así los enteros enormes.
    """
    mantissa, exponent = f"{float(value):.{digits - 1}e}".split("e")
    return rf"$\mathrm{{{mantissa.replace('.', '{,}')}}}\times10^{{{int(exponent)}}}$"


def _short(value: float) -> str:
    """Los decimales justos, como en la presentación: 678 · 31 · 26,3 · 0,99 · 0,04."""
    if value >= 100:
        return fmt_int(round(value))
    text = fmt_dec(value, 1 if value >= 1 else 2)
    return text.rstrip("0").rstrip(",")


# ---------------------------------------------------------------- cifras


def _keyspace_macros(e2: dict[str, Any]) -> dict[str, str]:
    bits = e2["bits_por_componente"]
    return {
        "ELclavesSinAnillos": sci(e2["total_sin_anillos"]),
        "ELbitsSinAnillos": fmt_dec(e2["bits_sin_anillos"]),
        "ELclavesConAnillos": sci(e2["total_con_anillos"]),
        "ELbitsConAnillos": fmt_dec(e2["bits_con_anillos"]),
        "ELbitsOrden": fmt_dec(bits["Orden de rotores"]),
        "ELbitsPosiciones": fmt_dec(bits["Posiciones"]),
        "ELbitsAnillos": fmt_dec(bits["Anillos"]),
        "ELbitsPlugboard": fmt_dec(bits["Plugboard"]),
        "ELfraccionPlugboard": fmt_pct(e2["fraccion_plugboard"]),
        "ELbarrido": fmt_int(e2["barrido_bombe"]),
        "ELbitsBarrido": fmt_dec(e2["bits_barrido"]),
        "ELanosFuerzaBruta": fmt_int(round(e2["anos_a_1e9"])),
        "ELcablesMaximo": fmt_int(e2["cables_maximo"]),
        "ELcablesClave": fmt_int(ks.DEFAULT_CABLES),
    }


def _validation_macros(e1: dict[str, Any]) -> dict[str, str]:
    cycles, outside = cycle_structure(notch_sets(["Q", "E", "V"]))  # rotores I-II-III
    return {
        "ELvectoresOk": fmt_int(e1["vectores_ok"]),
        "ELvectoresTotal": fmt_int(e1["vectores_total"]),
        "ELpyenigmaCasos": fmt_int(e1["pyenigma_casos"]),
        "ELpyenigmaCoinciden": fmt_int(e1["pyenigma_coincidencias"]),
        "ELpyenigmaICbajo": fmt_pct(e1["pyenigma_ic95"][0], 2),
        "ELpyenigmaLetras": fmt_int(e1["pyenigma_letras"]),
        "ELpropiedadesClaves": fmt_int(e1["propiedades_claves"]),
        "ELpropiedadesLetras": fmt_int(e1["propiedades_letras"]),
        "ELpuntosFijos": fmt_int(e1["puntos_fijos"]),
        "ELinvolucion": fmt_int(e1["involucion_ok"]),
        "ELperiodo": fmt_int(max(cycles)),
        "ELfueraCiclo": fmt_int(outside),
    }


def _crib_macros(e4: dict[str, Any], e3: dict[str, Any]) -> dict[str, str]:
    random, german = e4["aleatorio"]["por_L"], e4["aleman"]["por_L"]
    r13, g13 = random["13"], german["13"]
    return {
        "ELcribN": fmt_int(e4["n_por_L"]),
        "ELcribLetras": fmt_int(e4["letras_por_mensaje"]),
        "ELsobreviveTrece": fmt_pct(r13["p"]),
        "ELsobreviveTreceBajo": fmt_pct(r13["ic"][0]),
        "ELsobreviveTreceAlto": fmt_pct(r13["ic"][1]),
        "ELteoriaTrece": fmt_pct(r13["teorico"]),
        "ELsobreviveCincuenta": fmt_pct(random["50"]["p"]),
        "ELsobreviveTreceAleman": fmt_pct(g13["p"]),
        "ELteoriaKappaTrece": fmt_pct(g13["teorico_kappa"]),
        "ELkappaAleman": fmt_dec(e4["kappa_aleman_x"], 4),
        "ELdentroICaleatorio": e4["aleatorio"]["teoria_25_26_dentro_del_ic"],
        "ELdentroICaleman": e4["aleman"]["teoria_25_26_dentro_del_ic"],
        "ELdentroICkappa": e4["aleman"]["teoria_kappa_dentro_del_ic"],
        "ELicCorpusAleman": fmt_dec(e3["aleman"]["ic_corpus"], 4),
        "ELicReferencia": fmt_dec(e3["ic_referencia_aleman"], 4),
        "ELicCifrado": fmt_dec(e3["aleman"]["ic_cifrado"][0], 4),
    }


def _bombe_macros(e5: dict[str, Any], table: pd.DataFrame) -> dict[str, str]:
    twelve = e5["doce_letras"]
    names = ("Cero", "Uno", "Dos", "Tres")
    macros = {}
    for k, name in enumerate(names):
        cell = twelve[str(k)]
        macros[f"ELparadas{name}"] = _short(cell["paradas"])
        macros[f"ELturing{name}"] = _short(cell["turing"])
        macros[f"ELsinDiagonal{name}"] = _short(cell["sin_diagonal"])
        macros[f"ELenSesenta{name}"] = _short(cell["en_60_ordenes"])
        macros[f"ELturingSesenta{name}"] = _short(cell["turing_en_60"])
    close, total = turing_agreement(table)
    macros |= {
        "ELmenusPorCelda": fmt_int(e5["n_por_celda"]),
        "ELmenus": fmt_int(e5["menus"]),
        "ELceldasCerca": fmt_int(close),
        "ELceldasTuring": fmt_int(total),
        "ELexitoBletchley": fmt_pct(e5["exito_bletchley"]),
        "ELexitoSinVuelta": fmt_pct(e5["exito_bletchley_sin_vuelta"]),
        "ELvuelta": fmt_pct(e5["vuelta_frac"]),
        "ELexitoRobusto": fmt_pct(e5["exito_robusto"]),
        "ELrobustoTiempo": fmt_dec(e5["robusto_tiempo_relativo"], 1),
        "ELrobustoParadas": fmt_dec(e5["robusto_paradas_relativas"], 1),
        "ELsegundosOrden": fmt_dec(e5["s_por_orden_bletchley"], 3),
        "ELsegundosOrdenRobusto": fmt_dec(e5["s_por_orden_robusto"], 2),
        "ELdiagonalFactor": fmt_int(round(twelve["1"]["sin_diagonal"] / twelve["1"]["paradas"])),
    }
    return macros


def _banburismus_macros(e6: dict[str, Any]) -> dict[str, str]:
    turing = e6["simulacion"]["tasa_1_17/letras_1_17"]
    german = e6["simulacion"]["aleman/letras_1_17"]
    trigrams = e6["simulacion"]["aleman/trigramas"]
    weights, gap = e6["pesos"], e6["brecha_wald"]["profundidad"]
    rate = e6["tasas"]["corpus_x"]
    return {
        "ELparesBanbu": fmt_int(e6["n_pares"]),
        "ELdecibanRepeticion": "+" + fmt_dec(weights["repeticion_db"], 3),
        "ELdecibanNoRepeticion": fmt_dec(weights["no_repeticion_db"], 3),
        "ELderivaProfundidad": "+" + fmt_dec(weights["por_letra_profundidad_db"], 4),
        "ELderivaAzar": fmt_dec(weights["por_letra_azar_db"], 4),
        "ELumbral": fmt_dec(weights["umbral_db"], 2),
        "ELwaldProfundidad": fmt_int(round(e6["wald"]["profundidad"])),
        "ELwaldAzar": fmt_int(round(e6["wald"]["azar"])),
        "ELexactoProfundidad": fmt_dec(e6["exacto"]["profundidad"]["letras"], 1),
        "ELexactoAzar": fmt_dec(e6["exacto"]["azar"]["letras"], 1),
        "ELsimProfundidad": fmt_int(round(turing["profundidad"]["letras"])),
        "ELsimProfundidadBajo": fmt_int(round(turing["profundidad"]["ic"][0])),
        "ELsimProfundidadAlto": fmt_int(round(turing["profundidad"]["ic"][1])),
        "ELsimAzar": fmt_int(round(turing["azar"]["letras"])),
        "ELsimAzarBajo": fmt_int(round(turing["azar"]["ic"][0])),
        "ELsimAzarAlto": fmt_int(round(turing["azar"]["ic"][1])),
        "ELsobrepasoArriba": fmt_dec(e6["exacto"]["profundidad"]["sobrepaso_arriba_db"], 2),
        "ELbrechaSobrepaso": fmt_dec(gap["sobrepaso_arriba"], 1),
        "ELbrechaTotal": fmt_dec(gap["total"], 1),
        "ELalemanLetrasProfundidad": fmt_int(round(german["profundidad"]["letras"])),
        "ELalemanTrigramasProfundidad": fmt_int(round(trigrams["profundidad"]["letras"])),
        "ELalemanTrigramasAzar": fmt_int(round(trigrams["azar"]["letras"])),
        "ELtasaCorpus": fmt_dec(rate, 4),
        "ELtasaCorpusInversa": fmt_dec(1 / rate, 1),
    }


def _demo_macros(bench: dict[str, Any] | None) -> dict[str, str]:
    """La demo 2 en la app (``make bench-demo``), con la configuración recomendada."""
    if not bench or not bench.get("recomendada"):
        missing = (
            "ELdemoExito",
            "ELdemoPnoventaycinco",
            "ELdemoCasos",
            "ELdemoLetras",
            "ELdemoNucleos",
        )
        return dict.fromkeys(missing, "—")
    chosen = next(c for c in bench["configuraciones"] if c["id"] == bench["recomendada"])
    return {
        "ELdemoExito": f"{fmt_int(chosen['exitos'])} de {fmt_int(chosen['n'])}",
        "ELdemoCasos": fmt_int(chosen["n"]),
        "ELdemoPnoventaycinco": fmt_dec(chosen["p95"], 1),
        "ELdemoLetras": fmt_int(bench["letras_mensaje"]),
        "ELdemoNucleos": fmt_int(bench["equipo"]["nucleos_logicos"]),
    }


REJEWSKI_MACROS = (
    "ELrejConfiguraciones",
    "ELrejCaracteristicas",
    "ELrejUnicas",
    "ELrejMayor",
    "ELkuhlCaracteristicas",
    "ELkuhlUnicas",
    "ELkuhlMayor",
    "ELrejDias",
    "ELrejTodas",
    "ELrejTodasTeoria",
    "ELrejPermutacion",
    "ELrejCaracteristicaMensajes",
    "ELrejEncontrada",
    "ELrejVuelta",
)
ATTACK_MACROS = (
    "ELataqueMensajes",
    "ELataqueN",
    "ELataqueUbicaciones",
    "ELataqueSegundos",
    "ELataqueLseis",
    "ELataqueSeisLargo",
    "ELataqueDiezLargo",
    "ELataqueLargo",
    "ELataqueOraculoCorto",
    "ELataqueOraculoECorto",
    "ELataqueCorto",
    "ELataqueDiezCorto",
)


def _rejewski_macros(e7: dict[str, Any] | None) -> dict[str, str]:
    """El catálogo de Rejewski frente a Kuhl y los mensajes de un día (E7)."""
    if not e7:
        return dict.fromkeys(REJEWSKI_MACROS, "—")
    cat, traffic = e7["catalogo"], e7["trafico"]
    kuhl, levels = cat["kuhl"], traffic["por_nivel"]
    return {
        "ELrejConfiguraciones": fmt_int(cat["configuraciones"]),
        "ELrejCaracteristicas": fmt_int(cat["caracteristicas_distintas"]),
        "ELrejUnicas": fmt_int(cat["caracteristicas_unicas"]),
        "ELrejMayor": fmt_int(cat["mayor_clase"]),
        "ELkuhlCaracteristicas": fmt_int(kuhl["caracteristicas_distintas"]["kuhl"]),
        "ELkuhlUnicas": fmt_int(kuhl["caracteristicas_unicas"]["kuhl"]),
        "ELkuhlMayor": fmt_int(kuhl["mayor_clase"]["kuhl"]),
        "ELrejDias": fmt_int(traffic["dias"]),
        "ELrejTodas": fmt_dec(levels["todas"]["dia"][0], 1),
        "ELrejTodasTeoria": fmt_dec(levels["todas"]["teoria_dia"], 1),
        "ELrejPermutacion": fmt_dec(levels["permutacion"]["dia"][0], 1),
        "ELrejCaracteristicaMensajes": fmt_dec(levels["caracteristica"]["dia"][0], 1),
        "ELrejEncontrada": fmt_pct(traffic["catalogo"]["encontrada"]),
        "ELrejVuelta": fmt_pct(e7["vuelta"]["fraccion"]),
    }


def _attack_macros(e8: dict[str, Any] | None) -> dict[str, str]:
    """El ataque moderno (E8): éxito en los extremos de longitud y con la ubicación dada."""
    if not e8:
        return dict.fromkeys(ATTACK_MACROS, "—")
    cells = e8["celdas"]
    lengths, cables = e8["longitudes"], e8["cables"]
    short, long_ = lengths[0], lengths[-1]
    probe = 100 if 100 in lengths else lengths[len(lengths) // 3]
    few, many = min(cables), max(cables)

    def cell(k: int, length: int, field: str = "exito") -> str:
        return fmt_pct(cells[f"{k}/{length}"][field], 0)

    l50 = ((e8.get("logistica") or {}).get("l50") or {}).get(str(few))
    return {
        "ELataqueMensajes": fmt_int(e8["mensajes"]),
        "ELataqueN": fmt_int(e8["n_por_celda"]),
        "ELataqueUbicaciones": fmt_int(e8["ubicaciones_fase1"]),
        "ELataqueSegundos": fmt_dec(e8["segundos_por_mensaje"], 1),
        "ELataqueLseis": fmt_int(round(l50["letras"])) if l50 else "—",
        "ELataqueSeisLargo": cell(few, long_),
        "ELataqueDiezLargo": cell(many, long_),
        "ELataqueLargo": fmt_int(long_),
        "ELataqueOraculoCorto": cell(many, probe, "oraculo"),
        "ELataqueOraculoECorto": cell(many, probe, "oraculo_e"),
        "ELataqueCorto": fmt_int(probe),
        "ELataqueDiezCorto": cell(many, short, "oraculo_e"),
    }


def macros(results_dir: Path | None = None) -> dict[str, str]:
    """Todas las cifras del informe, como texto listo para LaTeX, por nombre de macro."""
    folder = results_dir or paths.RESULTS
    summary = read_summary(folder)
    bench_path = folder / "bench_demo2.json"
    bench = json.loads(bench_path.read_text(encoding="utf-8")) if bench_path.is_file() else None
    seconds = sum(float(summary[e].get("segundos", 0)) for e in summary)
    run = max((summary[e]["corrida"] for e in summary), key=lambda r: r["fecha"])
    values = (
        _keyspace_macros(summary["e2"])
        | _validation_macros(summary["e1"])
        | _crib_macros(summary["e4"], summary["e3"])
        | _bombe_macros(summary["e5"], pd.read_parquet(folder / "e5_bombe.parquet"))
        | _banburismus_macros(summary["e6"])
        | _rejewski_macros(summary.get("e7"))
        | _attack_macros(summary.get("e8"))
        | _demo_macros(bench)
        | {
            "ELsemilla": str(run["semilla"]),
            "ELmodo": run["modo"],
            "ELcommit": run["commit"],
            "ELfecha": run["fecha"],
            "ELminutosExperimentos": fmt_int(max(1, round(seconds / 60))),
        }
    )
    return {name: tex(value) for name, value in values.items()}


def numbers_tex(values: dict[str, str]) -> str:
    """El contenido de ``report/numbers.tex``: una macro por cifra, en orden alfabético."""
    lines = [
        "% Generado por  make report  (python -m enigma_lab.informe) a partir de",
        "% results/summary.json y los resultados guardados. No lo edites a mano.",
        "",
    ]
    lines += [rf"\newcommand{{\{name}}}{{{value}}}" for name, value in sorted(values.items())]
    return "\n".join(lines) + "\n"


def write_numbers(path: Path = NUMBERS, results_dir: Path | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(numbers_tex(macros(results_dir)), encoding="utf-8")
    return path


# ---------------------------------------------------------------- compilación


def find_engine() -> tuple[str, str] | None:
    """El compilador de LaTeX disponible: (nombre, ruta) de latexmk o Tectonic, o ``None``."""
    latexmk = shutil.which("latexmk")
    if latexmk:
        return "latexmk", latexmk
    candidates = [shutil.which("tectonic"), os.environ.get("TECTONIC")]
    local = os.environ.get("LOCALAPPDATA")
    if local:
        candidates.append(str(Path(local) / "Programs" / "tectonic" / "tectonic.exe"))
    for candidate in candidates:
        if candidate and Path(candidate).is_file():
            return "tectonic", candidate
    return None


def page_count(log: Path) -> int | None:
    """Páginas del PDF según el registro de TeX («Output written on … (3 pages»)."""
    if not log.is_file():
        return None
    found = re.search(r"Output written on .*?\((\d+) pages?", log.read_text(errors="replace"))
    return int(found.group(1)) if found else None


def compile_pdf(engine: tuple[str, str]) -> subprocess.CompletedProcess[str]:
    """Compila ``report/informe.tex`` en ``report/informe.pdf``."""
    name, executable = engine
    if name == "latexmk":
        command = [executable, "-pdf", "-interaction=nonstopmode", "-halt-on-error", SOURCE.name]
    else:
        command = [executable, "--keep-logs", SOURCE.name]
    return subprocess.run(command, cwd=REPORT, capture_output=True, text=True, check=False)


def main() -> int:
    """Cifras, figuras y PDF del informe; devuelve el código de salida para ``make``."""
    import matplotlib

    matplotlib.use("Agg")  # solo archivos, sin ventanas
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    from enigma_lab.figuras import report_figures

    print(f"Cifras: {write_numbers().relative_to(paths.ROOT).as_posix()}")
    for path in report_figures():
        print(f"Figura: {path.relative_to(paths.ROOT).as_posix()}")
    engine = find_engine()
    if engine is None:
        print(
            "Aviso: no hay latexmk ni Tectonic. El informe no se compiló; sube la carpeta "
            "report/ a Overleaf (informe.tex, numbers.tex y figuras/)."
        )
        return 0
    print(f"Compilando con {engine[0]} ({engine[1]})…", flush=True)
    result = compile_pdf(engine)
    if result.returncode != 0:
        print(result.stdout[-3000:], result.stderr[-3000:], sep="\n")
        print("Error: el informe no compiló.")
        return 1
    pages = page_count(REPORT / "informe.log")
    print(f"PDF: report/informe.pdf · {pages if pages is not None else '?'} páginas")
    if pages is not None and pages > MAX_PAGES:
        print(f"Error: el informe pasa de {MAX_PAGES} páginas (spec, sección 10).")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
