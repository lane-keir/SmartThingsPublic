"""Build mockup/sqdcp-board.html from the sample extracts.

Re-implements the Power Query + DAX rules (shift mapping, report day, targets,
RAG status, worst-KPI pillar roll-up) so the mockup shows the numbers Power BI
should produce from the same files - useful for checking the model once built.

    python3 tools/build_mockup.py
"""
import csv
import html
import os
from collections import defaultdict
from datetime import date, datetime, timedelta

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATA = os.path.join(ROOT, "sample-data")
TODAY = date.today()
COLOURS = {"Green": "#2E7D32", "Amber": "#F9A825", "Red": "#C62828", "Info": "#1565C0", "No Data": "#BDBDBD"}
RANK = {"Red": 3, "Amber": 2, "Green": 1, "Info": 0}


def rows(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return list(csv.DictReader(f))


def ts(s):
    return datetime.strptime(s, "%Y-%m-%d %H:%M") if s else None


def shift_of(dt):  # mirrors fnShift
    h = dt.hour
    shift = "Early" if 6 <= h < 14 else "Late" if 14 <= h < 22 else "Night"
    return (dt.date() - timedelta(days=1) if h < 6 else dt.date()), shift


# ---------------------------------------------------------------- FactKPI (value, denominator) per KPI per day
fact = defaultdict(lambda: [0.0, 0.0])


def add(day, code, value, den=0.0):
    fact[(day, code)][0] += value
    fact[(day, code)][1] += den


for r in rows("ehs_events.csv"):
    code = {"Accident": "S01", "Incident": "S02", "Near Miss": "S03", "Hazard": "S04"}[r["EventType"]]
    if code == "S04" and not (r["Status"] == "Contained" or r["ContainedDateTime"]):
        continue
    add(shift_of(ts(r["EventDateTime"]))[0], code, 1)
for r in rows("qms_records.csv"):
    code = {"Product Safety Report": "Q01", "Escape": "Q02", "Concession": "Q03", "NCR": "Q04"}[r["RecordType"]]
    add(shift_of(ts(r["RaisedDateTime"]))[0], code, 1)
for r in rows("test_results.csv"):
    if r["AttemptNo"] == "1":
        code = {"Final": "D01", "Verify": "D02", "System": "D03"}[r["TestStage"]]
        add(shift_of(ts(r["TestDateTime"]))[0], code, 1 if r["Result"] == "PASS" else 0, 1)
for r in rows("thermal_deviations.csv"):
    add(shift_of(ts(r["StartDateTime"]))[0], "D04", 1)
for r in rows("andon_calls.csv"):
    start, resp = ts(r["CallDateTime"]), ts(r["ResponseDateTime"]) or datetime.now()
    add(shift_of(start)[0], "D05", (resp - start).total_seconds() / 60, 1)
for r in rows("erp_scrap_rework.csv"):
    d = date.fromisoformat(r["PostingDate"])
    if r["TransType"] == "SCRAP":
        add(d, "C01", float(r["Value_GBP"]))
    else:
        add(d, "C02", float(r["Hours"]))
for r in rows("customer_visits.csv"):
    add(date.fromisoformat(r["VisitDate"]), "P01", 1)

kpis = rows("kpi_master.csv")
for k in kpis:
    k["DailyTarget"] = float(k["DailyTarget"]) if k["DailyTarget"] else None
    k["AmberTolerance"] = float(k["AmberTolerance"]) if k["AmberTolerance"] else 0.0
pillars = []
for k in kpis:
    if k["Pillar"] not in pillars:
        pillars.append(k["Pillar"])


# ---------------------------------------------------------------- measures
def actual(k, days):
    days = [d for d in days if d <= TODAY]
    if not days:
        return None
    num = sum(fact[(d, k["KPI_Code"])][0] for d in days if (d, k["KPI_Code"]) in fact)
    den = sum(fact[(d, k["KPI_Code"])][1] for d in days if (d, k["KPI_Code"]) in fact)
    if k["Aggregation"] == "Ratio":
        return num / den if den else None
    return num


def status(k, days):
    a = actual(k, days)
    n = len([d for d in days if d <= TODAY])
    if n == 0:
        return None
    if a is None:
        return "No Data"
    t = k["DailyTarget"]
    if k["Polarity"] == "Info" or t is None:
        return "Info"
    scale = n if k["Aggregation"] == "Sum" else 1
    t, tol = t * scale, k["AmberTolerance"] * scale
    if k["Polarity"] == "LowerIsBetter":
        return "Green" if a <= t else "Amber" if a <= t + tol else "Red"
    return "Green" if a >= t else "Amber" if a >= t - tol else "Red"


def pillar_status(p, days):
    ranks = [RANK[s] for k in kpis if k["Pillar"] == p for s in [status(k, days)] if s in RANK]
    return {3: "Red", 2: "Amber", 1: "Green", 0: "Info"}[max(ranks)] if ranks else None


def fmt(k, v):
    if v is None:
        return "–"
    u = k["Unit"]
    return f"{v:.0%}" if u == "%" else f"£{v:,.0f}" if u == "GBP" else f"{v:,.1f}" if u == "Hours" else f"{v:,.0f}"


def fmt_target(k):
    t = k["DailyTarget"]
    if t is None:
        return "track"
    op = "≥" if k["Polarity"] == "HigherIsBetter" else "≤"
    return f"{op} {fmt(k, t)}/day" if k["Aggregation"] == "Sum" else f"{op} {fmt(k, t)}"


# report period: mirrors DimDate[IsReportDay]
prev_working = max(TODAY - timedelta(days=i) for i in range(1, 8) if (TODAY - timedelta(days=i)).weekday() < 5)
report_days = [prev_working + timedelta(days=i) for i in range((TODAY - prev_working).days)]
last7 = [TODAY - timedelta(days=i) for i in range(1, 8)]
prior7 = [TODAY - timedelta(days=i) for i in range(8, 15)]
month_start = report_days[-1].replace(day=1)
month_days = [month_start + timedelta(days=i) for i in range(31) if (month_start + timedelta(days=i)).month == month_start.month]
mtd = [d for d in month_days if d <= report_days[-1]]


def trend(k):
    c, p = actual(k, last7), actual(k, prior7)
    if c is None or p is None or c == p:
        return "→", "#616161"
    arrow = "↑" if c > p else "↓"
    if k["Polarity"] == "Info":
        return arrow, "#616161"
    good = (c < p) == (k["Polarity"] == "LowerIsBetter")
    return arrow, "#2E7D32" if good else "#C62828"


# ---------------------------------------------------------------- HTML
e = html.escape
period = (report_days[0].strftime("%A %d %b %Y") if len(report_days) == 1
          else f"{report_days[0]:%a %d %b} – {report_days[-1]:%a %d %b %Y}")

cols_html = []
for p in pillars:
    ps = pillar_status(p, report_days) or "No Data"
    tiles = []
    for k in [k for k in kpis if k["Pillar"] == p]:
        s = status(k, report_days) or "No Data"
        arrow, acol = trend(k)
        tiles.append(f"""
        <div class="tile" style="border-left-color:{COLOURS[s]}">
          <div class="kname">{e(k['KPI_Name'])}</div>
          <div class="kval">{e(fmt(k, actual(k, report_days)))}</div>
          <div class="kmeta"><span>{e(fmt_target(k))}</span>
            <span>MTD {e(fmt(k, actual(k, mtd)))}</span>
            <span class="arrow" style="color:{acol}" title="7 days vs previous 7">{arrow}</span></div>
          <div class="chip" style="background:{COLOURS[s]}">{e(s)}</div>
        </div>""")
    cal = []
    for d in month_days:
        st = pillar_status(p, [d]) if d <= TODAY - timedelta(days=1) else None
        bg = COLOURS[st] if st else "transparent"
        cls = "day" + ("" if st else " future")
        cal.append(f'<div class="{cls}" style="background:{bg}" title="{d:%a %d %b}: {st or "-"}">{d.day}</div>')
    cols_html.append(f"""
    <section class="pillar">
      <header style="background:{COLOURS[ps]}"><span class="letter">{p[0]}</span>
        <span class="pname">{e(p)}</span><span class="pstat">{e(ps)}</span></header>
      {''.join(tiles)}
      <div class="calhead">{month_start:%B} letter calendar</div>
      <div class="cal">{''.join(cal)}</div>
    </section>""")

actions = rows("actions.csv")
act_html = "".join(
    f"<tr class='{'overdue' if a['Status'] != 'Closed' and date.fromisoformat(a['DueDate']) < TODAY else ''}'>"
    f"<td>{e(a['ActionID'])}</td><td>{e(a['Pillar'])}</td><td>{e(a['Area'])}</td><td>{e(a['Issue'])}</td>"
    f"<td>{e(a['Countermeasure'])}</td><td>{e(a['Owner'])}</td><td>{e(a['DueDate'])}</td><td>{e(a['Status'])}</td></tr>"
    for a in actions if a["Status"] != "Closed")
visits = [v for v in rows("customer_visits.csv") if TODAY <= date.fromisoformat(v["VisitDate"]) <= TODAY + timedelta(days=7)]
vis_html = "".join(f"<li><b>{e(v['VisitDate'])}</b> {e(v['Customer'])} – {e(v['Purpose'])} ({e(v['Area'])})</li>" for v in visits) or "<li>None planned</li>"

last_acc = max((d for (d, c) in fact if c == "S01" and d <= TODAY), default=None)
days_since = (TODAY - last_acc).days if last_acc else "–"

page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>SQDCP Start of Shift</title>
<style>
:root {{ --bg:#ECEFF1; --card:#FFFFFF; --ink:#212121; --muted:#616161; --line:#E0E0E0; --head:#263238; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#121417; --card:#1E2227; --ink:#ECEFF1; --muted:#A7B0B8; --line:#2C3238; --head:#0B0D0F; }} }}
:root[data-theme="dark"] {{ --bg:#121417; --card:#1E2227; --ink:#ECEFF1; --muted:#A7B0B8; --line:#2C3238; --head:#0B0D0F; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--ink); font:14px/1.35 "Segoe UI", system-ui, sans-serif; }}
.top {{ background:var(--head); color:#fff; padding:12px 16px; display:flex; flex-wrap:wrap; gap:8px 24px; align-items:baseline; }}
.top h1 {{ font-size:20px; margin:0; }} .top .sub {{ opacity:.8; }}
.banner {{ display:flex; flex-wrap:wrap; gap:12px; padding:12px 16px 0; }}
.stat {{ background:var(--card); border:1px solid var(--line); border-radius:6px; padding:8px 12px; min-width:150px; }}
.stat b {{ display:block; font-size:22px; }} .stat span {{ color:var(--muted); font-size:12px; }}
.grid {{ display:grid; grid-template-columns:repeat(5, minmax(0,1fr)); gap:12px; padding:12px 16px; }}
@media (max-width:1100px) {{ .grid {{ grid-template-columns:repeat(2, minmax(0,1fr)); }} }}
@media (max-width:600px) {{ .grid {{ grid-template-columns:1fr; }} }}
.pillar {{ background:var(--card); border:1px solid var(--line); border-radius:6px; overflow:hidden; }}
.pillar header {{ color:#fff; display:flex; align-items:center; gap:10px; padding:8px 12px; }}
.letter {{ font-size:28px; font-weight:700; width:34px; }} .pname {{ font-weight:600; flex:1; }} .pstat {{ font-size:12px; text-transform:uppercase; letter-spacing:.05em; }}
.tile {{ position:relative; border-left:6px solid; margin:8px; padding:6px 10px; background:var(--bg); border-radius:4px; }}
.kname {{ font-size:12px; color:var(--muted); }} .kval {{ font-size:26px; font-weight:600; }}
.kmeta {{ display:flex; gap:10px; font-size:11px; color:var(--muted); }} .arrow {{ font-weight:700; font-size:14px; margin-left:auto; }}
.chip {{ position:absolute; top:6px; right:8px; color:#fff; font-size:10px; padding:1px 6px; border-radius:8px; }}
.calhead {{ font-size:11px; color:var(--muted); padding:4px 10px 0; }}
.cal {{ display:grid; grid-template-columns:repeat(7, 1fr); gap:3px; padding:6px 10px 10px; }}
.day {{ color:#fff; font-size:10px; text-align:center; border-radius:3px; padding:3px 0; }}
.day.future {{ color:var(--muted); border:1px dashed var(--line); }}
.lower {{ display:grid; grid-template-columns:3fr 1fr; gap:12px; padding:0 16px 16px; }}
@media (max-width:900px) {{ .lower {{ grid-template-columns:1fr; }} }}
.panel {{ background:var(--card); border:1px solid var(--line); border-radius:6px; padding:10px 12px; overflow-x:auto; }}
.panel h2 {{ font-size:14px; margin:0 0 8px; }}
table {{ border-collapse:collapse; width:100%; font-size:12px; }} th, td {{ text-align:left; padding:4px 6px; border-bottom:1px solid var(--line); }}
tr.overdue td {{ color:#C62828; font-weight:600; }}
.note {{ color:var(--muted); font-size:11px; padding:0 16px 16px; }}
</style></head><body>
<div class="top"><h1>SQDCP – Start of Shift</h1><span class="sub">Reviewing: {e(period)}</span>
<span class="sub">All areas · All shifts</span><span class="sub" style="margin-left:auto">Mockup generated {datetime.now():%d %b %H:%M} from sample data</span></div>
<div class="banner">
  <div class="stat"><b>{days_since}</b><span>days since last accident</span></div>
  <div class="stat"><b>{sum(1 for a in actions if a['Status'] != 'Closed')}</b><span>open actions</span></div>
  <div class="stat"><b>{sum(1 for a in actions if a['Status'] != 'Closed' and date.fromisoformat(a['DueDate']) < TODAY)}</b><span>overdue actions</span></div>
  <div class="stat"><b>{len(visits)}</b><span>customer visits next 7 days</span></div>
</div>
<div class="grid">{''.join(cols_html)}</div>
<div class="lower">
  <div class="panel"><h2>Open actions (Tier 1)</h2><table><thead><tr><th>ID</th><th>Pillar</th><th>Area</th><th>Issue</th><th>Countermeasure</th><th>Owner</th><th>Due</th><th>Status</th></tr></thead><tbody>{act_html}</tbody></table></div>
  <div class="panel"><h2>Coming to site</h2><ul>{vis_html}</ul></div>
</div>
<div class="note">Layout mockup of Page 1 of the Power BI report. Tile border = status vs target for the review period; arrow = last 7 days vs previous 7 (green = improving).
Calendar cells = worst KPI status in the pillar for each day. Blue = tracked, no target (leading indicators).</div>
</body></html>"""

os.makedirs(os.path.join(ROOT, "mockup"), exist_ok=True)
with open(os.path.join(ROOT, "mockup", "sqdcp-board.html"), "w", encoding="utf-8") as f:
    f.write(page)
print("Report days:", report_days)
for k in kpis:
    print(f"  {k['KPI_Code']} {k['KPI_Name']:<24} {fmt(k, actual(k, report_days)):>8}  {status(k, report_days)}")
