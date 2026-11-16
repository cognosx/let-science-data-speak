# Book 2 — Make Science Data Speak: companion files

Companion files for *Make Science Data Speak: Mapping and Measuring Science with Open Data and AI You Can Check* (Let Science Data Speak, Book 2), by Maxime Descartes Mbogning Fonkou. The book keeps principles, traps and checks; the material here changes faster, so it lives here with dates.

The notebooks were run on real data on 10 November 2026 (PubMed, Europe PMC, OpenAlex, ROR, World Bank, ClinicalTrials.gov). Counts will differ slightly if you run them later, because the databases keep growing.

## Run the notebooks

1. `pip install -r requirements.txt`
2. Put your own email in `config.yml` (NCBI asks for one).
3. `export OPENALEX_API_KEY=...` (free key from openalex.org). Never write a key into a file; notebook 11 checks this.
4. Run `notebooks/01_search.ipynb` to `10_review_bridge.ipynb` in order, or set `RUN_ALL = True` in `11_pipeline.ipynb`.

`src/` holds the same notebooks as plain Python. `data/final/` and `logs/` hold the results quoted in the book. Raw downloads (about 280 MB) are not included; `01_search` rebuilds them.

| Notebook | Chapter |
| --- | --- |
| 05_validate_ai | 1. GenAI you can trust: the validation recipe |
| 01_search | 2. From question to corpus |
| 02_dedup_screen | 3. Duplicates and screening |
| 03_enrich | 4. Enriching your data |
| 04_entities | 5. Extracting entities |
| 06_topics | 6. Topic maps and semantic search |
| 07_networks | 7. Networks and knowledge graphs |
| 08_indicators | 8. Indicators and responsible metrics |
| 09_lab_to_patient | 9. From lab to patient |
| 10_review_bridge | 10. From landscape to review |
| 11_pipeline | 11. Pipelines that check themselves |

## What is in this folder

| Folder | What it holds | Book chapters |
| --- | --- | --- |
| `notebooks/`, `src/` | The malaria vaccine analysis, step by step | 1–11 |
| `logs/trap_catalogue_v2.csv` | All 34 traps of Appendix A, as a spreadsheet | Appendix A |
| `other_topics/` | Each chapter's method on three other topics: the respiratory microbiome, phage therapy and AI in research (moved from the printed chapters) | 1–11 |
| `cases/` | Code and data for those three topics | 1–11 |
| `code_checks/` | The short code check from each chapter | 1–11 |
| `prompts/` | The prompts tested, with samples and results (former Appendix D), dated November 2026 | 1, 5, 6, 9 |
| `agent_runs/` | The two agent runs of 16 November 2026: code, numbers and the list of decisions of the supervised run | 12 |

The numbers for the three other topics come from rules applied to database fields and titles. Their validation samples are ready to label but have not yet been checked by hand: read them as first estimates.

Licence: CC BY 4.0 (see the LICENSE file at the root of this repository).
