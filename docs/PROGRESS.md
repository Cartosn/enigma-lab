# Progreso

Última actualización: 22-11-2026 · fase 5 cerrada: E7 (Rejewski) y E8 (ataque moderno). Docker
probado después de la fase 5; Experimentos ya funciona sin el corpus completo (D-071). Repositorio
remoto creado, con la CI en verde.

| Fase | Estado | Semana |
| --- | --- | --- |
| 0 · Andamiaje | Cerrada (20-11-2026) | 1 |
| 1 · Núcleo Enigma | Cerrada (20-11-2026) | 1 |
| 2 · Estadística y cribs | Cerrada (20-11-2026) | 1–2 (reunión con el profe) |
| 3 · Bombe | Cerrada (21-11-2026) | 2 |
| 4 · Banburismus | Cerrada (21-11-2026) | 3 |
| 5 · Extensiones P2 | Cerrada (22-11-2026), después de la fase 6 | 3 |
| 6 · Pulido y entrega | Cerrada (22-11-2026) | Fin de la 3 |

## Fase 5 · Extensiones P2

Se hizo después de cerrar la fase 6, sobre la entrega ya armada: lo que la fase 6 marcó como
«no se hizo» quedó actualizado (README, informe, `cifras.py`, la página Experimentos y este
documento).

**Criterio de aceptación** (spec, sección 9: «E7 comparado con Kuhl; E8 con su curva de éxito»):
se cumple.

| Criterio | Resultado |
| --- | --- |
| E7 comparado con Kuhl (21.230 / 11.466 / 1.771) | El catálogo da 21.225 / 11.578 / 1.728 con los supuestos documentados (D-062). No coincide del todo y no se ajustó nada: ninguna de 33 variantes de los supuestos reproduce las cifras de Kuhl (`scripts/kuhl_variantes.py`); la forma coincide (14 de las 15 clases de su tabla 1) y su artículo tiene erratas (VALIDACION) |
| Supuestos de E7, documentados y comparados | Solo gira el derecho durante el indicador (Kuhl dice que simula el ciclómetro, sin más); los anillos no importan; el catálogo se comprueba contra la máquina real con hypothesis; el central se mueve en 176 de cada 676 posiciones del día |
| E8 con su curva de éxito | Éxito según la longitud (25 a 1.500 letras) y los cables (6, 8 y 10), con 24 mensajes por celda y los 60 órdenes, con IC de Wilson y regresión logística (statsmodels): con 6 cables, la mitad de los mensajes se lee desde unas 314 letras (IC 95 % 273–362; Gillogly: unas 300); con 8, desde unas 845 (752–950); con 10 no se llega a la mitad (25 % con 1.500 letras; Gillogly: un solo éxito, con 1.463). Tiempo: 1,7 s por mensaje (5,6 s con 1.500 letras) |

`make test` da 335 pruebas que pasan en 2 min 4 s, con las lentas incluidas. `make lint` pasa sin
errores. `make reproduce` completo (corpus, E1 a E8, resumen y figuras) tarda **30 min 48 s** en
un clon limpio de `67e022b`, en este escritorio: E8, 25 min (1,7 s por mensaje); E5, 3 min 22 s;
E6, 49 s; E7, 21 s. La primera corrida, sobre `103df6c`, guardó todos los datos y se detuvo al
dibujar la figura de E8 (un bigote de Wilson negativo por redondeo, con 0 éxitos de 24); se
corrigió en `67e022b` y se repitió entera, con cifras idénticas (D-067). `make rapido`, con los
ocho experimentos en modo rápido, tarda 1 min 19 s (E8, 26 s). `make report`: 9 s; el informe
queda en 3 páginas justas, con poco margen para reescribir los párrafos `% REVISAR`.

**Docker después de la fase 5** (22-11-2026). La imagen que había era de antes de la fase 5 (el
Dockerfile cambió en `103df6c`). Desde un clon limpio de `9e55377`, `docker compose build
--no-cache` tarda 2 min 21 s: las dependencias, 26 s; Numba de la Bombe y de Gillogly, 18,6 s
dentro de la imagen; exportar la imagen, de 2,8 GB, 87 s. La app responde a `/_stcore/health`
3,1 s después de `docker compose up -d`. En el navegador integrado, contra el contenedor:
- Inicio, con 9 de 9 vectores, a lo sumo 6,3 s después de abrirla por primera vez.
- Rejewski carga en 3,3 s: el tráfico del día, los ciclos, el catálogo (3 candidatas, entre ellas
  la verdadera) y la comparación con Kuhl.
- Ataque moderno: 600 letras, 6 cables y 60 órdenes en 3,4 s, con el 100 % de las letras.
- Demo 1: «Vector BDZGO» y «Portada» responden al instante («Portada», 0,24 s después del clic).
  Caso de respaldo: barrido en 0,8 s y «Verificar» en 0,5 s.
- Demo 2 con un mensaje de 86 letras cifrado con «Clave aleatoria» en Máquina (menú de 15 letras
  y 0 lazos): barrido robusto de los 60 órdenes en 7,8 s y el mensaje descifrado letra por letra.
