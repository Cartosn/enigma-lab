# Guía de estudio

Para defender el proyecto frente al profesor (spec, sección 8.4). Cada tema explica la
idea en lenguaje claro, da la fórmula y dice en qué archivo y función está. Crece con
cada fase.

**Temas:**
1. [El espacio de claves](#1-el-espacio-de-claves) (fase 0)
2. La máquina y el doble paso (fase 1)
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
