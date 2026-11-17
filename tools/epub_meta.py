"""Add description, subjects and accessibility metadata to a built EPUB (EPUB 3 / schema.org accessibility)."""
import zipfile, re, shutil, os, html
BOOKS = {
 "Science as Data": dict(
  desc="Science produces more than anyone can read: articles, theses, citations, patents, grants, trials, datasets, policy documents and the careers of the people behind them. This open-access book is a plain-English guide to all of them. For each source it shows what it records, where to get it free or paid, what you can learn from it, and what it gets wrong. It ends by showing how to combine sources, use AI carefully and turn any research topic into questions that decision-makers care about.",
  subj=["science of science","bibliometrics","scientometrics","research evaluation","open data","OpenAlex","patents","clinical trials","research funding","research data","global health research","Africa","AI in research","research methods"]),
 "Science You Can Check": dict(
  desc="A hands-on guide to mapping and measuring a research field with open data and AI you can check. Using one real case, malaria vaccine research in Africa, it walks through searching several databases, screening, enrichment, entity extraction, topic maps, networks, indicators, links from lab to patient and patent landscapes, and on to novelty, funding effects and careers. Every AI step comes with a validation recipe, and the 49 traps found along the way are collected in a catalogue. Companion notebooks run on real data.",
  subj=["science of science","bibliometrics","scientometrics","systematic reviews","large language models","AI validation","research metrics","OpenAlex","PubMed","patent landscapes","research funding","malaria vaccines","Africa","reproducible research"]),
 "Science That Serves": dict(
  desc="A checked finding can become many outputs: a sharper research question, an article, an open dataset, a brief for a ministry, a review for a funder, a landscape for a company, a story for the public or a course. This book shows how to make each one with AI help without saying more than the evidence allows, using a simple pipeline built around an evidence pack and a claim check. It ends with careers in the science of science and in science intelligence.",
  subj=["research communication","science policy","policy briefs","open data","data papers","research funding","foresight","patent landscapes","science journalism","research impact","AI in research","science of science","Africa","careers in research"]),
}
A11Y = ["schema:accessMode\">textual","schema:accessMode\">visual","schema:accessModeSufficient\">textual",
        "schema:accessibilityFeature\">alternativeText","schema:accessibilityFeature\">tableOfContents",
        "schema:accessibilityFeature\">readingOrder","schema:accessibilityFeature\">structuralNavigation",
        "schema:accessibilityHazard\">none"]
SUMMARY = ("This publication meets basic accessibility requirements: headings give structure, the contents are navigable, "
           "every figure has alternative text, and tables are real tables with header rows.")
def add(path, title):
    b = BOOKS[title]; tmp = path + ".tmp"
    zin = zipfile.ZipFile(path); zout = zipfile.ZipFile(tmp, "w")
    for it in zin.infolist():
        data = zin.read(it.filename)
        if it.filename.endswith(".opf"):
            s = data.decode()
            s = re.sub(r"<dc:description>.*?</dc:description>\s*", "", s, flags=re.S)
            s = re.sub(r"<dc:subject>.*?</dc:subject>\s*", "", s, flags=re.S)
            if 'xmlns:schema' not in s:
                s = s.replace("<package ", "<package prefix=\"schema: http://schema.org/\" ", 1) if "prefix=" not in s.split("<package",1)[1].split(">",1)[0] else s
            meta = [f"<dc:description>{html.escape(b['desc'])}</dc:description>"]
            meta += [f"<dc:subject>{html.escape(k)}</dc:subject>" for k in b["subj"]]
            meta += [f"<meta property=\"{m}</meta>" for m in A11Y]
            meta += [f"<meta property=\"schema:accessibilitySummary\">{SUMMARY}</meta>"]
            s = s.replace("</metadata>", "\n    " + "\n    ".join(meta) + "\n  </metadata>", 1)
            data = s.encode()
        zi = zipfile.ZipInfo(it.filename, it.date_time)
        zi.compress_type = zipfile.ZIP_STORED if it.filename == "mimetype" else zipfile.ZIP_DEFLATED
        zout.writestr(zi, data)
    zout.close(); zin.close(); shutil.move(tmp, path)
