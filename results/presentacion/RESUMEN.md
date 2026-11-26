# Resumen de resultados para la presentación

- **Fecha:** 2026-11-26 00:23 UTC
- **Commit:** 295f15b
- **Semilla:** 2026
- **Modo:** completo
- **Corridas:** E1: modo completo, 2026-11-22 16:43 UTC, commit 67e022b; E2: modo completo, 2026-11-22 16:43 UTC, commit 67e022b; E3: modo completo, 2026-11-22 16:43 UTC, commit 67e022b; E4: modo completo, 2026-11-22 16:43 UTC, commit 67e022b; E5: modo completo, 2026-11-22 16:47 UTC, commit 67e022b; E6: modo completo, 2026-11-22 16:48 UTC, commit 67e022b; E7: modo completo, 2026-11-22 16:48 UTC, commit 67e022b; E8: modo completo, 2026-11-22 17:13 UTC, commit 67e022b

Generado por `make resumen` a partir de `results/summary.json` y los Parquet, sin volver a correr experimentos. Cada cifra sale del código.

## 1. Por diapositiva de resultados

### Diapositiva 9 · Rejewski (E7)

- **Cifra para la diapositiva:** el catálogo de los rotores I–III con el reflector A tiene 105.456 configuraciones (6 × 17.576) y 21.225 características distintas; 11.578 señalan una sola configuración (54,5 %) y la más frecuente, (13 13)(13 13)(13 13), 1.728. Es exacto (sin azar).
- **Kuhl (2007):** 21.230, 11.466 y 1.771. Diferencias: −0,02 %, 1,0 % y −2,4 %. De las 15 características de su tabla 1, 14 están entre nuestras 15 más frecuentes (ver Discrepancias).
- Con 41.088 configuraciones en clases de 10 o menos, una configuración al azar comparte su característica con 111,7 en promedio (mediana 20): las clases grandes pesan mucho.
- **Mensajes de un día** (4.000 días con claves de mensaje al azar, semilla 2026): ver las 26 letras de AD, BE y CF pide 128,0 mensajes (IC 95 % 127,0–129,1); la teoría exacta da 127,1 (una sola permutación: 100,9, frente a 26·H₂₆ = 100,2). Por eliminación, 90,5 mensajes (IC 95 % 89,9–91,0). Con el teorema de los ciclos en parejas, la característica queda determinada en 49,1 mensajes (IC 95 % 48,8–49,4) y las tres permutaciones en 60,7 mensajes (IC 95 % 60,3–61,0): los «unos sesenta» de Rejewski.
- **El catálogo encuentra el día** en el 75,4 % de los días (IC 95 % 74,0 %–76,7 %): en el 100,0 % de los días en que el rotor central no se mueve durante el indicador y en el 1,4 % de los demás. El central se mueve en 176 de cada 676 posiciones del día (26,0 %).
- Datos para dibujarla: `r5_rejewski.csv` (tamaños de clase con la tabla 2 de Kuhl).

### Diapositiva 14 · Validación (E1)

- **Cifra para la diapositiva:** 10.000 de 10.000 claves y mensajes aleatorios coinciden con py-enigma (100 %; IC 95 % de Wilson 99,96 %–100,00 %). N = 10.000, semilla 2026, 1.007.710 letras.
- Por modelo: Enigma I: 4.945 de 4.945, M3: 2.568 de 2.568, M4: 2.487 de 2.487. Cables de 0 a 10 (py-enigma no admite más); reflectores B y C (B y C delgados en la M4).
- Propiedades con 2.000 claves de Enigma I y 200.000 letras: 0 puntos fijos; cifrar dos veces devolvió el original en 2.000 claves; el cifrado por lotes coincidió con el escalar en 2.000.
- Vectores de prueba: 9 de 9 coinciden (tabla en `r1_validacion.csv`). CyberChef coincide en 6 de 6 casos comprobados a mano.
- Mensaje real: el simulador descifra letra por letra el del U-264 (Enigma M4, 25-11-1942, roto por el M4 Project en 2006).

### Diapositiva 15 · Cribs (E4)

