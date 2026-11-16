# Let Science Data Speak — companion notebooks

Free, runnable notebooks that go with the open book series **Let Science Data Speak** by Maxime Descartes Mbogning Fonkou.

Book 1 stays free of code and case data. Books 2 and 3 keep their principles and checks in print; their notebooks, templates, prompts and other material that changes fast live here, with dates. Each book has its own folder.

| Book | Folder | Notebooks |
| --- | --- | --- |
| Book 1 — *Science as Data: What Research Produces, and What Each Source Gets Wrong* | [book1/](book1/) | 1 (Chapter 5) |
| Book 2 — *Science You Can Check: Mapping and Measuring Research with Open Data and AI* (draft) | [book2/](book2/) | 11 (Chapters 1–11), plus agent runs, other topics and prompts |
| Book 3 — *Science That Serves: Turning Research Findings into Papers, Policy Briefs, Datasets and Public Impact* (draft) | [book3/](book3/) | Templates, exercises and publishing lists |

## How to use

1. Open a book's folder and click **Open in Colab** next to a notebook (no installation needed), or download it and run it in Jupyter or VS Code (`pip install -r requirements.txt`).
2. Change only the **Settings** cell: your question, your search, the years and the region you study.
3. Choose **Run all**.

### OpenAlex API key (optional)

Without a key, OpenAlex gives a small free daily budget shared by everyone on your network, and the notebooks read up to 10,000 records. A free personal key gives you your own budget: get one at [openalex.org/settings/api](https://openalex.org/settings/api) and store it as an environment variable named `OPENALEX_API_KEY` (in Colab: the key icon, *Secrets*). Never paste a key into a notebook you share.

## Licence

Notebooks and text: [CC BY 4.0](LICENSE). Data from [OpenAlex](https://openalex.org) is CC0.

## Cite

Mbogning Fonkou MD. *Let Science Data Speak*: companion notebooks. GitHub; 2026. https://github.com/cognosx/let-science-data-speak