- Ninguna petición sale de localhost en las diez páginas, tampoco desde los componentes.
- **Experimentos fallaba; quedó corregido (D-071).** Al preparar la pestaña E4,
  `e4_cribs.aggregate` recalculaba κ con `data/corpora/completo/aleman.txt`, que la imagen no
  trae (`.dockerignore`), y la página se cortaba con `FileNotFoundError`: E4 a E8 no se veían.
  Pasaba lo mismo en un clon sin `make corpus` (comprobado con `ENIGMA_LAB_ROOT` apuntando al
  clon) y, por la misma causa, en las descargas PNG y SVG de E4 y E6. Además, la tabla de E3 de
  la app calculaba la columna teórica de la χ² con la muestra: 8,07 % frente al 8,00 % guardado
  (alemán, 1.000 letras). Ahora, con los resultados guardados, la página lee las tablas y las
  figuras de `results/`, y ninguna cifra cambia. Con la imagen reconstruida (30 s, con las
  dependencias en caché), las ocho pestañas se ven en el contenedor con las cifras guardadas
  (E4: 61,6 %, y la teoría con el IC del alemán, 61,4 %), las descargas de E4 y E6 entregan los
  archivos guardados sin dibujar nada, «Correr ahora» funciona con la muestra y ninguna petición
  sale de localhost. `make test`: 337 pruebas (2 nuevas) en 2 min 11 s; `make lint`, sin errores.

**Repositorio remoto** (22-11-2026): https://github.com/Cartosn/enigma-lab, público, con `main`
desde `0845913`. La CI (ruff, mypy y pytest en Ubuntu y Windows) corrió por primera vez y pasó:
337 pruebas en los dos sistemas, sin el corpus completo; 2 min 16 s en Ubuntu y 3 min 17 s en
Windows, con la instalación. El enlace ya está en el encabezado del informe (sigue en 3 páginas),
en el inicio rápido del README y en el pendiente de la diapositiva 21 de `RESUMEN.md`
(`resumen.py`).

**Qué quedó:**
- **`rejewski/`:**
  - `characteristic.py`: las seis permutaciones del indicador con la máquina real, AD, BE y CF, su
    estructura de ciclos y las 101 particiones de 13;
  - `catalog.py`: el catálogo de las 105.456 configuraciones con las tablas del aleatorizador de la
    Bombe (1,4 s), sus clases y la búsqueda;
  - `traffic.py`: un día de tráfico, la completación con el teorema de los ciclos en parejas
    (comprobada contra la fuerza bruta) y el coleccionista de cupones exacto.
- **`attacks/`:** `gillogly.py` (las tres fases en Numba, con vecinas y reajuste de anillos,
  D-066) y `hillclimb.py` (IC y trigramas, y la búsqueda parcial de la E de Ostwald y Weierud).
- **Experimentos:** E7 (exacto el catálogo; 4.000 días de tráfico) y E8 (864 mensajes con los 60
  órdenes), con sus figuras y sus datos de referencia: `data/reference/kuhl_2007.json` y
  `ostwald_weierud_2017.json`.
- **App:** páginas Rejewski (el tráfico de un día, AD, BE y CF dibujadas como ciclos con
  `components/cycles.html`, la búsqueda en el catálogo y los tamaños de clase frente a Kuhl) y
  Ataque moderno (la curva del IC de la fase 1, la subida del hill climbing, el descifrado y la
  curva de éxito de E8); pestañas E7 y E8 en Experimentos; las dos páginas respetan el modo demo y
  se revisaron en el navegador. Los núcleos nuevos se precalientan al abrir la app y en la
  construcción de la imagen de Docker (el Dockerfile cambió, pero la imagen no se volvió a
  construir: Docker Desktop estaba apagado).
- **Integración:** la sección de la diapositiva 9 en `RESUMEN.md`, E8 en «Otros resultados» (para
  «¿Hoy se rompería por fuerza bruta?»), la diferencia con Kuhl en «Discrepancias»,
  `r5_rejewski.csv` y `r6_ataque.csv`; dos cifras de la diapositiva 9 en `cifras.py` (D-063); el
  respaldo 16:9 de E7 y E8; las macros `\ELrej…`, `\ELkuhl…` y `\ELataque…` del informe, con el
  párrafo nuevo marcado `% REVISAR`.
- **Documentos:** DECISIONES D-062 a D-070, VALIDACION, FUENTES (Kuhl y Ostwald y Weierud, leídos
  el 22-11-2026), ARQUITECTURA, el tema 6 de la guía de estudio, README (dos capturas nuevas).

**Cifras obtenidas** (modo completo, semilla 2026, commit `103df6c`):
- **E7, el catálogo** (exacto): 105.456 configuraciones; 21.225 características distintas; 11.578
  únicas (54,5 %); la más frecuente, (13 13)(13 13)(13 13), con 1.728 (Kuhl: 21.230, 11.466 y
  1.771). Una configuración al azar comparte su característica con 111,7 en promedio (mediana 20).
- **E7, el tráfico** (4.000 días):
  - ver las 26 letras de AD, BE y CF: 128,0 mensajes (IC 95 % 127,0–129,1; teoría exacta 127,1); de
    una sola permutación, 100,9 (26·H₂₆ = 100,2);
  - por eliminación: 90,5 (teoría 90,0);
  - con el teorema de los ciclos en parejas: la característica en 49,1 y las tres permutaciones en
    60,7 (IC 60,3–61,0), los «unos sesenta» de Rejewski;
  - el catálogo encuentra la configuración del día en el 75,4 % de los días (IC 74,0 %–76,7 %): en
    el 100 % de los días en que el central no se mueve durante el indicador y en el 1,4 % de los
    demás.
