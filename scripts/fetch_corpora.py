"""Descarga el corpus de dominio público y arma las muestras del repositorio.

Los textos vienen de Project Gutenberg, a través de su espejo oficial del Mirror Service
(Reino Unido). URL y SHA-256 están fijos: si el archivo remoto cambia, la descarga
falla en vez de cambiar los resultados en silencio.

- ``data/corpora/fuentes/``: los archivos tal como se descargan (no se versionan).
- ``data/corpora/completo/{idioma}.txt``: el cuerpo de cada libro, sin el encabezado
  ni el pie de Project Gutenberg (no se versiona).
- ``data/corpora/muestras/{idioma}.txt``: unos 200 KB por idioma, que sí se versionan
  para que la app funcione sin internet.

Uso:  uv run python scripts/fetch_corpora.py   (o  make corpus)
"""

from __future__ import annotations

import hashlib
import sys
import urllib.request
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CORPORA = ROOT / "data" / "corpora"
MIRROR = "https://www.mirrorservice.org/sites/ftp.ibiblio.org/pub/docs/books/gutenberg"
USER_AGENT = "enigma-lab-corpus/1.0"
SAMPLE_CHARS = 200_000  # unos 200 KB por idioma


@dataclass(frozen=True)
class Book:
    """Un libro de Project Gutenberg: dónde está, cómo se lee y dónde empieza el texto."""

    language: str
    ebook: int
    title: str
    author: str
    year: int
    path: str
    encoding: str
    sha256: str
    start: str  # primeras palabras del texto (lo anterior son títulos e índices)

    @property
    def url(self) -> str:
        return f"{MIRROR}/{self.path}"


BOOKS = (
    Book(
        "aleman",
        5323,
        "Effi Briest",
        "Theodor Fontane",
        1895,
        "5/3/2/5323/5323-0.txt",
        "utf-8",
        "f582a4b31c666cfb188fbf95963a3dbe22aa45a51c5ae6658cbb3392a5969241",
        "In Front des schon",
    ),
    Book(
        "aleman",
        22367,
        "Die Verwandlung",
        "Franz Kafka",
        1915,
        "2/2/3/6/22367/22367-8.txt",
        "latin-1",
        "fe91c871104780ce5a8fe3e12e79b757f6fb5ffa28ed83d6186e618fb3bf344a",
        "Als Gregor Samsa",
    ),
    Book(
        "espanol",
        2000,
        "El ingenioso hidalgo don Quijote de la Mancha",
        "Miguel de Cervantes Saavedra",
        1605,
        "2/0/0/2000/2000-0.txt",
        "utf-8",
        "1d0eb85cbe75661d50cc5b50c4537cddd37b6ae9f29d778dded2d80c689fe1dc",
        "En un lugar de la Mancha",
    ),
)


def download(book: Book) -> bytes:
    """Descarga un libro (o lo lee de la caché local) y verifica su SHA-256."""
    cache = CORPORA / "fuentes" / Path(book.path).name
    from_cache = cache.is_file()
    if from_cache:
        data = cache.read_bytes()
    else:
        request = urllib.request.Request(book.url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(request, timeout=120) as response:
            data = response.read()
    digest = hashlib.sha256(data).hexdigest()
    if digest != book.sha256:
        raise RuntimeError(
            f"SHA-256 distinto para {book.title} ({book.url}):\n  esperado {book.sha256}\n"
            f"  obtenido {digest}\n"
            + (
                f"La copia local {cache} está dañada: bórrala y corre otra vez make corpus."
                if from_cache
                else "El archivo remoto cambió: revísalo antes de actualizar el hash."
            )
        )
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_bytes(data)
    return data


def body(book: Book, data: bytes) -> str:
    """El texto del libro: desde sus primeras palabras hasta el pie de Project Gutenberg."""
    text = data.decode(book.encoding).replace("\r\n", "\n")
    start = text.index(book.start)
    end = text.index("*** END OF", start)
    return text[start:end].strip() + "\n"


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    texts: dict[str, list[str]] = {}
    for book in BOOKS:
        text = body(book, download(book))
        texts.setdefault(book.language, []).append(text)
        print(f"{book.author}, {book.title} ({book.year}): {len(text):,} caracteres")

    for folder in ("completo", "muestras"):
        (CORPORA / folder).mkdir(parents=True, exist_ok=True)
    for language, parts in texts.items():
        full = "\n".join(parts)
        (CORPORA / "completo" / f"{language}.txt").write_text(full, encoding="utf-8")
        share = SAMPLE_CHARS // len(parts)  # la muestra reparte los caracteres entre los libros
        sample = "\n".join(part[:share].rsplit("\n", 1)[0] for part in parts) + "\n"
        (CORPORA / "muestras" / f"{language}.txt").write_text(sample, encoding="utf-8")
        print(f"{language}: completo {len(full):,} caracteres · muestra {len(sample):,}")


if __name__ == "__main__":
    main()
