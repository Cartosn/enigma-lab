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

## Fase 3 · Bombe (21-11-2026)

### D-031 · «Letras del menú» son vértices (resuelve P-002)
- **La fuente.** La tabla de Wikipedia «Bombe» (revisión 1385546242) se titula por el
  «Number of letters on the menu», y el artículo llama menú al grafo de las letras del crib
  y del cifrado: sus letras son los nodos. Es la misma convención de 6.5 (11 letras, 13
  aristas). Otra frase del artículo usa «letras» para las letras del crib («con 12 letras
  o menos caben tres órdenes en una Bombe», una pila de tambores por letra), pero esa no
  es la de la tabla.
- **La comprobación.** E5 mide las dos lecturas sin proponérselo. Con vértices, la
  columna de 12 letras queda cerca de la de Turing (820 · 31 · 1,2 · 0,04); contando
  aristas, con 3 lazos sale unas diez veces más.
- **Consecuencia.** Una celda de E5 con V letras y k lazos son menús conexos de cribs de
  V − 1 + k letras.

### D-032 · Modos Bletchley y robusto
- **Posición candidata.** La de las ventanas antes de la primera letra del crib, con
  anillos AAA. Los rotores avanzan antes de cada letra: el paso i del crib usa el
  derecho en C + i + 1. Es la convención de CyberChef, que informa las paradas igual.
- **Bletchley.** Dentro del tramo solo gira el derecho. Un movimiento del central justo
  en la primera pulsación queda absorbido en la posición candidata.
- **Robusto.** Variante k = 1, …, L − 1: el central avanza al cifrar la letra k del crib
  (las aristas con paso i ≥ k usan el central + 1). Son L variantes con la de Bletchley.
- **Lo que no cubre.** Dos movimientos dentro del tramo: una vuelta seguida de un doble
  paso, o un doble paso con el izquierdo. Pasa en cerca de 1 de cada 26 vueltas.
  `sweep.true_stop` dice qué variante debe dar la parada verdadera, o que ninguna.

### D-033 · Criterio de parada y stecker candidato
- **Parada.** Hay parada si los 26 hilos del cable de prueba no quedan en una sola
  componente. No depende del hilo que se energice (por omisión, el A).
- **Candidatos.** Los hilos del cable de prueba que quedan solos en su componente. Con 1
  encendido es T↔x; con 25, el apagado; con otros conteos puede haber varios o ninguno.
  El verificador los prueba todos, y descarta la parada que no tiene ninguno.
- **Letra de prueba.** La de `menu_stats` (mayor grado en la componente con más lazos),
  y se puede cambiar en la página.

### D-034 · Qué conexiones usa la Bombe
- **Aristas.** Todas las del menú, de todas sus componentes; el diagonal board las
  acopla.
- **Diagonal board.** Solo entre cables de letras del menú. Lo que conecta en un cable sin
  aleatorizadores queda colgando y no cambia ninguna parada; la máquina de verificación sí
  revisa esas deducciones.
- **CyberChef.** Usa solo la componente con más lazos. Por eso los casos de comparación
  tienen menús conexos, donde las dos reglas coinciden (D-041).

### D-035 · Máquina de verificación (etapa 1)
- **La hipótesis T↔x.** Se leen todos los hilos que enciende: cada uno es un stecker
  P(a) = u, y también P(u) = a. Cae si una letra queda con dos parejas.
- **Las demás componentes.** Cada una necesita al menos una hipótesis compatible. En la
  posición verdadera siempre la hay: la verdadera. Si tiene exactamente una, sus
  steckers se suman al plugboard parcial.
- **Por qué.** Con WETTERBERICHT los menús suelen tener 3 componentes, y la letra de
  prueba ve solo la suya. En 8 casos de la demo 2 en modo robusto (60 órdenes), esta
  revisión bajó las hipótesis de hasta 241.155 a menos de 800.

### D-036 · Verificador (etapa 2)
- **Modelo del idioma.** Cuadrigramas interpolados con trigramas, bigramas y letras
  (λ = 0,6 · 0,25 · 0,1 · 0,05), entrenados con la muestra alemana con la X como
  separador. Se puntúa log₁₀ P(texto) por la regla de la cadena, incluidas las tres
  primeras letras.
- **Puntaje rápido.** Hill climbing del plugboard sobre el crib y 13 letras a cada lado.
  Fuera del crib se prueba cada punto donde pudo volver a avanzar el central. Se descifran
  las 25 mejores hipótesis. Si ninguna da un texto plausible, se sigue bajando por el
  ranking hasta encontrar una, con un máximo de 300, como seguía Bletchley con la parada
  siguiente. Así se resolvió el único fallo del primer banco de la demo 2: la hipótesis
  verdadera había quedado 34.ª en el puntaje rápido.
- **Anillos.** Se prueban los 676 pares (central, derecho) y los arranques que llevan a
  la parada. El hill climbing se hace para cada secuencia distinta de posiciones, y luego
  se alterna: con el mejor plugboard se vuelve a elegir la secuencia y se sube otra vez.
- **Elección bayesiana.** A priori toda clave (anillos y arranque) es igual de probable:
  una secuencia que dan k claves suma log₁₀ k.
- **Plausible.** Si el log₁₀ P por letra supera −1,5. El alemán da cerca de −0,67 y las
  letras al azar, −2,66.