- **L = 13:** con texto aleatorio sobrevive el 60,1 % de las alineaciones falsas (IC 95 % 59,9 %–60,3 %); teoría (25/26)^13 = 60,1 %. Con **alemán real**, el 61,6 % (61,4 %–61,8 %).
- **L = 50:** con texto aleatorio sobrevive el 14,1 % de las alineaciones falsas (IC 95 % 13,9 %–14,3 %); teoría (25/26)^50 = 14,1 %. Con **alemán real**, el 15,4 % (15,2 %–15,6 %).
- Texto aleatorio: (25/26)^L cae dentro del IC 95 % en 10 de 10 longitudes.
- Alemán real (X como separador, κ = 0,0802): (25/26)^L cae dentro del IC en 0 de 10 longitudes. La teoría corregida, (1 − (1 − κ)/25)^L, cae dentro en 10 de 10. Con alemán sobreviven un poco más alineaciones falsas: una letra del crib igual a la letra plana de esa posición nunca puede chocar.
- Diseño: 1.000 mensajes de 250 letras por longitud y por tipo de texto, claves aleatorias de Enigma I con 10 cables, semilla 2026. La alineación verdadera sobrevivió siempre: sí. Tabla completa en `r2_cribs.csv`.

### Diapositiva 16 · Bombe (E5)

- **Cifra para la diapositiva** (menús de 12 letras, con diagonal board, modo Bletchley): paradas falsas por orden de rotores con 0, 1, 2 y 3 lazos: 678 · 26,3 · 0,99 · 0,11. Turing: 820 · 31 · 1,2 · 0,04. IC 95 %: 672–684; 25,1–27,4; 0,766–1,21; 0,0484–0,172. N = 100 menús por celda, un orden de rotores por menú, semilla 2026.
- **En 60 órdenes:** con 2 lazos, unas 59,4 paradas falsas (Turing: 72); con 3 lazos, 6,6 (Turing: 2,4).
- **Cada lazo divide las paradas** por 25,8, 26,5, 9,0 (de 0 a 1, de 1 a 2 y de 2 a 3 lazos; Turing: por unas 26). Con las letras fijas, un lazo más es una arista más con las mismas letras. Con 3 lazos hubo solo 11 paradas falsas en 100 menús, así que el último cociente es impreciso.
- **Sin diagonal board** (los mismos menús): 17.575 · 17.040 · 729 · 27,4 paradas falsas por orden con 0 a 3 lazos. Sin lazos, la Bombe para en casi todas las 17.576 posiciones: sin el diagonal board un menú sin lazos no descarta nada.
- **Toda la tabla de Turing** (8 a 16 letras): en 15 de 17 celdas con valor exacto, las hipótesis abiertas por orden que medimos están entre la mitad y el doble de la estimación de Turing. Detalle por celda en `r3_bombe.csv` (columnas `paradas_media`, `hipotesis_media` y `turing`).
- **Pocas letras y sin lazos:** con 8 letras Turing da 40.000 paradas por orden, más que las 17.576 posiciones. Su cifra cuenta hipótesis abiertas, no posiciones: medimos 37.546 hipótesis en 17.219 posiciones.
- **Éxito:** en modo Bletchley aparece la parada verdadera en el 55,0 % de los menús. El central se movió dentro del tramo en el 45,0 %; sin esa vuelta, en el 100,0 %.
- **Modo robusto** (menús de 12 y 16 letras): éxito 98,0 %, 12,0 veces el tiempo y 10,9 veces las paradas del modo Bletchley.
- **Tiempo por orden** (17.576 posiciones, en el equipo de `make reproduce`): 0,008 s en modo Bletchley, en promedio con todos los menús (8 a 16 letras), y 0,114 s en modo robusto, con los de 12 y 16 letras. En esos mismos menús el modo Bletchley tarda 0,009 s: de ahí las 12,0 veces.
- **«Letras» son vértices** (P-002, D-031): las letras distintas del menú. Con esa lectura la columna de 12 letras queda cerca de la de Turing (entre 0,8 y 2,8 veces su valor); contando aristas no.

### Diapositiva 17 · Banburismus (E6)

