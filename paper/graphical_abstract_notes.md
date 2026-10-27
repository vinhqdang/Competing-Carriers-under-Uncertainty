# Graphical abstract note

Built only from existing figures and generated results; no new result. Left to right, white background, three panels.

1. **Problem** (schematic, no numbers). City leader with a zone-charge dial above three to six carrier depots on a zone grid; each carrier has routes with a probability box on every arc. Caption: "Each carrier solves an NP-hard routing problem; carriers compete and congest; the city sets charges." The zone grid can be cropped from one panel of `figures/overview_equilibria_light.png`.
2. **Methods** (three short text lines): BRL, exact best responses under probability boxes with unknown dependence; DIP, charges from best-response cuts; ARP, charges from observed zone totals only.
3. **Evidence**: `figures/arp_calls_vs_gain.png` (gain relative to the best exact grid point against routing-oracle calls, log scale; grid, DIP, ARP and tariff variants), with one line: "Levels depend on how carriers plan; orderings and policy directions do not." Caption: "Leader methods need a fraction of the grid's routing calls; gains above 100% partly reflect zone-specific charges."

Notes for the author
- Keep the log-scale call axis; it is the main message of the figure.
- Do not use the broad-objective panels (shut-down optima are an artifact of a proxy).
- Check image size and file-type rules in the Guide for Authors of the chosen journal.
