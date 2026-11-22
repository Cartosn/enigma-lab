# Fuentes

Toda cifra de la app, las figuras, el informe o el resumen que no calcule el código sale
de una de estas fuentes (spec, sección 0). Las de la sección 12 del spec van tal cual.

## Criptoanálisis de Enigma (spec, sección 12)

- Turing, A. M. (c. 1941–42). *The Applications of Probability to Cryptography*. The National Archives, HW 25/37. Edición en arXiv: https://arxiv.org/abs/1505.04714
- Rejewski, M. (1980). An application of the theory of permutations in breaking the Enigma cipher. *Applicationes Mathematicae*, 16(4), 543–559. https://impan.pl/Great/Rejewski/article.html
- Wilcox, J. (2006). *Solving the Enigma: History of the Cryptanalytic Bombe*. NSA, Center for Cryptologic History. https://www.nsa.gov/portals/75/documents/about/cryptologic-heritage/historical-figures-publications/publications/wwii/solving_enigma.pdf
- Good, I. J. (1979). A. M. Turing's statistical work in World War II. *Biometrika*, 66(2), 393–396.
- Kuhl, A. (2007). Rejewski's catalog. *Cryptologia*, 31(4), 326–331. https://archive.math.arizona.edu/mbbush/enigma/Rejewskis%20catalog.pdf
- Gillogly, J. J. (1995). Ciphertext-only cryptanalysis of Enigma. *Cryptologia*, 19(4), 405–413.
- Ostwald, O. y Weierud, F. (2017). Modern breaking of Enigma ciphertexts. *Cryptologia*, 41(5), 395–421. https://www.cryptocellar.org/pubs/enigma-modern-breaking.pdf
- Weinbaum, J. *Action This Day* (tesis de maestría, Dartmouth College). https://jonahweinbaum.github.io/material/action_this_day.pdf
- Pommerening, K. Notas de criptología clásica, Universidad de Mainz: https://www.staff.uni-mainz.de/pommeren/Cryptology/Classic/6_Enigma/EnigmaDescr.html
- Wikipedia: «Bombe», «Banburismus», «Cryptanalysis of the Enigma» y «Enigma rotor details».
- py-enigma: https://pypi.org/project/py-enigma/ · CyberChef (GCHQ): https://gchq.github.io/CyberChef/ y su API de Node.
- Project Gutenberg (corpus de dominio público): https://www.gutenberg.org/

## Datos usados por el código

- **Cableados y muescas:** Wikipedia, «Enigma rotor details», revisión 1275803743 del
  15-02-2025, consultada el 20-11-2026. Comprende los rotores I–VIII, Beta y Gamma, y los
  reflectores A, B, C, B delgado y C delgado. https://en.wikipedia.org/wiki/Enigma_rotor_details
- **Mensaje histórico:** Rijmenants, D. *The M4 Project*, en Cipher Machines and
  Cryptology. Es el mensaje de Hartwig Looks (U-264) del 25-11-1942, con clave, cifrado
  y texto descifrado. https://www.ciphermachinesandcryptology.com/en/m4project.htm
  (consultado el 20-11-2026). El proyecto original: Krah, S. *M4 Message Breaking
  Project*. https://www.bytereef.org/m4_project.html
- **Implementación independiente:** py-enigma 1.0.2, de Brian Neal (licencia MIT).
  https://pypi.org/project/py-enigma/
- **Validación a mano:** CyberChef, versión web (GCHQ), consultada el 20-11-2026.
  https://gchq.github.io/CyberChef/

- **Tabla de Turing (E5, diapositiva 16):** Wikipedia, «Bombe», tabla «Estimated number of
  bombe stops per rotor order», revisión 1385546242 (13-11-2026), consultada el 21-11-2026.
  https://en.wikipedia.org/w/index.php?title=Bombe&oldid=1385546242 · Transcrita completa en
  `data/reference/turing_stops.csv`. Wikipedia la cita de Carter, F., «From Bombe 'stops'
  to Enigma keys», Bletchley Park Trust, Technical Papers, p. 3.
- **Banburismus (fase 4, diapositivas 13 y 17):** Wikipedia, «Banburismus», revisión
  1372577431 (01-09-2026), consultada el 21-11-2026.
  https://en.wikipedia.org/w/index.php?title=Banburismus&oldid=1372577431 · De ahí salen:
  - las tasas de repetición: 1 de cada 26 al azar y 1 de cada 17 en los mensajes navales
    alemanes;
  - los desplazamientos de −25 a +25;
  - el ejemplo VFG/VFX: el mejor desplazamiento es 8, con nueve repeticiones (dos de ellas
    bigramas) en 56 letras de solapamiento.

  El artículo no da pesos en decibanes: +1,845, −0,093 y los demás los calcula el código
  con esas tasas (`banburismus/scoring.py`).
- **Prueba secuencial de Wald:**
  - Wald, A. (1945). Sequential tests of statistical hypotheses. *The Annals of
    Mathematical Statistics*, 16(2), 117–186. Umbrales y aproximación del número esperado
    de observaciones.
  - Wikipedia, «Sequential probability ratio test», revisión 1321902819 (13-11-2025),
    consultada el 21-11-2026. Umbrales a ≈ log(β/(1 − α)) y b ≈ log((1 − β)/α), y la nota de
    que son aproximados en el caso discreto porque el puntaje cruza el umbral entre dos
    observaciones.
