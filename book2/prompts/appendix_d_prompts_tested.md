## Appendix D — Prompts We Tested, and What They Got Wrong

This appendix gives four prompts used for tasks in this book, the samples they were tested on, the reference they were measured against, and what went wrong. Copy them as a starting point, never as a finished tool: the point of each one is what its test revealed.

### How the prompts were tested

- **Model and date.** Each prompt was run on 10 November 2026 by Claude Opus 5.5, the AI assistant used to help prepare this book, reading each record in turn inside the working session. The run used no settings for temperature or randomness, and each record was read once. Results from a different model, a different date, or the same model through an API with fixed settings may differ (Chapter 1, Step 5).
- **The same assistant wrote the prompts and ran them.** That is a risk: a model may follow its own wording better than a stranger's. Before you rely on any prompt here, run it on your own sample, with your own model, and preferably with someone else writing the reference labels.
- **References came from outside the prompt.** Each test compares the prompt's answers with something it did not see: PubMed's publication types, Europe PMC's record types, the full text of the paper, or the rules from the character cases. None of these references is perfect, and each test says where the reference itself was the problem.
- **Samples are small.** Between 24 and 35 records per prompt, chosen to include the hard cases. The intervals are wide on purpose: they show how little a small test can prove.

All samples, answers and scores are in the companion files (`prompts/`).

### Prompt 1. Is this paper a phase 3 trial report? (malaria vaccines, Chapters 1 and 5)

**The task.** The rule flagged papers that mention a phase 3 trial, and only one in five of those was a phase 3 trial report (Trap T16). Can a prompt tell reporting from mentioning?

**The prompt (version 1).**

> You will read the title and abstract of a paper. Answer one question: is this paper the report of a phase 3 clinical trial, meaning that it presents the design or results of a phase 3 trial that the authors conducted? A paper that only mentions, reviews or models a phase 3 trial is not one. Answer YES, NO or UNCLEAR. Then copy the sentence from the abstract that supports your answer.

**The sample and reference.** 24 malaria vaccine abstracts that The rule had flagged: 12 indexed by PubMed as *Clinical Trial, Phase III* and 12 not. The reference is PubMed's publication type.

**The result.**

| | Indexed as phase 3 (12) | Not indexed as phase 3 (12) |
| ------------------------- | ---------: | ---------: |
| Prompt said YES | 5 | 0 |
| Prompt said UNCLEAR | 4 | 0 |
| Prompt said NO | 3 | 12 |

Every YES was right: precision 5 of 5 (95% CI 0.57–1.00). But by the indexers' standard, recall was only 5 of 12 (0.42, 0.19–0.68).

**What went wrong, and with what.** Reading the seven "misses" showed that the prompt and the indexers answered different questions. Four were secondary analyses or studies nested inside a phase 3 trial, or a paper describing a trial's design without stating its phase: the prompt said UNCLEAR, as asked. Three were **modelling studies** that used phase 3 data to predict public health impact; PubMed had indexed them as phase 3 trial publications, and the prompt said NO, following its own definition. Neither side was simply wrong. The task had not been defined precisely enough for the two to agree.

**Version 2 (not yet tested).** Split the question in two: "Does the paper report original results from a phase 3 trial (primary or secondary analysis)?" and "Does the paper use phase 3 trial data in a model or review?" Each is closer to one decision a reader would make.

**Use it as.** A second reader beside your rule, at Amber, for finding primary trial reports. Not as the definition of a phase 3 paper: write that definition first, in your codebook.

### Prompt 2. Which culture medium was used? (respiratory microbiome, Chapter 5)

**The task.** Extract the culture medium used to grow each new species, without inventing one.

**The prompt (version 1).**

> From the title and abstract below, list the culture medium or media used to grow the new species. Copy the exact words from the text. If no medium is named, answer NOT REPORTED. Do not use outside knowledge.

**The sample and reference.** The 35 species descriptions in the respiratory corpus whose full text is open in Europe PMC. The reference for "is a medium reported at all?" is the full text, read by the analyst's rules.

**The result.** The prompt returned a medium for 3 of 35 abstracts, each copied word for word from the text: no value was invented. The full texts named a medium for 29 of the 35.

**What went wrong.** Nothing in the prompt; everything in the source. Abstracts of species descriptions rarely name the medium, so a prompt that obeys "not reported" returns an almost empty column. Two of the three values it found came from records that were not bacteria at all: a yeast grown on a chromogenic medium, and an archaeon grown in a gas-free medium. the analyst's search had collected fungi and an archaeon along with bacteria, which the prompt's answers made visible.

