# Validación

Cómo se comprueba que el simulador y los ataques son correctos (spec, sección 6). La
validación es P0 y bloqueante: las pruebas de este documento corren con `make test`.

| Sección | Qué se valida | Estado |
| --- | --- | --- |
| 6.1 | Vectores de prueba: BDZGO, EWTYX, doble paso, py-enigma, odómetro, traza, portada y respaldo de la Bombe | Fase 1 |
| 6.1 | Mensaje histórico real con clave documentada | Fase 1 |
| 6.2 | py-enigma en 10.000 claves y mensajes aleatorios (meta: 100 %) | Fase 1 |
| 6.2 | CyberChef: API de Node en Docker o, si no, 5 casos de Enigma y 3 de Bombe a mano | Fases 1 y 3 |
| 6.3 | Propiedades con hypothesis: involución, sin puntos fijos, lotes = escalar, Bombe Numba = referencia | Fases 1 y 3 |
| 6.4 | Bombe en 200 casos aleatorios: la clave verdadera siempre da parada y se recupera | Fase 3 |
| 6.5 | Casos deterministas de las diapositivas 10 y 11 | Fase 2 |

## Ya validado (fase 0)

- **Espacio de claves (5.2):** `tests/test_keyspace.py` reproduce todas las cifras
  exactas del spec. Una propiedad de hypothesis comprueba además la recurrencia
  N(k) · k = N(k − 1) · C(26 − 2(k − 1), 2) para k de 1 a 13.
- **Cifras de la presentación (11.3):** `tests/test_presentacion.py` comprueba las del
  espacio de claves (diapositivas 2, 7, 8 y 20). Las demás aparecen como pendientes, con
  la fase en que llegan.