- **Cómo se eligió.** Primero se probó la suma de cuadrigramas, sin interpolar y sin el
  término de las claves. Fallaba en 1 o 2 de los 200 casos de la prueba 6.4, siempre con
  el plugboard exacto y 1 o 2 letras distintas, por un anillo mal elegido. El diseño final
  se ajustó con esos 200 casos (200 de 200) y se comprobó con 200 casos nuevos (198 de 200;
  ver VALIDACION).

### D-037 · Rendimiento, Numba y Streamlit
- **Union-find.** Con compresión por mitades. Las paradas se guardan como arreglos de
  NumPy, no como objetos: con menús de pocos lazos puede haber cientos de miles.
- **Salida temprana.** El barrido deja de unir en cuanto los 26 hilos del cable de prueba
  quedan juntos.
- **Paralelismo.** Las 17.576 posiciones se reparten en 676 bloques con `prange`. En
  Windows la capa de hilos de Numba es OpenMP (MS).
- **Streamlit.** Cada sesión corre en su propio hilo, y la capa «workqueue» no admite
  lanzamientos simultáneos. Por eso un candado (`sweep._LOCK`) deja un solo barrido a la
  vez, con cualquier capa.
- **Precalentado.** Los núcleos llevan `cache=True`. La app los compila o carga, y
  precalcula el aleatorizador de los 60 órdenes (27 MB), en `_setup_once` al arrancar.

### D-038 · Diseño de E5
- **Menús.** Conexos, de cribs alemanes reales (X como separador), con clave aleatoria de
  Enigma I con 10 cables. Las celdas se llenan por muestreo con rechazo.
- **Medición.** Un orden por menú, el verdadero. Las paradas falsas excluyen la verdadera.
  La vuelta del central dentro del tramo queda como sale de la clave al azar: así se mide
  cuánto falla el modo Bletchley.
- **Hipótesis abiertas.** También se cuentan las hipótesis (hilos aislados) de cada parada.
  La tabla de Turing da 40.000 paradas por orden con 8 letras sin lazos, más que las
  17.576 posiciones: cuenta hipótesis, no posiciones.
- **Modo robusto.** Solo en menús de 12 y 16 letras, con diagonal board.
- **Modos de corrida.** Rápido: 8, 12 y 16 letras, 10 menús por celda. Completo: 8 a 16
  letras de dos en dos, 100 menús por celda.

### D-039 · Banco de la demo 2
- **Casos.** Clave como «Clave aleatoria» (10 cables) y mensaje alemán de 78 letras, como
  el caso de respaldo, que empieza por el crib, con X entre palabras. Crib en la
  posición 0.
- **Flujo.** El de la página: barrido, máquina de verificación y «Verificar». Éxito: el
  descifrado es el mensaje letra por letra.
- **Configuraciones, de la más simple a la menos:**
  1. 60 órdenes en modo robusto;
  2. rotores I, II y III en modo robusto;
  3. el crib acordado WETTERBERICHTXFUER (18 letras: «Wetterbericht für») con 60 órdenes.
- **Criterio.** El spec: éxito de al menos 95 % y p95 del tiempo total de 30 s o menos.
- **Rotores permitidos.** «Clave aleatoria» de la página Máquina ahora admite rotores
  permitidos, para la configuración 2.

### D-040 · Página La Bombe
- **Entrada.** Lo que deja la página Cribs (`bombe_input`) o el botón «Caso de respaldo»,
  que fija el modo Bletchley y los 60 órdenes.
- **Tambores.** Durante el barrido, una tripleta por conexión del menú gira como un
  odómetro: es una animación, no la posición en curso, que la muestran la barra y el
  contador. Al terminar, cada tripleta muestra las letras de la parada que manda Python.
- **Tabla.** Hasta 300 paradas, primero las consistentes. Si se conoce la clave (caso de
  respaldo), se marca la verdadera.
- **Verificar.** Reutiliza las hipótesis de la etapa 1, calculadas al terminar el barrido.

### D-041 · CyberChef para la Bombe, a mano en la web (resuelve P-003)
Docker Desktop seguía apagado. Se aplicó el respaldo del spec:
- `scripts/cyberchef_urls.py` arma las URL con la receta «Bombe», sin y con máquina de
  verificación.
- Hay tres casos con menú conexo: el de respaldo (3 lazos), uno de 2 lazos y uno de 1
  lazo con el crib en la posición 3.
- Resultado en VALIDACION (6.2).

## Fase 4 · Banburismus (21-11-2026)

### D-042 · La profundidad dura todo el solapamiento
- **El spec (5.6)** dice que los dos mensajes quedan en profundidad «hasta que se mueve el
  rotor central».
- **Con la máquina real** no es así. Si las claves de mensaje coinciden en el rotor
  izquierdo y en el central, las dos máquinas recorren la misma sucesión de estados del
  odómetro, una adelantada respecto de la otra. Desde el primer estado en que coinciden,
  coinciden en todos: el central, el doble paso y el izquierdo avanzan en el mismo estado en
  las dos.
- **Lo que hace el central** es decidir el desplazamiento. Sea δ = (derecho₂ − derecho₁)
  mod 26:
  - si el central no avanza mientras el derecho del mensaje 1 recorre esos δ pasos, el
    desplazamiento es +δ;
  - si avanza, es δ − 26.
  Con los rotores I–V (una muesca) pasa exactamente uno de los dos. Por eso se prueban los
  desplazamientos de −25 a +25, como en Wikipedia.
- **Cómo se implementó.** `depth.true_offset` no usa esta regla: compara los estados de la
  máquina (`core/stepping.step`). Las pruebas comprueban con la máquina escalar que los
  estados coinciden letra por letra, y que en ese desplazamiento el cifrado repite
  exactamente donde repite el texto plano.
