# Venue decision memo

Prepared 2026-10-26. All web data were retrieved on that date (RETR = 2026-10-26) with a search tool and a page fetcher.

How to read the evidence tags:

* **[V]** read on a primary or near-primary page during this session (EURO's EJOR report for 2025, Elsevier's AI-policy page, the ScienceDirect call listing as shown in search results).
* **[A]** taken from an aggregator or consultancy page (journalmetrics.org, BioxBio, SciJournal, Editage, Manusights, LetPub, myhuiban and similar). These sources disagree with each other and with Clarivate, so treat every number marked [A] as approximate.
* **[K]** general knowledge of the author, not re-checked on the web. Verify before relying on it.
* **[?]** uncertain or conflicting.

The publisher sites for INFORMS (pubsonline.informs.org metric pages), Elsevier (ScienceDirect call-for-papers and guide-for-authors pages) and Wiley returned HTTP 403 to the fetcher, so official Guides for Authors could not be read. Before submitting, open the guide of the chosen journal and re-check length, template, APC and AI rules. Impact factors are Clarivate JCR values; the 2025 JCR edition (June 2026) reports the metric year 2025 in the aggregator pages and the 2024 edition (June 2025) reports metric year 2024. The year is given for every number.

---

## 1. What the paper is, in terms a referee will use

Source files read: `docs/EXPERIMENTS.md`, `theory/new_algorithm_B/algorithm.md` (BRL exact pricing), `theory/new_algorithm_C/algorithm.md` (DIP), `theory/new_algorithm_D/algorithm.md` (ARP), `paper/main.tex` (class `elsarticle`, preprint, 12pt, about 174 kB of source).

* Problem: a city (leader) sets zone charges above competing delivery carriers; each carrier solves an NP-hard routing problem with p-box travel times and unknown dependence; carriers interact through zone prices and traffic (D1 Cournot-congestion game; D2 vehicle-count congestion variant).
* Contributions, with the novelty level the author states honestly: (i) exact pricing for the dependence-robust VRP (completion-window dominance, comonotone-coupling identity, one extra resource per loss kink) inside branch-and-price; the core decomposition is classical. (ii) Two leader methods, DIP (best-response cuts, about 5-9% of grid oracle calls) and ARP (aggregate-only adaptive charges with a contraction proof), both resting on classical ideas (marginal-contribution tolls, inverse-optimisation cutting planes, tatonnement). (iii) Theory: credal absorption theorem, D1/D2 complexity split, partial Lean 4 formalisation. (iv) Evidence on nine metro maps (OSM, GHSL 2025, web parameters), seed-sensitive. (v) A reusable instance pipeline.
* Self-declared weaknesses: no single breakthrough result; stylised model (22 customer zones per carrier, all-or-nothing lots, linear congestion); weak calibration inputs; the ZMC negative result.

Two facts matter for every venue below. First, the paper is OR-methodological, so venues that want "managerial insight from a real case" or "transport policy" are poor fits. Second, the paper's own prior-art paragraph lists a closest competitor (zeroth-order toll updates around an equilibrium solver for freight carriers with hard tour problems, cited as Masiha 2026), so a referee in this niche will test the incremental claim hard.

---

## 2. The Omega special issue

* Title as given by the author: "Omega 55th Anniversary Special Issue: Data-Driven Optimization for Smart Cities", deadline 31 August 2027.
* Search retrieved a ScienceDirect call-for-papers listing with this title, deadline 31 August 2027 and guest editors Ilke Bakir, Hao Fu, Kai Pan, Jorge A. Sefair, Duygu Tas and Ming Zhao [A: snippet was jumbled, the pairing of editors with the deadline is [?]]. URLs: https://www.sciencedirect.com/journal/omega/about/call-for-papers and https://www.sciencedirect.com/journal/omega/special-issues (could not be opened by the fetcher, 403; RETR 2026-10-26). The same listing shows another smart-city-related Omega issue (deadline 31 December 2026, editors Shi, Hu, Lu, Lee, He) that is out of scope for this paper [?].
* Scope as supplied in the task: DRO, learning-augmented optimisation, urban logistics, last-mile, vehicle routing, platform operations, public-private coordination; a methodological contribution beyond applying an existing method to an urban dataset is required. The fit is close on four of the topics (DRO, urban logistics/VRP, public-private coordination, platform operations).
* Practical consequence: the requirement is stated against "applying an existing method to a dataset". This paper does not do that, but its own list of contributions concedes that every piece rests on classical ideas. The cover letter must name the specific new objects: the completion-window dominance rule with its exactness proof, the credal absorption theorem, the contraction proof for ARP, and the D1/D2 complexity split.
* Special issues of Omega are normally handled by the guest editors with the regular Omega referee standard [K]. Papers are usually reviewed on arrival, not after the deadline, so an early submission gets a decision earlier; confirm in the call text.

---

## 3. Candidate journals, one by one

Metrics table first, details after. "IF" is the Clarivate 2-year impact factor.

