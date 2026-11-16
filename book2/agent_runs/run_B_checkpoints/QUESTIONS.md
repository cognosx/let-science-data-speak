# Open decisions (checkpoint G)

Each item is a choice that could change the answer. I took the option marked **Taken** and went on. Where I could, I tested the other option (see report.md, "Sensitivity").

**Q1. Is a preprint the same work as its later journal article?**
Options: (a) one work; (b) two works.
**Taken: (a).** I merged them only when the title, year (within 1 year) and first author also agree. For one cluster I keep the journal version's year and data. Effect: dropping works that exist only as preprints changes the 2020–2026 first-author share from 22.1% to 21.7%.

**Q2. What counts as a "paper"?**
Options: (a) any journal-type item (articles, reviews, editorials, letters, news, preprints); (b) research articles and reviews only; (c) every work, including patents, theses, datasets and book chapters.
**Taken: (a)** (19,955 of 23,594 works; 16,458 from 2000–2026). I excluded errata, retractions, patents, theses, datasets, peer-review reports, supplementary files, books and book chapters. Results for (b) and (c) are in the report, and the direction is the same.

**Q3. Should the unscreened records be screened for relevance before computing shares?**
Options: (a) use all records as downloaded; (b) use a keyword-screened subset; (c) screen by hand (not possible in the time).
**Taken: (a) for the main numbers, with (b) reported next to them.** The keyword screen is a malaria term AND a vaccine term in a title, or the PubMed MeSH term "Malaria Vaccines". On my 200-title sample it has 64% precision and 91% recall. The screened subset shows the same direction with a larger rise (7.5% → 8.9% → 24.0% for first authors).

**Q4. Single-author papers: the author is both first and last?**
**Taken: yes.** Restricting to papers with two or more authors gives almost the same numbers (22.2% / 19.3% in 2020–2026).

**Q5. When OpenAlex and the PubMed affiliation text give different countries, which one wins?**
Options: (a) OpenAlex institution country first; (b) PubMed affiliation text first.
**Taken: (b).** OpenAlex often codes African branches of foreign institutes to the parent country (for example MRC Unit The Gambia and KEMRI-Wellcome Kilifi coded as the UK). In 179 of 230 disagreements, the PubMed text says sub-Saharan Africa (SSA) and OpenAlex does not. Option (a) lowers every share by about 1 point and keeps the direction.

**Q6. An author with affiliations in several countries.**
Options: (a) first-listed country; (b) SSA if any affiliation is in SSA; (c) SSA only if all affiliations are in SSA.
**Taken: (a).** (b) and (c) bracket the result: 2020–2026 first author 24.0% vs 20.3%.

**Q7. Which publication year, when sources disagree (1,224 works)?**
**Taken:** PubMed year, then Europe PMC, then OpenAlex, with the journal version before the preprint. Using the earliest year instead moves 118 papers between periods and changes no share by more than 0.2 points.

**Q8. Income group: the classification at the time of publication, or today's?**
**Taken:** the classification in the publication year, from OGHIST.xlsx ("Country Analytical History"; the GNI calendar year equals the publication year). Years 2024–2026 use the last column (FY25, 2023 GNI). Today's classification (CLASS.xlsx) is reported too. The two differ a lot for 2000–2009: low income 8.9% vs 2.4%, because Kenya, Ghana, Nigeria and India were low income then.

**Q9. "Africa" in the question.**
**Taken:** World Bank region "Sub-Saharan Africa" (48 economies, including Sudan and Mauritius), as the brief asks. North Africa (Egypt, Morocco and others) is not included. A funder who means the whole continent would get slightly higher shares; I did not compute them.

**Q10. 2026 is a partial year (download date 10 November 2026).**
**Taken:** kept 2026 in 2020–2026, as the brief asks. The results without 2026 (2020–2025) are also shown: 19.5% / 16.8%.

**Q11. Territories and unclassified economies.**
**Taken:** French Guiana, Martinique, Guadeloupe, Réunion and Mayotte are counted as France (they are not separate World Bank economies; 10 papers). Venezuela has no current income group (17 papers): it is left out of the current-income denominator, but it is classified in the publication-year version.

**Q12. Near-duplicates in the uncertain band (title similarity 0.85–0.95, or ≥0.95 with a different marker such as "correction" or "additional file").**
**Taken:** not merged (541 pairs listed in work/out/uncertain_band_pairs.csv). Also not merged: 120 near-identical pairs that carry two different PMIDs with no preprint or shared DOI to explain them, and 263 groups with the same title and year but a missing or different first author.

**Q13. The relevance ratings for checkpoint F were made by one rater (the agent), from titles only.** A second, human rater is needed if these numbers will be published.
