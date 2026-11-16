## Chapter 10 — Dashboards and Living Reports

> **Essentials.** A dashboard shows key indicators that update as new data arrives; a living report updates its text and figures on a regular schedule. Both turn a one-time analysis into a lasting service. They work when they answer a small set of questions for named users, are built on a reproducible pipeline, show their date, sources and limits on every page, and have someone responsible for keeping them alive. A dashboard nobody updates is worse than none. *Trust level: Amber. Let AI write chart and update code; every update reruns the checks, and a person reads what changed before release.* *Trap to watch (Book 2, Appendix A):* T04, access rules that change. Log the source, date and access route of every update.

### 1. The output and its reader

Picture a beautiful dashboard with 30 charts, 12 filters and every indicator from a landscape. It is launched with an email. After a month, nobody opens it. After six months, the data is out of date and nobody notices.

Picture instead a simple page with five indicators chosen with three programme managers, updated on the first day of each month, with a date and a short note on what changed. They open it before every monthly meeting.

The difference is not technology. It is the users, the questions and the routine.

| Output | What it is | Who it serves |
| -------------------------- | ------------------------------------------ | ------------------------------ |
| Dashboard | An interactive page of indicators and charts with filters | Programme managers, funders, research offices, the public |
| Living report | A document or web page whose text and figures are updated on a schedule | Funders, policymakers, research communities |
| Monthly update note | A short note on what changed since the last update | Regular users |

### 2. What you need from your analysis

- A reproducible pipeline with an update routine (Book 2, Chapter 11)
- Indicators defined with care (Book 2, Chapter 8)
- Automatic checks that stop bad data from reaching users
- A person responsible for updates

### 3. Step by step, with AI and the claim check

*1. Name the users and their questions.* Meet two or three users. Ask what they decide, how often, and what they need to see. Write five questions at most.

*2. Choose indicators*: one or two per question, from Book 2, Chapter 8. Write an indicator card for each: definition, source, counting method, update frequency, limits.

*3. Choose the tool.* Simpler is often better.

| Tool type | Examples | Good for |
| -------------------------- | ------------------------------------------ | ------------------------------ |
| Spreadsheet-based | Google Sheets or Excel with charts; Looker Studio | Small teams, few indicators, no coding |
| Business intelligence tools | Power BI, Tableau Public | Interactive filters, larger data |
| Code-based web apps | Shiny (R), Streamlit or Dash (Python), Observable | Full control, custom analysis |
| Document-based | Quarto or R Markdown reports and dashboards | Living reports that rebuild from data |
| Chart tools | Datawrapper, Flourish | Clear, embeddable charts for websites and stories |

*4. Design for reading.* The most important indicator at the top left; one chart per question; message titles; plain labels; filters only where users need them.

*5. Show date, sources and limits* on every page: "Data: OpenAlex and PubMed, updated 1 December 2026. Counts for the last 12 months are incomplete because of indexing delays."

*6. Connect to the pipeline* so updates do not need manual steps, or document every manual step.

*7. Add checks*: stop the update if counts drop or jump unexpectedly, if key columns are missing, or if the date did not change.

*8. Test with users*, then launch.

*9. Set the routine*: update day, person responsible, a backup person, and a change log.

*10. Review every six months*: are users still using it? Are the questions still right? Should it end?

#### Living reports

A living report is updated on a schedule, often monthly or quarterly. It suits fast-moving fields, such as a new technology or an emerging disease, and topics where decisions recur.

| Element | Content |
| -------------------------- | ------------------------------------------------------------ |
| Version and date | At the top of every version |
| What changed | Three to five bullet points |
| Key indicators | Updated figures, with the previous value |
| Short commentary | One paragraph per key change |
| Methods and limits | Stable text, with a link to the full methods |
| Archive | Every past version kept, with a DOI for major versions |

#### Watch out for incomplete recent data

Recent data is always incomplete. Papers are indexed weeks or months after publication, and citations take years to accumulate. Dashboards that show the last few months as a "drop" mislead users. Shade or flag the most recent period, or show it separately, and explain why.

#### With AI, and the claim check

AI can draft the monthly "what changed" note from the updated tables, write indicator cards, and suggest chart titles. Check that every number in the note matches the dashboard, that changes due to indexing delays are not described as real trends, and that no interpretation goes beyond the data. Keep the prompt and model version in the pipeline (Book 2, Chapter 1).

### 4. Worked example: malaria vaccines

A monthly malaria vaccine dashboard for a funder and two national programmes answers four questions:

| Question | Indicator | Chart |
| -------------------------------------- | ------------------------------------------ | ---------------------------- |
| How active is the field? | New papers and preprints per month, by target stage | Line chart, last 24 months, recent months shaded |
| What is in the pipeline? | Registered trials by phase and status | Bar chart by phase, filter by country |
| Who leads? | Share of new papers with an endemic-country first or last author, rolling 12 months, with interval | Line with band |
| What has changed? | New WHO or national policy documents citing vaccine research | List with links |

It is built with a Quarto dashboard that rebuilds from the Book 2 pipeline on the first day of each month. A one-paragraph note goes to users with the update: what changed and anything unusual. The team reviews the dashboard with users every six months.

#### Through the release pipeline

The monthly malaria vaccine dashboard for programme managers shows trials, linked papers and the share of papers led from the region. Each update is an output, so each goes through a short pipeline: the notebook reruns (Book 2, Chapter 11), its checks pass, the evidence pack updates itself, and a person reads the changes before release. The dashboard shows two things most dashboards hide: the date of the data on every chart, and a "what changed since last month" line. When the number of completed trials without a visible paper drops from 37 to 35, the line says why: two papers found by name.

### 5. Common mistakes

- Building for everyone, and therefore for no one.
- Too many indicators and filters.
- No date, sources or limits on the page.
- Reading indexing delays as declines.
- Manual updates with no routine, which stop when the analyst leaves.
- No review, so dashboards outlive their usefulness.

#### Checklist

- [ ] Users named; five questions or fewer
- [ ] Indicator cards written
- [ ] Simple tool chosen
- [ ] Date, sources and limits on every page
- [ ] Recent incomplete periods flagged
- [ ] Connected to the pipeline, with checks
- [ ] Update routine, responsible person and change log
- [ ] Review date set

### Key takeaways

-   Start from users and a few questions; choose indicators to answer them.
-   Show date, sources and limits; flag incomplete recent data.
-   Connect to a reproducible pipeline, with checks and a named person responsible.

### References

-   Datawrapper Academy: guidance on clear charts. datawrapper.de/academy.
-   Elliott JH, Synnot A, Turner T, et al. Living systematic review: 1. Introduction—the why, what, when, and how. *Journal of Clinical Epidemiology*. 2017;91:23–30.
-   Quarto documentation on dashboards: quarto.org.
-   Book 2, Chapters 8 and 11 of this series.
