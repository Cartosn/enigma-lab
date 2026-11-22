# Resumen de resultados para la presentación

- **Fecha:** 2026-11-22 10:30 UTC
- **Commit:** de697e4
- **Semilla:** 2026
- **Modo:** completo
- **Corridas:** E1: modo completo, 2026-11-22 10:24 UTC, commit 82fda70; E2: modo completo, 2026-11-22 10:24 UTC, commit 82fda70; E3: modo completo, 2026-11-22 10:24 UTC, commit 82fda70; E4: modo completo, 2026-11-22 10:24 UTC, commit 82fda70; E5: modo completo, 2026-11-22 10:27 UTC, commit 82fda70; E6: modo completo, 2026-11-22 10:28 UTC, commit 82fda70

Generado por `make resumen` a partir de `results/summary.json` y los Parquet, sin volver a correr experimentos. Cada cifra sale del código.

## 1. Por diapositiva de resultados

### Diapositiva 14 · Validación (E1)

- **Cifra para la diapositiva:** 10.000 de 10.000 claves y mensajes aleatorios coinciden con py-enigma (100 %; IC 95 % de Wilson 99,96 %–100,00 %). N = 10.000, semilla 2026, 1.007.710 letras.
- Por modelo: Enigma I: 4.945 de 4.945, M3: 2.568 de 2.568, M4: 2.487 de 2.487. Cables de 0 a 10 (py-enigma no admite más); reflectores B y C (B y C delgados en la M4).
- Propiedades con 2.000 claves de Enigma I y 200.000 letras: 0 puntos fijos; cifrar dos veces devolvió el original en 2.000 claves; el cifrado por lotes coincidió con el escalar en 2.000.
- Vectores de 6.1: 9 de 9 coinciden (tabla en `r1_validacion.csv`). CyberChef coincide en 6 de 6 casos comprobados a mano.
- Nuevo para la diapositiva 14, si cabe: el simulador descifra letra por letra un mensaje real, el del U-264 (Enigma M4, 25-11-1942, roto por el M4 Project en 2006).

### Diapositiva 15 · Cribs (E4)

- **L = 13:** con texto aleatorio sobrevive el 60,1 % de las alineaciones falsas (IC 95 % 59,9 %–60,3 %); teoría (25/26)^13 = 60,1 %. Con **alemán real**, el 61,6 % (61,4 %–61,8 %).
- **L = 50:** con texto aleatorio sobrevive el 14,1 % de las alineaciones falsas (IC 95 % 13,9 %–14,3 %); teoría (25/26)^50 = 14,1 %. Con **alemán real**, el 15,4 % (15,2 %–15,6 %).
- Texto aleatorio: (25/26)^L cae dentro del IC 95 % en 10 de 10 longitudes. Es el criterio de aceptación de la fase 2 y se cumple.
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
- **Modo robusto** (menús de 12 y 16 letras): éxito 98,0 %, 13,2 veces el tiempo y 10,9 veces las paradas del modo Bletchley.
- **Tiempo por orden** (17.576 posiciones, en el equipo de `make reproduce`): 0,007 s en modo Bletchley y 0,104 s en modo robusto.
- **«Letras» son vértices** (P-002, D-031): las letras distintas del menú. Con esa lectura la columna de 12 letras queda cerca de la de Turing (entre 0,8 y 2,8 veces su valor); contando aristas no.

### Diapositiva 17 · Banburismus (E6)