- **E8:** (864 mensajes, 24 por celda, con los 60 órdenes):
  - éxito: 43,1 % de los mensajes con 6 cables, 21,9 % con 8 y 3,5 % con 10 (de 25 a 1.500 letras);
    con 1.500 letras, 96 %, 83 % y 25 %;
  - regresión logística: logit p = −6,85 + 5,67·log₁₀ L − 1,22·cables (pseudo-R² 0,55); la mitad
    de los mensajes se lee desde unas 314 letras con 6 cables (IC 95 % 273–362) y 845 con 8
    (752–950); con 10, fuera de las longitudes medidas;
  - con la ubicación dada: todos los mensajes desde 200 letras; con 100, el 79 %, el 63 % y el 29 %
    (6, 8 y 10 cables), y con la búsqueda parcial de la E, el 100 %, el 79 % y el 46 %; con 25
    letras, casi ninguno (1 de 24 con 6 y con 8 cables, con la búsqueda parcial);
  - la fase 1: con los anillos verdaderos, la ubicación correcta quedaría primera (en mediana) desde
    200, 600 y 1.500 letras con 6, 8 y 10 cables; con los supuestos, con 10 cables y 1.500 letras,
    su puesto mediano es el 7.190;
  - los resultados son bimodales: el 22,7 % de los mensajes se leyó completo, el 76,0 % quedó bajo
    el 20 % de letras correctas y el 1,2 %, entre el 20 % y el 36 %; ningún mensaje se leyó con el
    orden equivocado;
  - tiempo: 1,7 s por mensaje en promedio (5,6 s con 1.500 letras), unos 25 min todo E8.
- **Cifras de la presentación:** 45 de 45 coinciden; ninguna queda sin calcular.

**Qué falta:** nada del código.

**Pendiente del autor:**
- actualizar con `results/presentacion/` la diapositiva 9 (la diferencia con Kuhl
  está en «Discrepancias»), la respuesta a «¿Hoy se rompería por fuerza bruta?» (E8) y el enlace
  del repositorio en la diapositiva 21;
- reescribir con su voz el párrafo nuevo del informe (`% REVISAR`, «Rejewski y ataque moderno»);
- lo que ya estaba pendiente: `make bench-demo` y el ensayo en el portátil (P-001).

## Fase 6 · Pulido y entrega

**Criterio de aceptación:** se cumple en este equipo. La sección 10 está completa (README,
informe, datos para las diapositivas y prueba final desde un clon limpio) y las dos demos del
guion corren dentro de su tiempo. Falta repetir el banco y el ensayo en el portátil del autor
(P-001).

| Criterio | Resultado |
| --- | --- |
| README (spec 10) | En español, con 5 capturas y el GIF de la demo 2 (`docs/img/`), inicio rápido con Docker y en local, `make reproduce`, estructura, validación, limitaciones (la fase 5 entre ellas) y fuentes |
| Informe | `report/informe.pdf`: 3 páginas a 11 pt, una columna, con 3 figuras (E4, E5 y E6) y 1 tabla (E1 y E2); todas las cifras entran por `report/numbers.tex` (108 macros generadas desde los resultados); los párrafos de análisis van marcados `% REVISAR` |
| Datos para las diapositivas | `results/presentacion/` (RESUMEN.md, cifras.json y los CSV) y el respaldo 16:9 oscuro de E2 a E6 en `results/figures/slides/` |
| Modo demo sin internet | Ninguna petición sale de localhost (revisado en el navegador, también con la app en Docker); Numba se precalienta al abrir la app |
| Demo 1 (diapositiva 4, 45 s) | «Vector BDZGO» y «Portada» responden en 0,18 s del clic al texto; el resto lo pone la exposición |
| Demo 2 (diapositiva 12, 1:15) | Un caso real de compañero, en modo robusto con los 60 órdenes: barrido y máquina de verificación en 10,3 s, «Verificar» en 1,1 s y el mensaje descifrado letra por letra |
| Prueba final desde un clon limpio | Clon de `395c9b3` en una carpeta temporal. `docker compose up`: imagen construida (Numba compilado en 12,2 s dentro de ella) y app respondiendo en 2 min 14 s; el caso de respaldo se descifró en el contenedor sin ninguna petición externa. `make install` (8 s) y `make reproduce` (5 min 30 s, con la descarga del corpus): sin errores, y las cifras iguales a las comprometidas (solo cambian fechas y tiempos) |

`make test` da 305 pruebas que pasan y 1 cifra sin calcular (la de Kuhl, de la fase 5), en
1 min 49 s. `make lint` pasa sin errores. `make reproduce` completo (corpus, E1 a E6, resumen
y figuras) tarda 4 min 29 s en este equipo, y `make report`, 9 s (la primera vez, 1 min 40 s,
porque Tectonic baja sus paquetes).

**Qué quedó:**
- **Modo demo** (D-049):
  - letra de 20 px como mínimo en toda la app, también en los gráficos (plantilla de 22 px) y,
    con la barra lateral plegada, de 18 a 21 px dentro de las animaciones;
  - oculta los «¿Qué estoy viendo?», la clave de Máquina, las tablas largas, las descargas y
    la comparación con y sin diagonal board;
  - el resultado en grande en Máquina y en La Bombe, con la lectura con la X como espacio;
  - queda en la URL (`?demo=1`): sobrevive a una recarga y se puede abrir directo;
  - en Máquina, solo «Vector BDZGO» y «Portada»; en La Bombe, «Cifrado del compañero» y
    «Caso de respaldo», y el menú visible, como pide el guion.
- **«Cifrado del compañero»** (D-050): vacía el cifrado y aplica la configuración que
  recomendó `make bench-demo` en el equipo. Al recorrer la demo en el navegador apareció un
  error real: el modo volvía a «Bletchley» al pegar el cifrado. Quedó corregido y probado.
- **Reglas de 8.3:**
  - *Nada bloquea más de 1 s sin indicador:* Experimentos tardaba de 5 a 8 s en blanco al
    abrirse; con las tablas en caché y las figuras diferidas abre en menos de 1 s, y los
    módulos pesados se precargan al arrancar, con el indicador «Preparando Enigma Lab…»
    (D-051, D-057).
  - *Cada página tiene su «¿Qué estoy viendo?»:* las 8; una prueba lo comprueba.
  - *Todo gráfico se exporta:* la figura desde la barra de Plotly (PNG a 2x) y los datos con
    «Datos (CSV)», sacados de la propia figura; las animaciones exportan su traza, sus
    alineaciones o sus aristas (D-051).
