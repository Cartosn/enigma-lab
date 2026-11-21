# Validación

Cómo se comprueba que el simulador y los ataques son correctos (spec, sección 6). La
validación es P0 y bloquea las demás fases: las pruebas de este documento corren con
`make test`, y E1 (`make reproduce`) guarda sus cifras en `results/summary.json`.

| Sección | Qué se valida | Estado |
| --- | --- | --- |
| 6.1 | Vectores de prueba y un mensaje histórico real | **Hecho** (9 de 9) |
| 6.2 | py-enigma en 10.000 claves y mensajes aleatorios | **Hecho** (100 %) |
| 6.2 | CyberChef: 5 casos de Enigma a mano en la web | **Hecho** (6 de 6) |
| 6.2 | CyberChef: 3 casos de la Bombe | Fase 3 |
| 6.3 | Propiedades con hypothesis | **Hecho** (salvo la Bombe, fase 3) |
| 6.4 | Bombe en 200 casos aleatorios | Fase 3 |
| 6.5 | Casos deterministas de las diapositivas 10 y 11 | Fase 2 |

## 6.1 · Vectores de prueba

Están en `data/reference/test_vectors.json` y los comprueba `enigma_lab.core.vectors`.
Esa comprobación la usan tres sitios: `tests/test_vectors.py`, el experimento E1 y la
página Inicio, que la muestra en vivo.

| Vector | Esperado | Resultado |
| --- | --- | --- |
| AAAAA con I-II-III, reflector B, anillos y posición AAA | BDZGO | Coincide |
| Lo mismo con anillos BBB | EWTYX | Coincide |
| Doble paso desde ADU (4 pulsaciones) | ADU → ADV → AEW → BFX → BFY | Coincide |
| Ejemplo de py-enigma (II-IV-V, B-U-L, 10 cables): KCH → BLA, y desde BLA | THEXRUSSIANSXAREXCOMINGX | Coincide |
| Odómetro de I-II-III | periodo 16.900; 676 fuera del ciclo | Coincide |
| Traza de la letra A (diapositiva 4) | A → A → C → D → F → S → S → E → B → B → B | Coincide |
| Mensaje de la portada (diapositiva 1) | LGNEVYPYZQDVKESNPUYYQVWSKYNZJHE | Coincide |
| Caso de respaldo de la Bombe (78 letras) | ICGWNXTXINRGBWML… | Coincide |
| Mensaje real del U-264 (M4, 25-11-1942, 232 letras) | VONVONJLOOKS… | Coincide |

**Mensaje histórico.** No se encontró una fuente verificable del mensaje de Barbarossa
(1941): no está en Wikipedia ni en las páginas de Crypto Museum y Rijmenants que se
revisaron. Se usó el mensaje de Hartwig Looks (U-264), interceptado el 25-11-1942 y
roto por el M4 Project de Stefan Krah en 2006, con la clave, el cifrado y el texto
publicados por D. Rijmenants (ver `docs/FUENTES.md`). Por eso el simulador incluye
también la Enigma M4. Su descifrado coincide letra por letra con el texto publicado.

## 6.2 · Implementaciones independientes

### py-enigma 1.0.2

Ejecutado por E1 y por `tests/test_pyenigma.py` (la versión de 10.000 casos está
marcada como `lento`).

- **Diseño:** 10.000 claves y mensajes aleatorios, con semilla 2026. La mitad son de
  Enigma I y el resto se reparte entre M3 y M4. Llevan de 0 a 10 cables y mensajes de 1
  a 200 letras.
- **Lo que no cubre py-enigma:** no trae el reflector A ni admite más de 10 cables. Ese
  terreno lo cubren las pruebas con hypothesis, con 0 a 13 cables y todos los
  reflectores.
- **Resultado (E1, modo completo):** 10.000 de 10.000 coinciden, con 1.007.710 letras
  en total. El IC 95 % de Wilson es [99,96 %, 100 %].
  - Enigma I: 4.945 de 4.945.
  - M3: 2.568 de 2.568.
  - M4: 2.487 de 2.487.

### CyberChef (GCHQ)

Node.js no está instalado, y Docker Desktop estaba apagado cuando se validó. Por eso se
validó a mano en la web, como prevé el spec. `scripts/cyberchef_urls.py` arma para cada
caso la URL de CyberChef con la receta «Enigma» y el texto ya puestos; cualquiera puede
abrirlas y repetir la comparación. Se hizo el 20-11-2026 en https://gchq.github.io/CyberChef/.

| Caso | Salida de CyberChef | ¿Igual al simulador? |
| --- | --- | --- |
| AAAAA con I-II-III, AAA | BDZGO | Sí |
| AAAAA con anillos BBB | EWTYX | Sí |
| Portada (II-V-III, ENI, GMA, 10 cables) | LGNEVYPYZQDVKESNPUYYQVWSKYNZJHE | Sí |
| U-264 (M4, Beta-II-IV-I, B delgado, AAAV, VJNA) | VONVONJLOOKS… (232 letras) | Sí |
| py-enigma desde BLA (II-IV-V, BUL, 10 cables) | THEXRUSSIANSXAREXCOMINGX | Sí |
| M3 al azar (I-VI-II, reflector C, MCJ, QJV, 10 cables, 120 letras) | PARJVOMZYPGH… (120 letras) | Sí |

El último caso pone a prueba el rotor VI, que tiene dos muescas (Z y M), y el reflector C.

**Formato de CyberChef:**
- **Rotores:** cableado, «<» y la letra de llegada del arrastre. CyberChef escribe
  «<R» para el rotor I, cuya muesca nosotros escribimos «Q».
- **Reflector:** se escribe como parejas de letras.

Los 3 casos de la Bombe con CyberChef llegan en la fase 3.

## 6.3 · Propiedades con hypothesis

`tests/test_properties.py` genera claves de cualquier modelo (Enigma I, M3 y M4), con
cualquier reflector y de 0 a 13 cables. Hypothesis corre en modo determinista.

- **Cifrar dos veces devuelve el original:** pasa.
- **Ninguna letra se cifra a sí misma:** pasa.
- **El cifrado por lotes (`encrypt_batch`) coincide con el escalar:** pasa, con claves de
  Enigma I y M3.
- **Prueba de las diapositivas 6 y 14:** 2.000 claves y 200.000 letras. Da 0 puntos
  fijos, involución en las 2.000 claves y lotes iguales al escalar.
- **La Bombe en Numba coincide con la de referencia:** fase 3.

## Otras comprobaciones

- **Cableados:** coinciden con los de py-enigma (`tests/test_wiring.py`). Cada rotor es
  una permutación y cada reflector es una involución sin puntos fijos.
- **Paso de los rotores (`tests/test_stepping.py`):**
  - el doble paso desde ADU;
  - un solo ciclo de 16.900 posiciones con 676 fuera;
  - el arrastre de los rotores de dos muescas en Z y en M;
  - el rotor griego de la M4, que nunca gira.
- **Animación (`tests/test_machine_page.py`):** recibe exactamente la traza de
  `Enigma.trace`, y su HTML no contiene ningún cableado: no reimplementa la máquina. En
  el navegador, la letra 1 de «Vector BDZGO» recorre A → A → C → D → F → S → S → E → B
  → B → B, como en la diapositiva 4.
- **Cifras de la presentación (`tests/test_presentacion.py`):** comprueba las 29 que ya
  tienen código. Las 5 restantes aparecen como pendientes, con su fase.
