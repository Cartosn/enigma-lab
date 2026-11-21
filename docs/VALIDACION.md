# Validación

Cómo se comprueba que el simulador y los ataques son correctos (spec, sección 6). La
validación es P0 y bloquea las demás fases: las pruebas de este documento corren con
`make test`, y E1 (`make reproduce`) guarda sus cifras en `results/summary.json`.

| Sección | Qué se valida | Estado |
| --- | --- | --- |
| 6.1 | Vectores de prueba y un mensaje histórico real | **Hecho** (9 de 9) |
| 6.2 | py-enigma en 10.000 claves y mensajes aleatorios | **Hecho** (100 %) |
| 6.2 | CyberChef: 5 casos de Enigma a mano en la web | **Hecho** (6 de 6) |
| 6.2 | CyberChef: 3 casos de la Bombe | **Hecho** (3 de 3, paradas y verificación) |
| 6.3 | Propiedades con hypothesis | **Hecho** |
| 6.3 | La Bombe en Numba coincide con la de referencia | **Hecho** (24 casos) |
| 6.4 | Bombe en 200 casos aleatorios | **Hecho** (parada 200 de 200; clave 200 de 200) |
| 6.5 | Casos deterministas de las diapositivas 10 y 11 | **Hecho** |
| 6.5 | Caso de respaldo en la Bombe | **Hecho** (para en II-III-I; descifra las 78 letras) |
| Fase 3 | Un orden en menos de 3 s; los 60 en menos de 2 min | **Hecho** |

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

### CyberChef: la Bombe (fase 3)

Docker Desktop seguía apagado, así que también se validó a mano en la web, el
21-11-2026 (D-041). `scripts/cyberchef_urls.py` arma, para cada caso, la URL con la receta
«Bombe» y el cifrado como entrada, sin y con la máquina de verificación de CyberChef, e
imprime las paradas que da nuestra Bombe en el orden verdadero.

**Qué se compara.** La Bombe de CyberChef supone anillos AAA y que solo gira el rotor
derecho, como nuestro modo Bletchley, y siempre usa el diagonal board. Informa cada parada
con la posición antes de la primera letra del crib, nuestra misma convención. Usa solo la
componente del menú con más lazos, así que los tres casos tienen menús conexos, donde eso
no cambia nada. La letra de prueba se fijó en la que eligió CyberChef.

| Caso | Paradas de CyberChef | ¿Iguales a las nuestras? | Con máquina de verificación | ¿Iguales? |
| --- | --- | --- | --- | --- |
| Respaldo (II-III-I, WETTERBERICHT, 3 lazos) | 1: HEC, T↔Q | Sí | 1: HEC, con 10 steckers | Sí, los mismos steckers |
| Al azar (V-IV-II, crib de 12 letras, 2 lazos) | 1: ZBJ, V↔W | Sí | 1: ZBJ, con 10 steckers | Sí |
| Al azar (I-II-III, crib de 11 letras en la posición 3, 1 lazo) | 84, entre ellas la verdadera (LZK, T↔C) | Sí, las 84 con su stecker | 5 | Sí: las mismas 5 y sus steckers |

El tercer caso es el exigente: 84 paradas, 83 de ellas falsas, con el crib desplazado. Las
dos implementaciones dan exactamente el mismo conjunto de posiciones y de steckers. La
máquina de verificación de CyberChef deja las mismas 5 paradas que nuestra etapa 1
(`checker.consistent_stops`), con los mismos steckers deducidos.

## 6.3 · Propiedades con hypothesis

`tests/test_properties.py` genera claves de cualquier modelo (Enigma I, M3 y M4), con
cualquier reflector y de 0 a 13 cables. Hypothesis corre en modo determinista.

- **Cifrar dos veces devuelve el original:** pasa.
- **Ninguna letra se cifra a sí misma:** pasa.
- **El cifrado por lotes (`encrypt_batch`) coincide con el escalar:** pasa, con claves de
  Enigma I y M3.
- **Prueba de las diapositivas 6 y 14:** 2.000 claves y 200.000 letras. Da 0 puntos
  fijos, involución en las 2.000 claves y lotes iguales al escalar.
- **La Bombe en Numba coincide con la de referencia:** pasa, en 24 casos
  (`tests/test_bombe.py::test_numba_matches_reference`). La referencia
  (`bombe/bombe_reference.py`) es independiente en lo que importa:
  - saca el aleatorizador de la máquina escalar y no de las tablas;
  - propaga la corriente hilo por hilo, como la máquina real, y no con union-find;
  - halla los hilos aislados energizando uno por uno los 26 del cable de prueba.

  Los 24 casos cubren cribs de 8 a 16 letras, con y sin diagonal board, en modo Bletchley
  y robusto. En cada uno se comparan, posición por posición y variante por variante, los
  hilos encendidos y la máscara de hilos aislados en la posición verdadera, 6 paradas y 6
  posiciones al azar.