- **Correcciones encontradas al revisar la app:** los índices del arrastre del crib no
  quedaban sobre su letra (D-059); el menú amontonaba sus componentes (D-058); y los
  componentes pasan de `components.html`, obsoleto, a `st.iframe` (D-056).
- **Docker** (D-054, D-055): `Dockerfile`, `docker-compose.yml` y `.dockerignore`; Python 3.12
  con uv 0.13.9 y `uv sync --frozen --no-dev`; Numba compilado dentro de la imagen; usuario sin
  privilegios; `ENIGMA_LAB_ROOT` y `NUMBA_CACHE_DIR` con escritura; Streamlit headless en el
  puerto 8501; la app funciona sin internet.
- **Informe** (D-052, D-053): `report/informe.tex`, `informe.py` (cifras y compilación) y
  `figuras.py` (figuras del informe y respaldo de las diapositivas); `make report` y
  `make figuras`. Tectonic 0.17.0 instalado en la carpeta de usuario.
- **Documentos:**
  - README final, con capturas tomadas en el navegador integrado y un GIF de la demo 2 (D-061);
  - guía de estudio: índice de dónde está cada algoritmo, el tema 6 (Rejewski y el ataque
    moderno, solo teoría) y las 15 preguntas más probables, con las 6 del guion;
  - ARQUITECTURA con el diagrama al día y la imagen de Docker;
  - DECISIONES D-049 a D-061; el banco de la demo 2 de 60 casos, a pedido del autor (D-060).

**Tiempos medidos en este equipo** (escritorio i5-9400F, 6 núcleos, 16 GB; navegador
integrado):
- **Arranque de la app** con la caché de Numba en disco: 5,6 s hasta ver Inicio, con el
  indicador visible. Con la caché vacía, compilar Numba toma 16,4 s; la imagen de Docker ya la
  trae compilada (12,4 s al construirla).
- **Demo 1:** del clic en «Portada» al texto descifrado, 0,18 s.
- **Demo 2,** caso de compañero cifrado en Máquina con «Clave aleatoria» (86 letras, menú de 16
  letras, 3 componentes y 0 lazos, con vuelta del central en la letra 8): 388.817 paradas y 618
  hipótesis consistentes; barrido y máquina de verificación en 10,3 s desde el clic (en una
  segunda corrida, para el GIF, el barrido marcó 7,4 s); «Verificar» en 1,1 s. Es un caso
  difícil: sin lazos.
- **Caso de respaldo** (plan B) dentro del contenedor: barrido en 2,4 s y «Verificar» en 0,9 s.
- **Docker:** la primera construcción tardó 2 min 37 s (con las descargas); la imagen pesa
  2,79 GB y responde a `/_stcore/health` 4 s después de `docker compose up`.

**Cifras obtenidas** (modo completo, semilla 2026): las de las fases 1 a 4, sin cambios; la
corrida final las reprodujo. Las del informe están en `report/numbers.tex`:
- 10.000 de 10.000 claves iguales a py-enigma; 9 de 9 vectores; 0 puntos fijos en 200.000
  letras.
- E4: con 13 letras sobrevive el 60,1 % de las alineaciones falsas (alemán real: 61,6 %).
- E5: 678 · 26,3 · 0,99 · 0,11 paradas falsas por orden con 12 letras y 0 a 3 lazos (Turing:
  820 · 31 · 1,2 · 0,04); 15 de 17 celdas de su tabla entre la mitad y el doble.
- E6: 983 letras en profundidad (Wald: 929; exacto: 959,7).
- **Cifras de la presentación:** 43 de 43 coinciden; la de Kuhl queda sin calcular (fase 5).

**Qué falta:** nada del código. La fase 5 (Rejewski y el ataque moderno) no se hizo en esta fase;
se hizo después (ver «Fase 5»).

**Pendiente del autor:**
- correr `make bench-demo` en el portátil y ensayar allí las dos demos (P-001);
- actualizar con `results/presentacion/` la configuración de la demo 2 y los
  ajustes del guion;
- reescribir con su voz los párrafos `% REVISAR` del informe;
- crear el repositorio remoto, para la CI y el enlace de la diapositiva 21 (y ponerlo en el
  encabezado del informe).

## Fase 4 · Banburismus

**Criterio de aceptación:** se cumple.

| Criterio | Resultado |
| --- | --- |
| Simulación del SPRT comparada con la aproximación de Wald (929 y 1.062 letras) | E6, con letras sueltas, tasa 1/17 y la máquina real (2.000 pares): 983 letras en profundidad (IC 95 % 954–1.012) y 1.090 al azar (1.061–1.120) |
| La diferencia, explicada | Es el sobrepaso de los umbrales. El cálculo exacto da 959,7 y 1.067,4, dentro de los dos IC. En profundidad, 30,7 de las 30,9 letras de diferencia con Wald salen del sobrepaso de arriba, de 0,65 dB en promedio. Al azar, la diferencia es de 5,1 letras: 2,4 por el sobrepaso de abajo y 2,9 porque el error real (0,86 %) queda bajo el 1 % (D-048) |

`make test` da 281 pruebas que pasan y 1 cifra pendiente (fase 5), en 1 min 45 s, con las
lentas incluidas. `make lint` pasa sin errores. `make reproduce` completo (corpus y E1 a E6)
tarda 4 min 20 s en este equipo; E6, 46 s.