- **Rotores.** Las claves son de Enigma I (rotores I–V), como en el resto del proyecto. Con
  los rotores de dos muescas de la M3 naval (VI–VIII) un par puede no quedar nunca en
  profundidad: `true_offset` devuelve `None` y `make_pairs` sortea otra clave.

### D-043 · Dos fuentes de texto plano
- **«Tasa 1/17».** El mensaje 1 son letras uniformes. La letra j del mensaje 2 es la j + d
  del 1 con probabilidad 1/17; si no, otra letra al azar. Es el modelo de Turing:
  repeticiones independientes, 1/17 en profundidad y 1/26 al azar. Pasa por la máquina real.
- **«Alemán».** Dos fragmentos del corpus con la X como separador, como en E4 y E5. Se
  sortean de modo que no se solapen dentro del corpus.
- **Sin ajustes.** Con el alemán no se toca nada para acercarse a 1/17: se reporta lo que da
  (unas 1 de cada 12,5 repeticiones).

### D-044 · Puntuaciones y modelo de multigramas
- **Cuatro puntuaciones:**
  - letras sueltas con 1/17 (Turing; los pesos del spec);
  - letras sueltas con la tasa medida en el corpus;
  - bigramas y trigramas;
  - hasta tetragramas.
- **Multigramas.** El spec pide puntuarlos, pero no da sus tasas. Turing usaba tablas del
  tráfico naval, que no tenemos. Se usa la regla de la cadena: la probabilidad de repetir
  depende de la racha de columnas que acaban de repetir, h_r, y se calcula con ρₙ, la
  probabilidad de que dos n-gramas del corpus coincidan (`scoring.run_probabilities`). Así
  el puntaje sigue siendo el logaritmo de un cociente de verosimilitudes, y los umbrales de
  Wald conservan su sentido.
- **De dónde salen los ρₙ.** Del mismo corpus del texto plano: la muestra en la app y en el
  modo rápido, y el corpus completo en el modo completo. Son cuatro números, así que no hay
  riesgo de sobreajuste.
- **Para qué la segunda puntuación.** Separa dos efectos: usar la tasa correcta y usar
  multigramas. Las tres medidas en el corpus solo se aplican al texto alemán, porque el
  texto con tasa 1/17 no tiene racimos.

### D-045 · Diseño de E6
- **Pares.** 2.000 por fuente en modo completo y 300 en el rápido. Cada par aporta una
  prueba en profundidad (el desplazamiento verdadero) y una al azar (otro de los 50
  desplazamientos, al azar). Todas las puntuaciones y todos los umbrales se evalúan sobre
  los mismos pares.
- **Solapamiento máximo.** 10.000 letras (6.000 en el rápido). Con letras sueltas y 1/17,
  la probabilidad de no decidir en 10.000 letras es ínfima; la columna `sin_decidir` lo
  confirma.
- **Solapamientos cortos** (25 a 1.600 letras). Es la misma prueba, truncada.
- **Umbrales.** α = β de 5 %, 1 % y 0,1 %.
- **Medidas:**
  - *aciertos:* decisión correcta dentro del solapamiento;
  - *letras leídas:* hasta decidir, o todo el solapamiento si no decide;
  - *identificación:* el desplazamiento verdadero saca el mayor puntaje de los 51; con k
    empatados cuenta 1/k;
  - *ROC y AUC* del puntaje sin detenerse; el AUC es la U de Mann-Whitney sobre n₁·n₀.
- **Referencias.** Wald con el modelo de cada puntuación y, para la fuente con tasa 1/17,
  el cálculo exacto (D-048).

### D-046 · CSV extra para la diapositiva 17
`r4_banburismus.csv` lleva primero las columnas del spec y después las extras: fuente,
hipótesis, α, `identifica`, `wald`, `exacto` y otras. Las trayectorias y la curva ROC no
caben en esa tabla, así que van aparte:
- `r4_trayectorias.csv`: 10 pares por hipótesis, un punto cada 20 letras, con la tasa 1/17
  y con alemán y trigramas;
- `r4_roc.csv`: las curvas ROC.

### D-047 · PNG a 2x
`save_figure` guardaba fuera del bloque `with` del estilo, donde no rigen `savefig.dpi` ni
`savefig.bbox`. Por eso los PNG de E1 a E5 salían a 1x (630 × 360 px) y no a 2x, como pide
el spec (sección 7). Ahora la función fija 200 puntos por pulgada y el recorte ajustado. Los
PNG de E1 a E5 cambian en la siguiente corrida; los SVG y PDF conservan su contenido.

### D-048 · El cálculo exacto del SPRT
- **Para qué.** Explicar la diferencia con Wald sin el ruido de la simulación.
- **Cómo.** Con letras sueltas independientes, el estado tras n letras es el número r de
  repeticiones. Se propaga la probabilidad de cada r sin decidir, y se retiran las que
  cruzan un umbral (`sprt.exact_letters`). Da exactos E[N], los errores reales y el
  sobrepaso medio. La identidad de Wald se cumple con un error relativo de 10⁻⁹.
- **La descomposición** (`sprt.wald_gap`). Con α = β = 1 %:
  - en profundidad, 30,9 letras más que Wald: 30,7 por el sobrepaso de arriba y 0,2 por el
    error real;
  - al azar, 5,1 letras más: 2,4 por el sobrepaso de abajo y 2,9 porque el error real
    (0,86 %) queda bajo el 1 %, menos 0,3 por el sobrepaso de arriba.