**Two instructions did the work.** "Copy the exact words" made every value checkable in a second, and "answer NOT REPORTED" gave the model a way to say nothing. Remove either, and a model asked to fill a table may fill it with the media most species of that genus grow on: plausible, and not in the paper.

**Use it as.** Amber on full texts, with every value checked against its copied sentence. Do not use it on abstracts for fields that abstracts do not report.

### Prompt 3. Research, or commentary? (AI in research, Chapters 1 and 3)

**The task.** Separate research papers from editorials, comments, letters and corrections.

**The prompt (version 1).**

> Classify this paper from its title and abstract as RESEARCH (it reports original data or an original analysis), COMMENTARY (editorial, comment, letter, reply, correction or opinion), or UNCLEAR. Do not guess from the journal name.

**The sample and reference.** 30 papers on large language models from the AI-in-research corpus: 15 that Europe PMC types as editorials, comments or letters, and 15 that it does not. The reference is that record type.

**The result.**

| Europe PMC type | Prompt: RESEARCH | Prompt: COMMENTARY | Prompt: UNCLEAR |
| ---------------------------- | ---------: | ---------: | ---------: |
| Editorial, comment or letter (15) | 2 | 5 | 8 |
| Other (15) | 12 | 3 | 0 |

**What went wrong, and with what.** Three things, and only one of them was the prompt.

- **11 of the 15 commentary records had no abstract.** With a title alone, the prompt said UNCLEAR eight times, which is the honest answer. For this task, the database's record type is a better tool than any prompt.
- **Two "letters" were research letters**, short reports of original studies published as letters. The prompt called them research, and it was right. The record type was the weaker reference here.
- **Two "research" records were corrections** ("Correction: …", "Author Correction: …"). The analyst's own rule had missed them, because its pattern did not include the word "correction". The prompt caught them, and the next version of his rule makes corrections a category of their own.

The third disagreement in that row was an essay on AI and consciousness: opinion by its content, typed as a research article by its record.

**Use it as.** A check on your metadata, not a replacement for it. Run the record type first; send only the records that have abstracts, and the records where type and title disagree, to the prompt.

### Prompt 4. What is this phage patent for? (phage therapy, Chapters 6 and 9)

**The task.** Classify phage patent applications by use from their titles.

**The prompt (version 1).**

> From the patent title only, classify the main use of the invention as THERAPY (treating or preventing infection or disease in people, or unspecified antibacterial use), FOOD (food safety, agriculture or veterinary use), TOOLS (phage display, cloning, diagnostics, vaccine platforms), or UNCLEAR. If the title does not say what the invention is used for, answer UNCLEAR.

**The sample and reference.** 30 phage applications from the phage therapy data. There is no human reference yet, so the prompt was compared with the analyst's rules.

**The result.** The prompt and the rules agreed on 24 of 30 (80%). Of the six disagreements, four had UNCLEAR on one side: titles such as "Pseudomonas bacteriophage and uses thereof", which name a target but not a use. In the other two, the rules were weaker. A title about controlling *Pseudomonas* growth in meat products was read as therapy by the rules, because they saw a pathogen's name, and as food by the prompt. A phage composition carrying a CRISPR system was read as a laboratory tool by the rules, because they saw "CRISPR", and as therapy by the prompt.

**What this does and does not show.** Agreement between two methods is not accuracy: both can be wrong in the same way, and both read only the title. It shows where the hard cases are, which is where the analyst reads the first claim (Chapter 9, step 6).

**Use it as.** A first sort, at Amber, with every UNCLEAR and every disagreement read by a person.

### Seven rules that the four tests share

1. **Define the task before the prompt.** Prompt 1's main "error" was a definition that differed from the reference. Write the codebook first (Chapter 1, Step 1).
2. **Always give a way out.** UNCLEAR and NOT REPORTED were the most useful answers in every test.
3. **Make every answer checkable.** Ask for the exact words or sentence, and check that they are in the text.
4. **Test on the hard cases, not only random ones.** Each sample here was built to include them, which is why each test found something.
5. **Know what your reference measures.** In two of four tests, the reference was the weaker side for some records.
6. **Prefer metadata where it exists.** Record types, publication types and registry fields are free, fast and stable. Use prompts where metadata stops.
7. **Record the model, date, prompt version and sample.** And run the test again when any of them changes.

```{=openxml}
<w:p><w:r><w:br w:type="page"/></w:r></w:p>
```