**Qué quedó:**
- **`banburismus/`:**
  - `depth.py`:
    - pares de mensajes en profundidad, cifrados con la máquina por lotes;
    - el desplazamiento verdadero, que sale de comparar los estados de la máquina (D-042);
    - texto sintético con tasa 1/17, o fragmentos del corpus que no se solapan.
  - `scoring.py`: decibanes de Turing, modelo de rachas para bigramas, trigramas y
    tetragramas medido en el corpus (D-044), puntaje por desplazamiento y trayectorias.
  - `sprt.py`:
    - umbrales y aproximación de Wald;
    - cálculo exacto con sobrepaso y su descomposición (D-048);
    - el SPRT en Numba, con una versión en Python para las pruebas.
- **E6:**
  - *Factores:* dos fuentes de texto, cuatro puntuaciones, tres umbrales y solapamientos de
    25 a 10.000 letras.
  - *Medidas:* aciertos, letras hasta decidir, identificación del desplazamiento y curvas
    ROC (D-045).
- **Resumen y cifras:**
  - la sección de la diapositiva 17 y `r4_banburismus.csv`;
  - `r4_roc.csv` y `r4_trayectorias.csv`, para dibujarla (D-046);
  - seis cifras nuevas en `cifras.py` (diapositivas 13 y 17).
- **App:**
  - página Banburismus: dos mensajes con el desplazamiento oculto, decibanes por
    desplazamiento, trayectorias con los umbrales, las cuatro puntuaciones y la curva ROC;
  - pestaña E6 en Experimentos;
  - las dos revisadas en el navegador.
- **`save_figure`** guarda el PNG a 2x (D-047); antes salía a 1x.
- **Documentos:**
  - guía de estudio: el tema 5 y «¿Qué es un decibán?»;
  - VALIDACION y DECISIONES (D-042 a D-048);
  - ARQUITECTURA y FUENTES: Wikipedia «Banburismus» y Wald (1945);
  - README.

**Cifras obtenidas** (modo completo, semilla 2026, 2.000 pares por fuente):
- **Turing:**
  - +1,845 dB por repetición y −0,093 por no repetición;
  - +0,0211 y −0,0184 dB por letra;
  - umbrales de ±19,96 dB;
  - Wald: 929 y 1.062 letras.

  Las seis cifras coinciden con las diapositivas 13 y 17.
- **SPRT con letras sueltas y tasa 1/17:**
  - *Simulación:* 983 letras en profundidad y 1.090 al azar, con errores de 1,1 % y 1,2 %.
  - *Cálculo exacto:* 959,7 y 1.067,4, con errores de 0,99 % y 0,86 %.
  - *Sobrepaso medio:* 0,65 dB arriba y 0,045 abajo.
- **Tasa de repetición del corpus:**
  - 0,0802 con la X (1 de cada 12,5) y 0,0757 sin ella (1 de cada 13,2), frente a
    1/17 = 0,0588;
  - medida con la máquina, en profundidad, 1 de cada 12,5, y al azar, 1 de cada 26.
- **Alemán real, con α = β = 1 %** (letras hasta decidir):

  | Puntuación | En profundidad | Al azar | Errores |
  | --- | --- | --- | --- |
  | Letras sueltas, tasa 1/17 (Turing) | 332 | 1.090 | 0 % y 0,65 % |
  | Letras sueltas, tasa del corpus | 262 | 323 | 1,8 % y 0,55 % |
  | Bigramas y trigramas | 254 | 357 | 1,15 % y 0,75 % |
  | Hasta tetragramas | 254 | 357 | 1,15 % y 0,75 % |

  Con texto real, la profundidad se confirma mucho antes que con 1/17. Los multigramas no
  aceleran mucho frente a letras sueltas con la tasa del corpus, pero dejan el error en
  torno al 1 %: las repeticiones del texto real vienen en racimos.
- **Identificación del desplazamiento.** El verdadero gana entre los 51 en esta fracción de
  pares, con 100, 200 y 400 letras de solapamiento:
  - alemán, letras sueltas: 39 %, 64 % y 88 %;
  - alemán, bigramas y trigramas: 42 %, 67 % y 90 %;
  - tasa 1/17: 13 %, 22 % y 40 %.
- **AUC con 200 letras:** 0,824 con tasa 1/17; 0,953 en alemán con letras sueltas y 0,956
  con bigramas y trigramas.
- **Cifras de la presentación:** 43 de 43 coinciden; la de Kuhl llega en la fase 5.

**Qué falta (fase 5, P2, solo si alcanza el tiempo):** Rejewski (E7) y el ataque moderno
(E8). Después, la fase 6: modo demo completo, Docker, informe y entrega.

**Pendiente del autor:**
- actualizar con `results/presentacion/` las diapositivas 13 y 17;
- correr `make bench-demo` en el portátil y confirmar la configuración de la demo 2
  (P-001);
- crear el repositorio remoto.

## Fase 3 · Bombe

**Criterios de aceptación:** se cumplen.

| Criterio | Resultado |
| --- | --- |
| Pruebas de 6.4 (200 casos) | Parada verdadera 200 de 200; clave equivalente 200 de 200 |
| Un orden en menos de 3 s | 0,006 s en modo Bletchley y 0,10 s en robusto (E5, solo el barrido) |
| Los 60 órdenes en menos de 2 min | 1,9 s en modo Bletchley (página La Bombe, caso de respaldo); en robusto con WETTERBERICHT, p50 5,6 s y p95 7,3 s (banco de la demo 2) |
| Paradas comparadas con la tabla de Turing | E5: con 12 letras, 678 · 26,3 · 0,99 · 0,11 por orden (Turing: 820 · 31 · 1,2 · 0,04); 15 de 17 celdas entre la mitad y el doble |