- **Cifras de Turing** (diapositivas 13 y 17, comprobadas en `test_presentacion.py`): +1,845 dB por repetición y −0,093 dB por no repetición; en promedio, +0,0211 dB por letra en profundidad y −0,0184 dB al azar. Umbrales con α = β = 1 %: ±19,96 dB. Aproximación de Wald: 929 letras para confirmar la profundidad y 1.062 para descartarla.
- **Cifra para la diapositiva: la simulación del SPRT** (criterio de la fase 4). Letras sueltas y un texto cuyas columnas en profundidad repiten con 1/17 exacta, cifrado con la máquina real; 2.000 pares, semilla 2026. Confirmar la profundidad toma 983 letras (IC 95 % 954–1.012) y descartarla, 1.090 letras (IC 95 % 1.061–1.120). El cálculo exacto, sin simulación, da 959,7 y 1.067,4, dentro de los dos IC. Errores en la simulación: 1,1 % en profundidad y 1,2 % al azar (exactos: 0,99 % y 0,86 %).
- **La diferencia con Wald es el sobrepaso.** Wald supone que el puntaje se detiene justo en ±19,96 dB; en realidad se detiene al cruzarlo, y lo pasa. Una repetición suma 1,845 dB de golpe: arriba, el puntaje pasa el umbral por 0,65 dB en promedio (simulación: 0,67). La identidad de Wald, E[N] = E[S_N] / μ, es exacta, así que en profundidad son 30,9 letras más: 30,7 por ese sobrepaso y 0,2 por lo demás. Abajo, cada no repetición resta solo 0,093 dB y el sobrepaso es de 0,045 dB. Al azar la diferencia es de 5,1 letras: 2,4 por el sobrepaso de abajo, 2,9 porque el error real queda por debajo del 1 % y −0,3 por el de arriba. Con la simulación, E[S_N] / μ da 963 y 1.072 letras.
- **Con texto alemán real** (corpus, X como separador): en profundidad las letras repiten 1 de cada 12,5, medido con la máquina, y no 1 de cada 17. El IC del corpus es 0,0802 con la X y 0,0757 sin ella (1 de cada 13,2); al azar se miden 1 de cada 26. Con los pesos de Turing, confirmar la profundidad toma 332 letras (IC 95 % 325–340): la decisión llega antes que las 929 de Wald. Descartarla toma 1.090 letras (IC 95 % 1.063–1.118), como con 1/17.
- **Cuánto aceleran los multigramas** (pesos medidos en el corpus, α = β = 1 %). Con letras sueltas y la tasa del corpus: 262 letras en profundidad y 323 al azar, con un error de 1,8 % en profundidad: las repeticiones del texto real vienen en racimos, y un modelo de letras independientes no lo sabe. Con bigramas y trigramas: 254 y 357, con errores de 1,1 % y 0,8 %; hasta tetragramas, 254 y 357. Frente a los pesos de Turing, los bigramas y trigramas necesitan un 24 % menos de letras para confirmar y un 67 % menos para descartar.
- **Solapamientos de mensajes reales** (100, 200 y 400 letras). El desplazamiento verdadero saca el mayor puntaje de los 51 en el 39 %, 64 % y 88 % de los pares de texto alemán con letras sueltas, en el 42 %, 67 % y 90 % con bigramas y trigramas y en el 13 %, 22 % y 40 % con la tasa 1/17. El SPRT (α = β = 1 %) confirma la profundidad dentro de ese solapamiento en el 20 %, 49 % y 82 % de los pares (alemán, bigramas y trigramas).
- **Curva ROC** del puntaje tras 200 letras, sin detenerse (AUC): tasa 1/17 0,824; alemán con letras sueltas 0,953; alemán con bigramas y trigramas 0,956. Con letras sueltas el puntaje solo depende del número de repeticiones, así que las dos tasas dan la misma curva.
- Datos para los gráficos: `r4_banburismus.csv` (tabla larga: fuente, puntuación, solapamiento, α e hipótesis), `r4_roc.csv` (curvas ROC) y `r4_trayectorias.csv` (decibanes acumulados, 10 pares por hipótesis).

### Otros resultados útiles

- **E3 (diapositivas 6 y 23):** IC del corpus alemán 0,0757 (Pommerening: 0,0758); español 0,0750. Con mensajes de 1.000 letras, el IC del alemán pasa de 0,0760 en el plano a 0,0385 en el cifrado (1/26 = 0,0385).
- La prueba χ² (α = 5 %), con 1.000 letras, rechaza la uniformidad del 100 % de los textos planos en alemán y del 10,0 % de los cifrados (un cifrado uniforme daría 5 %).
- **Antifrecuencia:** como ninguna letra se cifra a sí misma, la letra c sale cifrada con probabilidad (1 − f_c)/25. Las letras comunes del idioma salen un poco menos: la E, el 17,1 % del alemán, debería ser el 3,32 % del cifrado y no el 3,85 %. Con esa distribución, la χ² no central predice un 8,0 % de rechazos con 1.000 letras; se midió 10,0 %. Las frecuencias del idioma se filtran débiles y al revés.
- Puntos fijos: 0 en 3.850.000 letras.
- **E2 (diapositiva 7):** 1,6 × 10²⁰ claves (67,11 bits); el plugboard aporta el 70,2 %; la Bombe barre 1.054.560 configuraciones; máximo de N(k) con 11 cables.