| Journal | IF (year) | CiteScore (year) | First decision | Acceptance | OA / APC | Template |
|---|---|---|---|---|---|---|
| Omega (Elsevier) | 7.2 (2024) [V: EURO EJOR report, comparison slide]; 6.7 (2023) [V]; 6.9 on a ScienceDirect listing, year not stated [A] | 11.5, year not stated [A] | "3 days" on ScienceDirect header vs 4-8 or 6-10 weeks in a consultancy FAQ [A, ?] | not published [?] | hybrid; APC not found [?] | elsarticle (LaTeX) or Word [A, K] |
| EJOR (Elsevier / EURO) | 6.0 (2024) [V] | 13.2 (2024) [V] | not in report; mean peer review is long [?]; 6.5 reviewers invited per accepted article [V] | about 13% in 2024 [V] (4,424 new submissions in 2024 [V]) | hybrid; APC not found [?] | elsarticle |
| TR-B (Elsevier) | 6.5 (2025), 6.3 (2024) [A] | 11.6, year not stated [A] | not found [?] | not published | hybrid; APC 3,590 or 3,620 USD [A, ?] | elsarticle |
| TR-E (Elsevier) | 9.3 (2025), 8.8 (2024) [A]; other aggregators 10.8 [A, ?] | 11.6 or 15, year not stated [A, ?] | about 3 months peer review [A, ?] | not published | hybrid; APC not found [?] | elsarticle |
| Transportation Science (INFORMS) | 5-year IF 6.2 [V-ish: editor's statement 2025, found via search snippet]; 2-year not found | not found | mean 100 days for papers sent to external review; average 45 days over all decided manuscripts, as of 2025 [A: the INFORMS statements as relayed by the search tool and a consultancy page] | not published | subscription; OA optional [K] | INFORMS template |
| Operations Research (INFORMS) | not retrieved; rank 42/106 in OR&MS category (2024, Q2) [A] | not found | not retrieved | not published | subscription; OA optional [K] | INFORMS template |
| INFORMS J. Computing | 2.1 (2025), 5-year 2.7 [A]; 2.5 per another aggregator [A, ?]; rank 52/106 (2024) [A] | not found | not retrieved | not published | subscription; OA optional [K] | INFORMS template |
| Networks (Wiley) | 1.3 (2025), 5-year 1.9 [A]; 2.0 elsewhere [A, ?] | not found | not found | not found | hybrid [K] | Wiley, generic LaTeX [K] |
| Computers & OR (Elsevier) | 4.6 (2025), 4.3 (2024) [A] | 8.3, year not stated [A] | not found | not published | hybrid; APC not found [?] | elsarticle |
| TR-C (Elsevier) | 7.9 (2025), 5-year 10.0 [A]; 9.0 elsewhere [A, ?] | not found | not found | not published | hybrid | elsarticle |
| Naval Research Logistics (Wiley) | 2.1 (2025) on Wiley page [A]; 2.3 on Wikipedia [A] | not found | 18 days to first decision on Wiley page [A, ?] | 18% on Wiley page [A, ?] | hybrid [K] | Wiley |
| OR Spectrum (Springer) | 1.9 (2025), 5-year 2.8 [A]; 2.3 elsewhere [A, ?] | not found | not found | not published | hybrid, Springer Open Choice [K] | Springer (sn-jnl) |
| MSOM (INFORMS) | 4.2 (2025) [A: relayed by INFORMS and others]; INFORMS reports 4.8 to 4.2 drop (2024 edition) [A]; rank 28/106 (2024) [A] | not found | INFORMS publishes a chart [not read] | not published | subscription; OA optional [K] | INFORMS template |
| POM (SAGE / POMS) | not retrieved | not retrieved | not retrieved | not retrieved | [K] hybrid | not retrieved |

"Not retrieved / not found" means the search did not return the value; it is not a claim that the value does not exist.

### 3.1 Omega (regular submission)

* Scope statements. Elsevier shop page lists article types Theory and Methodology Advances ("research papers offering new contributions to the methodologies and theoretical foundations of Management Sciences and Operations Analytics"), Innovative Applications, Invited Reviews, Short Communications [A: shop.elsevier.com/journals/omega/0305-0483, via search result]. A consultancy page quotes the official scope as "data and problem-driven models for practical optimization and business analytics challenges" [A: manusights.com/blog/omega-submission-guide]. Older descriptions say papers with implications for management practice are preferred and purely theoretical papers are discouraged [A].
* Length: a consultancy page reports a 35-page limit in the Guide for Authors [A, ?]. Highlights (3-5 bullets) and a graphical abstract are requested (the repo already has `paper/highlights.txt` and `paper/graphical_abstract_notes.md`).
* Single-author algorithmic OR with real-data case studies: Omega publishes both algorithmic papers and application papers; single-author papers are accepted [K].
* Game-theoretic / bilevel routing: occasional [K]. I did not retrieve recent Omega examples; do a Scopus search on "bilevel" and "vehicle routing" in Omega before writing the cover letter.
* Review risk: a referee will ask what the managerial or policy takeaway is, whether 22 zones per carrier is realistic, and why p-boxes (versus Wasserstein or moment ambiguity). Omega referees often want "practical relevance"; the weak calibration inputs are the exposed flank.
* Acceptance chance (author's estimate): **medium** for the special issue (topic fit is high, competition is probably lower than in the regular stream, and the call asks for a methodological contribution, which this paper has in part); **low to medium** for the regular stream.

### 3.2 European Journal of Operational Research

* Scope: EJOR's own 2025 report says editors "became more strict regarding the focus of the submissions on Operational Research" and are "more demanding regarding the centrality of the use of OR methodology to support decision-making on real-world inspired problems" [V: https://www.euro-online.org/media_site/reports/EJOR_2025.pdf, RETR 2026-10-26]. This is a good fit for a paper that is OR-method-centred, and a warning against a model that looks stylised.
* Article types: Innovative Applications of OR, Decision Support, Discrete Optimization, Stochastic and Dynamic Models, Computational OR, and others [K]. A route through "Discrete Optimization" or "Transportation" is plausible. Length: no hard limit I could verify [?].
* Acceptance 13% in 2024; 97% of accepted papers had at least one major revision [V]. These numbers imply a long road.
* Single-author and bilevel/game routing papers: both appear in EJOR [K]. Examples to retrieve through Scopus before submission; I did not obtain URLs from EJOR.
* Review risk: "what is the new method?" The exact pricer is an application of an ESPPRC with a resource-extension; DIP and ARP are classical ideas by the author's own account; a referee in EJOR's discrete-optimisation area will probably say that completion-window dominance is an incremental improvement of labelling rules. A stylised 22-zone model will draw "not convincing for real-world inspired decision-making".
* Acceptance chance: **low to medium** (13% base rate; the author's chances depend on the strength of the headline result).

### 3.3 Transportation Research Part B

* Scope (aggregator quote of the current aims and scope): the journal "publishes papers on all methodological aspects" of transportation "particularly those that require mathematical analysis", with listed topics including network design and analysis, optimisation, pricing and investment, and traveller/shipper behaviour; an older version excluded purely mathematical exercises "which could relate to any kind of network" and required algorithm papers to show relevance to transportation [A, ?: scholar.korea.ac.kr/journal/34086 and the Elsevier shop page, via search results; check whether the older wording survives].
* Template: elsarticle. Length: no hard limit retrieved [?].
* Single-author algorithmic OR and game/bilevel routing: TR-B regularly publishes such work [K]. A recent DRO-VRP example from the TRID index (Zhou, Zhang, Baldacci, distributionally robust VRP with crowdshipping and time windows, exact branch-price-and-cut; the journal is probably TR-B, not confirmed) https://trid.trb.org/View/2721773 [A, ?].
* Review risk: TR-B wants mathematical depth with transportation substance. The theory here (absorption theorem, contraction, complexity split) is the part that matters; a referee will ask for sharper results, such as a price-of-anarchy bound for flat charges or a Stackelberg existence result with explicit conditions. The stylised model and weak calibration will be judged less harshly at TR-B than at TR-E, but "no breakthrough result" is a strong objection there.
* Acceptance chance: **low to medium**.

### 3.4 Transportation Research Part E

* Scope: logistics and transportation with "no limitations to the research methods utilized"; topics include logistics and operations models, supply-chain management, sustainability, risk and disruption (Elsevier journal page text as relayed by search) [A].
* Template elsarticle; no hard length limit retrieved [?]. TR-E has handled very large submission volumes and the bar varies by editor [K].
* Single-author algorithmic and game-theoretic: accepted [K]; examples to be retrieved.
* Review risk: TR-E referees want a managerial or policy message: what should a city do? The paper has a policy-relevant output (zone charges, equilibrium service levels in nine cities) and this is its best home for the application half of the story. Expect the objection that the model is stylised and that calibration is by web parameters.
* Acceptance chance: **medium**. It is the most natural "fit plus tolerance" venue among the transportation journals, but the base rate is not published.

### 3.5 Transportation Science

* Scope: "fundamental theories, mathematical models, advanced methodologies and novel applications" in transportation and logistics; areas: Logistics & Routing; Modes & Industries; Traffic, Demand & Network Analysis; Emerging & Cross-Functional Topics [A: consultancy page https://manusights.com/blog/transportation-science-submission-guide, RETR 2026-10-26; the editor's statement is at https://pubsonline.informs.org/doi/10.1287/trsc.2025.ed.v60.n1, 403 to fetcher].
* Limits: 35 pages including references plus 15 pages of appendices; single column, 1.5 spacing, 11 pt; no footnotes; abstract up to 300 words; INFORMS template, PDF accepted at submission [A, consultancy page].
* Speed: editor's statement (2025) projects more than 600 submissions, and mean 100 days to first decision for externally reviewed papers [A: via search snippet of the editorial].
* Desk-reject reasons listed on the same consultancy page: generic optimisation or algorithmic work where transportation is only the dataset; contribution buried in the literature review [A].
* Examples of game/bilevel work: Lim and Masoud, "Dynamic Usage Allocation and Pricing for Curb Space Operation", Transportation Science 58(6), 2024, a Stackelberg game recast as a single-level convex program, https://ideas.repec.org/a/inm/ortrsc/v58y2024i6p1252-1276.html [V: read]. Competing pickup-and-delivery operators and congestion-game properties, Transportation Science 55(6), 2021, https://ideas.repec.org/a/inm/ortrsc/v55y2021i6p1232-1259.html [A: abstract seen in search snippet only]. Munari et al., robust VRPTW by branch-price-and-cut, Transportation Science 2019 [A, via search].
* Review risk: TS is the right home for the exact BRL pricer if the author can make it the headline. As a leader-pricing paper with weak calibration it faces "incremental on both sides". The Associate Editor will screen for "transportation centrality" (satisfied) and for a method that beats state of the art on standard benchmarks (not yet shown for BRL on stochastic-travel-time VRP benchmarks).
* Acceptance chance: **low** unless the headline is rebuilt around the exact algorithm.

### 3.6 Operations Research (INFORMS)

* Scope: broad OR including methodology and applications; very selective (not retrieved verbatim). Category rank 42/106 in 2024 (Q2) on the INFORMS metrics page as shown in search results [A].
* Single-author algorithmic: fine in principle; however OR looks for a result of lasting theoretical significance. The paper's own list says no single breakthrough result.
* Review risk: desk rejection on contribution. Not recommended.
* Acceptance chance: **very low**.

### 3.7 INFORMS Journal on Computing

* Scope: "papers in the intersection of operations research and computer science", with Feature Articles, Expository and State-of-the-Art Reviews (consultancy/aggregator description of the INFORMS page) [A]. The journal requires code and data to be submitted under its reproducibility policy [K].
* AI/policy detail found: IJOC bans generative AI in reviewing; a 2026 editorial says a few submissions with generative-AI-written literature reviews were rejected for fabricated references and that the journal now vets references; a committee is drafting a broader policy [A: https://pubsonline.informs.org/doi/pdf/10.1287/ijoc.2025.ed.v37.n3 and a search summary of a 2026 editorial].
* Fit: the reusable instance pipeline, open code and the BRL implementation align with IJOC. The paper is long and mixes theory and game solving; IJOC papers are usually computation-focused.
* Review risk: "what computational advance beyond state-of-the-art ESPPRC / labelling?" Needs head-to-head against known exact methods on public benchmarks.
* Acceptance chance: **low to medium**, higher if the paper is split and the BRL pricer plus branch-and-price forms its own paper.

### 3.8 Networks

* Scope (aggregator): analytic modelling of problems using networks, mathematical analysis of network problems, efficient network algorithms, case studies of network applications [A: scijournal.org/networks, journalmetrics.org/journal/networks]. IF 1.3 (2025) [A].
* A special issue "Interdiction and Stochastic Programming on Networks" (in memory of R. Kevin Wood) has a submission deadline of 2026-12-31 [A: via search result]; bilevel structure is related but the paper is not about interdiction.
* Fit: partial; the paper is not network-theoretic. Prestige low in this table. Acceptance chance: **medium** but low reward.

### 3.9 Computers & Operations Research

* IF 4.6 (2025), 4.3 (2024) [A]; CiteScore 8.3, year not stated [A]. Elsevier template (elsarticle). Publishes algorithmic OR papers, single-author, real-instance computational studies; bilevel and game-based routing appear frequently [K].
* Review risk: asks for comparison with heuristics and published benchmarks; lower theoretical bar, bigger emphasis on computation. The paper's computational evidence is strong (branch-and-price verified on 800 instances, nine-city runs).
* Acceptance chance: **medium to high**. Best fallback.

### 3.10 Transportation Research Part C

* Scope: emerging technologies applied to transportation (OR, CS, AI, control), with effects on system performance [A: journalmetrics.org/journal/transportation-research-part-c-emerging-technologies and others]. IF 7.9 (2025), 5-year 10.0 [A, ?].
* Fit: weak. The paper has no sensing, learning or real-time component; "learning-augmented" is not in it (ARP is adaptive pricing from aggregates, which is the one overlap). Acceptance chance: **low**.

### 3.11 Naval Research Logistics

* Scope: "major methodological advances in operations research and management" plus applications of modelling [A: Wiley page text as relayed]. IF 2.1 (2025) [A]; Wiley page lists 18% acceptance and 18 days submission to first decision [A, ?: figures are taken from an aggregator snapshot of the journal page and could be a desk-decision median].
* Fit: acceptable for a methods paper; the venue likes clean theory plus computational evidence and accepts single authors. Acceptance chance: **medium**.

### 3.12 OR Spectrum

* Scope: "applied and theoretical papers which contribute to Operations Research as a scientific instrument, covering quantitative methods for decision-making in management" [A]. IF 1.9 (2025), 5-year 2.8 [A, ?]. Springer template.
* A "Data-driven Optimization" special issue tied to IFORS 2026 exists with guest editors Steinhardt, Ulmer, Fleckenstein, Zehtabian (deadline not retrieved) [A: found via search; confirm the call and deadline]. The topic is a partial match (ARP uses observed aggregates).
* Acceptance chance: **medium**; lower prestige than Omega and EJOR, fast and tolerant.

### 3.13 Manufacturing & Service Operations Management and Production and Operations Management

* MSOM: IF 4.2 (2025) [A]. Scope is analytical research on operations management with managerial insight; platform and sharing economy work is popular. A city-pricing model with p-box routing is far from the stylised closed-form analyses MSOM wants. Acceptance chance: **very low**.
* POM: not retrieved. It is closer to MSOM than to this paper. Acceptance chance: **very low**.

### 3.14 Other venues worth considering

* **EURO Journal on Transportation and Logistics** (IF 2.7 for 2024, 2.1 for 2023 per the EURO EJOR slide [V]): open-access, EURO-run, scope matches freight and routing; lower prestige but fast and well targeted. Acceptance chance: **medium to high**.
* **International Transactions in Operational Research** (IF 2.9 for 2024 [V]): has previously run optimisation-for-smart-cities special issues (a "Developments in Optimization for Smart Cities" issue is listed in a search result [A]); acceptance chance **medium to high**, low prestige.
* **Discrete Applied Mathematics / ISCO 2026 special issue**: an open call invites extended ISCO papers (no deadline retrieved) [A: https://www.euro-online.org/bb/topic/35109]; poor fit for the application half.
* **Transportation Research Part D / Part A, Journal of Transport Economics and Policy**: policy-oriented; would require recasting. Not recommended.
* **Conferences**:
  * TRISTAN XII was held 22-27 June 2025 (Tokyo/Ryukyus/Tohoku), 4-page extended abstract, deadline 15 or 31 October 2024 [A, ?]; next edition (XIII) is being sought for June 2028 [A]. Not available before 2028. https://tristanconference.org/editions/tristan-xii/cfp
  * ISCO 2026 took place 6-8 May 2026 in Kusadasi (Turkey), 41 full papers accepted from 64 submissions [A]; the next ISCO is outside the window, and the paper is long.
  * CPAIOR 2027: 24th edition, 1-4 June 2027, Toulouse; aggregator lists a submission deadline of 2026-12-01 (past patterns: early-to-mid December) [A, ?: no official page found]. CPAIOR proceedings are LNCS-format and accept CP/OR hybrids; the paper's content (branch-and-price with dominance rules under p-boxes) fits only as a short, algorithm-only version, and publishing a conference version first can complicate later journal submissions (check overlap policy, usually fine if extended).
  * AAMAS 2027 (Hanoi, 3-7 May 2027): abstract deadline 1 October 2026 and paper deadline 8 October 2026 have already passed; the AAAI fast track deadline is 11 December 2026 for papers already submitted to AAAI-27; AAMAS has a new "Findings" track [V: https://warwick.ac.uk/fac/sci/dcs/aamas2027/calls/call-for-main-track/ via search snippets, RETR 2026-10-26]. Not feasible; the paper is also a poor match for a multi-agent audience unless recast as a mechanism-design paper.
  * IJCAI 2027 (Kyoto, August 2027): deadline unconfirmed, between 4 and 15 January 2027 [A, ?]. The paper would need to be recast as an AI/game-theory paper; fit is weak, acceptance chance low.
* **Preprint servers**:
  * arXiv: categories math.OC (primary) with cs.GT cross-list. First-time submitters need an endorsement [K]. Secondary reporting says that in mid-May 2026 arXiv's computer-science section chair announced a one-year ban for submissions with incontrovertible evidence of unchecked LLM output (such as hallucinated references or leftover chatbot text), after which later submissions must first be accepted at a peer-reviewed venue [A: https://the-decoder.com/arxiv-tightens-penalties-for-ai-bungling-in-scientific-papers/ and https://gptzero.me/news/arxiv-ban/; primary statement not read; check arxiv.org policy pages].
  * Optimization Online: moderated eprint repository; PDF only; coordinators check relevance, not correctness; authors must take the paper down (or link to the published version) after copyright transfer [A: https://optimization-online.org]. Free, no endorsement hurdle.
  * SSRN: free, indexed by Elsevier's network, useful for management audiences (Omega, TR-E) [K]; its policy was not retrieved.
  * Journal preprint policies (Elsevier, INFORMS, Wiley, Springer all allow preprints on arXiv-type servers as a rule [K]). One soft INFORMS fact seen: Mathematics of Operations Research uses soft double-anonymous review and still allows online preprints [A]. Confirm Omega's and TS's rule on anonymisation (author names on preprints) before posting.

---

## 4. Publisher policies on AI-assisted writing (neutral summary)

The author decides what to declare. This section lists what each publisher requires, so the declaration can be made accurately.

**Elsevier (Omega, EJOR, TR-B, TR-C, TR-E, C&OR)** [V: https://www.elsevier.com/about/policies-and-standards/the-use-of-generative-ai-and-ai-assisted-technologies-in-writing-for-elsevier, RETR 2026-10-26]
* Authors should disclose the use of AI tools in manuscript preparation in a separate statement at the end of the manuscript, immediately above the references, titled "Declaration of Generative AI and AI-assisted technologies in the writing process"; the statement is published.
* The statement records the tool name, the purpose of use and the extent of the author's oversight. Template: "During the preparation of this work the author used [tool] in order to [reason]. After using this tool the author reviewed and edited the content and takes full responsibility for the content of the publication."
* Exemptions: basic grammar, spelling and punctuation checks need no declaration; reference managers without a generative option need no declaration, but AI used to select, collate, generate or edit references should be noted in the methods section or the declaration. AI used in the research process (as opposed to writing) should be described in the methods section if relevant.
* Restrictions: AI tools may not be listed as an author or co-author or cited as an author; authors "cannot use output from AI agents or deep research directly as the text of their manuscript" (output may only serve as inspiration) [V, as phrased on the page fetched; the page also states that authors may use AI to improve language and readability with disclosure, so the two sentences should be read together and the exact wording re-checked on the journal's own Guide]; no generative AI to create or alter images (including graphical abstracts), unless it is part of the research method and described reproducibly; authors must not upload previously published or copyrighted content into open AI tools.
* Editors and reviewers may not upload manuscripts to AI tools or use AI to review.

**INFORMS (Transportation Science, Operations Research, IJOC, MSOM)** [A: could not read the INFORMS policy page, 403]
* A search summary says INFORMS journals share one policy: authors, reviewers and editors remain responsible and accountable for any claim they make; the reference point is a June 2023 INFORMS editorial with permitted uses and guidelines (found via the INFORMS Journal on Data Science LLM-policy page).
* IJOC specifically: generative AI must not be used in reviewing; a 2026 editorial reports rejections for fabricated references in AI-written literature reviews, reference vetting, and a committee drafting a fuller author policy [A]. Re-read the current IJOC submission guidelines, because this is changing.

**Springer / Springer Nature (OR Spectrum, ISCO and CPAIOR proceedings in LNCS)** [A: third-party summaries, official page not retrieved]
* No AI tool may be listed as an author. Substantive use of a large language model must be documented in the Methods section (or a suitable alternative section); AI-assisted copy editing (readability, grammar, spelling, tone) does not need disclosure. AI-generated images are generally barred. Authors remain responsible for accuracy.

**Wiley (Naval Research Logistics, Networks, ITOR)** [A: summaries of Wiley's AI guidelines for authors]
* Disclose AI use at submission; keep documentation of the tools used, the purpose, whether they affected key arguments or conclusions, and how the output was reviewed. Disclosure goes in Methods, a disclosure statement or Acknowledgements. Spelling, grammar and general editing tools are excluded from disclosure. Translation with AI is permitted. Generative tools must not create, alter or manipulate original research data or results. AI cannot be an author.

**arXiv / Optimization Online / SSRN**
* arXiv: author is responsible for the content; the May 2026 enforcement described above applies to unchecked output [A, ?]. Optimization Online: authors represent that the work is original and that they hold permissions [A]. SSRN: not retrieved.

**Practical reading for the author.** Across publishers the shared points are: AI is not an author; the human author is accountable for every claim, derivation, number and reference; reference lists get checked (a fabricated or wrong reference is the commonest reason for a rejection or sanction at present); and a statement of any AI use that went beyond grammar and spelling is expected, with the placement depending on the publisher (a separate statement above the references at Elsevier; Methods or Acknowledgements at Wiley and Springer). The Lean 4 formalisation and the code in this repository give the paper machine-checkable parts, which can be mentioned as a verification measure. Before submission, run a reference check of every entry in `paper/references.bib` against its DOI.

---

## 5. Ranked recommendation

Ranking criteria: scope fit, probability of a publishable outcome within about 12-15 months, prestige, and tolerance for a paper that has no single breakthrough.

| Rank | Venue | Chance (author's estimate) | Main reason |
|---|---|---|---|
| 1 | Omega 55th Anniversary Special Issue | medium | Topic list matches the paper on four counts (DRO, urban VRP/last-mile, platform operations, public-private coordination); deadline 31 August 2027 allows time to strengthen the paper; IF 7.2 (2024); the paper is an elsarticle manuscript already. |
| 2 | Transportation Research Part E | medium | Most natural general-purpose logistics venue; no method restriction; tolerant of stylised models if the policy message is clear; IF about 9 (2025, aggregators disagree). |
| 3 | Computers & Operations Research | medium to high | Algorithm-and-computation journal; the exact pricer and nine-city evidence suit it; lower prestige (IF 4.6, 2025 [A]). |
| 4 (stretch, only if the paper is strengthened) | Transportation Research Part B or Transportation Science | low to medium / low | Higher prestige, but a referee will say "no breakthrough result"; use only after Section 6 mitigations are done. |
| Fallback | EURO Journal on Transportation and Logistics, OR Spectrum, Naval Research Logistics or ITOR | medium to high | Fast, targeted, tolerant. |

Not recommended: Operations Research, MSOM, POM, TR-C, AAMAS/IJCAI (fit or contribution mismatch), EJOR as a first attempt (13% acceptance in 2024 [V], and the editors demand a strong OR core; keep it as a stretch after Omega if the referees' comments are mostly about presentation).

### Submission order

1. **Now to January 2027: strengthen, then post a preprint.** Complete the Section 6 items that need no new theory (more seeds, sensitivity, reference check), then post to arXiv (math.OC, cross-list cs.GT) and Optimization Online. Timing argument: a preprint establishes priority over the Masiha-type competitor and invites comments. Check anonymisation rules of the target journal first. SSRN is optional.
2. **February to April 2027: submit to the Omega special issue**, not at the deadline. A submission well before 31 August 2027 leaves time for a second attempt elsewhere within the year if the answer is a rejection; the call's own rules on early submission and rolling review should be confirmed in the call text [?].
3. **If rejected (expected 3-5 months, Elsevier time scale [K]):** submit to TR-E with a version rewritten to carry the policy message; if rejected again, submit to C&OR; then EJTL or OR Spectrum.
4. **Rejection-tolerant alternative route** (if the author prefers speed over prestige): go directly to C&OR or TR-E in December 2026 and skip the special issue. This loses the special issue's topical advantage and gains about 6-8 months.
5. Do not submit to two journals at once; the same text cannot be under review in two places (Elsevier, INFORMS and Wiley all forbid simultaneous submission) [K].
6. **Splitting option.** The paper bundles an exact routing algorithm, two leader methods, theory and an empirical study. A referee at a top venue may ask for focus. Two papers (a) BRL exact pricing with branch-and-price for dependence-robust VRP (TS, IJOC or C&OR) and (b) the game-and-pricing paper (Omega, TR-E) would each be easier to defend and would remove the "no single breakthrough" problem for (a). It costs time. Decide before Step 2.

### What to prepare for each first-tier venue

**Omega special issue.** Cover letter: (i) state how the call's topics map to the paper in four sentences; (ii) name the methodological contributions and what is not claimed (classical decomposition, classical tolls); (iii) say the paper applies to nine metropolitan areas through an instance pipeline released with the paper; (iv) disclose the preprint. Suggested reviewer areas: robust/DRO routing (Wasserstein and p-box/credal sets), exact VRP (branch-price-and-cut), toll design and congestion games, urban logistics policy. Declarations: Elsevier generative-AI statement if applicable, data and code availability, conflict of interest, funding, CRediT line (single author). Format: elsarticle, highlights, graphical abstract, 35-page limit check [A, ?].

**TR-E.** Cover letter: lead with the policy question (what zone charge, what service and congestion outcome), then the method. Reviewer areas: city logistics, congestion pricing, freight policy, robust routing. Add a short "managerial and policy implications" section and a "limitations" section.

**C&OR.** Cover letter: lead with the exact algorithm and computational evidence (800 of 800 branch-and-price verification cases, call-saving of 5-9% for DIP). Reviewer areas: ESPPRC/labelling, branch-and-price, bilevel algorithms, equilibrium computation. Release code and the instance pipeline.

---

## 6. Reviewer-risk mitigations to do before submitting

Ordered by expected gain per effort. The venue where each item raises the paper most is in brackets.

1. **Replace seed-sensitive claims with a proper statistical statement.** Run 10 or more seeds per city for the headline comparisons (E2, E3, E4), report confidence intervals, and state which findings are robust and which are not. Say plainly what the ZMC negative result shows and why it is kept. [all venues; cheap]
2. **Benchmark the exact pricer on public instances.** Solve stochastic-travel-time VRPTW instances from the literature (Solomon or Homberger families with p-boxes built from samples) and compare with the best published exact robust and DRO methods (budgeted, Wasserstein, CVaR) in solved-instance counts and times. [TS, TR-B, C&OR, IJOC; medium effort; this is the single most important experiment for a computational or algorithmic referee]
3. **Justify the p-box model against alternatives.** Show on a small set where Wasserstein or moment ambiguity gives different routes or costs; show how conservative the comonotone worst case is relative to data-driven dependence structure on observed days. [Omega, TR-B, EJOR]
4. **Scale beyond 22 customer zones per carrier.** Show runs with 50 and 100 zones, even with a time limit and reported gaps, and report where branch-and-price stops. Remove the A1 lot restriction in at least one robustness run (split lots). [TR-E, Omega, EJOR]
5. **Calibration against something observable.** Compare modelled equilibrium service and slowdown against published figures for cities with real freight or congestion charges (for example London, Stockholm, Singapore); even a coarse plausibility check, clearly labelled, answers the "weak calibration" objection. [TR-E, Omega, TR-B]
6. **Sharper theory where cheap.** (a) A price-of-anarchy or loss bound for flat zone charges that is explicit in the lot-asymmetry number, with a tightness example; (b) a rate for ARP in terms of observable quantities; (c) a statement of when the credal absorption theorem is tight and when it is not. Complete the Lean 4 items that remain, or state exactly which statements are machine-checked. [TR-B, TS, NRL]
7. **Baselines for the leader problem.** Compare DIP and ARP with derivative-free and Bayesian-optimisation baselines and with the zeroth-order toll update of the closest competitor, on the same budget of oracle calls. [EJOR, Omega, TR-B; needed if the "5-9% of oracle calls" claim is the headline]
8. **Position the novelty honestly in the introduction.** State a one-sentence claim per contribution and a list of what is classical (the paper already does this in its prior-art paragraph). Put the contribution statement in the introduction, not in the literature review (a stated desk-reject reason at TS). [all venues]
9. **Reproducibility package.** Public repository with a tagged release, a data-and-code availability statement, the instance pipeline documented, and a one-command reproduction of the headline tables. [IJOC requires it; helps at every venue]
10. **Length and format.** Cut the main text to about 35 pages including references with appendices after (TS/Omega limits [A, ?]); the source is 174 kB of LaTeX, so a split (Section 5, step 6) or an appendix move is likely needed.

---

## 7. Source list (RETR 2026-10-26 unless noted)

* EJOR report, EURO, 2025 (IF 2024 = 6.0, CiteScore 2024 = 13.2, acceptance about 13% in 2024, 4,424 submissions in 2024, Omega IF 7.2 (2024) and 6.7 (2023), EJTL 2.7 and ITOR 2.9 for 2024, editorial-focus statement): https://www.euro-online.org/media_site/reports/EJOR_2025.pdf [V]
* Elsevier generative-AI policy for authors: https://www.elsevier.com/about/policies-and-standards/the-use-of-generative-ai-and-ai-assisted-technologies-in-writing-for-elsevier [V]
* Omega call listing and special-issue index (not openable by the fetcher; seen in search results): https://www.sciencedirect.com/journal/omega/about/call-for-papers, https://www.sciencedirect.com/journal/omega/special-issues [A]
* Omega consultancy summary: https://manusights.com/blog/omega-submission-guide [A]; Elsevier shop page: https://shop.elsevier.com/journals/omega/0305-0483 [A]
* Transportation Science: https://manusights.com/blog/transportation-science-submission-guide [A]; editor's statement https://pubsonline.informs.org/doi/10.1287/trsc.2025.ed.v60.n1 [A, snippet]; metrics page https://pubsonline.informs.org/authorportal/journal-metrics/transportation-science [not opened]
* Aggregators: https://www.journalmetrics.org/journal/transportation-research-part-b-methodological-2, https://www.bioxbio.com/journal/TRANSPORT-RES-E-LOG, https://www.journalmetrics.org/journal/networks, https://www.bioxbio.com/journal/COMPUT-OPER-RES, https://www.journalmetrics.org/journal/or-spectrum, https://www.journalmetrics.org/journal/naval-research-logistics, https://www.journalmetrics.org/journal/transportation-research-part-c-emerging-technologies, https://www.journalmetrics.org/journal/informs-journal-on-computing, https://www.servsig.org/wordpress/?p=15556 (MSOM) [A]
* Examples: https://ideas.repec.org/a/inm/ortrsc/v58y2024i6p1252-1276.html [V: read]; https://ideas.repec.org/a/inm/ortrsc/v55y2021i6p1232-1259.html [A]; https://trid.trb.org/View/2721773 [A]; https://arxiv.org/pdf/2304.09170 (bilevel compensation and routing in last-mile delivery) [A]; https://arxiv.org/pdf/2412.06482 (combinatorial bilevel congestion pricing) [A]
* Conferences: https://tristanconference.org/editions/tristan-xii/cfp; https://warwick.ac.uk/fac/sci/dcs/aamas2027/calls/call-for-main-track/; https://www.myhuiban.com/conference/2409 and https://www.beri.net/events/cpaior-2027 (CPAIOR 2027); https://www.opencurious.com/ai-conference-deadlines/ijcai-2027 and https://www.beri.net/events/ijcai-2027 (IJCAI 2027); https://www.euro-online.org/bb/topic/34423 and https://www.euro-online.org/bb/topic/35109 (ISCO 2026) [A]
* Preprints: https://optimization-online.org; https://the-decoder.com/arxiv-tightens-penalties-for-ai-bungling-in-scientific-papers/; https://gptzero.me/news/arxiv-ban/ [A]
* AI policies, INFORMS and IJOC: https://pubsonline.informs.org/page/ijds/llm-policy, https://pubsonline.informs.org/doi/pdf/10.1287/ijoc.2025.ed.v37.n3 [A, snippets]; Springer Nature and Wiley via third-party summaries (https://casrai.org/dictionary/term/nature-portfolio-ai-policy, https://www.enago.com/responsible-ai-movement/publisher-ai-guidelines/wiley-ai-guidelines/) [A]

### Open items for the author

1. Open the ScienceDirect special-issue page and confirm deadline, guest editors, early-submission rules and the special-issue article type.
2. Read the Guides for Authors of Omega, TR-E and C&OR for page limits and the AI-declaration wording; the fetcher could not.
3. Pull the official JCR and Scopus values for the three target journals; the numbers above are aggregator-grade.
4. Confirm the current arXiv AI-content rule on arxiv.org before posting.
5. Run a Scopus search for 2024-2026 bilevel or game-theoretic routing papers in Omega, EJOR, TR-B and TR-E to add recent examples to the cover letters; this memo found examples mainly in Transportation Science and INFORMS-adjacent sources.