## Fase 6 · Pulido y entrega (22-11-2026)

### D-049 · Modo demo
- **Qué oculta.** Los paneles «¿Qué estoy viendo?», la clave de Máquina, las tablas largas (la
  de paradas, las de Experimentos), «Hipótesis examinadas», la comparación con y sin diagonal
  board y los botones de descarga. En Máquina quedan solo los preajustes de la demo 1 («Vector
  BDZGO» y «Portada»); en La Bombe, «Cifrado del compañero» y «Caso de respaldo».
- **Cómo oculta los controles.** Streamlit borra el estado de un control que no se dibuja, así
  que la clave de Máquina se dibuja dentro de un contenedor con clave `nodemo_…` y el CSS del
  modo demo lo esconde (`ui/layout.py` · `hidden_in_demo`). Lo demás simplemente no se dibuja.
- **20 px.** La letra base sube a 20 px y lo que Streamlit dibuja más pequeño (pies de texto,
  etiquetas, métricas, insignias, cuadros de texto) se lleva a 1rem. La plantilla Plotly
  `enigma_dark_demo` parte de 22 px para que las marcas de los ejes queden en 20. Las
  animaciones agrandan su letra en modo demo; el SVG escala con el ancho, y con la barra lateral
  plegada sus rótulos quedan entre 18 y 21 px.
- **El resultado en grande.** `ui/layout.py` · `big_result`: el texto en grupos de 5 a 3rem
  (60 px) y debajo la lectura con la X como espacio. En Máquina la lectura solo aparece al
  descifrar (cuando la salida trae más X que la entrada).
- **El menú sí se ve en la demo 2.** Antes el modo demo lo ocultaba; el guion pide mostrarlo
  («Muestra el menú y sus lazos»).
- **En la URL.** El interruptor se refleja en `?demo=1`, así que una recarga o un enlace guardado
  abren la app en modo demo.

### D-050 · «Cifrado del compañero» (demo 2)
- **Qué hace.** Vacía el cifrado, deja el crib en la posición 0 y aplica la configuración que
  recomendó `make bench-demo` en ese equipo: lee `results/bench_demo2.json` (órdenes, crib y
  modo). Si no hay banco, usa la más simple: los 60 órdenes en modo robusto con WETTERBERICHT.
  Así, si el banco del portátil recomienda otra configuración, el botón la sigue sin tocar código.
- **El error que corrige.** Al probar la demo en el navegador, el modo volvía a «Bletchley» al
  pegar el cifrado: con el cifrado vacío la página se detiene antes de dibujar la configuración,
  y Streamlit borra el estado de esos controles. Ahora los botones guardan sus ajustes aparte
  (`bombe_pending`) y cada control los toma justo antes de dibujarse (`_apply_pending`).

### D-051 · Exportar los gráficos (spec 8.3)
- **La figura:** la barra de cada gráfico de Plotly la baja en PNG a 2x.
- **Los datos:** cada gráfico de las páginas lleva «Datos (CSV)», con las series de la propia
  figura (`viz/plotly_figs.py` · `figure_table`) o la tabla que lo origina. En Experimentos, cada
  pestaña baja su tabla y la figura del informe en PNG y SVG.
- **Descargas diferidas.** El CSV y las figuras se arman solo al pulsar el botón (Streamlit
  1.67 acepta una función como `data`). Antes, Experimentos dibujaba seis figuras de Matplotlib en
  cada carga y tardaba de 5 a 8 s sin indicador; ahora abre en menos de 1 s después del arranque.
- **Las animaciones** (máquina, crib, menú, tambores) no se exportan como figura: exportan sus
  datos (la traza, las alineaciones y las aristas del menú, en CSV).

### D-052 · Figuras y tabla del informe
- **Figuras:** E4 (supervivencia de cribs), E5 (paradas frente a Turing) y E6 (SPRT frente a
  Wald). Son los tres resultados que comparan una medida propia con una referencia publicada o
  teórica: (25/26)^L, la tabla de Turing y la aproximación de Wald, y son las diapositivas 15 a 17.
  E1 y E2 no necesitan figura: son cifras exactas, y van en la tabla.
- **Tabla:** validación (E1) y espacio de claves (E2): las cifras que sostienen la pregunta
  («67 → 20 bits») y la confianza en el simulador.
- **Formato.** Figuras compactas propias del informe (`figuras.py`, estilo `enigma_print` con
  letra de 8 pt), no las de los experimentos, que están pensadas para una página. Papel carta,
  márgenes de 1,8 cm y 11 pt: entra en 3 páginas con unas 7 líneas de margen para la reescritura
  del autor.
- **Las cifras** entran por `report/numbers.tex`, que `informe.py` genera desde
  `results/summary.json`, `results/e5_bombe.parquet` (las celdas de Turing) y
  `results/bench_demo2.json`. El periodo del odómetro sale del código (`core/stepping.py`). Una
  prueba comprueba que toda macro `\EL…` del informe exista.

### D-053 · LaTeX con Tectonic
El equipo no tenía LaTeX. Con la aprobación del autor se instaló Tectonic 0.17.0 (el zip oficial
para Windows de GitHub, SHA-256 verificado) en `%LOCALAPPDATA%\Programs\tectonic`, sin tocar el
PATH. `informe.py` busca latexmk en el PATH y Tectonic en el PATH, en la variable `TECTONIC` y en
esa carpeta. La primera compilación baja los paquetes de LaTeX (necesita internet esa vez).
`informe.tex` compila también con pdfLaTeX (por ejemplo, en Overleaf).

