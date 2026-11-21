# Decisiones

Registro de las decisiones tomadas ante ambigüedades o limitaciones (spec, sección 0,
punto 5): se elige la opción más simple coherente con el spec y se anota aquí.

## Fase 0 · Andamiaje (20-11-2026)

### D-001 · Herramientas en Windows
- El equipo no tenía uv, GNU Make ni Python 3.12. Con la aprobación del autor se
  instalaron con winget, a nivel usuario: uv 0.13.9 (`astral-sh.uv`) y GNU Make 4.4.1
  (`ezwinports.make`). uv descargó CPython 3.12.16 sin tocar el Python 3.14 del sistema.
- El Makefile exporta `PYTHONUTF8=1`, porque la consola de Windows (cp1252) falla al
  imprimir tildes, y sus recetas solo usan `uv` y `python`, porque en Windows corren en
  `cmd.exe` o en `sh` según la terminal.

### D-002 · Nombre del PDF de la presentación
El spec lo llama `docs/presentacion/presentacion.pdf`; el archivo real es
`docs/presentacion/Romper Enigma presentación final.pdf`. No se renombra porque
`docs/presentacion/` no se edita, y ningún código depende de ese nombre.

### D-003 · La especificación
La especificación del proyecto la guarda el autor fuera del repositorio. Cuando el código o
estos documentos citan «el spec» o «spec, sección N», se refieren a sus secciones.

### D-004 · El piloto
`piloto_enigma.py` pasó a `scripts/piloto_enigma.py`, sin cambios y excluido de ruff. Es
una referencia (las diapositivas 6 y 15 citan sus cifras), no parte de la arquitectura.
`scripts/exploracion_demo2.py` lo usa para la medición exploratoria del plan.

### D-005 · `core/keyspace.py` se adelantó a la fase 0
La página Inicio muestra «67 → 20 bits» y ninguna cifra se escribe a mano, así que los
conteos exactos del espacio de claves, con sus pruebas, llegaron en la fase 0. En la
fase 2 se completan la página «Espacio de claves» y el experimento E2.

### D-006 · Años de 365,25 días
El estimador de fuerza bruta divide por segundos de un año juliano. Así reproduce las
«unos 5.037 años» del spec; con años de 365 días daría 5.041.

### D-007 · Navegación de la app
- `app/Inicio.py` es el punto de entrada: arma la navegación con `st.navigation`,
  aplica el tema y el modo demo. El contenido de Inicio vive en `app/pages/inicio.py`.
- Archivos de página con nombres ASCII (`pages/maquina.py`) y títulos con tildes en
  `st.Page` («Máquina», «La Bombe»), para evitar problemas de Unicode en rutas.
- `app/ui/catalog.py` lista los módulos: la navegación y las tarjetas de Inicio se
  generan de esa lista.
- Limitación de las pruebas: al volver a ejecutar, `AppTest` corre la página y no el
  punto de entrada, así que las pruebas fijan `session_state` antes de la primera
  ejecución.

### D-008 · Fuentes empaquetadas
Para que la app funcione sin internet (spec 8.2, punto 11), Inter 4.1 (variable, WOFF2) y
JetBrains Mono 2.304 (WOFF2) están en `app/static/fonts/`, servidas por Streamlit
(`enableStaticServing`). Matplotlib no lee WOFF2: usa copias TTF en
`src/enigma_lab/viz/fonts/`. Ambas fuentes tienen licencia SIL OFL 1.1, que va junto a
los archivos. Origen y SHA-256: `docs/FUENTES.md`.

### D-009 · Orden de la paleta Okabe-Ito
El spec pide Okabe-Ito. El negro se excluye porque es invisible sobre el fondo oscuro.
Las siete restantes se ordenaron con el validador de paletas de una guía de visualización
(OKLab ΔE ×100, daltonismo simulado con Machado, Oliveira y
Fernandes, 2009). Se enumeraron los órdenes y se eligió el que maximiza la peor
separación entre series vecinas, con el piso de visión normal ΔE ≥ 15:

