# Resumen de resultados para la presentación

- **Fecha:** 2026-11-21 02:56 UTC
- **Commit:** 6b032e0
- **Semilla:** 2026
- **Modo:** completo (E1, corrido el 2026-11-21 02:56 UTC sobre el commit 6b032e0)

Generado por `make resumen` a partir de `results/summary.json` y los Parquet, sin volver a correr experimentos. Cada cifra sale del código.

## 1. Por diapositiva de resultados

### Diapositiva 14 · Validación (E1)

- **Cifra para la diapositiva:** 10.000 de 10.000 claves y mensajes aleatorios coinciden con py-enigma (100 %; IC 95 % de Wilson 99,96 %–100,00 %). N = 10.000, semilla 2026, 1.007.710 letras.
- Por modelo: Enigma I: 4.945 de 4.945, M3: 2.568 de 2.568, M4: 2.487 de 2.487. Cables de 0 a 10 (py-enigma no admite más); reflectores B y C (B y C delgados en la M4).
- Propiedades con 2.000 claves de Enigma I y 200.000 letras: 0 puntos fijos; cifrar dos veces devolvió el original en 2.000 claves; el cifrado por lotes coincidió con el escalar en 2.000.
- Vectores de 6.1: 9 de 9 coinciden (tabla en `r1_validacion.csv`).
- Nuevo para la diapositiva 14, si cabe: el simulador descifra letra por letra un mensaje real, el del U-264 (Enigma M4, 25-11-1942, roto por el M4 Project en 2006).

### Diapositiva 15 · Cribs (E4)

Pendiente (fase 2): la simulación con texto alemán real. La fórmula ya está comprobada en la tabla de abajo.

### Diapositiva 16 · Bombe (E5)

Pendiente (fase 3).

### Diapositiva 17 · Banburismus (E6)

Pendiente (fase 4).

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
| 9 | Kuhl: 105.456 · 21.230 · 11.466 | 105.456 · 21.230 · 11.466 | — | pendiente (fase 5 (P2): rejewski/; si no se hace, la diapositiva solo cita a Kuhl) |
| 10, 11 | casos deterministas de 6.5 (arrastre y menú) | 6 alineaciones; menú de 11 letras, 13 aristas y 3 lazos | — | pendiente (fase 2: cribs/) |
| 13, 17 | decibanes y aproximación de Wald | +1,845 dB; +0,0211 y −0,0184 dB; ±19,96 dB; 929 y 1.062 letras | — | pendiente (fase 4: banburismus/) |
| 15 | E4: fracción simulada con texto alemán real | dentro del IC de (25/26)^L | — | pendiente (fase 2: E4) |
| 16 | Turing, 12 letras: paradas por orden | 820 · 31 · 1,2 · 0,04; 72 y 2,4 en 60 | — | pendiente (fase 3: turing_stops.csv y E5) |

29 de 29 cifras calculadas coinciden; 5 llegan en fases siguientes.

## 3. Demos

- **Demo 1 (diapositiva 4):** el cálculo es instantáneo. La traza de «Vector BDZGO» tarda 0,2 ms y la de «Portada» 0,8 ms en el equipo donde corrió `make resumen` (Intel64 Family 6 Model 158 Stepping 10, GenuineIntel, 6 núcleos lógicos). Los 45 s del guion los pone la interacción. Falta cronometrar el recorrido completo en el portátil del autor.
- **Demo 2 (diapositiva 12):** pendiente (fase 3), con `make bench-demo`. Riesgo conocido: con WETTERBERICHT, el rotor central se mueve dentro del tramo en casi la mitad de las claves, y la mayoría de los menús tienen 0 o 1 lazos.

## 4. Discrepancias

Ninguna con las diapositivas ni con el guion en lo que cubre esta fase. Notas:

- py-enigma admite como máximo 10 cables: la comparación de 10.000 claves usa de 0 a 10 cables, y las pruebas con hypothesis cubren de 0 a 13.
- Mensaje histórico: no se encontró una fuente verificable del mensaje de Barbarossa (1941). Se usa el del U-264 (M4), con clave, cifrado y texto publicados por D. Rijmenants. Por eso el simulador incluye también la M4.

## 5. Pendientes

- Fase 2 · estadística y cribs (E2 a E4): semanas 1–2, antes de la reunión con el profe.
- Fase 3 · Bombe (E5) y configuración de la demo 2: semana 2.
- Fase 4 · Banburismus (E6): semana 3.
- Fase 5 · Rejewski (E7) y ataque moderno (E8), opcionales: semana 3.
- Fase 6 · modo demo completo, Docker, informe y entrega: fin de la semana 3.