### D-054 · Docker
- **Imagen:** `python:3.12-slim` con uv 0.13.9 (la versión que generó `uv.lock`); las
  dependencias en su propia capa (`uv sync --frozen --no-dev --no-install-project`) y el entorno
  en `/opt/venv`, fuera de la carpeta del proyecto.
- **Usuario sin privilegios** («enigma»), con escritura solo en `NUMBA_CACHE_DIR` y
  `MPLCONFIGDIR`. `ENIGMA_LAB_ROOT=/app`.
- **Numba compilado en la imagen:** la construcción corre `warm_up()`, así que el contenedor
  arranca en unos segundos y no en los ~16 s de compilar.
- **Streamlit:** headless, en `0.0.0.0:8501`, sin vigilar archivos (en WSL la vigilancia sería
  por sondeo) y con chequeo de salud en `/_stcore/health`.
- **Sin internet:** la imagen trae las muestras del corpus y `results/`; `.dockerignore` deja
  fuera el corpus completo, `docs/presentacion/`, `report/` y las pruebas.

### D-055 · Streamlit no consulta la IP pública
Sin navegador (headless), Streamlit consultaba en internet la IP pública para imprimir una
«External URL». `.streamlit/config.toml` fija `browser.serverAddress = "localhost"`: no hay
consulta externa y la dirección impresa es la que se usa.

### D-056 · `st.iframe` en lugar de `components.html`
Streamlit 1.67 marca `st.components.v1.html` como obsoleto («se quita después del
01-06-2026»). Los cuatro componentes pasan a `st.iframe` con el mismo HTML; siguen siendo solo
dibujo (la regla clave del spec 3 no cambia).

### D-057 · Ninguna espera sin indicador (spec 8.3)
- **Al arrancar** (`Inicio.py` · `_setup_once`, con el indicador «Preparando Enigma Lab…»):
  precalienta Numba y precarga los módulos pesados (SciPy, pandas, networkx, los experimentos).
  Así ninguna página queda en blanco al abrirla.
- **Experimentos:** tablas en caché y figuras diferidas (D-051); correr un experimento en modo
  rápido muestra su indicador.
- **Estadística:** el cifrado de cientos de mensajes para el mapa de calor lleva indicador.

### D-058 · Dibujo del menú por componentes
Con WETTERBERICHT el menú suele tener varias componentes, y Kamada-Kawai sobre todo el grafo las
amontonaba. Ahora cada componente se dibuja aparte y las componentes van una al lado de la otra
(`cribs/menu.py` · `layout`). Con una sola componente (el menú de la diapositiva 11) el dibujo
no cambia.

### D-059 · Índices del arrastre del crib
En la animación del crib, los números de posición iban más angostos que las letras y se corrían
(en la posición 17, unos 220 px a la izquierda de su letra). Ahora cada número queda sobre su
letra, también en modo demo.

### D-060 · Banco de la demo 2: el de 60 casos
`results/bench_demo2.json` tenía sin commit una corrida de 30 casos (21-11-2026, 21:27 UTC,
commit `2cfa34b`) que el `RESUMEN.md` comprometido citaba. A pedido del autor se restauró la de
60 casos (18:25 UTC, commit `5b34896`), con el mismo código de la Bombe, y el resumen final la
cita.

### D-061 · Capturas del README
Se tomaron con el navegador integrado de la app de escritorio, con la ventana emulada a
1024 × 640; el navegador las guarda a 800 px de ancho (el tamaño del panel). El GIF de la demo 2
son seis de esas capturas, armadas con Pillow.

## Fase 5 · Extensiones P2 (22-11-2026)

### D-062 · Supuestos del catálogo de Rejewski (E7)
- **El modelo.** Rotores I, II y III y el reflector A, como Kuhl (2007): 3! = 6 órdenes ×
  17.576 posiciones = 105.456 configuraciones. El cableado del reflector A es el de Wikipedia
  (`core/wiring.py`); Kuhl cita a Marks y Weierud (2000), que lo determinaron.
- **El rotor central.** Durante las seis letras del indicador solo gira el derecho: la pulsación k
  (1 a 6) usa el aleatorizador en (izq, cen, der + k), porque los rotores avanzan antes de cada
  letra. Kuhl solo dice que su programa «simula el proceso del ciclómetro». En la máquina real el
  central se mueve en 176 de cada 676 posiciones del día (26,0 %; prueba
  `test_middle_rotor_moves_in_176_of_676_positions`): esos días la característica no es la del
  catálogo, y E7 lo mide con el tráfico (D-064).
- **Los anillos.** Con el central quieto cada permutación depende solo de la posición del núcleo
  (ventana − anillo). El catálogo se indexa por la posición del núcleo al empezar el indicador; los
  anillos solo cambian qué ventanas le corresponden. Una prueba con hypothesis comprueba la
  entrada del catálogo contra la máquina real, con anillos y plugboard, en las posiciones sin
  vuelta del central.
- **La característica** es la terna de estructuras de AD, BE y CF; se guarda como el número de la
  partición de 13 de cada una (`characteristic.characteristic_code`). El orden (primero A, luego D)
  no cambia la estructura: DA es conjugada de AD.