- **Cifras de Turing** (diapositivas 13 y 17, comprobadas en `test_presentacion.py`): +1,845 dB por repetición y −0,093 dB por no repetición; en promedio, +0,0211 dB por letra en profundidad y −0,0184 dB al azar. Umbrales con α = β = 1 %: ±19,96 dB. Aproximación de Wald: 929 letras para confirmar la profundidad y 1.062 para descartarla.
- **Cifra para la diapositiva: la simulación del SPRT.** Letras sueltas y un texto cuyas columnas en profundidad repiten con 1/17 exacta, cifrado con la máquina real; 2.000 pares, semilla 2026. Confirmar la profundidad toma 983 letras (IC 95 % 954–1.012) y descartarla, 1.090 letras (IC 95 % 1.061–1.120). El cálculo exacto, sin simulación, da 959,7 y 1.067,4, dentro de los dos IC. Errores en la simulación: 1,1 % en profundidad y 1,2 % al azar (exactos: 0,99 % y 0,86 %).
- **La diferencia con Wald es el sobrepaso.** Wald supone que el puntaje se detiene justo en ±19,96 dB; en realidad se detiene al cruzarlo, y lo pasa. Una repetición suma 1,845 dB de golpe: arriba, el puntaje pasa el umbral por 0,65 dB en promedio (simulación: 0,67). La identidad de Wald, E[N] = E[S_N] / μ, es exacta, así que en profundidad son 30,9 letras más: 30,7 por ese sobrepaso y 0,2 por lo demás. Abajo, cada no repetición resta solo 0,093 dB y el sobrepaso es de 0,045 dB. Al azar la diferencia es de 5,1 letras: 2,4 por el sobrepaso de abajo, 2,9 porque el error real queda por debajo del 1 % y −0,3 por el de arriba. Con la simulación, E[S_N] / μ da 963 y 1.072 letras.
- **Con texto alemán real** (corpus, X como separador): en profundidad las letras repiten 1 de cada 12,5, medido con la máquina, y no 1 de cada 17. El IC del corpus es 0,0802 con la X y 0,0757 sin ella (1 de cada 13,2); al azar se miden 1 de cada 26. Con los pesos de Turing, confirmar la profundidad toma 332 letras (IC 95 % 325–340): la decisión llega antes que las 929 de Wald. Descartarla toma 1.090 letras (IC 95 % 1.063–1.118), como con 1/17.
- **Cuánto aceleran los multigramas** (pesos medidos en el corpus, α = β = 1 %). Con letras sueltas y la tasa del corpus: 262 letras en profundidad y 323 al azar, con un error de 1,8 % en profundidad: las repeticiones del texto real vienen en racimos, y un modelo de letras independientes no lo sabe. Con bigramas y trigramas: 254 y 357, con errores de 1,1 % y 0,8 %; hasta tetragramas, 254 y 357. Frente a los pesos de Turing, los bigramas y trigramas necesitan un 24 % menos de letras para confirmar y un 67 % menos para descartar.
- **Solapamientos de mensajes reales** (100, 200 y 400 letras). El desplazamiento verdadero saca el mayor puntaje de los 51 en el 39 %, 64 % y 88 % de los pares de texto alemán con letras sueltas, en el 42 %, 67 % y 90 % con bigramas y trigramas y en el 13 %, 22 % y 40 % con la tasa 1/17. El SPRT (α = β = 1 %) confirma la profundidad dentro de ese solapamiento en el 20 %, 49 % y 82 % de los pares (alemán, bigramas y trigramas).
- **Curva ROC** del puntaje tras 200 letras, sin detenerse (AUC): tasa 1/17 0,824; alemán con letras sueltas 0,953; alemán con bigramas y trigramas 0,956. Con letras sueltas el puntaje solo depende del número de repeticiones, así que las dos tasas dan la misma curva.
- Datos para los gráficos: `r4_banburismus.csv` (tabla larga: fuente, puntuación, solapamiento, α e hipótesis), `r4_roc.csv` (curvas ROC) y `r4_trayectorias.csv` (decibanes acumulados, 10 pares por hipótesis).

### Conexiones con el curso (diapositivas 3 a 7, 13 y 18)

Exactas, sin azar. La lista completa, semana por semana, está en la sección 7 de `docs/GUIA_DE_ESTUDIO.md`.

