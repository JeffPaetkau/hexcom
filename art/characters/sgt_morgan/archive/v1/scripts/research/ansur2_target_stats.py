#!/usr/bin/env python3 -I
"""Compute ANSUR II male statistics for the Sgt. Morgan target body.

Usage: python3 -I ansur2_target_stats.py <ANSUR_II_MALE_Public.csv> <out.md>

Filters males with stature 1830-1870 mm and weight 82-85 kg (ANSUR 'weightkg'
column is actually in hectograms per openlab.psu.edu/ansur2), then prints
n, mean, median for all 93 measurements, alongside full-sample 5/50/95th pct.
Also writes a tight-filter and a looser-filter (stature only) table.
"""
import csv, sys, statistics as st
import numpy as np

src, out = sys.argv[1], sys.argv[2]
rows = list(csv.DictReader(open(src, encoding="latin-1")))
cols = [c for c in rows[0].keys()]
# first 94 columns are numeric measurements (subjectid + 93 measures)
num_cols = []
for c in cols:
    try:
        float(rows[0][c]); num_cols.append(c)
    except ValueError:
        pass
num_cols = [c for c in num_cols if c not in ("subjectid", "SubjectId", "SubjectNumericRace", "DODRace", "Age", "Heightin", "Weightlbs")]

def col(c, subset):
    return np.array([float(r[c]) for r in subset])

stature = col("stature", rows); wt = col("weightkg", rows)  # hectograms
tight = [r for r in rows if 1830 <= float(r["stature"]) <= 1870 and 820 <= float(r["weightkg"]) <= 850]
loose = [r for r in rows if 1830 <= float(r["stature"]) <= 1870 and 780 <= float(r["weightkg"]) <= 900]
stat_only = [r for r in rows if 1830 <= float(r["stature"]) <= 1870]

lines = []
lines.append(f"ANSUR II MALE public dataset: n={len(rows)} subjects, {len(num_cols)} numeric measures. Units: mm (weightkg = hectograms).")
lines.append(f"Full sample stature mean {stature.mean():.0f} mm, median {np.median(stature):.0f}; weight mean {wt.mean()/10:.1f} kg.")
lines.append(f"Tight filter (stature 1830-1870 mm AND weight 82.0-85.0 kg): n={len(tight)}")
lines.append(f"Loose filter (stature 1830-1870 mm AND weight 78-90 kg): n={len(loose)}")
lines.append(f"Stature-only filter (1830-1870 mm): n={len(stat_only)}")
lines.append("")
lines.append("| Measure | Tight mean | Tight median | Loose mean | Stature-only mean | Full 5th | Full 50th | Full 95th |")
lines.append("|---|---|---|---|---|---|---|---|")
for c in num_cols:
    a = col(c, rows); t = col(c, tight); l = col(c, loose); s = col(c, stat_only)
    p5, p50, p95 = np.percentile(a, [5, 50, 95])
    lines.append(f"| {c} | {t.mean():.0f} | {np.median(t):.0f} | {l.mean():.0f} | {s.mean():.0f} | {p5:.0f} | {p50:.0f} | {p95:.0f} |")
open(out, "w").write("\n".join(lines) + "\n")
print("\n".join(lines[:8]))
print(f"... wrote {out} with {len(num_cols)} rows")