**verde azulado `#009E73`, azul `#0072B2`, bermellón `#D55E00`, celeste `#56B4E9`,
naranja `#E69F00`, púrpura rojizo `#CC79A7`, amarillo `#F0E442`.**

- Es el mismo orden sobre fondo oscuro (`#0F1216`) y sobre blanco: una serie conserva su
  color en la app y en el informe.
- Las tres primeras pasan todas las comprobaciones en los dos fondos, incluso comparando
  todos los pares. La peor separación con daltonismo es ΔE 11,0 (verde azulado y
  bermellón, deuteranopía), y la peor con visión normal, 18,7.
- Con las siete, la peor separación entre vecinas es ΔE 18,0 con daltonismo y 18,7 con
  visión normal.
- Lo que no pasa:
  - Sobre fondo oscuro, las posiciones 4 a 7 quedan por encima de la banda de
    luminosidad (son más claras).
  - Sobre blanco, el naranja, el celeste y el amarillo quedan bajo 3:1 de contraste.
  - Por eso, todo gráfico con cuatro series o más lleva leyenda y etiquetas directas,
    y sus datos se pueden descargar.

### D-010 · Rampas secuenciales ámbar
Para la magnitud (mapas de calor) se usa un solo tono: el del ámbar `#F2B134` (OKLCH,
tono 78,9°), con la luminosidad en pasos de 0,09 y la croma recortada al gamut sRGB.
- **Tema oscuro (`SEQUENTIAL_DARK`):** pasa las comprobaciones ordinales del
  validador. Es monótona, sus pasos difieren en ΔL ≥ 0,06, es de un solo tono, y su
  paso más oscuro tiene 2,01:1 de contraste sobre el fondo.
- **Tema impreso (`SEQUENTIAL_PRINT`):** su extremo claro queda en 1,23:1 sobre blanco.
  Es lo esperado en un mapa continuo, donde lo claro significa «poco». Para categorías
  ordenadas discretas sobre blanco se usan los pasos 3 a 7.

### D-011 · Formato de números
Las cifras para personas usan `enigma_lab.viz.numfmt`:
- punto de miles y coma decimal;
- signo menos tipográfico (−, U+2212), como las diapositivas;
- espacio no separable antes de «%».

La plantilla Plotly usa `separators=",."`. Los CSV y JSON guardan números, no texto
formateado.

### D-012 · `requirements.txt`
`make requirements` exporta `uv.lock` con todas las dependencias, también las de
desarrollo, para poder correr las pruebas con pip. Va sin hashes porque incluye el propio
proyecto en modo editable (`-e .`), que pip no acepta junto con hashes.

### D-013 · CI
`.github/workflows/ci.yml` corre ruff, mypy y pytest en Ubuntu y Windows con
`uv sync --locked`. Todavía no se ha ejecutado: el repositorio no tiene remoto.

### D-014 · Modo demo desde la fase 0
El interruptor de la barra lateral ya sube la letra base a 20 px. El modo demo completo
llega en la fase 6: ocultar lo que la demo no usa, resultados en grande y Numba
precalentado.

## Pendientes de decidir

### P-001 · Equipo de las mediciones de la demo 2 (fase 3)
Este equipo es un escritorio (i5-9400F, 6 núcleos, 16 GB). El presupuesto de 30 s de la
demo 2 es del portátil del autor. `make bench-demo` (fase 3) se correrá en el portátil,
y `RESUMEN.md` dirá en qué equipo se midió cada tiempo. Falta que el autor confirme qué
equipo se usará.

### P-002 · «Letras del menú» (fase 3)
En 6.5 «letras» son vértices: 11 letras y 13 aristas. En E5 y en la tabla de Turing no
queda claro si cuentan vértices o aristas. Se resolverá con la fuente original al
transcribir `data/reference/turing_stops.csv`.

### P-003 · CyberChef sin Node.js (fase 1)
Node.js no está instalado. El plan es correr la API de Node de CyberChef dentro de Docker
(imagen oficial `node`) con Docker Desktop encendido. Si no funciona, se validará a mano
en la web: 5 casos de Enigma y 3 de Bombe.