- **Conteo de permutaciones (diapositiva 6, semana 4):** 25!! = 7.905.853.580.625 involuciones sin puntos fijos (42,8 bits; son también los plugboards de 13 cables) entre 26! = 403.291.461.126.605.635.584.000.000 permutaciones (88,4 bits). `core/keyspace.py`.
- **La ρ (diapositivas 3 y 5, semana 6):** el ciclo tiene 16.900 posiciones y la cola 676: 650 a un paso del ciclo y 26 a dos. 650 posiciones del ciclo tienen dos predecesoras (una del ciclo y otra de la cola): las colisiones del doble paso. `core/stepping.py` · `rho_structure`.
- **Ataque paralelo (diapositiva 7, semana 3):** 5.037 años con una máquina de 10⁹ claves por segundo y 5,04 con 1.000. `core/keyspace.py` · `brute_force_years`.
- **Cumpleaños de las claves de mensaje (diapositiva 13, semana 3):** con 157 claves entre 17.576, alguna se repite con probabilidad 50,28 %; con 156, 49,84 % (cálculo exacto con fracciones). Para compartir solo las dos primeras letras (676 valores) bastan 31 (50,26 %). `banburismus/depth.py`.
- **La app:** cada página dice debajo del título su línea «En clase», con la etiqueta de su diapositiva tal cual (`app/ui/course.py`); en Experimentos, una por pestaña. Se ve también en modo demo.

### Otros resultados útiles

- **E3 (diapositivas 6 y 22):** IC del corpus alemán 0,0757 (Pommerening: 0,0758); español 0,0750. Con mensajes de 1.000 letras, el IC del alemán pasa de 0,0760 en el plano a 0,0385 en el cifrado (1/26 = 0,0385).
- La prueba χ² (α = 5 %), con 1.000 letras, rechaza la uniformidad del 100 % de los textos planos en alemán y del 10,0 % de los cifrados (un cifrado uniforme daría 5 %).
- **Antifrecuencia:** como ninguna letra se cifra a sí misma, la letra c sale cifrada con probabilidad (1 − f_c)/25. Las letras comunes del idioma salen un poco menos: la E, el 17,1 % del alemán, debería ser el 3,32 % del cifrado y no el 3,85 %. Con esa distribución, la χ² no central predice un 8,0 % de rechazos con 1.000 letras; se midió 10,0 %. Las frecuencias del idioma se filtran débiles y al revés.
- Puntos fijos: 0 en 3.850.000 letras.
- **E2 (diapositiva 7):** 1,6 × 10²⁰ claves (67,11 bits); el plugboard aporta el 70,2 %; la Bombe barre 1.054.560 configuraciones; máximo de N(k) con 11 cables.
- **E8 · Ataque moderno (pregunta «¿Hoy se rompería por fuerza bruta?»):** el ataque de Gillogly prueba 1.054.560 ubicaciones con el IC y sube el plugboard por hill climbing; 1,7 s por mensaje en este equipo. Con 24 mensajes por celda (864 en total, de 25 a 1.500 letras), lee el 43,1 % con 6 cables, el 21,9 % con 8 cables, el 3,5 % con 10 cables.
- Regresión logística: la mitad de los mensajes se lee con 6 cables desde unas 314 letras (IC 95 % 273–362); con 8 cables desde unas 845 letras (IC 95 % 752–950); con 10 cables, el 50 % no se alcanza en las longitudes medidas.
- Referencias: Gillogly, unas 300 letras con 6 cables o menos y un solo éxito con 10 cables (1.463 letras); distancia de unicidad, unas 23 letras; los mensajes reales no pasaban de 250 letras (Ostwald y Weierud 2017).
- Con la ubicación dada (lo que queda si la fase 1 no falla), el hill climbing lee el 73,3 % de los mensajes y con la búsqueda parcial de la E, el 80,0 %. El cuello de botella es la fase 1: supone los anillos, y el central y el izquierdo giran en otra letra (D-067). Datos: `r6_ataque.csv`.
- Respuesta corta: no hace falta fuerza bruta; un computador de escritorio lee en segundos un mensaje largo con pocos cables, y los ataques de hoy (Ostwald y Weierud) llegan cerca de la unicidad agotando todas las ubicaciones con hill climbing durante días.

## 2. Cifras de la presentación

