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

## Fase 1 · Núcleo Enigma (20-11-2026)

### D-015 · Mensaje histórico: el del U-264, y con él la M4
No se encontró una fuente verificable del mensaje de Barbarossa (1941). Se revisaron
Wikipedia en alemán e inglés, Crypto Museum y las páginas de D. Rijmenants. La única
fuente con un mensaje real y su clave completa fue el M4 Project: el mensaje del U-264,
de 1942. Para descifrarlo, el núcleo incluye la Enigma M4, que el spec marca como
opcional: un rotor griego fijo a la izquierda y un reflector delgado. El cifrado por
lotes sigue siendo solo para tres rotores.

### D-016 · py-enigma como dependencia normal
E1 forma parte de `make reproduce` y compara con py-enigma. Por eso py-enigma pasó de
las dependencias de desarrollo a las normales; es un paquete pequeño, en Python puro.

### D-017 · Límites de py-enigma
py-enigma rechaza más de 10 cables («Please specify 10 or less pairs») y no trae el
reflector A. La comparación de 10.000 claves usa de 0 a 10 cables y los reflectores B y
C (B y C delgados en la M4). Las pruebas con hypothesis cubren de 0 a 13 cables y el
reflector A.

### D-018 · CyberChef a mano en la web (resuelve P-003 para la máquina)
Docker Desktop estaba apagado y Node.js no está instalado, así que se aplicó el respaldo
del spec: 6 casos validados a mano en la web de CyberChef. `scripts/cyberchef_urls.py`
genera las URL con la receta incluida, para poder repetir la validación. Los 3 casos de
la Bombe quedan para la fase 3, con Docker si está disponible.

### D-019 · E1 y `make resumen` llegan en la fase 1
El criterio de la fase 1 («100 % frente a py-enigma en 10.000 claves») es la medida de
E1, y el spec pide `make resumen` al cerrar la fase 1. Por eso en esta fase ya existen:
- el marco de experimentos: `experiments/common.py` y `__main__.py`;
- E1, con su Parquet, su figura y su entrada en `summary.json`;
- `make reproduce`, `make rapido`, `make experimento` y `make resumen`.

La página Experimentos sigue siendo de la fase 2.

### D-020 · Un solo registro de cifras
`enigma_lab/cifras.py` lista las cifras de la tabla 11.3 con la función que calcula cada
una. Lo usan `tests/test_presentacion.py` y la tabla «Cifras de la presentación» de
`RESUMEN.md`, así que las dos no pueden divergir.

### D-021 · `results/` se versiona
Los resultados son pequeños (E1 ocupa unos 0,7 MB) y la app, el informe y el resumen los
leen. Al versionarlos, un clon limpio muestra resultados sin esperar `make reproduce`.
Cada corrida registra el commit del código que la produjo. Por eso los resultados van en
un commit propio, justo después del commit del código.

### D-022 · Página Máquina
- **«Clave aleatoria»:** usa azar del sistema, sin semilla, porque la usa el compañero
  de la demo 2 y cada clave debe ser distinta. Todo lo demás usa la semilla 2026.
- **Texto de entrada:** se normaliza con `to_machine_letters`, que quita tildes (Ü → U),
  cambia Ñ → N y ß → SS y descarta lo demás. La normalización del corpus de la fase 2 es
  otra: en alemán escribe Ü → UE.
- **«Reiniciar posición»:** vuelve a la posición inicial de la última clave cargada.
- **Animación:** muestra como máximo 200 letras; el resto se cifra pero no se anima. Va
  en turquesa a la ida y en ámbar a la vuelta. La lámpara de la tecla pulsada se dibuja
  con contorno punteado: nunca se enciende.

### D-023 · Semántica de la traza y de las muescas
- **Traza:** cada etapa guarda la letra que **sale** de ese componente, como en la
  diapositiva 4.
- **Muesca:** se guarda como la letra de ventana desde la que el rotor arrastra al
  siguiente (Q en el rotor I), igual que Wikipedia y py-enigma. CyberChef escribe la
  letra de llegada (R); la conversión está en `scripts/cyberchef_urls.py`.