Además:
- **6.3:** la Bombe en Numba coincide con la de referencia en 24 casos.
- **Caso de respaldo (6.5):** en modo Bletchley para en II-III-I y el verificador
  descifra las 78 letras.
- **CyberChef (P-003):** da las mismas paradas en 3 de 3 casos; en el más largo, 84 con su
  stecker. Su máquina de verificación deja las mismas paradas, con los mismos steckers,
  que nuestra etapa 1.

`make test` da 248 pruebas que pasan y 2 cifras pendientes (fases 4 y 5), en unos 2 min,
con las lentas incluidas. `make lint` pasa sin errores. `make reproduce` completo
(corpus y E1 a E5) tarda 3 min 23 s en este equipo; E5, 2 min 44 s.

**Qué quedó:**
- **`bombe/`:**
  - `scrambler.py`: el aleatorizador de las 17.576 posiciones, por orden.
  - `wiring.py`: el menú como cables, aristas y pares del diagonal board.
  - `bombe_numba.py`: el barrido con union-find, con salida temprana, y la máquina de
    verificación.
  - `sweep.py`: ajustes, modos Bletchley y robusto, paradas como arreglos y la parada
    verdadera de una clave conocida.
  - `bombe_reference.py`: la misma Bombe en Python puro, para las pruebas.
  - `checker.py`: el verificador. Hace el puntaje rápido, prueba los 676 anillos, completa
    el plugboard por hill climbing y da la clave equivalente.
  - `cases.py`: los casos de prueba compartidos.
- **`stats/ngrams.py`:** modelo de 4 letras interpolado y puntaje por la regla de la
  cadena.
- **E5,** con la tabla de Turing completa en `data/reference/turing_stops.csv`.
  «Letras del menú» son vértices (D-031, resuelve P-002).
- **App:**
  - página La Bombe, con menú, configuración, barrido con barra, contador, cronómetro y
    tambores; tabla de paradas, «Verificar» y comparación con y sin diagonal board; todo
    revisado en el navegador;
  - pestaña E5 en Experimentos;
  - rotores permitidos en «Clave aleatoria»;
  - precalentado de Numba al arrancar.
- **Demo 2:** `scripts/bench_demo2.py` y `make bench-demo`.
- **Documentos:**
  - guía de estudio (tema 4 y respuestas del guion);
  - VALIDACION (6.2 a 6.5 de la Bombe);
  - DECISIONES (D-031 a D-041);
  - ARQUITECTURA y FUENTES.

**Cifras obtenidas** (modo completo, semilla 2026, commit `66213fd`; el banco de la demo 2,
commit `5b34896`, con el mismo código de la Bombe):
- **E5, 12 letras, con diagonal board y en modo Bletchley:**
  - Paradas falsas por orden con 0 a 3 lazos: 678 · 26,3 · 0,99 · 0,11.
  - IC 95 %: 672–684; 25,1–27,4; 0,77–1,21; 0,05–0,17.
  - Turing: 820 · 31 · 1,2 · 0,04.
  - En 60 órdenes: 59,4 con 2 lazos (Turing: 72) y 6,6 con 3 (Turing: 2,4).
- **Toda la tabla de Turing:** en 15 de 17 celdas con valor exacto, las hipótesis
  abiertas por orden quedan entre la mitad y el doble de la estimación de Turing. Con 8
  letras y sin lazos: 37.546 hipótesis por orden (Turing: 40.000) en 17.219 posiciones.
- **Sin diagonal board** (12 letras, 0 a 3 lazos): 17.575 · 17.040 · 729 · 27,4 paradas
  por orden.
- **Éxito:**
  - El modo Bletchley encuentra la parada verdadera en el 55,0 % de los menús: el central
    se movió dentro del tramo en el 45,0 %, y sin esa vuelta la encuentra en el 100 %.
  - El modo robusto la encuentra en el 98,0 %, con 13,9 veces el tiempo y 10,9 veces las
    paradas.
- **Tiempo por orden** (solo el barrido, con las tablas precalculadas): 0,006 s en modo
  Bletchley y 0,10 s en robusto.
- **Demo 2** (`make bench-demo`, 60 casos por configuración, en este escritorio):

  | Configuración | Éxito (IC 95 %) | p50 | p95 |
  | --- | --- | --- | --- |
  | 60 órdenes, modo robusto | 60 de 60 (94 %–100 %) | 6,4 s | 9,8 s |
  | Rotores I–III, modo robusto | 60 de 60 (94 %–100 %) | 1,3 s | 1,7 s |
  | Crib WETTERBERICHTXFUER, 60 órdenes | 59 de 60 (91 %–100 %) | 8,9 s | 10,4 s |

  La falla del crib largo tuvo dos movimientos del central dentro del tramo, que ningún
  modo cubre. Recomendada, por ser la más simple que cumple: los 60 órdenes en modo
  robusto. Si en el portátil su p95 se acerca a 30 s, la de rotores I–III dio el mismo
  éxito en menos de 2 s. Falta medir en el portátil (P-001).
- **Cifras de la presentación:** 37 de 37 coinciden; 2 llegan en las fases 4 y 5.

**Qué falta (fase 4):**
- `banburismus/`: decibanes y SPRT;
- la página Banburismus;
- E6, con la simulación del SPRT frente a la aproximación de Wald (929 y 1.062 letras).

**Pendiente del autor:**
- correr `make bench-demo` en el portátil y confirmar la configuración de la demo 2
  (P-001);
- crear el repositorio remoto.

## Fase 2 · Estadística y cribs

**Criterios de aceptación:** se cumplen.

| Criterio | Resultado |
| --- | --- |
| Cifras de 5.2 exactas | Todas (desde la fase 0; E2 las reúne) |
| E4 coincide con (25/26)^L dentro del IC | Texto aleatorio: dentro del IC 95 % en 10 de 10 longitudes |

