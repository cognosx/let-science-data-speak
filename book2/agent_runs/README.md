# Agent runs of 16 November 2026 (Book 2, Chapter 12)

The same AI agent (Claude Fable 5.2, in a closed folder with no internet) ran the malaria vaccine analysis twice on the exports of 10 November 2026.

- `run_A_short_brief/`: the task and nothing more.
- `run_B_checkpoints/`: the same task with eight written checkpoints; `QUESTIONS.md` lists the 13 decisions it took instead of guessing.

Each folder holds the agent's code and its `results.json`. Raw data are not included (see `../notebooks/01_search.ipynb`).

Share of papers with a first author based in sub-Saharan Africa:

| Run | 2000–2009 | 2010–2019 | 2020–2026 |
| --- | --- | --- | --- |
| Validated in the book (PubMed records) | 8.1% | — | 20.0% |
| Run A | 9.3% | 10.7% | 25.5% |
| Run B | 7.7% | 10.2% | 22.1% |

The checks reported by the agents were run by the agents on their own work. Traps T31 to T34 in `../logs/trap_catalogue_v2.csv` come from these runs.