## 2. Cifras de la presentación

| Diap. | Cifra | En la presentación | Del código | ¿Coincide? |
| --- | --- | --- | --- | --- |
| 2, 7, 20 | claves sin anillos | 158.962.555.217.826.360.000 | 158.962.555.217.826.360.000 | sí |
| 2, 7, 20 | claves sin anillos, redondeado | 1,6 × 10²⁰ | 1,6 × 10²⁰ | sí |
| 7, 8 | bits sin anillos | 67,11 | 67,11 | sí |
| 7 | claves con anillos | 1,0746 × 10²³ | 1,0746 × 10²³ | sí |
| 7 | claves con anillos, redondeado | 1,07 × 10²³ | 1,07 × 10²³ | sí |
| 7 | bits con anillos | 76,51 | 76,51 | sí |
| 7 | bits del orden de rotores | 5,91 | 5,91 | sí |
| 7 | bits de las posiciones | 14,10 | 14,10 | sí |
| 7 | bits de los anillos | 9,40 | 9,40 | sí |
| 7 | bits del plugboard | 47,10 | 47,10 | sí |
| 7 | fracción del plugboard en los 67,11 bits | 70,2 % | 70,2 % | sí |
| 8, 20 | configuraciones que barre la Bombe | 1.054.560 | 1.054.560 | sí |
| 8, 20 | bits del barrido de la Bombe | 20,01 | 20,01 | sí |
| 7 | años de fuerza bruta a 10⁹ claves por segundo | 5.037 | 5.037 | sí |
| 3, 5, 14 | periodo del odómetro I-II-III | 16.900 | 16.900 | sí |
| 5 | posiciones fuera del ciclo | 676 | 676 | sí |
| 5, 14 | doble paso desde ADU | ADU → ADV → AEW → BFX | ADU → ADV → AEW → BFX | sí |
| 1 | mensaje cifrado de la portada | LGNEV YPYZQ DVKES NPUYY QVWSK YNZJH E | LGNEV YPYZQ DVKES NPUYY QVWSK YNZJH E | sí |
| 1, 4 | la portada descifrada | ROMPERXENIGMAXCRIPTOGRAFIAXUNAL | ROMPERXENIGMAXCRIPTOGRAFIAXUNAL | sí |
| 4 | traza de la letra A | plugboard A → III C → II D → I F → reflector S → I S → II E → III B → plugboard B | plugboard A → III C → II D → I F → reflector S → I S → II E → III B → plugboard B | sí |
| 14 | AAAAA con I-II-III y anillos AAA | BDZGO | BDZGO | sí |
| 14 | lo mismo con anillos BBB | EWTYX | EWTYX | sí |
| 14 | ejemplo de py-enigma (10 cables) | THEXRUSSIANSXAREXCOMINGX | THEXRUSSIANSXAREXCOMINGX | sí |
| 6 | (25/26)¹⁰⁰: ningún punto fijo en 100 letras al azar | 1,98 % | 1,98 % | sí |
| 6, 14 | claves con involución (de 2.000) | 2.000 | 2.000 | sí |
| 6, 14 | letras cifradas con esas 2.000 claves | 200.000 | 200.000 | sí |
| 6, 14 | puntos fijos en esas 200.000 letras | 0 | 0 | sí |
| 15, 20 | (25/26)¹³: sobreviven a un crib de 13 letras | 60,1 % | 60,1 % | sí |
| 15 | (25/26)⁵⁰: sobreviven a un crib de 50 letras | 14,1 % | 14,1 % | sí |
| 10 | alineaciones de WETTERBERICHT sobre BBGCCKITCTTEZZZLCZ | 6 | 6 | sí |
| 10 | alineaciones sin conflictos | 0, 1, 2, 3 | 0, 1, 2, 3 | sí |
| 10 | conflicto de las alineaciones 4 y 5 | T sobre la T de la posición 7 | T sobre la T de la posición 7 | sí |
| 11 | menú de la alineación 0: letras, aristas, componentes y lazos | 11 · 13 · 1 · 3 | 11 · 13 · 1 · 3 | sí |
| 11 | letra de prueba y su grado | T, grado 6 | T, grado 6 | sí |
| 6.5 | menú del caso de respaldo: letras, aristas, componentes y lazos | 11 · 13 · 1 · 3 | 11 · 13 · 1 · 3 | sí |
| 6.5 | letra de prueba del caso de respaldo | T, grado 4 | T, grado 4 | sí |
| 9 | Kuhl: 105.456 · 21.230 · 11.466 | 105.456 · 21.230 · 11.466 | — | sin calcular (fase 5 (P2), que no se hizo: la diapositiva solo cita a Kuhl (2007)) |
| 13, 17 | decibanes por repetición: 10·log₁₀((1/17)/(1/26)) | +1,845 dB | +1,845 dB | sí |
| 5.6 | decibanes por no repetición: 10·log₁₀((16/17)/(25/26)) | −0,093 dB | −0,093 dB | sí |
| 17 | decibanes por letra, en promedio, en profundidad | +0,0211 dB | +0,0211 dB | sí |
| 17 | decibanes por letra, en promedio, al azar | −0,0184 dB | −0,0184 dB | sí |
| 13, 17 | umbrales de Wald con α = β = 1 % | ±19,96 dB | ±19,96 dB | sí |
| 13, 17 | letras esperadas según Wald, en profundidad y al azar | 929 y 1.062 | 929 y 1.062 | sí |
| 16 | Turing, 12 letras: paradas por orden con 0, 1, 2 y 3 lazos; en 60 órdenes con 2 y 3 | 820 · 31 · 1,2 · 0,04; 72 y 2,4 en 60 | 820 · 31 · 1,2 · 0,04; 72 y 2,4 en 60 | sí |

