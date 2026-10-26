"""Markdown tables of the ten-seed study (results/tables_seeds10.md) from results/summary_seeds10_ci.csv and seeds10_conclusions.csv."""
import numpy as np
import pandas as pd

from common import RES
from summarize_seeds10 import CITIES, FULL

HEAD = [("gain_congestion_only_pct", "congestion-only gain (% of |SC|)", "{:.2f}"), ("gain_delivery_only_pct", "delivery-only gain (%)", "{:.1f}"),
        ("gain_both_pct", "two-instrument gain (%)", "{:.1f}"), ("share_delivery", "delivery-only share of combined gain", "{:.2f}"),
        ("poa_zmc", "PoA (ZMC)", "{:.3f}"), ("poa_worst", "PoA (worst NE found)", "{:.3f}"), ("pos", "PoS", "{:.3f}"),
        ("priced_gap_pct", "priced gap, grid-best (% of W_SO)", "{:.2f}"), ("dip_gain_pct", "DIP gain (%)", "{:.1f}"),
        ("dip_vs_grid_gain", "DIP gain / grid-best gain", "{:.2f}"), ("dip_calls_share63", "DIP calls / 63-point grid calls", "{:.3f}"),
        ("arp_vs_dip_gain", "ARP flat gain / DIP gain", "{:.2f}"), ("mct_br_vs_dip_gain", "tariff + BR gain / DIP gain", "{:.2f}"),
        ("so_share_grid", "gain share vs social optimum: grid-best", "{:.2f}"), ("so_share_dip", "gain share vs social optimum: DIP", "{:.2f}"),
        ("so_share_arp", "gain share vs social optimum: ARP flat", "{:.2f}"), ("so_share_mct_br", "gain share vs social optimum: tariff + BR", "{:.2f}")]


def main():
    ci = pd.read_csv(RES / "summary_seeds10_ci.csv")
    out = []
    for col, label, fmt in HEAD:
        d = ci[ci.quantity == col].set_index("city")
        rows = []
        for c in CITIES:
            if c not in d.index:
                continue
            r = d.loc[c]
            star = "" if c in FULL or not (col.startswith(("gain", "share", "dip_vs", "so_share_grid", "priced")) or col == "dip_calls_share63") else " *"
            rows.append(f"| {c}{star} | {int(r.n_seeds)} | {fmt.format(r['mean'])} | {fmt.format(r.sd) if np.isfinite(r.sd) else 'n/a'} | "
                        f"[{fmt.format(r.ci_lo)}, {fmt.format(r.ci_hi)}] | {fmt.format(r['min'])}..{fmt.format(r['max'])} | {fmt.format(r.mean_3) if np.isfinite(r.mean_3) else 'n/a'} |")
        out += [f"**{label}**", "", "| city | n seeds | mean | sd | bootstrap 95% CI of the mean | min..max | mean of seeds 0-2 |", "|---|---|---|---|---|---|---|"] + rows + [""]
    (RES / "tables_seeds10.md").write_text("\n".join(out))
    # compact headline table: mean (sd) [CI]
    cols = [("poa_zmc", "PoA", "{:.2f}"), ("poa_worst", "PoA worst NE", "{:.2f}"), ("dip_gain_pct", "DIP gain %", "{:.1f}"),
            ("gain_congestion_only_pct", "cong.-only %", "{:.2f}"), ("gain_delivery_only_pct", "del.-only %", "{:.1f}"), ("gain_both_pct", "both %", "{:.1f}"),
            ("priced_gap_pct", "priced gap %", "{:.2f}")]
    hdr = "| city | n (E1/E3/DIP) | " + " | ".join(l for _, l, _ in cols) + " | n (grid) |"
    rows = [hdr, "|" + "---|" * (len(cols) + 3)]
    for c in CITIES:
        cells = []
        for col, _, fmt in cols:
            d = ci[(ci.city == c) & (ci.quantity == col)]
            if d.empty:
                cells.append("n/a")
                continue
            r = d.iloc[0]
            cells.append(f"{fmt.format(r['mean'])} ({fmt.format(r.sd)}) [{fmt.format(r.ci_lo)}, {fmt.format(r.ci_hi)}]")
        n1 = ci[(ci.city == c) & (ci.quantity == "poa_zmc")].n_seeds.iloc[0]
        ng = ci[(ci.city == c) & (ci.quantity == "gain_both_pct")].n_seeds.iloc[0]
        rows.append(f"| {c}{'' if c in FULL else ' *'} | {int(n1)} | " + " | ".join(cells) + f" | {int(ng)} |")
    (RES / "tables_seeds10_headline.md").write_text("\n".join(rows))
    con = pd.read_csv(RES / "seeds10_conclusions.csv")
    rows = ["| claim | city | metric | threshold | 3 seeds | all seeds | n | 95% CI | verdict | note |", "|---|---|---|---|---|---|---|---|---|---|"]
    f = lambda v: "n/a" if not np.isfinite(v) else f"{v:.3g}"
    for _, r in con.iterrows():
        rows.append(f"| {r.claim} | {r.city} | {r.metric} | {r.threshold} | {f(r.value_3seeds)} | {f(r.value_10seeds)} | {int(r.n_seeds)} | [{f(r.ci_lo)}, {f(r.ci_hi)}] | {r.verdict} | {r.note if isinstance(r.note, str) else ''} |")
    (RES / "tables_seeds10_conclusions.md").write_text("\n".join(rows))
    print("wrote tables")


if __name__ == "__main__":
    main()
