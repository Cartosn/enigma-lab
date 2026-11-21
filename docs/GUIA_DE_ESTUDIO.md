# Guía de estudio

Para defender el proyecto frente al profesor (spec, sección 8.4). Cada tema explica la
idea en lenguaje claro, da la fórmula y dice en qué archivo y función está. Crece con
cada fase.

**Temas:**
1. [El espacio de claves](#1-el-espacio-de-claves) (fase 0)
2. [La máquina y el doble paso](#2-la-máquina-y-el-doble-paso) (fase 1)
3. Cribs y menús (fase 2)
4. La Bombe, el diagonal board y el verificador (fase 3)
5. Banburismus y la prueba secuencial (fase 4)
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

## Preguntas probables

Las 15 más probables, con su respuesta y el código que la respalda, se completan a
medida que llegan los módulos. Las del guion («Preguntas probables») van todas:

| Pregunta | Fase en que queda respondida con código |
| --- | --- |
| ¿Y la máquina de Turing? | 3 (contexto de la Bombe) |
| ¿Y si el crib está mal? | 3 (`bombe/`) |
| ¿Por qué cada lazo divide por 26? | 3 (E5) |
| ¿Qué hace el diagonal board? | 3 (`bombe/`) |
| ¿Hoy se rompería por fuerza bruta? | 0 y 5 (`core/keyspace.py`, `attacks/`) |
| ¿Qué es un decibán? | 4 (`banburismus/`) |
