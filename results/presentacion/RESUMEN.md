# Resumen de resultados para la presentación

- **Fecha:** 2026-11-21 03:33 UTC
- **Commit:** 6bd632e
- **Semilla:** 2026
- **Modo:** completo
- **Corridas:** E1: modo completo, 2026-11-21 03:33 UTC, commit 6bd632e; E2: modo completo, 2026-11-21 03:33 UTC, commit 6bd632e; E3: modo completo, 2026-11-21 03:33 UTC, commit 6bd632e; E4: modo completo, 2026-11-21 03:33 UTC, commit 6bd632e

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

Pendiente (fase 3).

### Diapositiva 17 · Banburismus (E6)

Pendiente (fase 4).

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
| 9 | Kuhl: 105.456 · 21.230 · 11.466 | 105.456 · 21.230 · 11.466 | — | pendiente (fase 5 (P2): rejewski/; si no se hace, la diapositiva solo cita a Kuhl) |
| 13, 17 | decibanes y aproximación de Wald | +1,845 dB; +0,0211 y −0,0184 dB; ±19,96 dB; 929 y 1.062 letras | — | pendiente (fase 4: banburismus/) |
| 16 | Turing, 12 letras: paradas por orden | 820 · 31 · 1,2 · 0,04; 72 y 2,4 en 60 | — | pendiente (fase 3: turing_stops.csv y E5) |

36 de 36 cifras calculadas coinciden; 3 llegan en fases siguientes.

## 3. Demos

- **Demo 1 (diapositiva 4):** el cálculo es instantáneo. La traza de «Vector BDZGO» tarda 0,2 ms y la de «Portada» 0,6 ms en el equipo donde corrió `make resumen` (Intel64 Family 6 Model 158 Stepping 10, GenuineIntel, 6 núcleos lógicos). Los 45 s del guion los pone la interacción. Falta cronometrar el recorrido completo en el portátil del autor.
- **Demo 2 (diapositiva 12):** pendiente (fase 3), con `make bench-demo`. Riesgo conocido: con WETTERBERICHT, el rotor central se mueve dentro del tramo en casi la mitad de las claves, y la mayoría de los menús tienen 0 o 1 lazos.

## 4. Discrepancias

Ninguna contradicción con las diapositivas ni con el guion. Notas:

- Diapositiva 15: con alemán real, el 60 % de 13 letras pasa a 61,6 %, por encima de (25/26)^13 y fuera de su IC. No es un error del filtro: es el efecto del IC del idioma, y la corrección (1 − (1 − κ)/25)^13 = 61,4 % lo explica. La diapositiva puede seguir diciendo «60 %» para la teoría y agregar el valor real.
- py-enigma admite como máximo 10 cables: la comparación de 10.000 claves usa de 0 a 10 cables, y las pruebas con hypothesis cubren de 0 a 13.
- Mensaje histórico: no se encontró una fuente verificable del mensaje de Barbarossa (1941). Se usa el del U-264 (M4), publicado con clave, cifrado y texto por D. Rijmenants.
- Corpus: gutenberg.org estaba en mantenimiento el 20-11-2026; se descargó de su espejo oficial (Mirror Service), con SHA-256 verificado.

## 5. Pendientes

- Fase 3 · Bombe (E5) y configuración de la demo 2: semana 2.
- Fase 4 · Banburismus (E6): semana 3.
- Fase 5 · Rejewski (E7) y ataque moderno (E8), opcionales: semana 3.
- Fase 6 · modo demo completo, Docker, informe y entrega: fin de la semana 3.