43 de 43 cifras calculadas coinciden; 1 sin calcular, de la fase 5, que no se hizo.

## 3. Demos

- **Demo 1 (diapositiva 4):** el cálculo es instantáneo. La traza de «Vector BDZGO» tarda 0,2 ms y la de «Portada» 0,7 ms en el equipo donde corrió `make resumen` (Intel64 Family 6 Model 158 Stepping 10, GenuineIntel, 6 núcleos lógicos). Los 45 s del guion los pone la interacción. Falta cronometrar el recorrido completo en el portátil del autor.
- **La app en clase:** abre `http://localhost:8501/maquina?demo=1` (el modo demo queda en la URL y sobrevive a una recarga) y, en otra pestaña, `http://localhost:8501/bombe?demo=1`; pliega la barra lateral para ganar ancho. En modo demo, Máquina muestra solo «Vector BDZGO» y «Portada», y La Bombe, «Cifrado del compañero» y «Caso de respaldo» (plan B).
- **Demo 2 (diapositiva 12):** `make bench-demo` del 2026-11-21 18:25 UTC (commit 5b34896) en Intel64 Family 6 Model 158 Stepping 10, GenuineIntel, 6 núcleos lógicos, Windows 11. Casos de compañero: clave como la de «Clave aleatoria» (10 cables), mensaje alemán de 78 letras que empieza por el crib, crib en la posición 0. Flujo completo de la página La Bombe: barrido, máquina de verificación y «Verificar». Éxito: el descifrado es el mensaje letra por letra.

| Configuración | Éxito (IC 95 %) | p50 | p95 | Barrido p95 | ¿Cumple? |
| --- | --- | --- | --- | --- | --- |
| 60 órdenes, modo robusto | 60 de 60 (94 %–100 %) | 6,4 s | 9,8 s | 7,3 s | sí |
| Rotores I, II y III (6 órdenes), modo robusto | 60 de 60 (94 %–100 %) | 1,3 s | 1,7 s | 0,8 s | sí |
| Crib WETTERBERICHTXFUER, 60 órdenes, modo robusto | 59 de 60 (91 %–100 %) | 8,9 s | 10,4 s | 10,4 s | sí |

