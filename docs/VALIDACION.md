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
| Fase 4 | SPRT simulado frente a la aproximación de Wald (929 y 1.062 letras) | **Hecho** (983 y 1.090; exacto 959,7 y 1.067,4) |

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

**Rendimiento (criterio de la fase 3: un orden en menos de 3 s y los 60 en menos de 2
minutos).** Medido en este equipo (i5-9400F, 6 núcleos), sin otros procesos pesados:
- E5 (solo el barrido, con las tablas precalculadas): 0,006 s por orden en modo
  Bletchley y 0,10 s en robusto;
- página La Bombe, caso de respaldo: los 60 órdenes en modo Bletchley tardaron 1,9 s;
- banco de la demo 2: con WETTERBERICHT, en modo robusto, los 60 órdenes tardan 5,6 s
  (p50) y 7,3 s (p95).

`test_performance_one_order_and_sixty` lo comprueba en cada `make test`. Con la máquina
ocupada en otras tareas, los tiempos llegaron a triplicarse; el portátil del autor puede
dar otros (P-001).

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

## Fase 4 · Banburismus

`tests/test_banburismus.py`, `tests/test_experiments.py::test_e6_banburismus_small` y la
página (`tests/test_pages.py`).

**Los mensajes en profundidad, contra la máquina.**
- *Máquina escalar.* Con `core.machine.Enigma`, los dos mensajes de un par dan el mismo
  cifrado que el lote (`encrypt_batch`). En el desplazamiento verdadero, la letra j del
  mensaje 2 usa las mismas ventanas que la j + d del 1, letra por letra
  (`test_depth_against_the_scalar_machine`).
- *Repeticiones.* En 200 pares de texto alemán con 400 columnas, el cifrado repite
  exactamente donde repite el texto plano. En desplazamientos falsos repite con
  1/26 ± 0,003.
- *Desplazamiento.* En 1.500 claves al azar, siempre hay profundidad, y el desplazamiento
  verdadero es +δ o δ − 26. Es positivo en la mitad de los casos (±5 %), como se espera
  con δ uniforme (D-042).
- *Texto con tasa 1/17.* Repite con 1/17 ± 0,002 en el desplazamiento verdadero.

**Decibanes y Wald.**
- +1,845, −0,093, +0,0211 y −0,0184 dB, ±19,96 dB y 929 y 1.062 letras. Las seis cifras
  están en `cifras.py` y las comprueba `tests/test_presentacion.py` con el formato de las
  diapositivas.
- *Cálculo exacto* (`sprt.exact_letters`). Cumple la identidad de Wald, E[S_N] = μ·E[N],
  con un error relativo menor que 10⁻⁹. La probabilidad sin decidir al cortar es menor
  que 10⁻¹². Los errores reales quedan bajo el 1 % nominal, y el sobrepaso medio está entre
  0 y el salto de un paso.
- *Simulación frente a cálculo exacto.* Con 2.000 secuencias de Bernoulli de 10.000 letras,
  la media de letras cae a menos de 4 errores estándar del valor exacto, en profundidad y
  al azar.
- *Numba frente a Python.* El núcleo de Numba (`_sprt_kernel`) da las mismas letras, la
  misma decisión y el mismo puntaje final que `sprt_reference` en 200 secuencias. Se probó
  con letras sueltas y con trigramas, y con dos pares de umbrales a la vez. Sus puntajes
  anotados coinciden con la trayectoria vectorizada (`scoring.trajectory`).

**Multigramas.** La cadena de rachas reproduce, a la larga, la tasa de repetición del
corpus (ρ₁) y la de dos columnas seguidas (ρ₂), con 1, 3 y 4 n-gramas. Un bigrama repetido
pesa más que dos letras sueltas, y con letras sueltas da igual dónde caigan las
repeticiones.

**E6 frente a la referencia** (modo completo, 2.000 pares, semilla 2026). Con letras sueltas
y tasa 1/17, el SPRT pide 983 letras en profundidad (IC 95 % 954–1.012) y 1.090 al azar
(1.061–1.120).
- *Wald* da 929 y 1.062. El primero queda fuera del IC por debajo: es la diferencia que
  explica el sobrepaso (D-048).
- *El cálculo exacto* da 959,7 y 1.067,4, dentro de los dos IC.
- *La identidad de Wald* con el puntaje final medido da 963 y 1.072 letras.

## Fase 5 · Rejewski (E7)

**La característica no depende del plugboard** (`tests/test_rejewski.py`, con hypothesis): en
claves al azar de Enigma I, M3 y M4, con 0 a 13 cables, la estructura de AD, BE y CF con la
máquina real es la misma que sin plugboard, y cada producto tiene sus ciclos en parejas.

**El catálogo contra la máquina.** En claves de 1932 al azar (rotores I–III, reflector A,
anillos, posición y 0 a 13 cables), cuando el central no se mueve durante el indicador, la
entrada del catálogo en la posición del núcleo es la característica que da la máquina real. La
búsqueda devuelve la configuración consultada, y la clase tiene tantas configuraciones como
dice su tamaño. El central se mueve en exactamente 176 de las 676 posiciones del central y del
derecho.

**El catálogo contra Kuhl (2007)** (exacto, sin azar):

