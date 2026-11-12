# Let Science Data Speak — companion notebooks

Free, runnable notebooks that go with the open book series **Let Science Data Speak** by Maxime Descartes Mbogning Fonkou.

The books stay free of code and case data. These notebooks let you try the analyses on your own topic.

## Book 1 — *What Science Produces, and What Each Source Gets Wrong*

| Notebook | Chapter | What it does | Open |
| --- | --- | --- | --- |
| [book1_ch05_articles.ipynb](notebooks/book1_ch05_articles.ipynb) | 5. Journal articles | The chapter's first analysis with OpenAlex: search log, cleaning, first-author country, works per year, top countries and journals, share led from your region | [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/descartesmbogning/let-science-data-speak/blob/main/notebooks/book1_ch05_articles.ipynb) |

## How to use

1. Click **Open in Colab** (no installation, no account needed to run), or download the notebook and run it in Jupyter or VS Code (`pip install -r requirements.txt`).
2. Change only the **Settings** cell: your question, your search, the years and the region you study.
3. Choose **Run all**.

### OpenAlex API key (optional)

Without a key, OpenAlex gives a small free daily budget shared by everyone on your network, and the notebook reads up to 10,000 records. A free personal key gives you your own budget: get one at [openalex.org/settings/api](https://openalex.org/settings/api) and store it as an environment variable named `OPENALEX_API_KEY` (in Colab: the key icon, *Secrets*). Never paste a key into a notebook you share.

## Licence

Notebooks and text: [CC BY 4.0](LICENSE). Data from [OpenAlex](https://openalex.org) is CC0.

## Cite

Mbogning Fonkou MD. *Let Science Data Speak, Book 1: What Science Produces, and What Each Source Gets Wrong*. Companion notebooks. GitHub; 2026. https://github.com/descartesmbogning/let-science-data-speak