- **No coincide con Kuhl.** E7 da 21.225 características, 11.578 únicas y 1.728 en la más
  frecuente; Kuhl, 21.230, 11.466 y 1.771. No se ajustó nada. `scripts/kuhl_variantes.py` prueba 33
  variantes de los supuestos (paso real del central con y sin doble paso, registrando antes o
  después de avanzar, anillos AAA y ZZZ, la muesca corrida una letra, un odómetro puro, las
  posiciones de un odómetro real desde AAA, los cableados inversos, el reflector A girado y los
  reflectores B y C): ninguna reproduce sus cifras, y la suma de las diferencias con su tabla 2 va
  de 256 a 895 características (442 con nuestros supuestos). Coinciden la forma de la
  distribución y 14 de las 15 características de su tabla 1. El artículo tiene además erratas
  internas (VALIDACION, E7).

### D-063 · La cifra de la diapositiva 9
La diapositiva cita a Kuhl: «hay 21.230 estructuras distintas, y 11.466 señalan una sola
configuración». Como el catálogo de E7 no reproduce esas cifras, `cifras.py` las separa en dos:
- *105.456 configuraciones:* la calcula el catálogo (6 × 17.576) y coincide.
- *Kuhl: 21.230 · 11.466:* se comprueban contra lo transcrito en `data/reference/kuhl_2007.json`,
  como las cifras de Turing de la diapositiva 16 contra `turing_stops.csv`.

Las cifras propias de E7 van a la sección de la diapositiva 9 de `RESUMEN.md` y la diferencia, a
«Discrepancias», para decidir cómo decirlo en la diapositiva.

### D-064 · El tráfico de un día (E7)
- **La clave del día:** rotores I–III en algún orden, reflector A, anillos y posición del día al
  azar y 6 cables (Kuhl: «en 1932, la Enigma tenía seis cables»).
- **Las claves de mensaje son al azar** y uniformes: no se modela cómo las elegían los
  operadores.
- **El indicador** se cifra con la máquina real (`characteristic.indicator_permutations`): con el
  plugboard y con el central moviéndose cuando le toca.
- **Cuatro niveles de reconstrucción** por producto y por día (el máximo de los tres productos):
  1. las 26 letras vistas como primera letra;
  2. 25 letras (la última imagen, por eliminación);
  3. la permutación: la única completación con los ciclos en parejas;
  4. la característica: todas las completaciones con los ciclos en parejas tienen la misma
     estructura.
- **Cómo se cuentan las completaciones** (`traffic.completions`). Lo conocido forma ciclos cerrados
  y cadenas abiertas; completar es agrupar las cadenas en ciclos nuevos (un grupo de g cadenas se
  recorre en (g − 1)! órdenes). Para cada una de las 101 estructuras posibles se cuenta de cuántas
  formas se alcanza, con un conteo por multiconjuntos y memoria. Coincide con la fuerza bruta en
  150 de 150 casos de prueba (`tests/test_rejewski.py`) y en 300 de 300 al desarrollarlo. Basta
  distinguir 0, 1 y «2 o más», y la búsqueda para ahí. Determinado, sigue determinado.
- **La teoría** del coleccionista de cupones es exacta: las primeras letras de AD, BE y CF son
  sorteos uniformes e independientes, así que P(máx ≤ n) = P(T ≤ n)³, con la distribución de las
  letras distintas por una cadena de Markov (`traffic.coupon_cdf`).
- **N:** 4.000 días en modo completo y 400 en el rápido, hasta 600 mensajes por día (con 600, la
  probabilidad de que falten letras es del orden de 10⁻⁹ por día; si pasara, el experimento se
  detiene).
- **El catálogo encuentra el día** si la característica del día coincide con la de su
  configuración verdadera (orden y posición del núcleo).

### D-065 · El ataque de Gillogly (E8)
- **De dónde sale.** El artículo de Gillogly (1995) no está libre; se implementa como lo describen
  Ostwald y Weierud (2017): IC con los anillos fijos y el plugboard vacío en todas las ubicaciones;
  los 676 anillos del central y del derecho para las mejores; hill climbing del plugboard con cables
  de prueba, pasando del IC a los trigramas.
- **Parámetros:** las 200 mejores ubicaciones de la fase 1 pasan a la fase 2 y las 20 mejores de
  la fase 2, a la 3; gana el mejor puntaje de trigramas por letra. El hill climbing primero con el
  IC y luego con trigramas, como Sullivan y Weierud (según Ostwald y Weierud).
- **Trigramas:** la muestra alemana con la X como separador (`stats/ngrams.py`), igual que el
  verificador de la Bombe. En el modo completo los mensajes salen del corpus completo, que incluye
  la muestra (un tercio): un sesgo leve a favor del ataque, que se deja anotado.
- **Éxito:** el descifrado coincide con el texto en al menos el 90 % de las letras. Los resultados
  son bimodales: en E8, el 22,7 % de los mensajes se leyó completo, el 76,0 % quedó bajo el 20 % de
  letras correctas y solo el 1,2 %, entre el 20 % y el 36 %. El umbral no cambia nada.
- **Numba.** El primer núcleo de la fase 1 calculaba mal: dentro del `prange`, la posición no
  avanzaba y todas las ubicaciones daban el IC del propio cifrado. Se aisló el descifrado de una
  ubicación en una función (`gillogly._ic_from`) y una prueba compara el núcleo con Python puro.

### D-066 · Vecinas y reajuste de los anillos
- **El problema.** Con los anillos supuestos, el central y el izquierdo giran en la fase 1 en otra
  letra que en la máquina verdadera. En las primeras pruebas, varios mensajes con el orden
  correcto salían descifrados solo en parte (entre el 62 % y el 96 % de las letras): la fase 1
  había elegido la posición con el izquierdo o el central una posición corridos, en las dos
  direcciones.
