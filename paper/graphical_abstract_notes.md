# Graphical abstract note

Built only from existing figures and generated results; no new result. Left to right, white background, three panels, plain labels.

1. **Problem: three layers** (schematic, no numbers). Redraw Figure 1 of the manuscript (the TikZ schematic in Section 1.1) in a compact form: carriers' routing under probability-box travel times -> carriers' game (equilibrium) -> city's charges. Caption: "Each carrier solves an NP-hard routing problem; carriers compete and congest; the city sets charges."
2. **Methods** (three short text lines next to the layers): BRL, exact best responses under probability boxes with unknown dependence; DIP, charges from best-response cuts; ARP, charges from observed zone totals only.
3. **Evidence**: `figures/arp_calls_vs_gain.png` (gain relative to the best exact grid point against routing-oracle calls, log scale; grid, DIP, ARP and tariff variants), with one line: "Policy directions hold across carrier criteria; levels do not." Caption: "Leader methods need a fraction of the grid's routing calls; gains above 100% partly reflect zone-specific charges."

Notes for the author
- Keep the log-scale call axis; it is the main message of the evidence panel.
- Do not use the broad-objective panels (shut-down optima are an artifact of a proxy).
- Elsevier's Guide for Authors asks for a single-panel image of at least 531 x 1328 pixels (height x width) or proportionally more, readable at about 5 x 13 cm, in TIFF, EPS, PDF or Office format. Confirm the current rule on the submission site before exporting.
- The panel must not suggest a digital-twin, human-in-the-loop or real-time result; none was produced.