| | E7 | Kuhl | Diferencia |
| --- | --- | --- | --- |
| Configuraciones | 105.456 | 105.456 | 0 |
| Características distintas | 21.225 | 21.230 | −5 (−0,02 %) |
| Únicas (una sola configuración) | 11.578 | 11.466 | +112 (+1,0 %) |
| La más frecuente, (13 13)(13 13)(13 13) | 1.728 | 1.771 | −43 (−2,4 %) |
| Con 10 configuraciones o menos | 19.556 | 19.604 (su tabla 2) | −48 |

- *La forma coincide:* los tamaños de 1 a 16 difieren poco (por ejemplo, 3.345 frente a 3.381 de
  tamaño 2), y 14 de las 15 características de su tabla 1 están entre nuestras 15 más
  frecuentes, con tamaños a menos del 13 % de los suyos.
- *Las cifras no:* `scripts/kuhl_variantes.py` prueba 33 variantes de los supuestos (D-062).
  Ninguna da 21.230, 11.466 y 1.771; la suma de diferencias con su tabla 2 va de 256 a 895
  (442 con nuestros supuestos). Girar el reflector A no cambia nada (es renombrar posiciones), y
  las distribuciones de los reflectores B y C se parecen tanto como la nuestra.
- *Erratas del artículo:* escribe dos veces 105.465 configuraciones; da 11.466 como el 54,40 %
  (11.466/21.230 es el 54,01 %); y dice que 20.433 características tienen 10 configuraciones o
  menos, cuando su tabla 2 suma 19.604 para esos tamaños (y 19.604/21.230 es el 92,34 % que él
  mismo da). Su tabla 2 salta del tamaño 14 al 16.
- *Conclusión:* no ajustamos nada. Kuhl no publica su programa ni dice qué supone del rotor
  central y de los anillos; nuestros supuestos están escritos y probados contra la máquina real.

**Completar con el teorema** (`traffic.completions`): el conteo de completaciones con los ciclos
en parejas coincide con la fuerza bruta (todas las formas de cerrar las cadenas) en 150 de 150
productos con 1 a 5 letras desconocidas.

## Fase 5 · Ataque moderno (E8)

- **La tabla de sucesores** del paso (`gillogly.step_table`) coincide con `core/stepping.step` en
  600 ventanas al azar de tres órdenes.
- **El núcleo de la fase 1** (Numba, en paralelo) da el mismo IC que un cálculo en Python puro en
  cuatro posiciones (D-065 cuenta el error que esta prueba atrapó).
- **La ubicación y el plugboard verdaderos descifran como la máquina:** el aleatorizador de cada
  letra (`paths_for`) con el plugboard verdadero da el texto plano exacto (10 cables, 700 letras,
  rotores I–V), y la clave equivalente que arma `location_config` descifra igual con
  `core/machine.py`.
- **El hill climbing** desde la ubicación verdadera recupera los 10 cables exactos en 300 letras.
- **El ataque completo** lee un mensaje de 800 letras con 6 cables entre los 6 órdenes de I–III,
  con el orden verdadero, y la ubicación verdadera queda entre las 100 mejores de la fase 1.
- **La regresión logística** de E8 recupera la longitud con 50 % de éxito de datos simulados con
  una curva conocida (L₅₀ = 200 dentro de su IC).
- **La figura** se dibuja con celdas sin éxitos. La primera corrida completa se detuvo ahí: con 0
  de 24, el límite inferior de Wilson salía a un error de redondeo sobre la proporción y el bigote
  quedaba negativo. `67e022b` lo recorta y la corrida se repitió entera (D-067).

**E8 frente a las referencias** (modo completo, 864 mensajes, los 60 órdenes, semilla 2026):
- *Gillogly, «unas 300 letras con 6 cables o menos»:* la regresión logística da que, con 6
  cables, la mitad de los mensajes se lee desde unas 314 letras (IC 95 % 273–362).
- *Gillogly, «un solo éxito con 10 cables, con 1.463 letras»:* con 10 cables el ataque lee el 25 %
  de los mensajes de 1.500 letras, el 12,5 % de los de 1.000 y casi ninguno más corto.
- *La distancia de unicidad, unas 23 letras:* con 25 letras ni siquiera el hill climbing desde la
  ubicación verdadera lee los mensajes (ninguno con el plugboard vacío; con la búsqueda parcial
  de la E, 1 de 24 con 6 cables y 1 de 24 con 8). Ostwald y Weierud dicen que bajo unas 20 letras los mensajes son
  prácticamente irrompibles y que en sus pruebas el umbral rondó las 24; su método agota todas las
  ubicaciones, y aquí la fase 1 es la de Gillogly.
- *Sin falsos éxitos:* ningún mensaje se leyó con el orden equivocado.

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
- **Cifras de la presentación (`tests/test_presentacion.py`):** comprueba las 45, entre ellas
  las de Turing de la diapositiva 16 contra `data/reference/turing_stops.csv`, las seis del
  Banburismus (diapositivas 13 y 17) y las dos de la diapositiva 9: las 105.456 configuraciones
  del catálogo y las cifras de Kuhl contra `data/reference/kuhl_2007.json` (D-063).
