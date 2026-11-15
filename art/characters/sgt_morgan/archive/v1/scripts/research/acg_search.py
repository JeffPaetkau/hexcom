#!/usr/bin/env python3
"""Query ambientCG API v2 for several keywords; print compact candidate list.
Usage: python3 -I acg_search.py <out_json> <query1> <query2> ...
"""
import json, sys, urllib.request, urllib.parse, time

out = sys.argv[1]
queries = sys.argv[2:]
res = {}
for q in queries:
    url = ("https://ambientcg.com/api/v2/full_json?"
           + urllib.parse.urlencode({"q": q, "type": "Material", "limit": 40,
                                     "sort": "Popular",
                                     "include": "downloadData,tagData,dimensionsData"}))
    t0 = time.time()
    with urllib.request.urlopen(url, timeout=60) as r:
        d = json.load(r)
    dt = time.time() - t0
    rows = []
    for a in d.get("foundAssets", []):
        dl = a.get("downloadFolders", {}).get("default", {}).get("downloadFiletypeCategories", {}).get("zip", {}).get("downloads", [])
        two_k = [x for x in dl if x["attribute"] == "2K-JPG"]
        rows.append({
            "id": a["assetId"], "name": a.get("displayName"), "cat": a.get("displayCategory"),
            "method": a.get("creationMethod"), "tags": a.get("tags", []),
            "dimXY_cm": [a.get("dimensionX"), a.get("dimensionY")],
            "pop": round(a.get("popularityScore", 0), 1), "dl": a.get("downloadCount"),
            "zip2k": two_k[0]["downloadLink"] if two_k else None,
            "zip2k_size_mb": round(two_k[0]["size"] / 1e6, 1) if two_k else None,
            "url": a.get("shortLink"),
        })
    res[q] = {"n": d.get("numberOfResults"), "t_s": round(dt, 2), "rows": rows}
    print(f"\n=== {q}: {d.get('numberOfResults')} results ({dt:.1f}s)")
    for r_ in rows[:25]:
        print(f"  {r_['id']:<22} {str(r_['cat']):<14} {r_['method']:<22} pop={r_['pop']:<6} "
              f"dim={r_['dimXY_cm']} tags={','.join(r_['tags'][:8])}")
json.dump(res, open(out, "w"), indent=1)
