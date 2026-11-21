# Guía de estudio

Para defender el proyecto frente al profesor (spec, sección 8.4). Cada tema explica la
idea en lenguaje claro, da la fórmula y dice en qué archivo y función está. Crece con
cada fase.

**Temas:**
1. [El espacio de claves](#1-el-espacio-de-claves) (fase 0)
2. [La máquina y el doble paso](#2-la-máquina-y-el-doble-paso) (fase 1)
3. [Estadística del idioma, cribs y menús](#3-estadística-del-idioma-cribs-y-menús) (fase 2)
4. [La Bombe, el diagonal board y el verificador](#4-la-bombe-el-diagonal-board-y-el-verificador) (fase 3)
5. [Banburismus, decibanes y la prueba secuencial](#5-banburismus-decibanes-y-la-prueba-secuencial) (fase 4)
6. Rejewski y el ataque moderno (fase 5)
7. [Preguntas probables](#preguntas-probables)

## 1. El espacio de claves

**Idea.** Una clave de Enigma se arma con cuatro elecciones independientes: los rotores
y su orden, la posición inicial de cada uno, los anillos y los cables del plugboard. El
total es el producto de las opciones de cada elección. Medido en bits (log₂), es la
suma de los bits de cada componente.

| Componente | Opciones | Bits | Función |
| --- | --- | --- | --- |
| Orden de rotores | P(5, 3) = 5 · 4 · 3 = 60 | 5,91 | `core/keyspace.py` · `rotor_orders` |
| Posiciones | 26³ = 17.576 | 14,10 | `rotor_positions` |
| Anillos efectivos | 26² = 676 | 9,40 | `effective_ring_settings` |
| Plugboard, 10 cables | N(10) = 150.738.274.937.250 | 47,10 | `plugboard_settings` |

**El plugboard.** N(k) = 26! / ((26 − 2k)! · k! · 2^k).
- Se eligen en orden 2k letras distintas: 26! / (26 − 2k)! listas.
- Se emparejan de dos en dos. Cada plugboard aparece k! veces, porque el orden de las
  parejas no importa, y 2^k veces más, porque la pareja AB es la misma que BA.

**Totales.**
- Sin anillos: 60 · 17.576 · N(10) = 158.962.555.217.826.360.000 ≈ 1,6 × 10²⁰ (67,11 bits).
- Con anillos: 1,0746 × 10²³ (76,51 bits).
- El plugboard pone el 70,2 % de los 67,11 bits.

**La idea clave del proyecto.** La Bombe no prueba claves: aparta el plugboard y solo
recorre órdenes × posiciones = 1.054.560 configuraciones (20,01 bits). Probar las
1,6 × 10²⁰ claves a 10⁹ por segundo tomaría unos 5.037 años; el barrido de la Bombe es
2⁴⁷ veces más pequeño. La fase 3 pide que la Bombe en software recorra los 60 órdenes
en menos de 2 minutos. (`KeySpace.bombe_sweep` y `brute_force_years`)

**Preguntas que pueden salir:**
- *¿Por qué el anillo izquierdo no cuenta?* El anillo solo importa en dos cosas: dónde
  está el cableado respecto a la letra de la ventana y cuándo arrastra al rotor
  siguiente. El izquierdo no arrastra a ninguno, así que cambiar su anillo equivale a
  cambiar su posición inicial, que ya está contada.
  (`effective_ring_settings`)
- *¿Por qué el máximo es con 11 cables y no con 13?* N(k) crece mientras quedan
  suficientes letras libres para formar parejas nuevas. Con 11 cables quedan 4 letras
  libres; con 13 no queda ninguna, y N(13) = 7.905.853.580.625 < N(11) =
  205.552.193.096.250. (`best_cable_count`; prueba `test_plugboard_maximum_is_eleven_cables`)
- *¿Cómo se comprueba la fórmula de N(k)?* Además de los valores exactos del spec, una
  prueba con hypothesis verifica para todo k la recurrencia
  N(k) · k = N(k − 1) · C(26 − 2(k − 1), 2): cada plugboard de k cables sale de uno de
  k − 1 cables agregando una pareja, de k maneras. (`tests/test_keyspace.py`)

## 2. La máquina y el doble paso

**Idea.** Enigma es una sustitución que cambia con cada letra. La tecla cierra un
circuito que recorre:
1. el plugboard (P);
2. los tres rotores de derecha a izquierda (R, M, L);
3. el reflector (U);
4. los mismos rotores de vuelta;
5. otra vez el plugboard, hasta encender una lámpara.

Antes de cada letra, el rotor derecho avanza un paso, así que la sustitución de la
siguiente letra ya es otra.

**Fórmula del camino.** lámpara = P⁻¹ · R⁻¹ · M⁻¹ · L⁻¹ · U · L · M · R · P (tecla).

**Fórmula de un rotor desplazado.** Si la ventana muestra p y el anillo está en r, el
cableado W queda corrido s = p − r lugares. La salida para la entrada x es
W[(x + s) mod 26] − s (mod 26). El anillo solo cambia dónde queda el cableado respecto
a la letra de la ventana. (`core/machine.py` · `Enigma._rotor`)

**Por qué cifrar es descifrar y nunca hay puntos fijos.** El reflector U es una
involución sin puntos fijos: U(U(x)) = x y U(x) ≠ x. La permutación completa es una
conjugación de U, E = C⁻¹ · U · C con C = L · M · R · P, y conjugar conserva ambas
propiedades:
- E(E(x)) = x, así que cifrar dos veces devuelve el original;
- E(x) ≠ x, así que ninguna letra se cifra a sí misma.

La segunda propiedad es la grieta que usan los cribs y la Bombe.
(`core/wiring.py` · `is_reflector`; pruebas en `tests/test_properties.py`)

**El paso de los rotores y el doble paso.** (`core/stepping.py` · `step`)
- El derecho avanza siempre.
- El central avanza si el derecho está en su muesca.
- El izquierdo avanza si el central está en su muesca.
- **El doble paso:** cuando el central está en su muesca, también avanza él mismo,
  porque el trinquete del izquierdo empuja esa muesca. Por eso el central se mueve en
  dos pulsaciones seguidas: ADU → ADV → AEW → BFX.

**El periodo: 16.900, no 17.576.** El paso es una función de las 26³ posiciones en sí
mismas.
- Con I-II-III, toda trayectoria cae en un único ciclo de 26 · 25 · 26 = 16.900
  posiciones.
- Quedan 676 posiciones fuera, por las que se pasa a lo sumo una vez.
- `cycle_structure` lo calcula aplicando el paso al conjunto de todas las posiciones
  hasta que deja de cambiar.

**La traza.** `Enigma.trace` devuelve, por letra:
- las ventanas antes y después del paso;
- qué rotores avanzaron y si hubo doble paso;
- la letra que sale de cada etapa.

Con I-II-III en AAA, la A sale B por el camino A → A → C → D → F → S → S → E → B →
B → B (diapositiva 4). La animación de la página Máquina dibuja esa traza y no calcula
nada.

**Cifrado por lotes.** Para los Monte Carlo, `core/batch.py` · `encrypt_batch` cifra N
mensajes a la vez. Precalcula la tabla T[r, s, x] de cada rotor r con cada
desplazamiento s, así cada etapa es una sola búsqueda en NumPy. Una prueba exige que
dé lo mismo que la versión escalar.

**La M4.** Agrega a la izquierda un rotor griego (Beta o Gamma) que nunca gira y usa un
reflector delgado. Con ella el simulador descifra un mensaje real del U-264 (1942).

**Preguntas que pueden salir:**
- *¿Por qué ninguna letra se cifra a sí misma?* Porque el reflector no tiene puntos
  fijos y la máquina completa es una conjugación del reflector.
- *¿Para qué sirve el anillo si no cambia el cableado?* Mueve el cableado respecto a la
  letra de la ventana, y con él el punto en que el rotor arrastra al siguiente: la
  muesca está en el anillo. Por eso la Bombe puede buscar con anillos AAA, y el
  verificador recupera después los anillos derecho y central.
- *¿Cómo sé que el simulador está bien?*
  - Reproduce los 9 vectores publicados (BDZGO, EWTYX, el doble paso…).
  - Coincide con py-enigma en 10.000 claves aleatorias y con CyberChef en 6 casos.
  - Descifra un mensaje real de 1942.

## 3. Estadística del idioma, cribs y menús

**El corpus.** Son textos de dominio público: en alemán, Fontane y Kafka; en español,
Cervantes. Se normalizan a A–Z: en alemán Ä → AE, Ö → OE, Ü → UE, ß → SS; en español
se quitan las tildes y Ñ → N. Con «X como separador», cada tramo de espacios y signos
se vuelve una X, como en los mensajes militares. (`stats/corpus.py` · `normalize`)

**Índice de coincidencia.** IC = Σ nᵢ(nᵢ − 1) / (N(N − 1)) es la probabilidad de que dos
letras del texto, tomadas al azar, sean iguales.
- En alemán ≈ 0,0758 (Pommerening); nuestro corpus da 0,0757.
- Al azar, 1/26 ≈ 0,0385.
- Una sustitución fija no lo cambia. Enigma lo lleva a 1/26, porque usa otra sustitución
  en cada letra.

(`stats/frequencies.py` · `index_of_coincidence`; experimento E3)

**Prueba χ².** χ² = Σ (Oᵢ − Eᵢ)²/Eᵢ, con Eᵢ = N/26 y 25 grados de libertad. Con
mensajes de 50 letras o más rechaza la uniformidad de casi todos los textos planos; en
los cifrados de Enigma la rechaza pocas veces (`chi2_uniform`; cifras de E3 en
`RESUMEN.md`).

**La antifrecuencia.** El cifrado no es del todo uniforme. Una letra plana p sale como
cualquiera de las otras 25 con la misma probabilidad, nunca como sí misma. Por eso la
letra c aparece en el cifrado con probabilidad (1 − f_c)/25: las letras frecuentes del
idioma salen un poco *menos* que 1/26. Con mensajes de 1.000 letras, la χ² ya lo detecta
más veces que el 5 % de un cifrado uniforme, y la χ² no central predice cuántas
(`enigma_cipher_frequencies`, `chi2_power`).

**El distinguidor.** Lo que Enigma no puede esconder es que ninguna letra se cifra a sí
misma: la diagonal de la matriz plano × cifrado es cero. Con una sustitución al azar,
que ninguna de L letras coincida pasaría con probabilidad (25/26)^L; con L = 100, el
1,98 %. (`stats/inference.py` · `no_fixed_point_probability`)

**N-gramas.** Para reconocer un descifrado bueno se suman los log₁₀ de las
probabilidades de sus cuadrigramas en el corpus.
- Texto alemán: unos −4,0 por cuadrigrama.
- Letras al azar: unos −7,2.
- Un cuadrigrama que no aparece en el corpus recibe un piso de 0,01 apariciones.

(`stats/ngrams.py`)

**El arrastre del crib.** El crib se coloca en cada posición del cifrado. Si una letra del
crib cae sobre la misma letra cifrada, esa posición es imposible (`cribs/dragging.py`).
- **Con letras al azar:** una alineación falsa sobrevive con probabilidad (25/26)^L; el
  60,1 % con L = 13 y el 14,1 % con L = 50.
- **Con alemán real:** sobreviven un poco más. La letra j del crib choca solo si es
  distinta de la letra plana de esa posición, y entonces con probabilidad 1/25. Con κ,
  la probabilidad de que dos letras del texto coincidan, queda
  P ≈ (1 − (1 − κ)/25)^L. Con κ = 1/26 vuelve a dar (25/26)^L.

E4 lo mide (`experiments/e4_cribs.py`).

**El menú.** Con el crib alineado, cada columna (p, c, paso i) es una arista p — c: esas
dos letras pasan por el mismo aleatorizador en el paso i. El grafo es un `MultiGraph`,
porque la misma pareja puede repetirse en dos pasos (`cribs/menu.py`).
- **Lazos:** el número ciclomático E − V + 1 de la componente usada.
- **Letra de prueba:** la de mayor grado en esa componente.
- **El ejemplo de la diapositiva 11:** 11 letras, 13 aristas y 3 lazos (E–B–I–T, el
  triángulo E–C–T y las dos aristas T–C); letra de prueba T, de grado 6.

**Preguntas que pueden salir:**
- *¿Por qué el IC del cifrado es 1/26 si Enigma es una sustitución?* Porque cambia de
  sustitución en cada letra: la misma letra plana sale cifrada como letras distintas,
  y las frecuencias se reparten.
- *¿Por qué con alemán sobreviven más alineaciones falsas que (25/26)^L?* Porque cuando
  la letra del crib coincide con la letra plana de esa posición, el conflicto es
  imposible. En alemán eso pasa con probabilidad κ ≈ 0,08 en vez de 1/26. El
  experimento E4 lo mide.
- *¿Qué es un lazo y por qué importa?* Es un ciclo del menú: una cadena de hipótesis de
  plugboard que debe volver a cerrar en la letra de partida. Con una hipótesis falsa
  casi nunca cierra, y cada lazo divide las paradas falsas por unas 26 (fase 3).

## 4. La Bombe, el diagonal board y el verificador

**Idea.** La Bombe no prueba claves: prueba hipótesis sobre el plugboard. Para cada orden
de rotores y cada una de sus 17.576 posiciones supone que la letra de prueba T va con una
letra x del plugboard y saca todas las consecuencias. Si llevan a una contradicción,
descarta la posición. Así recorre 60 × 17.576 = 1.054.560 configuraciones (20,01 bits) y no
las 1,6 × 10²⁰ claves: el plugboard queda fuera de la búsqueda.

**El aleatorizador.** Sin el plugboard, en cada pulsación la máquina es
S = R⁻¹ · M⁻¹ · L⁻¹ · U · L · M · R. Con el plugboard P la máquina completa es
E = P · S · P, porque P es su propia inversa. La Bombe busca con anillos AAA: una posición
es el corrimiento de cada rotor, s = ventana − anillo. El aleatorizador de las 17.576
posiciones de un orden se precalcula una vez, en una tabla (17.576 × 26).
(`bombe/scrambler.py` · `scrambler_table`)

**El menú como circuito.** (`bombe/wiring.py`)
- Cada letra del menú es un cable de 26 hilos. El hilo u del cable a es la hipótesis
  «P(a) = u».
- La arista (a, b, i) del menú dice que en el paso i del crib la máquina lleva a hasta b:
  Sᵢ(P(a)) = P(b). Por eso une el hilo u del cable a con el hilo Sᵢ(u) del cable b, para
  las 26 hipótesis a la vez.
- **Desfase.** Los rotores avanzan antes de cifrar cada letra. Si C es la posición antes de
  la primera letra del crib, el paso i usa el rotor derecho en C + i + 1.

**La corriente: union-find.** Energizar un hilo enciende todos los conectados con él: su
componente. Union-find las calcula todas a la vez. Cada hilo apunta a un «padre» hasta
llegar a la raíz de su componente; unir dos componentes es colgar una raíz de la otra.
Con compresión de caminos (cada nodo salta a su abuelo al subir), los caminos quedan
cortos. (`bombe/bombe_numba.py` · `_find`, `_union`, `_wire_up`)

**La parada.** Se energiza el hilo x del cable de prueba T.
- Si se encienden los 26 hilos de T, cada hipótesis T↔u lleva a otra: todas se
  contradicen, y se pasa a la siguiente posición.
- Si no, la Bombe se detiene: es una **parada**.
- La hipótesis verdadera, en la posición verdadera, solo enciende hipótesis verdaderas,
  un hilo por cable. Por eso el stecker candidato es un hilo que queda **solo**: con 1
  hilo encendido es T↔x; con 25, el apagado.
- Que haya parada no depende de qué hilo se energice.

(`bombe_numba.py` · `sweep`, `_test_register`; `bombe/sweep.py` · `run_bombe`)

**Por qué cada lazo divide las paradas por unas 26.** Un lazo es un camino del menú que
vuelve a su letra: a → b → … → a. La composición de los aleatorizadores del camino es una
permutación π. La hipótesis P(a) = u sobrevive solo si π(u) = u: si al dar la vuelta la
corriente vuelve al mismo hilo. En una posición falsa, π es como una permutación al azar,
y una letra es punto fijo con probabilidad 1/26. Cada lazo independiente multiplica por
1/26. La tabla de Turing (diapositiva 16) lo muestra: con 12 letras, 820 → 31 → 1,2 →
0,04 paradas por orden con 0 a 3 lazos. E5 lo mide con nuestra Bombe.
(`experiments/e5_bombe.py`; `data/reference/turing_stops.csv`)

**El diagonal board (Welchman).** El plugboard es simétrico: si P(a) = u, entonces
P(u) = a. El diagonal board une el hilo u del cable a con el hilo a del cable u.
- Así una deducción en un cable salta a otro, y las contradicciones se propagan por todo
  el menú.
- Sin él, un menú sin lazos nunca se contradice: cada hipótesis solo enciende un hilo por
  cable, y la Bombe para en casi todas las posiciones.
- Solo importan los cables de letras del menú: lo que el diagonal board conecta en un
  cable sin aleatorizadores no lleva la corriente a ningún otro lado.

(`wiring.py` · `_diagonal_pairs`; la página La Bombe compara las paradas con y sin él.)

**Modos.** (D-032)
- *Bletchley:* dentro del tramo del crib solo gira el rotor derecho. Falla si el central
  avanza dentro del tramo, cerca de (L − 1)/26 de las claves.
- *Robusto:* prueba además una variante por cada letra k del crib en que pudo avanzar el
  central. Son L variantes: unas L veces el tiempo y las paradas.
- `sweep.true_stop` dice, con la clave conocida, en qué posición y variante debe parar.

**El verificador.** Lo que se hacía después de cada parada. (`bombe/checker.py`)
1. **Máquina de verificación.** Lee todos los hilos que enciende cada hipótesis: son
   steckers deducidos. Si una letra queda con dos parejas, la hipótesis cae. Si el menú
   tiene varias componentes, cada una necesita una hipótesis compatible.
   (`bombe_numba.py` · `check_hypotheses`)
2. **Puntaje rápido.** Descifra con esos steckers las letras vecinas del crib, completa el
   plugboard de esas letras y mide cuánto se parece al alemán.
3. **Anillos.** Los anillos derecho y central deciden cuándo avanza el central fuera del
   crib. Se prueban los 676 pares y se queda con los que reproducen la parada.
4. **Plugboard.** Se completa por *hill climbing*: se prueba cada cambio de un cable y se
   aplica el que más mejora la probabilidad del texto, hasta que nada mejore.
5. **Elección.** El idioma se mide con un modelo de 4 letras interpolado:
   log₁₀ P(texto) por la regla de la cadena (`stats/ngrams.py` · `interpolated`,
   `chain_score`). Entre secuencias de posiciones, pesa también cuántas claves dan cada
   una (D-036).
6. **Clave equivalente.** El anillo izquierdo se fija en A. Un anillo y su posición se
   compensan, así que la clave puede tener otros anillos y dar el mismo cifrado.

**Preguntas que pueden salir:**
- *¿Por qué la Bombe no necesita los anillos?* El aleatorizador depende de cada rotor
  solo por s = ventana − anillo, así que buscar s con anillos AAA cubre todas las
  posibilidades. Los anillos solo deciden cuándo avanza el central, y eso lo resuelve el
  verificador.
- *¿Qué pasa si el central avanza dentro del crib?* En modo Bletchley no aparece la parada
  verdadera. El modo robusto prueba una variante por cada letra donde pudo avanzar. En E5
  se mide cuánto falla uno y cuánto cuesta el otro.
- *¿Cómo sabes que tu Bombe está bien?*
  - Una versión de referencia, que propaga la corriente hilo por hilo, da lo mismo en
    24 casos.
  - CyberChef da exactamente las mismas paradas en 3 casos: 84 en el más largo.
  - La clave verdadera da parada en 200 de 200 casos (6.4).
  - E5 reproduce la tabla de Turing.

  (`tests/test_bombe.py`; `docs/VALIDACION.md`)
- *¿Por qué con 12 letras y no con 12 aristas?* En la tabla de Turing, como en la
  diapositiva 11, «letras del menú» son las letras distintas del grafo: sus vértices.
  E5 lo confirma (D-031).

## 5. Banburismus, decibanes y la prueba secuencial

**Idea.** La Enigma naval cifraba todos los indicadores del día desde la misma posición
base. Si los indicadores cifrados de dos mensajes coinciden en las dos primeras letras, sus
claves de mensaje tienen el mismo rotor izquierdo y el mismo central, y solo difieren en el
derecho (VFG y VFX). Entonces las dos máquinas recorren la misma sucesión de estados,
corridas d letras: los mensajes quedan **en profundidad**. Banburismus buscaba ese d
comparando los dos mensajes en los 51 desplazamientos posibles, de −25 a +25.
(`banburismus/depth.py`)

**Por qué se nota la profundidad.** En un mismo estado, el cifrado es una biyección: dos
letras cifradas coinciden si y solo si coinciden las planas. Dos textos alemanes alineados
coinciden en una columna con probabilidad κ, el índice de coincidencia; dos letras cifradas
en estados distintos, con 1/26. Wikipedia da 1/17 para el tráfico naval alemán.

**El desplazamiento y el rotor central.** Sea δ = (derecho₂ − derecho₁) mod 26.
- Si el central no avanza mientras el derecho del mensaje 1 recorre esos δ pasos, d = +δ.
- Si avanza, es el mensaje 2 el que llega al arranque del 1: d = δ − 26.

Pasa uno solo de los dos. De ahí salía el «scritchmus»: el signo de d decía en qué tramo
estaba la muesca del rotor derecho, y eso descartaba rotores para la Bombe. Una vez
alineadas, las dos máquinas avanzan igual, así que la profundidad dura todo el solapamiento
(D-042). `true_offset` no usa la regla: compara los estados de la máquina.

**Decibanes.** El peso de la evidencia a favor de una hipótesis H1 frente a H0 es
10·log₁₀ del factor de Bayes, P(datos | H1) / P(datos | H0). El logaritmo convierte en suma
el producto de los factores de observaciones independientes: la evidencia se suma columna
por columna. Con las tasas de Turing:
- repetición: 10·log₁₀((1/17)/(1/26)) = +1,845 dB;
- no repetición: 10·log₁₀((16/17)/(25/26)) = −0,093 dB;
- por letra, en promedio: (1/17)(+1,845) + (16/17)(−0,093) = +0,0211 dB en profundidad y
  (1/26)(+1,845) + (25/26)(−0,093) = −0,0184 dB al azar.

Las dos últimas son las divergencias de Kullback-Leibler entre las hipótesis, en decibanes:
la evidencia que aporta cada letra, en promedio. Es muy poca.
(`scoring.py` · `repeat_weight`, `non_repeat_weight`, `expected_weight`; el registro de
cifras las comprueba contra las diapositivas 13 y 17)

**La prueba secuencial de Wald (SPRT).** Se suman los decibanes letra por letra y se
decide en cuanto la suma cruza un umbral:
- A = 10·log₁₀((1 − β)/α): se acepta la profundidad;
- B = 10·log₁₀(β/(1 − α)): se descarta;
- entre los dos, se sigue leyendo.

α es la probabilidad de aceptar una profundidad que no existe; β, la de descartar una
verdadera. Con α = β = 1 %, ±19,96 dB. (`sprt.py` · `thresholds`)

**Cuántas letras: la aproximación de Wald.** La identidad de Wald, E[S_N] = μ·E[N], dice
que el puntaje final medio es el avance medio por letra por las letras leídas. Si el
puntaje se detuviera justo en el umbral, en profundidad E[S_N] = (1 − β)·A + β·B =
0,98 · 19,96 dB, y E[N] ≈ 19,56 / 0,0211 = 929 letras. Al azar, 1.062. (`wald_letters`)

**El sobrepaso.** El puntaje no se detiene en el umbral: se detiene al cruzarlo, y lo pasa.
- Arriba, una repetición suma 1,845 dB de golpe, así que el puntaje pasa A por 0,65 dB en
  promedio.
- Abajo, cada no repetición resta solo 0,093 dB, así que pasa B por apenas 0,045 dB.

La identidad de Wald es exacta. Con el puntaje final verdadero salen 959,7 letras en
profundidad y 1.067,4 al azar.
- En profundidad son 30,9 letras más: 30,7 por el sobrepaso de arriba (0,65 dB / 0,0211
  dB por letra) y 0,2 por lo demás.
- Al azar, 5,1 más: 2,4 por el sobrepaso de abajo y 2,9 porque el error real (0,86 %) queda
  bajo el 1 %, menos 0,3 por el sobrepaso de arriba en las pocas falsas alarmas.

El sobrepaso también deja los errores reales por debajo del nominal. Estos valores no son
una simulación: `exact_letters` propaga la probabilidad de cada número de repeticiones
letra por letra, y `wald_gap` hace la descomposición (D-048).

**La simulación con la máquina** (E6, 2.000 pares, texto con tasa 1/17 exacta). Da 983
letras en profundidad (IC 95 % 954–1.012) y 1.090 al azar (1.061–1.120). Los valores
exactos quedan dentro de los IC; los de Wald, 929 y 1.062, quedan por debajo o en el
borde. Es el criterio de la fase 4.

**Multigramas.** En texto real las repeticiones vienen en racimos: si dos textos alineados
coinciden en una letra, es más probable que coincidan también en la siguiente. Turing
puntuaba aparte los bigramas, trigramas y tetragramas repetidos. Aquí se hace con la regla
de la cadena: la probabilidad de repetir, h_r, depende de cuántas columnas seguidas acaban
de repetir.
- Se calcula con ρₙ, la probabilidad de que dos n-gramas del corpus coincidan:
  h_r = (ρ_{r+1} − ρ_{r+2}) / (ρ_r − ρ_{r+1}), y en la última racha, ρ_k / ρ_{k−1}.
- Con el corpus completo, h = 7,5 %, 11,9 % y 25,2 % tras 0, 1 y 2 o más repeticiones.
  Repetir pesa +2,91, +4,90 y +8,17 dB: un trigrama repetido pesa mucho más que tres letras
  sueltas.
- El puntaje sigue siendo un logaritmo de cociente de verosimilitudes, así que los umbrales
  de Wald siguen valiendo (D-044).

(`scoring.py` · `RepeatModel`, `corpus_model`, `column_weights`)

**Lo que da el texto real** (E6, corpus alemán con la X como separador):
- **La tasa.** El corpus repite 1 de cada 12,5 letras (κ = 0,0802; sin la X, 0,0757, 1 de
  cada 13,2), no 1 de cada 17. Turing midió tráfico naval; el nuestro es literario.
- **Con los pesos de Turing,** confirmar la profundidad toma 332 letras y no 929: la
  decisión llega antes. Descartarla sigue tomando unas 1.090.
- **Con bigramas y trigramas,** 254 y 357 letras, con errores cerca del 1 %. Letras sueltas
  con la tasa del corpus dan 262 y 323, pero con un 1,8 % de error en profundidad: un modelo
  de letras independientes no sabe que las repeticiones vienen en racimos.
- **Con solapamientos de mensajes reales** (100, 200 y 400 letras), el desplazamiento
  verdadero gana entre los 51 en el 39 %, 64 % y 88 % de los pares con letras sueltas, en el
  42 %, 67 % y 90 % con trigramas, y en el 13 %, 22 % y 40 % con la tasa 1/17.

**Preguntas que pueden salir:**
- *¿Qué es un decibán?* La décima parte de un ban: 10·log₁₀ del factor de Bayes. Mide
  cuánto cambia una observación las probabilidades a favor de una hipótesis. Los decibanes
  de observaciones independientes se suman. (`scoring.decibans`)
- *¿Por qué la simulación pide más letras que Wald?* Por el sobrepaso: Wald supone que el
  puntaje se detiene en el umbral, y en realidad lo pasa. El cálculo exacto lo cuantifica:
  30,9 letras más en profundidad. (`sprt.exact_letters`, `sprt.wald_gap`)
- *¿Por qué hay que probar desplazamientos negativos?* Porque, si el central avanza entre
  las dos claves de mensaje, el desplazamiento verdadero es δ − 26 y no +δ.
- *¿Qué tiene que ver con lo que vimos en clase?* Es inferencia bayesiana: los decibanes son
  log-odds, y cada observación los mueve por su factor de Bayes. La profundidad es
  reutilizar el flujo: en AES-GCM o ChaCha20, repetir el nonce deja dos mensajes en
  profundidad.
- *¿Por qué 1/17, si su corpus repite 1 de cada 12,5?* Es la tasa del tráfico naval que da
  Wikipedia. Nuestro texto es literario; no se ajustó nada para coincidir.

## Preguntas probables

Las 15 más probables, con su respuesta y el código que la respalda, se completan a
medida que llegan los módulos. Las del guion («Preguntas probables») van todas.

- *¿Y la máquina de Turing?* Es el modelo teórico de computación de 1936. La Bombe es una
  máquina electromecánica de 1940, hecha para una búsqueda concreta: probar hipótesis de
  plugboard en cada posición de los rotores. Nuestra Bombe está en `src/enigma_lab/bombe/`.
- *¿Y si el crib está mal?* La Bombe solo da paradas falsas, o ninguna, y el verificador
  no encuentra un descifrado que parezca alemán. La página La Bombe lo dice: «Ninguna
  parada da un texto que parezca alemán» (`checker.Verification.plausible`, con el umbral
  `PLAUSIBLE`). Entonces se prueba otra posición del crib u otro crib.
- *¿Por qué cada lazo divide por 26?* La letra supuesta debe ser un punto fijo de la
  permutación que da la vuelta al lazo; al azar eso pasa con probabilidad 1/26 (tema 4).
  E5 lo mide frente a la tabla de Turing (`experiments/e5_bombe.py`).
- *¿Qué hace el diagonal board?* Impone la simetría del plugboard: une el hilo u del cable
  a con el hilo a del cable u (`bombe/wiring.py` · `_diagonal_pairs`). Así las
  contradicciones se propagan. La página La Bombe compara las paradas con y sin él para
  cada menú, y E5 para todos.
- *¿Hoy se rompería por fuerza bruta?* No hace falta (tema 1; `core/keyspace.py`). Los
  ataques modernos solo con texto cifrado llegan en la fase 5 (`attacks/`).
- *¿Qué es un decibán?* 10·log₁₀ del factor de Bayes, P(datos | profundidad) /
  P(datos | azar). La evidencia de observaciones independientes se suma, porque el
  logaritmo convierte el producto de los factores en una suma. Una repetición en la misma
  columna suma +1,845 dB a favor de la profundidad, y una no repetición, −0,093
  (`banburismus/scoring.py`; tema 5).
- *¿Cuántas letras necesita el Banburismus?* Con letras sueltas y errores del 1 %, unas 929
  según Wald, y 960 exactas por el sobrepaso. Por eso Turing puntuaba los multigramas
  (`banburismus/sprt.py`; E6).