- **Catálogo de Rejewski (fase 5, E7, diapositiva 9):** Kuhl, A. (2007). Rejewski's Catalog.
  *Cryptologia*, 31(4), 326–331. DOI 10.1080/01611190701299487. Leído el 22-11-2026 en
  https://archive.math.arizona.edu/mbbush/enigma/Rejewskis%20catalog.pdf (el PDF del artículo,
  descargado por la Universidad de Arizona). Transcrito en `data/reference/kuhl_2007.json`:
  - el modelo: rotores I–III, reflector A (el del primer catálogo polaco, con el cableado de
    Marks y Weierud, 2000), 6 × 26³ = 105.456 configuraciones; su programa «simula el proceso
    del ciclómetro», sin más detalle sobre el rotor central ni los anillos;
  - las cifras: 21.230 características, 11.466 únicas y 1.771 configuraciones en
    (13 13)(13 13)(13 13); 101 estructuras por producto y 101³ = 1.030.301 ternas;
  - la tabla 1 (las 15 características más frecuentes) y la tabla 2 (cuántas tienen 1 a 14 y 16
    configuraciones);
  - las citas de Rejewski (en Kozaczuk, 1984): unos sesenta mensajes del mismo día (apéndice D)
    y unos ochenta (apéndice E) para formar AD, BE y CF;
  - sus erratas: 105.465 en lugar de 105.456, 54,40 % (es 54,01 %) y 20.433 con 10 o menos
    (su tabla 2 suma 19.604, que es su 92,34 %).
- **Ataque moderno (fase 5, E8):** Ostwald, O. y Weierud, F. (2017). Modern breaking of Enigma
  ciphertexts. *Cryptologia*, 41(5), 395–421. DOI 10.1080/01611194.2016.1238423. Leída el
  22-11-2026 la versión 5 del manuscrito (marzo de 2017), en
  https://www.cryptocellar.org/pubs/enigma-modern-breaking.pdf. Transcrito en
  `data/reference/ostwald_weierud_2017.json`:
  - el método de Gillogly (1995) y sus límites: unas 300 letras con 6 cables o menos; con 10, un
    solo éxito, con 1.463 letras; su texto de prueba, de 647 letras;
  - el reglamento del ejército alemán: ningún mensaje de más de 250 letras;
  - la distancia de unicidad: H/D con H ≈ 72 bits y D ≈ 3,1 bits por letra, unas 23 letras;
  - el mensaje real más corto que rompieron, AMERI, de 32 letras;
  - el plugboard vacío con 10 cables: 10,1 % de letras planas y 18,5 % de sustitutos
    monoalfabéticos en la ubicación correcta;
  - la búsqueda parcial del plugboard: E-Stecker (26 arranques), R-Stecker (73) e I-Stecker (136).

  El artículo de Gillogly (1995) no está libre: sus cifras se citan desde Ostwald y Weierud.
- **Bombe de CyberChef (referencia de diseño y validación):** código fuente de GCHQ,
  `src/core/lib/Bombe.mjs`, `src/core/operations/Bombe.mjs` y `MultipleBombe.mjs`
  (licencia Apache 2.0), leído el 21-11-2026. https://github.com/gchq/CyberChef · La
  validación a mano usó la versión web el mismo día.

## Corpus (Project Gutenberg, dominio público)

Los descarga `scripts/fetch_corpora.py` del espejo oficial
https://www.mirrorservice.org/sites/ftp.ibiblio.org/pub/docs/books/gutenberg (consultado
el 20-11-2026). El detalle, con la licencia, está en `data/corpora/README.md`.

| Obra | Ebook | Archivo | SHA-256 |
| --- | --- | --- | --- |
| Fontane, T. (1895). *Effi Briest* | 5323 | `5323-0.txt` | `f582a4b31c666cfb188fbf95963a3dbe22aa45a51c5ae6658cbb3392a5969241` |
| Kafka, F. (1915). *Die Verwandlung* | 22367 | `22367-8.txt` | `fe91c871104780ce5a8fe3e12e79b757f6fb5ffa28ed83d6186e618fb3bf344a` |
| Cervantes, M. de (1605). *El ingenioso hidalgo don Quijote de la Mancha* | 2000 | `2000-0.txt` | `1d0eb85cbe75661d50cc5b50c4537cddd37b6ae9f29d778dded2d80c689fe1dc` |

## Citadas además en la presentación (diapositiva 24)

- Crypto Museum: páginas de la Bombe y de Colossus. https://www.cryptomuseum.com/
- Agar, J. (2014). UCL STS Observatory.
- Stanford Encyclopedia of Philosophy: «Alan Turing».

## Diseño y software

- Okabe, M. e Ito, K. (2008). *Color Universal Design (CUD): How to make figures and presentations that are friendly to colorblind people*. Origen de la paleta de las series de datos. https://jfly.uni-koeln.de/color/
- Inter 4.1, de Rasmus Andersson (licencia SIL Open Font License 1.1). https://github.com/rsms/inter/releases/download/v4.1/Inter-4.1.zip · SHA-256 del zip: `9883fdd4a49d4fb66bd8177ba6625ef9a64aa45899767dde3d36aa425756b11e`
- JetBrains Mono 2.304 (licencia SIL Open Font License 1.1). https://github.com/JetBrains/JetBrainsMono/releases/download/v2.304/JetBrainsMono-2.304.zip · SHA-256 del zip: `6f6376c6ed2960ea8a963cd7387ec9d76e3f629125bc33d1fdcd7eb7012f7bbf`
