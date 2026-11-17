# Ebook tools

Two small scripts used to build the EPUB editions of the three books.

- `epub.py` turns an assembled book (one markdown file) into an EPUB with pandoc, a table of contents and a simple stylesheet, then calls `epub_meta.py`.
- `epub_meta.py` adds the book description, 14 subject keywords and accessibility metadata (access modes, alternative text, table of contents, reading order, no hazards, and an accessibility summary) to the EPUB package file. No conformance certificate is claimed.

## Use

Requires Python 3 and pandoc.

```bash
python tools/epub.py book.md "Science as Data.epub" "Science as Data" "What Research Produces, and What Each Source Gets Wrong" path/to/figures
```

The title must match one of the three titles in `epub_meta.BOOKS` for the metadata to be added. To add metadata to an EPUB built another way:

```bash
python -c "import sys; sys.path.insert(0, 'tools'); import epub_meta; epub_meta.add('Science as Data.epub', 'Science as Data')"
```

Check the result with EPUBCheck (`pip install epubcheck`).
