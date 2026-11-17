"""Build an accessible EPUB from an assembled book markdown file (raw Word blocks, contents and index removed)."""
import re, subprocess, sys
def build(md_path, out, title, subtitle, resource_dir):
    t = open(md_path).read()
    t = re.sub(r"```\{=openxml\}.*?```", "", t, flags=re.S)                 # page breaks, Word contents
    t = re.sub(r'::: \{custom-style="ContentsTitle"\}.*?:::', "", t, flags=re.S)
    t = re.split(r"\n#+ Index\s*\n", t)[0]                                     # page-number index has no meaning in an EPUB
    t = re.sub(r'::: \{custom-style="[^"]+"\}\n', "::: {}\n", t)
    t = re.sub(r"!\[CognosX Books logo\]\([^)]*\)\{[^}]*\}", "", t)
    open("/tmp/_epub.md", "w").write(t)
    css = "/tmp/_epub.css"
    open(css, "w").write("body{font-family:serif;line-height:1.5} h1,h2,h3{font-family:sans-serif} table{border-collapse:collapse;font-size:0.85em} td,th{border:1px solid #ccc;padding:0.25em} img{max-width:100%}")
    subprocess.run(["pandoc", "/tmp/_epub.md", "-f", "markdown-implicit_figures", "-o", out, "--toc", "--toc-depth=2", "--split-level=2",
                    "--resource-path", resource_dir, "--css", css,
                    "--metadata", f"title={title}", "--metadata", f"subtitle={subtitle}",
                    "--metadata", "author=Maxime Descartes Mbogning Fonkou", "--metadata", "lang=en-CA",
                    "--metadata", "rights=CC BY 4.0", "--metadata", "publisher=CognosX Books"], check=True)
    import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import epub_meta
    if title in epub_meta.BOOKS: epub_meta.add(out, title)
if __name__ == "__main__":
    build(*sys.argv[1:6])
