# Arquitectura

Regla central (spec, sección 3): **la lógica de Enigma existe una sola vez, en Python**,
dentro de `src/enigma_lab/`. La app de Streamlit solo la llama y la muestra; los
componentes JavaScript de `app/components/` animan una «traza» en JSON que calcula Python
y nunca reimplementan la máquina.

## Módulos y flujo de datos

En gris punteado, lo que llega en fases siguientes.

```mermaid
flowchart LR
    subgraph data["data/"]
        ref["reference/<br/>vectores · Turing · Kuhl"]
        corp["corpora/<br/>alemán · español"]
        demo["demo/<br/>portada · respaldo"]
    end

    subgraph lib["src/enigma_lab/"]
        core["core<br/>máquina · espacio de claves"]
        stats["stats<br/>frecuencias · IC · n-gramas"]
        cribs["cribs<br/>arrastre · menú"]
        bombe["bombe<br/>Numba · verificador"]
        banb["banburismus<br/>decibanes · SPRT"]
        rej["rejewski<br/>características"]
        att["attacks<br/>Gillogly · hill climbing"]
        exp["experiments<br/>E1 a E8"]
        viz["viz<br/>tema · numfmt · figuras"]
    end

    app["app/<br/>Streamlit + componentes JS"]
    results["results/<br/>Parquet · figuras · summary.json"]
    pres["results/presentacion/<br/>RESUMEN.md · cifras.json · CSV"]
    report["report/<br/>informe.tex · numbers.tex"]

    corp --> stats
    ref --> exp
    demo --> app
    core --> cribs --> bombe
    core --> banb
    core --> rej
    stats --> bombe
    stats --> att
    core --> att
    core & stats & cribs & bombe & banb & rej & att --> exp
    exp --> results --> pres
    results --> report
    viz --> app
    viz --> exp
    core & stats & cribs & bombe & banb --> app
    results --> app

    classDef done fill:#171B21,stroke:#F2B134,color:#E8E6E3
    classDef todo fill:#0F1216,stroke:#2A3038,color:#9AA3AD,stroke-dasharray: 4 3
    class core,viz,app done
    class stats,cribs,bombe,banb,rej,att,exp,results,pres,report,ref,corp,demo todo
```

## Estado por fase

| Pieza | Qué hay hoy | Fase |
| --- | --- | --- |
| `core/keyspace.py` | Conteos exactos del espacio de claves | 0 (adelantado) |
| `viz/theme.py`, `viz/numfmt.py` | Tema, plantilla Plotly, estilos Matplotlib y formato español | 0 |
| `app/` | Punto de entrada, navegación, modo demo y página Inicio | 0 |
| `core/` (máquina) | Enigma I y M3, traza, versión por lotes | 1 |
| `stats/`, `cribs/` | Estadística del idioma, arrastre y menús | 2 |
| `bombe/` | Bombe en Numba, versión de referencia y verificador | 3 |
| `banburismus/` | Decibanes y SPRT | 4 |
| `rejewski/`, `attacks/` | Extensiones P2 | 5 |

## Convenciones de código

- Identificadores en inglés; docstrings y comentarios en español, explicando la
  matemática.
- Rutas con `pathlib`, desde `enigma_lab.paths`.
- Azar siempre con `numpy.random.Generator` sembrado (semilla global 2026).
- Las páginas importan sus utilidades como `ui.*` (`app/ui/`), porque Streamlit pone
  `app/` en `sys.path`.