## Fase 2 · Estadística y cribs (20-11-2026)

### D-024 · Corpus
- **Libros:**
  - alemán: *Effi Briest* (Fontane) y *Die Verwandlung* (Kafka), 578.365 letras;
  - español: el *Quijote*, 1.620.450 letras.
- **Descarte por derechos:** *Buddenbrooks* (Thomas Mann, †1955) se descartó. En
  Colombia la protección dura la vida del autor más 80 años, así que sigue protegido
  hasta 2035.
- **Descarga:** gutenberg.org estaba en mantenimiento (503), así que se descargó de su
  espejo oficial del Mirror Service, con URL y SHA-256 fijos.
- **Muestras del repositorio:** unos 200 KB por idioma. La alemana sale mitad de cada
  libro. La app y el modo rápido usan las muestras; el modo completo usa el corpus
  completo (`make corpus`, que `make reproduce` corre primero).

### D-025 · Normalización
Sigue el spec (5.3): en alemán Ä → AE, Ö → OE, Ü → UE, ß → SS; en español se quitan las
tildes y Ñ → N. Las demás marcas diacríticas se quitan. En el modo «X como separador»,
cada tramo de caracteres que no son letras (espacios, signos y también dígitos) se
vuelve una sola X.

### D-026 · Diseño de E3
- **Condiciones:** dos idiomas y longitudes de 25 a 1.000 letras (50 a 500 en modo
  rápido); 1.000 mensajes por condición (200 en modo rápido).
- **Claves:** cada mensaje lleva su propia clave aleatoria de Enigma I con 10 cables.
- **IC 95 % de la media:** aproximación normal.
- **Mapa de calor:** se acumula con los mensajes en alemán de la mayor longitud.

### D-027 · Diseño de E4
- **Mensajes:** de 250 letras, como el piloto.
- **Crib:** es el propio tramo del mensaje que empieza en una posición t al azar; así
  la alineación verdadera es t.
- **Texto alemán:** va en modo «X como separador», porque así se escribían los cribs
  reales (WETTERBERICHTX…).
- **IC:** como las alineaciones de un mismo mensaje no son independientes, se calcula
  con la media de las fracciones por mensaje (aproximación normal sobre los mensajes) y
  no con un Wilson sobre todas las alineaciones juntas.
- **Teoría corregida:** se agrega (1 − (1 − κ)/25)^L, con κ el IC del texto, como
  referencia adicional (columna `teorico_kappa`). Con texto aleatorio coincide con
  (25/26)^L.

### D-028 · Métricas del menú
- **Lazos:** el número ciclomático E − V + 1 de la componente usada. Esa componente es
  la de más lazos; si empatan, la de más letras.
- **Letra de prueba:** la de mayor grado en esa componente; si empatan, la primera en
  orden alfabético.
- **Aristas en lazos:** son las que no son puentes. Dos aristas paralelas, la misma
  pareja en dos pasos, cuentan como un lazo.

### D-029 · N-gramas
Los modelos se construyen con la muestra del idioma; la puntuación es la suma de log₁₀ p.
Los n-gramas que no aparecen reciben un piso de 0,01 apariciones, una convención habitual
en el criptoanálisis con n-gramas.

### D-030 · Página Experimentos
- **Por defecto:** muestra los resultados guardados en `results/` (modo completo).
- **«Correr ahora»:** repite el experimento en modo rápido dentro de la sesión, sin
  sobrescribir `results/`.
- **Descargas:** las figuras se generan con el estilo `enigma_print`, de modo que el PNG
  o SVG descargado es el del informe. Así no hace falta kaleido.

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

### P-003 · CyberChef para la Bombe (fase 3)
La parte de la máquina se resolvió en D-018. Para los 3 casos de la Bombe, la idea es
correr la API de Node de CyberChef dentro de Docker (imagen oficial `node`) si Docker
Desktop está encendido; si no, se harán a mano en la web.