Además, los casos de 6.5 (diapositivas 10 y 11 y caso de respaldo) pasan exactos.
`make test` da 189 pruebas que pasan y 3 cifras pendientes (fases 3 a 5), en unos 40 s.
`make lint` pasa sin errores. `make reproduce` completo (corpus y E1 a E4) tarda 39 s en
este equipo.

**Qué quedó:**
- **Corpus:**
  - alemán: Fontane y Kafka, 578.365 letras;
  - español: Cervantes, 1.620.450 letras;
  - se descarga de un espejo de Gutenberg con SHA-256 verificado;
  - el repo trae muestras de unos 200 KB por idioma.
- **`stats/`:** normalización según el spec, frecuencias, IC, χ², la antifrecuencia del
  cifrado y su potencia teórica, matriz plano × cifrado, cuadrigramas e intervalos.
- **`cribs/`:** arrastre del crib, escalar y vectorizado, y menú con lazos, aristas en
  lazos y letra de prueba.
- **Experimentos:** E2, E3 y E4, con figuras para el informe. El resumen agrega la
  diapositiva 15 y `r2_cribs.csv`.
- **App:**
  - páginas Espacio de claves, Estadística del cifrado, Cribs y menús, y Experimentos;
  - dos componentes nuevos, el arrastre del crib y el grafo del menú, que solo dibujan
    datos de Python;
  - todo revisado en el navegador.
- **Documentos:** guía de estudio (tema 3), VALIDACION (6.5), DECISIONES (D-024 a
  D-030), FUENTES (corpus) y ARQUITECTURA.

**Cifras obtenidas** (modo completo, semilla 2026, commit `6bd632e`):
- **E3:**
  - El IC del corpus alemán es 0,0757 (Pommerening: 0,0758) y el del español, 0,0750.
  - Con 1.000 letras, el IC del alemán baja de 0,0760 en el plano a 0,0385 en el
    cifrado.
  - La χ² rechaza la uniformidad del 100 % de los planos y del 10,0 % de los cifrados.
    La antifrecuencia (1 − f_c)/25 predice 8,0 %: el cifrado no es del todo uniforme.
  - No hubo ningún punto fijo en 3.850.000 letras.
- **E4, texto aleatorio:**
  - L = 13: sobrevive el 60,1 % de las alineaciones falsas (IC 59,9 %–60,3 %; teoría
    60,1 %).
  - L = 50: el 14,1 % (teoría 14,1 %).
- **E4, alemán real:**
  - L = 13: el 61,6 % (61,4 %–61,8 %); L = 50: el 15,4 %.
  - (25/26)^L queda fuera del IC en las 10 longitudes. La teoría corregida
    (1 − (1 − κ)/25)^L, con κ = 0,0802, queda dentro en las 10.
- **Cifras de la presentación:** 36 de 36 coinciden; 3 llegan en las fases 3 a 5.

**Qué falta (fase 3):**
- la Bombe: aleatorizador precalculado, versión en Numba y versión de referencia;
- el verificador;
- la página La Bombe;
- E5, con la tabla de Turing;
- `make bench-demo` para la demo 2;
- CyberChef para la Bombe.

**Pendiente del autor:**
- confirmar el equipo de la demo 2 (P-001);
- crear el repositorio remoto;
- encender Docker Desktop si quiere la validación automática con CyberChef (P-003).

## Fase 1 · Núcleo Enigma

**Criterios de aceptación:** se cumplen todos.

| Criterio | Resultado |
| --- | --- |
| Vectores de 6.1 | 9 de 9, con un mensaje real del U-264 (1942) |
| 100 % frente a py-enigma en 10.000 claves | 10.000 de 10.000 (IC 95 % de Wilson 99,96 %–100 %) |
| Propiedades | Involución, sin puntos fijos y lotes = escalar, con hypothesis |
| Periodo 16.900 y 676 fuera del ciclo | Un solo ciclo de 16.900; 676 fuera |
| La animación reproduce la traza | Lo comprueba una prueba (el JSON es la traza) y se vio en el navegador |

`make test` da 150 pruebas que pasan y 5 cifras pendientes, en unos 35 s en este equipo.
`make lint` (ruff y mypy) pasa sin errores.

**Qué quedó:**
- **Núcleo (`core/`):**
  - `wiring.py`: cableados I–VIII, Beta, Gamma y los reflectores A, B, C, B delgado y C
    delgado, tomados de Wikipedia.
  - `stepping.py`: paso con doble paso y estructura de ciclos.
  - `machine.py`:
    - `EnigmaConfig` inmutable, que lee hojas de claves;
    - `Enigma` con `encrypt` y `trace`, para Enigma I, M3 y M4.
  - `batch.py`: cifrado por lotes con tablas precalculadas.
  - `random_keys.py`: claves aleatorias con semilla.
  - `vectors.py`: los vectores de 6.1.
- **Validación:**
  - py-enigma en 10.000 claves (E1 y `tests/test_pyenigma.py`);
  - CyberChef a mano en 6 casos, todos iguales;
  - hypothesis.

  Detalle en `docs/VALIDACION.md`.
- **Experimentos:** marco común, E1 y `make reproduce`, `make rapido`,
  `make experimento` y `make resumen`. El registro único de cifras está en `cifras.py`.
- **App:**
  - Página Máquina, con:
    - los preajustes «Vector BDZGO», «Portada» y «Ejemplo histórico»;
    - los botones «Clave aleatoria» y «Reiniciar posición»;
    - salida en grupos de 5;
    - comprobaciones en vivo: cifrar la salida devuelve la entrada y no hay puntos fijos;
    - la animación SVG de la traza.
  - En Inicio, el estado de la validación en vivo.