| Diap. | Cifra | En la presentación | Del código | ¿Coincide? |
| --- | --- | --- | --- | --- |
| 2, 7, 19 | claves sin anillos | 158.962.555.217.826.360.000 | 158.962.555.217.826.360.000 | sí |
| 2, 7, 19 | claves sin anillos, redondeado | 1,6 × 10²⁰ | 1,6 × 10²⁰ | sí |
| 3, 7, 8, 19 | bits sin anillos | 67,11 | 67,11 | sí |
| 7 | claves con anillos | 1,0746 × 10²³ | 1,0746 × 10²³ | sí |
| 7 | claves con anillos, redondeado | 1,07 × 10²³ | 1,07 × 10²³ | sí |
| 7 | bits con anillos | 76,51 | 76,51 | sí |
| 7 | bits del orden de rotores | 5,91 | 5,91 | sí |
| 7 | bits de las posiciones | 14,10 | 14,10 | sí |
| 7 | bits de los anillos | 9,40 | 9,40 | sí |
| 7 | bits del plugboard | 47,10 | 47,10 | sí |
| 7 | fracción del plugboard en los 67,11 bits | 70,2 % | 70,2 % | sí |
| 8 | configuraciones que barre la Bombe | 1.054.560 | 1.054.560 | sí |
| 3, 8, 12, 19 | bits del barrido de la Bombe | 20,01 | 20,01 | sí |
| 7, 16 | años de fuerza bruta a 10⁹ claves por segundo | 5.037 | 5.037 | sí |
| 7 | años con 1.000 máquinas de 10⁹ claves por segundo (la etiqueta lo redondea a 5) | 5,04 | 5,04 | sí |
| 3, 5, 14 | periodo del odómetro I-II-III | 16.900 | 16.900 | sí |
| 3, 5 | posiciones fuera del ciclo: la cola de la ρ | 676 | 676 | sí |
| 5 | posiciones de la cola a un paso y a dos pasos del ciclo | 650 y 26 | 650 y 26 | sí |
| 5 | posiciones del ciclo con dos predecesoras, las colisiones del paso (guion, preguntas) | 650 | 650 | sí |
| 5, 14 | doble paso desde ADU | ADU → ADV → AEW → BFX | ADU → ADV → AEW → BFX | sí |
| 1 | mensaje cifrado de la portada | LGNEV YPYZQ DVKES NPUYY QVWSK YNZJH E | LGNEV YPYZQ DVKES NPUYY QVWSK YNZJH E | sí |
| 1, 4 | la portada descifrada | ROMPERXENIGMAXCRIPTOGRAFIAXUNAL | ROMPERXENIGMAXCRIPTOGRAFIAXUNAL | sí |
| 4 | traza de la letra A | plugboard A → III C → II D → I F → reflector S → I S → II E → III B → plugboard B | plugboard A → III C → II D → I F → reflector S → I S → II E → III B → plugboard B | sí |
| 14 | AAAAA con I-II-III y anillos AAA | BDZGO | BDZGO | sí |
| 14 | lo mismo con anillos BBB | EWTYX | EWTYX | sí |
| 14 | ejemplo de py-enigma (10 cables) | THEXRUSSIANSXAREXCOMINGX | THEXRUSSIANSXAREXCOMINGX | sí |
| 14 | mensaje real del U-264 (M4, 1942), descifrado | VONVONJLOOKS | VONVONJLOOKS | sí |
| 14 | claves aleatorias iguales a py-enigma (E1) | 10.000 de 10.000 | 10.000 de 10.000 | sí |
| 6 | (25/26)¹⁰⁰: ningún punto fijo en 100 letras al azar | 1,98 % | 1,98 % | sí |
| 6, 14 | claves con involución (de 2.000) | 2.000 | 2.000 | sí |
| 6, 14 | letras cifradas con esas 2.000 claves | 200.000 | 200.000 | sí |
| 6, 14 | puntos fijos en esas 200.000 letras | 0 | 0 | sí |
| 6 | involuciones sin puntos fijos de 26 letras: 25!! = 25 · 23 ··· 3 · 1 | 7.905.853.580.625 | 7.905.853.580.625 | sí |
| 6 | lo mismo, redondeado | 7,9 × 10¹² | 7,9 × 10¹² | sí |
| 6 | permutaciones de 26 letras: 26! | 403.291.461.126.605.635.584.000.000 | 403.291.461.126.605.635.584.000.000 | sí |
| 6 | lo mismo, redondeado | 4 × 10²⁶ | 4 × 10²⁶ | sí |
| 15, 19 | (25/26)¹³: sobreviven a un crib de 13 letras | 60,1 % | 60,1 % | sí |
| 15 | (25/26)⁵⁰: sobreviven a un crib de 50 letras | 14,1 % | 14,1 % | sí |
| 15 | sobreviven con alemán real, con 13 y con 50 letras (E4) | 61,6 % y 15,4 % | 61,6 % y 15,4 % | sí |
| 15 | κ del alemán; longitudes con la teoría corregida dentro del IC (E4) | κ = 0,080; 10 de 10 | κ = 0,080; 10 de 10 | sí |
| 15, 22 | E4: mensajes por longitud | 1.000 de 250 letras | 1.000 de 250 letras | sí |
| 22 | IC del alemán solo con letras (E3) y con X entre palabras (E4); al azar, 1/26 | 0,076 · 0,080 · 0,038 | 0,076 · 0,080 · 0,038 | sí |
| 10 | alineaciones de WETTERBERICHT sobre BBGCCKITCTTEZZZLCZ | 6 | 6 | sí |
| 10 | alineaciones sin conflictos | 0, 1, 2, 3 | 0, 1, 2, 3 | sí |
| 10 | conflicto de las alineaciones 4 y 5 | T sobre la T de la posición 7 | T sobre la T de la posición 7 | sí |
| 11 | menú de la alineación 0: letras, aristas, componentes y lazos | 11 · 13 · 1 · 3 | 11 · 13 · 1 · 3 | sí |
| 11 | letra de prueba y su grado | T, grado 6 | T, grado 6 | sí |
| 12 | menú del caso de respaldo: letras, aristas, componentes y lazos | 11 · 13 · 1 · 3 | 11 · 13 · 1 · 3 | sí |
| 12 | letra de prueba del caso de respaldo | T, grado 4 | T, grado 4 | sí |
| 12 | demo 2, 60 órdenes en modo robusto: casos resueltos; p50 · p95 · máximo (guion) | 60 de 60; 6,4 · 9,8 · 14,9 s | 60 de 60; 6,4 · 9,8 · 14,9 s | sí |
| 12 | letras de los mensajes del banco de la demo 2 (guion: «unas 80 letras») | 78 | 78 | sí |
| 9 | configuraciones del catálogo: 6 órdenes × 17.576 posiciones (E7) | 105.456 | 105.456 | sí |
| 9 | nuestro catálogo: características distintas y únicas (E7, exacto) | 21.225 · 11.578 | 21.225 · 11.578 | sí |
| 9 | Kuhl (2007): características distintas y únicas, junto a las nuestras | 21.230 · 11.466 | 21.230 · 11.466 | sí |
| 9 | días en que el catálogo encuentra la configuración del día (E7) | 75 % de 4.000 días | 75 % de 4.000 días | sí |
| 13 | claves de mensaje con las que una repetición pasa del 50 %, entre 17.576 (cumpleaños) | 157 | 157 | sí |
| 13 | P(alguna se repite) con 157 y con 156 claves de mensaje (cálculo exacto) | 50,28 % y 49,84 % | 50,28 % y 49,84 % | sí |
| 13 | claves que comparten las dos primeras letras (676 valores): repetición sobre el 50 % (guion, preguntas) | 31 (50,26 %) | 31 (50,26 %) | sí |
| 13, 17 | decibanes por repetición: 10·log₁₀((1/17)/(1/26)) | +1,845 dB | +1,845 dB | sí |
| 13 | decibanes por no repetición: 10·log₁₀((16/17)/(25/26)) | −0,093 dB | −0,093 dB | sí |
| 17 | decibanes por letra, en promedio, en profundidad | +0,0211 dB | +0,0211 dB | sí |
| 17 | decibanes por letra, en promedio, al azar | −0,0184 dB | −0,0184 dB | sí |
| 13, 17 | umbrales de Wald con α = β = 1 % | ±19,96 dB | ±19,96 dB | sí |
| 13, 17 | letras esperadas según Wald, en profundidad y al azar | 929 y 1.062 | 929 y 1.062 | sí |
| 17 | SPRT simulado, tasa 1/17: letras para confirmar y para descartar la profundidad (E6) | 983 · 1.090 | 983 · 1.090 | sí |
| 17 | alemán real: letras para confirmar, con bigramas y trigramas y con pesos de Turing (E6) | 254 · 332 | 254 · 332 | sí |
| 17, 22 | E6: pares por hipótesis | 2.000 | 2.000 | sí |
| 16 | Turing, 12 letras: paradas por orden con 0, 1, 2 y 3 lazos; en 60 órdenes con 2 y 3 | 820 · 31 · 1,2 · 0,04; 72 y 2,4 en 60 | 820 · 31 · 1,2 · 0,04; 72 y 2,4 en 60 | sí |
| 16 | nuestra Bombe, 12 letras, con diagonal board: paradas por orden con 0 a 3 lazos (E5) | 678 · 26 · 0,99 · 0,11 | 678 · 26 · 0,99 · 0,11 | sí |
| 16 | parada verdadera en modo Bletchley · menús en que gira el central · modo robusto (E5) | 55 % · 45 % · 98 % | 55 % · 45 % · 98 % | sí |
| 16 | modo robusto: veces el tiempo; segundos por orden frente al Bletchley, mismos menús (E5) | 12 veces; 0,11 s frente a 0,009 s | 12 veces; 0,11 s frente a 0,009 s | sí |
| 16, 22 | E5: menús de 12 letras distintas por celda | 100 | 100 | sí |
| 16, 19 | cada lazo divide las paradas falsas por (E5, media geométrica de 0 a 2 lazos) | 26 | 26 | sí |

