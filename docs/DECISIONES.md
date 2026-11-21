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

## Pendientes de decidir

### P-001 · Equipo de las mediciones de la demo 2
Este equipo es un escritorio (i5-9400F, 6 núcleos, 16 GB). El presupuesto de 30 s de la
demo 2 es del portátil del autor. `make bench-demo` ya existe; `RESUMEN.md` dice en qué
equipo se midió cada tiempo. Falta que el autor lo corra en el portátil y confirme la
configuración.
