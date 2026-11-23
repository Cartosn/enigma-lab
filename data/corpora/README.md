# Corpus

Textos de dominio público de Project Gutenberg, normalizados al alfabeto de Enigma por
`enigma_lab.stats.corpus`.

| Idioma | Libro | Autor | Año | Ebook |
| --- | --- | --- | --- | --- |
| Alemán | *Effi Briest* | Theodor Fontane (†1898) | 1895 | [5323](https://www.gutenberg.org/ebooks/5323) |
| Alemán | *Die Verwandlung* | Franz Kafka (†1924) | 1915 | [22367](https://www.gutenberg.org/ebooks/22367) |
| Español | *El ingenioso hidalgo don Quijote de la Mancha* | Miguel de Cervantes (†1616) | 1605 | [2000](https://www.gutenberg.org/ebooks/2000) |

- **`muestras/`** (se versiona): unos 200 KB de texto por idioma, para que la app funcione
  sin internet. En alemán, la mitad sale de cada libro.
- **`completo/`** y **`fuentes/`** (no se versionan): los generan `make corpus` o
  `scripts/fetch_corpora.py`. El script descarga del espejo oficial del Mirror Service
  (gutenberg.org estaba en mantenimiento el 20-11-2026) y verifica el SHA-256 de cada
  archivo.

**Licencia.** Las tres obras son de dominio público:
- en Estados Unidos, porque se publicaron antes de 1929;
- en Colombia (vida del autor + 80 años) y en la Unión Europea (+ 70 años), porque sus
  autores murieron antes de 1945.

Se guarda solo el cuerpo de cada libro, sin el encabezado ni el pie ni la marca de
Project Gutenberg. Por la misma razón de derechos se descartó *Buddenbrooks* de Thomas
Mann (†1955): en Colombia sigue protegido hasta 2035.

**Normalización.**
- Alemán: Ä → AE, Ö → OE, Ü → UE, ß → SS.
- Español: se quitan las tildes y Ñ → N.
- Modos: «solo letras», o «X como separador», donde cada tramo de espacios y signos se
  vuelve una X.