73 de 73 cifras calculadas coinciden.

## 3. Demos

- **Demo 1 (diapositiva 4):** solo «Portada». El cálculo es instantáneo: su traza tarda 0,8 ms en el equipo donde corrió `make resumen` (Intel64 Family 6 Model 158 Stepping 10, GenuineIntel, 6 núcleos lógicos). Los 30 s del guion los pone la interacción.
- **La app en clase:** abre `http://localhost:8501/maquina?demo=1` (el modo demo queda en la URL y sobrevive a una recarga) y, en otra pestaña, `http://localhost:8501/bombe?demo=1`; pliega la barra lateral para ganar ancho. En modo demo, Máquina muestra «Portada» y «Vector BDZGO» (que el guion ya no usa), y La Bombe, «Cifrado del compañero» y «Caso de respaldo» (plan B). Debajo del título, cada página muestra su línea «En clase», la misma etiqueta de su diapositiva.
- **Demo 2 (diapositiva 12):** `make bench-demo` del 2026-11-21 18:25 UTC (commit 5b34896) en Intel64 Family 6 Model 158 Stepping 10, GenuineIntel, 6 núcleos lógicos, Windows 11. Casos de compañero: clave como la de «Clave aleatoria» (10 cables), mensaje alemán de 78 letras que empieza por el crib, crib en la posición 0. Flujo completo de la página La Bombe: barrido, máquina de verificación y «Verificar». Éxito: el descifrado es el mensaje letra por letra.

