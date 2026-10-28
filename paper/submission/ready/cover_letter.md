**To:** The Guest Editors, Omega 55th Anniversary Special Issue "Data-Driven Optimization for Smart Cities"
Professor Kai Pan (lead), Professor Ilke Bakir, Professor Hao Fu, Professor Jorge A. Sefair, Professor Duygu Tas and Professor Ming Zhao

**Article type:** VSI: Omega55: Smart Cities
**Submission system:** Editorial Manager, https://submit.elsevier.com/OMEGA
**Date:** [insert at submission]

**Resubmission of a previously rejected paper:** this submission is based on the paper previously submitted as **OMEGA-D-26-03236**, whose decision was "reject & resubmit".

Dear Professor Pan and Guest Editors,

Please consider the enclosed manuscript, "City charges for competing delivery carriers: exact best responses under probability-box travel times and leader pricing without equilibrium search", for the special issue. It is a resubmission of OMEGA-D-26-03236 (previous decision: reject & resubmit), revised as described in the response below.

A city that charges or subsidises deliveries has to predict how competing carriers react. Each reaction is an NP-hard routing problem under uncertain travel times, and the carriers interact through a congestion game. The manuscript gives one algorithm for each layer. Budget-resource labelling prices routes exactly when travel times are probability boxes with unknown dependence, and with branch-and-price it solves each carrier's robust routing problem to proven optimality on nine metropolitan instances with 22 customer zones, and with 30 to 40 customers in London and New York. Dual implementation pricing computes zone charges that make a social target an equilibrium using one best response per carrier. Aggregate-response pricing sets charges from observed zone totals alone, with a contraction rate that does not depend on instance size in the convexified game. On nine cities built from OpenStreetMap and gridded population, dual implementation pricing reached 1.07 to 1.23 times the gain of the best grid point with 5.7 to 8.3% of its routing calls in the three cities with ten seeds. The paper also gives existence and complexity results for the carriers' game and shows that policy directions persist across carrier criteria while levels do not.

The work fits the call through urban logistics and vehicle routing, robust optimisation under data uncertainty, and public-private coordination. It is a methods paper with computation on open data; it uses no machine learning, digital twin or real-time control and claims nothing in those directions. Section 1 states the novelty level of each component and Section 8 the limits of the stylised instances.

**Response to the evaluation of OMEGA-D-26-03236**

The evaluation of the previous version raised no comments on the scientific content. The only issues listed were Writing and Formatting, namely the length limit and the formatting requirements of the Guide for Authors. Each is addressed below.

1. Length (at most 35 pages including abstract, figures, tables, main text and references). The previous version had 70 pages. The main manuscript now has **34 pages** including the abstract, all figures and tables and the references. To reach this length, the long proofs, the extended data and city descriptions, the per-city and per-seed tables, the extra experiments (the zone-market-clearing negative result, the details of the criterion-robustness study and of the benchmark of the labelling method on public instances), the description of the Lean verification and the parameter source tables were moved to a separate Supplementary Material (50 pages, uploaded as a separate file). The main text keeps the model, the three algorithms with their key theorem statements and a proof sketch for each, the headline tables and figures, a short data section (nine cities, sources, parameter grades), the discussion and limitations, and the conclusion. Every result in the main text points to the section of the Supplementary Material that contains its full statement or proof. The reference list of the main text was reduced to the works cited there (58 entries); the Supplementary Material has its own bibliography.
2. Format (A4 or letter, single column, 11 pt, 1.5 line spacing, no line numbering). The manuscript is set on A4 paper in a single column in 11 pt type with 1.5 line spacing throughout, including the references, and has no line numbers.
3. Writing. The text was shortened and the repetition between sections removed. No result was changed and no claim or experiment was added; material was condensed or moved to the Supplementary Material. The numbers in the main text and in the Supplementary Material are generated from the same result files as before, and the scope statements and limitations were kept.

The manuscript is original, unpublished and not under review elsewhere. Code, instance pipeline, data and table-generating scripts are at https://github.com/vinhqdang/Competing-Carriers-under-Uncertainty.

Yours sincerely,

Quang-Vinh Dang
British University Vietnam, Hung Yen, Vietnam
vinh.dq4@buv.edu.vn
ORCID 0000-0002-3877-8024