- **Lo que se agregó** (no está en la descripción de Gillogly; es un detalle de esta
  implementación): la fase 2 prueba la posición y sus vecinas con el izquierdo o el central una
  posición atrás (4 variantes); y, con el plugboard ya encontrado, `refine` vuelve a elegir
  anillos y vecina (9 variantes, en las dos direcciones) por trigramas y sube otra vez, hasta 3
  veces mientras mejore. Con eso, cuando la ubicación verdadera llega a la fase 2, el mensaje se
  lee completo.

### D-067 · Presupuesto de E8 y qué significa la tasa de éxito
- **Modo completo:** los 60 órdenes (sin recorte), longitudes de 25 a 1.500 letras (12), 6, 8 y 10
  cables y 24 mensajes por celda: 864 mensajes, unos 25 minutos en este escritorio. La tasa de
  éxito es la del ataque tal cual, contra 1.054.560 ubicaciones.
- **Modo rápido:** solo los rotores I–III (6 órdenes; la clave también sale de ellos), 4 longitudes,
  6 y 10 cables y 4 mensajes por celda (unos 25 s). Su tasa es la de un atacante que sabe que los
  rotores son I–III: compite con 10 veces menos ubicaciones falsas en la fase 1. No se compara con
  el modo completo.
- **El «oráculo»:** el hill climbing desde la ubicación verdadera (orden, posición y anillos). Es
  lo que lograría el ataque si la fase 1 nunca fallara: una cota superior. Ostwald y Weierud se
  acercan a ella haciendo el hill climbing en las 27.418.560 ubicaciones, con días de cómputo.
- **Diagnóstico de la fase 1:** el puesto de la ubicación verdadera entre todas (sus 9 vecinas
  cuentan, D-066) y el que tendría con sus anillos verdaderos. Si la fase 1 probara también los
  anillos, la competencia crecería en proporción (por 26 con el anillo derecho).
- **La corrida.** El primer `make reproduce` (sobre `103df6c`) guardó los datos de E8 y se detuvo
  al dibujar su figura: con 0 éxitos de 24, el límite inferior de Wilson salía a un error de
  redondeo por encima de la proporción, y Matplotlib rechaza un bigote negativo. Se corrigió la
  figura (`67e022b`) y se repitió `make reproduce` entero sobre ese commit; las cifras de E1 a E8
  salieron idénticas en las dos corridas (todo usa la semilla 2026; solo cambian fechas y
  tiempos).

### D-068 · E7 y E8 en el informe y en las diapositivas
El informe sigue con sus 3 figuras (E4, E5 y E6; D-052): E7 y E8 entran en el texto, con sus
cifras por macros (`\ELrej…`, `\ELkuhl…`, `\ELataque…`), en lugar de la limitación «no se hizo la
fase opcional». Para las diapositivas hay respaldo 16:9 de las dos figuras (`make figuras`) y sus
datos en `r5_rejewski.csv` y `r6_ataque.csv`.

### D-069 · Página Rejewski
- **El día** se simula con la máquina real (D-064) y el control elige cuántos de sus 250 mensajes se
  ven. La página dice, por producto, cuántas letras se conocen y si la estructura o la permutación
  ya quedaron determinadas por el teorema.
- **Los ciclos** los dibuja `components/cycles.html` con las coordenadas que calcula Python
  (`ui/rejewski_view.py`): ciclos cerrados (el mismo color para la misma longitud en los tres
  productos), cadenas abiertas que terminan en «?» y letras sin datos. Si el teorema deja una sola
  completación, se dibuja la permutación completa y los arcos deducidos, no vistos, van punteados.
- **El catálogo** se construye una vez por proceso (1,4 s, con indicador) y se busca la
  característica del día; con la clave revelada se marca la configuración verdadera. La columna
  «verdadera» solo aparece al revelar la clave.

### D-070 · Página Ataque moderno
- El ataque corre al pulsar «Atacar» (de 1 a 6 s con los 60 órdenes), no a cada cambio de un
  control. Se guarda solo lo que se dibuja: el histograma del IC de la fase 1 (no el millón de
  valores), la traza del hill climbing y el descifrado.
- Se puede elegir entre los 60 órdenes (las ubicaciones de la Bombe) y los 6 de I–III.
- El puesto de la ubicación verdadera y las letras correctas solo se muestran con la clave revelada.

## Después de la fase 5 (22-11-2026)

### D-071 · Experimentos muestra lo guardado sin leer el corpus completo
- **El problema.** Al probar la imagen de Docker después de la fase 5, la página Experimentos se
  cortaba en la pestaña E4 con `FileNotFoundError`: para mostrar la tabla guardada,
  `e4_cribs.aggregate` recalculaba κ con el corpus completo, que no está en la imagen
  (`.dockerignore`) ni en un clon sin `make corpus`. E4 a E8 no se veían. Por la misma causa
  fallaban las descargas PNG y SVG de E4 y E6, y la tabla de E3 de la app usaba las frecuencias
  de la muestra: 8,07 % en lugar del 8,00 % guardado (alemán, 1.000 letras).
- **La decisión.** Con los resultados guardados, la página no recalcula nada que dependa del
  corpus. Las tablas de E3, E4 y E6 son las de `results/` (`e3_condiciones`, `e4_cribs` y
  `e6_banburismus`), y las descargas PNG y SVG de las ocho pestañas son las figuras de
  `results/figures/`, las mismas del informe (`ui/charts.figure_data`). «Correr ahora» sigue
  calculando con la muestra del corpus, que está en el repositorio.
