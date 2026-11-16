## Chapter 11 — Teaching What You Know

> **Essentials.** Teaching multiplies the value of what you learned: each person you train can analyse their own field. Good workshops start from what learners should be able to do at the end, use one real dataset from start to finish, keep explanations short and practice long, and check learning with real tasks. Your analysis already provides the ingredients: a clean teaching dataset, worked examples and the mistakes you made along the way. *Trust level: Green for drafting course materials from your cases, with answer keys traced to the data.*

### 1. The output and its reader

The table of bacteria I built during my PhD was made by hand, one paper at a time. Many researchers learn the methods in this book the same way: slowly, by trial and error, without a course that shows them how to search several databases, remove duplicates, extract information at scale or check their results.

Today, many early-career researchers, especially in regions with fewer training opportunities, are in the same position. They have important questions about their fields and no time to discover the methods alone. A two-day workshop, built on one real dataset and taught by someone who has done the work, can save them months.

| Output | What it is | Who it serves |
| -------------------------- | ------------------------------------------ | ------------------------------ |
| Workshop | One to three days of hands-on training on a focused skill | Students, early-career researchers, librarians, analysts |
| Course module | Several sessions within a degree or training programme | Students in a programme |
| Teaching dataset and exercises | A small, clean dataset with tasks and solutions | Teachers and self-learners |
| Online materials | Slides, notebooks and videos, openly licensed | Anyone, anywhere |

### 2. What you need from your analysis

- A small, clean subset of your dataset (a few hundred to a few thousand records) with known answers
- Worked examples from Books 1 and 2, adapted to the subset
- Your logs of mistakes: the duplicates you missed, the gap that was not real, the AI label that was wrong
- Validated prompts and notebooks (Book 2)

### 3. Step by step, with AI and the claim check

*1. Know your learners.* Who are they, what do they know, what do they need to do afterwards? A short survey before the workshop helps.

*2. Write learning outcomes*: what learners will be able to do at the end, with action verbs. Example: *By the end, participants will be able to build a tested search in two databases, remove duplicates, screen 100 records with a partner and compute agreement.*

*3. Design backwards* from the outcomes: what task will show that each outcome is reached? What practice leads to that task? What short explanation is needed before the practice?

*4. Build one teaching dataset* that runs through the whole workshop, with documented answers. Learners remember a story they follow from start to finish.

*5. Plan short sessions*: about 15 minutes of explanation, 30 to 45 minutes of practice, 10 minutes of discussion. Use the three paths of Book 2: no code first, code as an option, AI with checks.

*6. Prepare for different levels*: core tasks for everyone, extension tasks for faster learners, helpers in the room if possible.

*7. Check learning*: short exercises with known answers, a final task on the learners' own topic, and peer review between learners.

*8. Collect feedback* at the end of each day, and change the next session.

*9. Share materials openly* with a licence such as CC BY, so others can teach them too.

*10. Train trainers.* The fastest way to reach many learners is to train people who will teach in their own institutions and languages.

#### A two-day workshop plan

| No. | Day 1 | Day 2 |
| ------------ | ------------------------------------------ | ------------------------------------------ |
| 1 | Why let science data speak: one story, three values (Book 1) | Enrichment: countries, income groups, funders (Book 2, Ch. 4) |
| 2 | From question to search; test sets (Book 2, Ch. 2) | Topic maps and networks in VOSviewer (Ch. 6–7) |
| 3 | Duplicates and screening with a partner; kappa (Ch. 2) | Indicators done responsibly (Ch. 8) |
| 4 | AI for screening, with validation (Ch. 5) | From analysis to outputs: each learner plans a portfolio (Book 3, Ch. 1) |
| End | Quiz and feedback | Short presentations; feedback; next steps |

#### Teaching with AI

Learners will use AI whether or not you teach it, so teach it well:

- show it helping (synonyms, code, plain-language drafts);
- show it failing on your teaching dataset (a missed relevant paper, an invented reference, a wrong country);
- make learners measure its accuracy on a small known sample;
- teach the reporting rules (Book 2, Chapter 1).

#### With AI, and the claim check

AI can help you draft session plans, exercises, quiz questions and translations of materials. Check every exercise against your teaching dataset, every answer key by doing it yourself, and every translation with a fluent speaker who knows the field.

### 4. Worked example: malaria vaccines

A two-day workshop for 25 early-career researchers from several West and East African institutions, run with a regional research network:

- Teaching dataset: 800 malaria vaccine records with known duplicates, screening decisions, countries and entity labels, deposited on Zenodo with a README.
- Outcomes: build and test a search; deduplicate and screen with agreement; map a field and its collaborations; compute two indicators responsibly; plan outputs from an analysis.
- Format: in person, with a parallel online version; materials in English and French; no-code path for everyone, notebooks for those who want them.
- Final task: each participant applies one method to a topic from their own work and presents a one-page portfolio plan.
- Trainers: two participants from the previous workshop co-teach, so the network can run future workshops on its own.

#### Through the release pipeline

Take a two-day workshop for doctoral students on using AI to map science. It is built on the trap catalogue (Book 2, Appendix A): each session starts with a trap from real data, lets students fall into it with an AI assistant, and then shows the check. The trap of the full-text search box, the 2013 affiliation change, the "sp. nov." phrase, the mean that misled, the class that was mostly something else. Students remember the trap they fell into more than any rule.

The course materials go through the pipeline too. The slides draw only on the evidence pack of each case. The exercises have answer keys traced to the data. And the AI-use statement for the course says which slides were drafted with AI and who checked them.

### 5. Common mistakes

- Too much talking, too little practice.
- Different datasets in every session, so learners never see the whole workflow.
- Assuming everyone codes, or that no one does.
- No known answers, so learners cannot check themselves.
- No follow-up, so skills fade.
- Materials kept closed, so nobody else can teach them.

#### Checklist

- [ ] Learners and their needs known
- [ ] Learning outcomes written with action verbs
- [ ] Tasks designed from outcomes
- [ ] One teaching dataset with documented answers
- [ ] Sessions short, practice-heavy, with three paths
- [ ] AI taught with its failures
- [ ] Feedback collected and used
- [ ] Materials shared openly; trainers trained

### Key takeaways

-   Start from what learners should be able to do, and design backwards.
-   Use one real teaching dataset from start to finish, with known answers.
-   Teach AI's failures as well as its uses.

### References

-   The Carpentries. Instructor training materials and teaching practices. carpentries.org.
-   Wiggins G, McTighe J. *Understanding by Design*. 2nd ed. Association for Supervision and Curriculum Development; 2005.
-   Book 2 of this series, which serves as the textbook for a methods course.