- **Recomendada (la más simple con éxito ≥ 95% y p95 ≤ 30 s):** 60 órdenes, modo robusto: el compañero usa «Clave aleatoria» sin restricciones y empieza su mensaje por WETTERBERICHT (con X entre palabras). En la demo, el botón «Cifrado del compañero» de La Bombe deja el crib en la posición 0, «Rotores I a V (60 órdenes)» y el modo robusto; se pega el cifrado y se pulsa Ctrl+Enter. Éxito 100,0 %, p95 9,8 s.
- Estos tiempos son del equipo indicado. Este equipo es un escritorio; el presupuesto de 30 s es del portátil del autor (P-001): corre `make bench-demo` allí antes de ensayar y usa la configuración que recomiende.

## 4. Discrepancias

Ninguna contradicción con las diapositivas ni con el guion. Notas:

- Diapositivas 13 y 17: 929 y 1.062 letras son la aproximación de Wald, que ignora el sobrepaso de los umbrales. Con las mismas tasas, el valor exacto es 959,7 y 1.067,4, y la simulación lo confirma. Las cifras de la diapositiva siguen bien si se presentan como «según Wald».
- Diapositiva 13 y guion («las letras se repiten 1 de cada 17 veces»): es la tasa del tráfico naval que da Wikipedia. Nuestro corpus literario repite 1 de cada 12,5 con la X como separador y 1 de cada 13,2 solo con letras. Con él, la profundidad se confirma en unas 332 letras con los pesos de Turing. No contradice la diapositiva: es otro texto.
- Spec 5.6 («en profundidad … hasta que se mueve el rotor central»): con la máquina real los dos mensajes recorren la misma sucesión de estados, así que la profundidad dura todo el solapamiento. El rotor central decide si el desplazamiento verdadero es +δ o δ − 26 (D-042); por eso se prueban los desplazamientos de −25 a +25.
- Diapositiva 16: la tabla de Turing cuenta «letras del menú» como letras distintas (vértices del grafo), igual que la diapositiva 11 (11 letras, 13 aristas). Con esa lectura, nuestra Bombe da 678 · 26,3 · 0,99 · 0,11 paradas falsas por orden con 12 letras y 0 a 3 lazos, frente a 820 · 31 · 1,2 · 0,04 de Turing. Si «letras» fueran aristas (letras del crib), no coincidirían (ver D-031).
- Guion, diapositiva 16: «en los 60 órdenes quedan unas 2 paradas falsas en total; con dos lazos serían unas 72» son cifras de Turing (0,04 y 1,2 por 60). Nuestra Bombe da 6,6 y 59,4. El mensaje del guion se sostiene (con 3 lazos, unas pocas paradas en los 60 órdenes; con 2, decenas).
- Verificador (spec 6.4, «siempre»): recupera una clave equivalente en 200 de 200 de los casos de la prueba, que se usaron para ajustar su diseño, y en 198 de 200 casos nuevos. Las 2 fallas tienen el plugboard exacto y difieren en una sola letra, la segunda o la última del mensaje: un doble paso del central justo en el borde que el texto no alcanza a decidir. La parada verdadera aparece siempre (400 de 400).
- Diapositiva 12 y guion: la configuración de la demo 2 es la recomendada en «Demos»; el guion la tiene pendiente.
- Diapositiva 15: con alemán real, el 60 % de 13 letras pasa a 61,6 %, por encima de (25/26)^13 y fuera de su IC. No es un error del filtro: es el efecto del IC del idioma, y la corrección (1 − (1 − κ)/25)^13 = 61,4 % lo explica. La diapositiva puede seguir diciendo «60 %» para la teoría y agregar el valor real.
- py-enigma admite como máximo 10 cables: la comparación de 10.000 claves usa de 0 a 10 cables, y las pruebas con hypothesis cubren de 0 a 13.
- Mensaje histórico: no se encontró una fuente verificable del mensaje de Barbarossa (1941). Se usa el del U-264 (M4), publicado con clave, cifrado y texto por D. Rijmenants.
- Corpus: gutenberg.org estaba en mantenimiento el 20-11-2026; se descargó de su espejo oficial (Mirror Service), con SHA-256 verificado.

## 5. Pendientes

- Fase 5 · Rejewski (E7) y ataque moderno (E8), opcionales: no se hicieron; la diapositiva 9 solo cita a Kuhl y el README los lista entre las limitaciones.
- Demos · correr `make bench-demo` en el portátil del autor (P-001) y ensayar las dos demos allí: antes de ensayar.
- Repositorio remoto · crearlo, para la CI y el enlace de la diapositiva 21: antes de la presentación.