p95: el 95 % de los casos tardó eso o menos; «Máximo» es el más lento.

| Configuración | Éxito (IC 95 %) | p50 | p95 | Máximo | Barrido p95 | ¿Cumple? |
| --- | --- | --- | --- | --- | --- | --- |
| 60 órdenes, modo robusto | 60 de 60 (94 %–100 %) | 6,4 s | 9,8 s | 14,9 s | 7,3 s | sí |
| Rotores I, II y III (6 órdenes), modo robusto | 60 de 60 (94 %–100 %) | 1,3 s | 1,7 s | 1,7 s | 0,8 s | sí |
| Crib WETTERBERICHTXFUER, 60 órdenes, modo robusto | 59 de 60 (91 %–100 %) | 8,9 s | 10,4 s | 12,5 s | 10,4 s | sí |

- **Recomendada (la más simple con éxito ≥ 95% y p95 ≤ 30 s):** 60 órdenes, modo robusto: el compañero usa «Clave aleatoria» sin restricciones, con el modelo Enigma I que trae Máquina, y escribe un mensaje de unas 80 letras, como los del banco, que empiece por WETTERBERICHT (con X entre palabras). En la demo, el botón «Cifrado del compañero» de La Bombe deja el crib en la posición 0, «Rotores I a V (60 órdenes)» y el modo robusto. Se pega el cifrado y se pulsa Ctrl+Enter: aparecen el menú y sus lazos. El barrido empieza con «Correr la Bombe», y al terminar, «Verificar» revisa todas las paradas consistentes y muestra el texto en grande. Éxito 100,0 %, p95 9,8 s y máximo 14,9 s.
- Estos tiempos son del equipo indicado, un escritorio que es también el de la exposición (D-072): no hace falta medirlos en otro equipo.

