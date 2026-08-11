#!/usr/bin/env python3
"""
Regenerate the impact page's DATA blob from the TRY Rugby master sheet.

Reads a CSV export of the sheet (from --csv PATH or the SHEET_CSV_URL env var),
strips PII to a hard column allowlist, applies the derivation rules, merges the
static geo data (scripts/geo.json), and rewrites the `const DATA = {...};` blob
in impact/index.html.

Deterministic: same input -> same output, so the scheduled workflow only commits
when the underlying data actually changed.
"""
import csv, io, json, os, re, sys, urllib.request
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(ROOT, "impact", "index.html")
GEO  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "geo.json")

# --- PII allowlist: only these columns are ever read. Contact name/email/phone
#     columns in the sheet are never touched. ---
SAFE_COLUMNS = {
    "School Name", "School Class", "Status", "Status 2025/2026", "Type",
    "City", "Catchment", "School Enrollment 25/26", "School Enrollment",
    "Status 2024/2025", "Status 2023/2024", "Lead",
}

# Type -> level band (authoritative map; heuristic fallback for unseen types).
TBMAP = {
    "3-6":"Elementary","5-12":"High","5-6 School":"Middle","6-12":"High",
    "6-8 School":"Middle","7-8":"Middle","7-8 School":"Middle",
    "Alternative School":"High","Community Center":"Community",
    "Elementary School":"Elementary","High School":"High",
    "Intermediate School":"Elementary","K-12 School":"K-12","K-2":"Elementary",
    "K-4 School":"Elementary","K-5":"Elementary","K-6":"Elementary",
    "K-8":"K-12","K-8 School":"K-12","K-9":"K-12","Middle School":"Middle",
    "Primary School":"Elementary","Private K-12":"K-12","Private K-8":"K-12",
}

# City-name fixes so mis-spellings in the sheet still match town coordinates.
CITY_ALIAS = {
    "cutbank":"cut bank","harlotown":"harlowton","brodus":"broadus",
    "willsaw":"wilsall","alree":"alder","sims":"simms",
}

CLASSES = {"AA","A","B","C"}
REACHED = {"try","rib","scheduled"}


def norm(x):
    return re.sub(r"\s+", " ", (x or "").strip()).lower().rstrip(".")


def band(t):
    if t in TBMAP:
        return TBMAP[t]
    s = t.lower()
    if any(k in s for k in ("k-12","k-8","k-9","k12")): return "K-12"
    if "communit" in s: return "Community"
    if any(k in s for k in ("high","9-12","6-12","5-12","7-12","alternative")): return "High"
    if any(k in s for k in ("middle","7-8","6-8","5-6","junior","jr")): return "Middle"
    return "Elementary"


def stage(status, s2026):
    if status == "Delivered - TRY Rugby": return "try"
    if status == "Delivered - Rugby In A Box": return "rib"
    if s2026 == "Try Rugby - Scheduled": return "scheduled"
    # Pipeline = In Discussion (main status) OR Rugby In A Box - Offered (2025/26).
    # Pursue and Prospect are intentionally NOT pipeline.
    if status == "In Discussion" or s2026 == "Rugby In A Box - Offered": return "pipeline"
    return "none"


def to_int(v):
    v = re.sub(r"[^\d]", "", str(v or ""))
    return int(v) if v else 0


def load_rows(csv_text):
    r = csv.DictReader(io.StringIO(csv_text))
    r.fieldnames = [ (h or "").strip() for h in (r.fieldnames or []) ]
    out = []
    for row in r:
        # keep only allowlisted columns — PII never enters the pipeline
        out.append({k.strip(): (v or "").strip()
                    for k, v in row.items() if k and k.strip() in SAFE_COLUMNS})
    return out


def build(rows, geo):
    cert = set(geo["certified"])
    coords = geo["coords"]
    ncoords = {norm(c): v for c, v in coords.items()}

    schools = []
    for r in rows:
        status = r.get("Status", "")
        if status == "No longer a School":
            continue
        name = r.get("School Name", "").strip()
        if not name:
            continue
        cat = r.get("Catchment", "")
        k = cat if cat in cert else "No Catchment"
        cls = r.get("School Class", "")
        typ = r.get("Type", "").replace("–", "-").replace("—", "-")  # en/em dash -> hyphen
        schools.append({
            "n": name,
            "c": r.get("City", ""),
            "k": k, "k0": k,
            "b": band(typ),
            "t": typ,
            "s": stage(status, r.get("Status 2025/2026", "")),
            "e": to_int(r.get("School Enrollment 25/26") or r.get("School Enrollment")),
            "l": r.get("Lead", ""),
            "y3": r.get("Status 2023/2024", ""),
            "y4": r.get("Status 2024/2025", ""),
            "y5": r.get("Status 2025/2026", ""),
            "r": 0,
            "cls": cls if cls in CLASSES else "",
        })

    # rank by enrollment desc, name for stable ties
    for i, s in enumerate(sorted(schools, key=lambda s: (-s["e"], s["n"])), 1):
        s["r"] = i

    # recompute towns from schools, keeping coordinates from geo
    agg = defaultdict(lambda: {"n": 0, "e": 0, "d": 0, "de": 0})
    for s in schools:
        a = agg[s["c"]]
        a["n"] += 1; a["e"] += s["e"]
        if s["s"] in REACHED:
            a["d"] += 1; a["de"] += s["e"]
    towns = []
    for c, a in agg.items():
        ll = coords.get(c) or ncoords.get(norm(c)) or ncoords.get(norm(CITY_ALIAS.get(norm(c), "")))
        if not ll:
            continue
        towns.append({"c": c, "lat": ll[0], "lon": ll[1],
                      "n": a["n"], "e": a["e"], "d": a["d"], "de": a["de"]})
    towns.sort(key=lambda t: (-t["e"], t["c"]))

    return {"certified": geo["certified"], "schools": schools,
            "towns": towns, "outline": geo["outline"]}


def get_csv_text(args):
    for i, a in enumerate(args):
        if a == "--csv" and i + 1 < len(args):
            return open(args[i + 1], encoding="utf-8-sig").read()
    url = os.environ.get("SHEET_CSV_URL")
    if not url:
        sys.exit("No CSV source: pass --csv PATH or set SHEET_CSV_URL")
    with urllib.request.urlopen(url, timeout=60) as resp:
        return resp.read().decode("utf-8-sig")


def main():
    rows = load_rows(get_csv_text(sys.argv[1:]))
    geo = json.load(open(GEO))
    data = build(rows, geo)
    if len(data["schools"]) < 100:
        sys.exit("Refusing to write: only %d schools parsed (bad CSV?)" % len(data["schools"]))

    html = open(HTML, encoding="utf-8").read()
    m = re.search(r"const DATA = (\{.*?\});", html, re.S)
    if not m:
        sys.exit("Could not find DATA blob in impact/index.html")
    blob = "const DATA = " + json.dumps(data, separators=(",", ":"), ensure_ascii=False) + ";"
    new_html = html[:m.start()] + blob + html[m.end():]
    if new_html != html:
        open(HTML, "w", encoding="utf-8").write(new_html)
        print("DATA updated: %d schools" % len(data["schools"]))
    else:
        print("No change.")

    from collections import Counter
    print("stages:", dict(Counter(s["s"] for s in data["schools"])),
          "| towns:", len(data["towns"]))


if __name__ == "__main__":
    main()