- **No cambia ninguna cifra.** La tabla guardada de E4 es idéntica a la recalculada con el corpus
  completo, y la de E3 es la que ya usaba el resumen.
- **Las pruebas.** `test_experiments_page_without_the_full_corpus` corre la página sin el corpus
  completo y compara las tablas de E3 y E4 con las guardadas; con la versión anterior falla con
  el mismo error que en Docker. `test_saved_results_download_the_saved_figure` comprueba que la
  descarga es el archivo guardado y que no se dibuja nada.

### D-072 · La exposición se hace en este equipo (resuelve P-001)
El autor expone con este escritorio (i5-9400F, 6 núcleos, 16 GB), el mismo donde se midieron
todos los tiempos: el banco de la demo 2 (`results/bench_demo2.json`, con la configuración
recomendada en p95 9,8 s frente al presupuesto de 30 s) y las demos en el navegador y en
Docker. No hace falta repetir las mediciones en otro equipo, y «Cifrado del compañero» sigue la
configuración de ese banco (D-050).

### D-073 · Presentación, versión 2: sus cifras en el registro y lo que no coincide
- **Qué llegó.** El autor reemplazó las diapositivas y el guion de `docs/presentacion/` por la
  versión 2 (22-11-2026), hecha con `RESUMEN.md`: E7 en la diapositiva 9, el U-264 y E1 en la
  14, el alemán real en la 15, E5 en la 16, E6 en la 17 y el enlace del repositorio en la 21.
- **Las cifras medidas entran al registro.** `cifras.py` tenía solo cifras exactas o citadas, y
  las medidas iban solo en el resumen. Ahora están todas las de las diapositivas: 16 nuevas, 61
  en total. Las medidas (E1 y E4 a E7) salen de la corrida completa guardada en
  `results/summary.json`, la misma del resumen y del informe, sin volver a correr nada. Sin esa
  corrida (un clon sin resultados, o después de `make rapido`, que escribe en el mismo lugar),
  `SinCorrida` salta la prueba y el resumen muestra la cifra sin calcular, con el motivo: un
  `make rapido` no debe romper `make test`.
- **Cifras que la diapositiva redondea o da como cota.** «IC 95 % de ±0,25 puntos o menos» (E4)
  se comprueba como el mayor semiancho de los 20 IC, redondeado hacia arriba a la centésima. El
  «÷ 26» de la diapositiva 20 es la media geométrica de 0 a 2 lazos, √(paradas con 0 / paradas
  con 2); de 2 a 3 lazos quedan tan pocas paradas que el cociente es impreciso.
- **Lo que no coincide va a «Discrepancias»** (`resumen._guion_notes`), sin editar el guion: los
  pasos de la demo 2 (Ctrl+Enter muestra el menú pero no corre la Bombe; hay una sola barra),
  «Vector BDZGO» ya escribe AAAAA, el pendiente del banco ya cumplido (D-072), la comparación de
  tiempos de la diapositiva 16 y tres respuestas de «Preguntas probables». Las notas que la
  versión 2 dejó resueltas se quitaron, y el texto de la demo 2 en «Demos» nombra ahora «Correr
  la Bombe»: su versión anterior («se pega el cifrado y se pulsa Ctrl+Enter») originó el error
  del guion.
- **Guía de estudio.** El guion tiene ahora 10 preguntas probables; las 15 de la guía empiezan
  por ellas, en su orden. Para seguir en 15, las de los anillos y del rotor central se unieron, y
  la del alemán real frente a (25/26)^L queda entre las del tema 3, donde ya estaba. El modo
  robusto cuesta «unas 12 veces el tiempo», como en la corrida actual, y no «13 a 14».

### D-074 · Presentación, versión 3: el tiempo de la diapositiva 16 y las notas que quedan
- **Qué llegó.** El autor reemplazó las diapositivas y el guion por la versión 3 (23-11-2026),
  hecha con «Discrepancias» de `RESUMEN.md`. El guion corrige las ocho notas de la versión 2 y
  nada más. El PDF es el mismo mazo en vectores (texto y gráficos) en vez de una imagen por
  página: 184 KB en lugar de 5,6 MB, con el mismo texto salvo «frente a 0,009 s» en la 16. Se
  guarda con el nombre de siempre, `Romper Enigma presentación final.pdf`.
- **El tiempo de la diapositiva 16 se compara en los mismos menús.** La cifra del registro era
  0,11 s frente a 0,008 s, el promedio del modo Bletchley con todos los menús (8 a 16 letras).
  Ahora es frente a 0,009 s, el del Bletchley en los menús de 12 y 16 letras donde se midió el
  robusto, que es lo que dan las 12,0 veces. `e5_bombe.bletchley_same_menus` lo calcula para el
  registro y para el resumen.
- **Notas nuevas en «Discrepancias»**, ninguna sobre una cifra. El «9,8 s en el peor 5 %» del
  guion es el p95: el caso más lento tardó 14,9 s, 6,3 de ellos en «Verificar». El banco midió
  con mensajes de 78 letras, y el guion no fija el largo. La diapositiva 15 llama «IC del
  alemán» a κ = 0,080, el del alemán con X entre palabras, y la 23 da 0,076, el de solo letras.
  «Demos» muestra ahora el máximo del banco y el largo del mensaje: de su «p95» salió el «peor
  5 %».

## Pendientes de decidir

Ninguno.