## 4. Discrepancias

**Con las diapositivas y el guion (versión 5, 25-11-2026).** Ninguna cifra contradice los resultados, y las seis notas de la versión 4 quedaron corregidas: el banco de la demo 2 (p50, p95 y el más lento) y «Verificar», el largo del mensaje del compañero, los dos IC del alemán (diapositivas 15 y 22), el rótulo «E1» de la diapositiva 6, los pasos 2 y 3 del doble paso con la cola de la ρ y el cumpleaños de las claves que comparten las dos primeras letras, ahora en «Preguntas probables». Las cifras nuevas de la versión 5 (los 31 mensajes, el IC de la diapositiva 22 y los tiempos de la demo 2) están en el registro y coinciden. No queda ninguna nota.

**Notas sobre los resultados y las fuentes.**

- Diapositivas 13 y 17: 929 y 1.062 letras son la aproximación de Wald, que ignora el sobrepaso de los umbrales. Con las mismas tasas, el valor exacto es 959,7 y 1.067,4, y la simulación lo confirma. Las dos diapositivas las presentan como de Wald, y así siguen bien.
- Diapositiva 13 y guion («en el tráfico naval … 1 de cada 17»): es la tasa del tráfico naval que da Wikipedia. Nuestro corpus literario repite 1 de cada 12,5 con la X como separador y 1 de cada 13,2 solo con letras. Con él, la profundidad se confirma en unas 332 letras con los pesos de Turing. No contradice la diapositiva: es otro texto.
- La descripción habitual («en profundidad … hasta que se mueve el rotor central»): con la máquina real los dos mensajes recorren la misma sucesión de estados, así que la profundidad dura todo el solapamiento. El rotor central decide si el desplazamiento verdadero es +δ o δ − 26 (D-042); por eso se prueban los desplazamientos de −25 a +25.
- Diapositiva 16: la tabla de Turing cuenta «letras del menú» como letras distintas (vértices del grafo), igual que la diapositiva 11 (11 letras, 13 aristas). Con esa lectura, nuestra Bombe da 678 · 26,3 · 0,99 · 0,11 paradas falsas por orden con 12 letras y 0 a 3 lazos, frente a 820 · 31 · 1,2 · 0,04 de Turing. Si «letras» fueran aristas (letras del crib), no coincidirían (ver D-031).
- Verificador: recupera una clave equivalente en 200 de 200 de los casos de la prueba, que se usaron para ajustar su diseño, y en 198 de 200 casos nuevos. Las 2 fallas tienen el plugboard exacto y difieren en una sola letra, la segunda o la última del mensaje: un doble paso del central justo en el borde que el texto no alcanza a decidir. La parada verdadera aparece siempre (400 de 400).
- Diapositiva 15: con alemán real, el 60 % de 13 letras pasa a 61,6 %, por encima de (25/26)^13 y fuera de su IC. No es un error del filtro: es el efecto del IC del idioma, y la corrección (1 − (1 − κ)/25)^13 = 61,4 % lo explica. La diapositiva da los dos valores: el 60 % de la teoría y el del alemán real.
- py-enigma admite como máximo 10 cables: la comparación de 10.000 claves usa de 0 a 10 cables, y las pruebas con hypothesis cubren de 0 a 13.
- Mensaje histórico: no se encontró una fuente verificable del mensaje de Barbarossa (1941). Se usa el del U-264 (M4), publicado con clave, cifrado y texto por D. Rijmenants.
- Corpus: gutenberg.org estaba en mantenimiento el 20-11-2026; se descargó de su espejo oficial (Mirror Service), con SHA-256 verificado.
- Diapositiva 9: nuestro catálogo da 21.225 características, 11.578 únicas y 1.728 en la más frecuente; Kuhl, 21.230, 11.466 y 1.771. No se ajustó nada: Kuhl no dice qué supone del rotor central ni de los anillos, y ninguna de las 33 variantes de los supuestos que probamos reproduce sus cifras (`scripts/kuhl_variantes.py`, VALIDACION). Su artículo tiene además erratas: escribe 105.465 configuraciones, da 11.466 como el 54,40 % (es el 54,01 %) y dice que 20.433 tienen 10 o menos cuando su tabla 2 suma 19.604. La diapositiva da las dos cifras, las nuestras y las de Kuhl.

## 5. Pendientes

- Ninguno.