- **El aleatorizador precalculado** coincide con la máquina escalar en 40 posiciones al
  azar y es una involución sin puntos fijos en las 17.576 posiciones.
- **Las paradas no dependen del hilo que se energiza:** con los hilos A y Q, mismas
  paradas y mismos hilos aislados.

## 6.4 · La Bombe en 200 casos aleatorios

`tests/test_bombe.py::test_section_64_two_hundred_cases`, marcada `lento` (unos 80 s);
otros 20 casos corren en cada `make test`.

- **Casos.** Clave aleatoria de Enigma I con 10 cables y mensaje alemán de 80 letras
  (corpus, X como separador). El crib, de 12 a 16 letras, es un tramo del mensaje en una
  posición al azar. Se vuelve a sortear hasta que el central no se mueva dentro del tramo.
- **Método.** Se barre el orden verdadero en modo Bletchley, con diagonal board, y se
  pasa el verificador completo por todas sus paradas.
- **La clave verdadera siempre da parada:** 200 de 200.
- **El verificador recupera una clave equivalente:** 200 de 200. «Equivalente»: descifra
  el mensaje letra por letra y vuelve a cifrarlo al mismo cifrado; anillos y posiciones
  pueden diferir, porque se compensan.
- **Con casos nuevos.** El verificador se ajustó con esos 200 casos (D-036), así que se
  comprobó también con otros 200, de semillas distintas:
  - parada verdadera: 200 de 200;
  - clave equivalente: 198 de 200.

  Las dos fallas tienen el plugboard exacto y difieren en una sola letra: la segunda del
  mensaje en una, la última en la otra. Un doble paso del central justo en el borde
  cambia solo esa letra, y el texto no alcanza a decidir cuál es la correcta. El
  verificador elige la secuencia que más claves producen (D-036), y en esos dos casos la
  verdadera era la rara.
- **Modo robusto.** En un caso con el central moviéndose dentro del crib, el modo robusto
  da la parada verdadera
  (`test_robust_mode_covers_a_turnover_in_the_crib`).

**Rendimiento (criterio de la fase 3).** En este equipo (i5-9400F, 6 núcleos), con un menú
de 14 letras, un orden tarda unos 0,03 s en modo Bletchley y los 60 órdenes unos 2 a 3 s;
el criterio es un orden en menos de 3 s y los 60 en menos de 2 minutos
(`test_performance_one_order_and_sixty`). El modo robusto con WETTERBERICHT, 13
variantes, tarda unos 0,2 s por orden.

## 6.5 · Casos de las diapositivas 10 y 11

`tests/test_cribs.py` los comprueba, y `enigma_lab/cifras.py` los lleva a `RESUMEN.md`.

- **Arrastre (diapositiva 10):** cifrado `BBGCCKITCTTEZZZLCZ`, crib `WETTERBERICHT`.
  - Hay 6 alineaciones, de la 0 a la 5. La 0, la 1, la 2 y la 3 no tienen conflictos.
  - En la 4 y la 5, una T del crib cae sobre la T de la posición 7.
  - La 4 además choca en la posición 11 (E sobre E); el spec no lo menciona, pero no lo
    contradice.
- **Menú (diapositiva 11), alineación 0:**
  - 11 letras, 13 aristas, 1 componente y 3 lazos; la letra de prueba es T, de grado 6.
  - Las aristas en lazos son exactamente las del texto: E–B (1), B–I (6), I–T (9),
    T–E (7), E–C (4) y las dos T–C (3 y 10).
- **Caso de respaldo:** 11 letras, 13 aristas y 3 lazos; letra de prueba T, de grado 4.
  - El central no se mueve en las 13 primeras letras.
  - En modo Bletchley, los 60 órdenes dan 11 paradas, de las que 3 pasan la máquina de
    verificación. Entre ellas está la verdadera, en el orden II-III-I, posición HEC, T↔Q.
  - El verificador descifra las 78 letras y da una clave equivalente: anillos AAW,
    posición HEY y el mismo plugboard. Lo comprueban
    `test_backup_case_stops_in_bletchley_mode_and_decrypts` y, en la página La Bombe,
    `test_bombe_page_backup_case_decrypts`.
- **Versión vectorizada del arrastre:** hypothesis comprueba que da lo mismo que la
  escalar.

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
- **Cifras de la presentación (`tests/test_presentacion.py`):** comprueba las 37 que ya
  tienen código, entre ellas las de Turing de la diapositiva 16 contra
  `data/reference/turing_stops.csv`. Las 2 restantes (Kuhl y Banburismus) aparecen como
  pendientes, con su fase.