- **Documentos:** VALIDACION, la guía de estudio (tema 2), DECISIONES (D-015 a D-023),
  FUENTES y ARQUITECTURA.

**Cifras obtenidas** (E1 en modo completo, semilla 2026, 19 s):
- **py-enigma:** 10.000 de 10.000 casos con 1.007.710 letras: Enigma I 4.945 de 4.945,
  M3 2.568 de 2.568 y M4 2.487 de 2.487.
- **Propiedades:** 2.000 claves de Enigma I con 200.000 letras dan 0 puntos fijos,
  involución en las 2.000 claves y lotes iguales al escalar en las 2.000.
- **CyberChef:** 6 de 6, incluido el U-264 (232 letras) y una clave M3 con el rotor VI y
  el reflector C.
- **Cifras de la presentación:** 29 de 29 coinciden; 5 llegan en las fases 2 a 5.
- **Demo 1:** el cálculo de la traza de «Vector BDZGO» y de «Portada» tarda menos de
  1 ms en este equipo.

**Qué falta (fase 2):**
- `keyspace` completo y la página «Espacio de claves» (E2);
- el corpus alemán y español, y `stats/` (E3);
- `cribs/` con los casos de 6.5 (E4);
- las páginas 3 a 5 y la página Experimentos.

**Pendiente del autor:**
- confirmar en qué equipo se hará la demo 2 (P-001);
- crear el repositorio remoto, para la CI y el enlace de la diapositiva 21;
- encender Docker Desktop cuando quiera la validación automática con CyberChef (P-003).

## Fase 0 · Andamiaje

**Criterio de aceptación:** `make test` y `make app` funcionan. Se cumple. `make test`
da 59 pruebas que pasan y 8 pendientes en unos 11 s en este equipo. `make app` sirve la
app en http://localhost:8501; se revisó en el navegador integrado, con las fuentes
cargadas desde la app y sin peticiones externas.

**Qué quedó:**
- Entorno: uv 0.13.9, CPython 3.12.16, `pyproject.toml`, `uv.lock` y `requirements.txt`.
  Versiones principales: NumPy 2.5.5, Numba 0.68.1, pandas 3.1.1, SciPy 1.18.1,
  statsmodels 0.15.0, Streamlit 1.67.0, Plotly 7.1.0, Matplotlib 3.11.2, networkx 3.7,
  py-enigma 1.0.2.
- Calidad: ruff, mypy (modo básico), pytest + hypothesis (determinista) y CI en Ubuntu y
  Windows (aún sin ejecutar: falta el remoto).
- `Makefile`: `help`, `install`, `test`, `test-rapido`, `lint`, `format`, `app` y
  `requirements`. Scripts de instalación `install.ps1` e `install.sh`.
- Tema «Bletchley nocturno»:
  - colores del spec, en `.streamlit/config.toml` y en `viz/theme.py`;
  - paleta Okabe-Ito en un orden validado;
  - rampa ámbar;
  - plantillas Plotly `enigma_dark` y `enigma_dark_demo`, y estilos Matplotlib
    `enigma_print` y `enigma_slides`;
  - fuentes Inter y JetBrains Mono en el repo.
- App: punto de entrada con navegación, interruptor de modo demo (20 px) y página Inicio,
  con la pregunta, «67 → 20 bits», la barra de bits, las tarjetas de los módulos, el
  estado de la validación y las fuentes.
- `core/keyspace.py`, adelantado a esta fase (D-005), y `viz/numfmt.py`.
- `docs/`: PROGRESS, DECISIONES, FUENTES, ARQUITECTURA, VALIDACION y
  GUIA_DE_ESTUDIO (tema 1).

**Cifras obtenidas** (todas del código y comprobadas en `tests/test_keyspace.py` y
`tests/test_presentacion.py`):
- Total sin anillos: 158.962.555.217.826.360.000 claves (67,11 bits). Con anillos:
  1,0746 × 10²³ claves (76,51 bits).
- Bits por componente: orden 5,91 · posiciones 14,10 · anillos 9,40 · plugboard 47,10. El
  plugboard es el 70,2 % de los 67,11 bits.
- Plugboard: N(6) = 100.391.791.500; N(10) = 150.738.274.937.250; el máximo es con 11
  cables, N(11) = 205.552.193.096.250.
- Barrido de la Bombe: 1.054.560 configuraciones (20,01 bits).
- Fuerza bruta a 10⁹ claves por segundo: 5.037 años.

**Exploración previa al plan** (no es un resultado del proyecto; la fase 3 la repite
con `enigma_lab`). `scripts/exploracion_demo2.py` usa el piloto con 5.000 claves y
semilla 2026:
- Con WETTERBERICHT, el rotor central se mueve dentro de las 13 letras en el 46,7 % de
  las claves.
- El menú tiene 0 lazos en el 39,8 % de las claves, 1 en el 46,1 %, 2 en el 11,9 % y 3 o
  más en el 2,2 %, con 15,41 letras en promedio.
- Por eso la demo 2 necesitará el modo robusto y un verificador automático de todas las
  paradas.

**Qué falta (fase 1):** `core/` con Enigma I y M3, el doble paso, la traza y la versión
por lotes; los vectores de 6.1 y un mensaje histórico; py-enigma en 10.000 claves;
hypothesis; CyberChef (P-003); la página Máquina con la animación y los preajustes
«Vector BDZGO» y «Portada»; `make resumen`.

**Pendiente del autor:** confirmar en qué equipo se hará la demo 2 (P-001) y crear el
repositorio remoto, para que corra la CI y para el enlace de la diapositiva 21.
