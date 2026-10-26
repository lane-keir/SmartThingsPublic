"""Generate realistic sample extracts that mimic each original source system.

The files are shaped like raw exports (timestamps, system IDs, statuses) rather
than pre-aggregated KPIs, so the Power Query layer does the same work it will do
against the live systems. Re-run to refresh the dates so they end yesterday:

    python3 tools/generate_sample_data.py [days]
"""
import csv
import os
import random
import sys
from datetime import date, datetime, time, timedelta

random.seed(42)
DAYS = int(sys.argv[1]) if len(sys.argv) > 1 else 60
OUT = os.path.join(os.path.dirname(__file__), "..", "sample-data")
END = date.today() - timedelta(days=1)
START = END - timedelta(days=DAYS - 1)
AREAS = ["Machining", "Heat Treat", "Assembly", "Test"]
SHIFT_STARTS = {"Early": 6, "Late": 14, "Night": 22}


def days():
    d = START
    while d <= END:
        yield d
        d += timedelta(days=1)


def is_working(d):
    return d.weekday() < 5


def stamp(d, shift):
    """Random timestamp inside a shift; night shift runs past midnight."""
    start = datetime.combine(d, time(SHIFT_STARTS[shift]))
    return start + timedelta(minutes=random.randint(0, 479))


def fmt(dt):
    return dt.strftime("%Y-%m-%d %H:%M")


def write(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"{name}: {len(rows)} rows")


def pick_shift():
    return random.choices(list(SHIFT_STARTS), weights=[5, 4, 2])[0]


# ---------------------------------------------------------------- EHS system
ehs, n = [], 1000
ehs_rates = {"Accident": 0.015, "Incident": 0.06, "Near Miss": 0.45, "Hazard": 0.7}
ehs_text = {
    "Accident": ["Hand laceration on swarf - lost time", "Strain lifting fixture - lost time"],
    "Incident": ["Minor cut, first aid given", "Forklift contact with racking", "Coolant splash to eye, rinsed"],
    "Near Miss": ["Pallet overhanging walkway", "Guard interlock bypass found", "Trailing cable at cell 4", "Load swung near operator"],
    "Hazard": ["Oil spill at machine", "Damaged pallet in aisle", "Missing floor marking", "Blocked fire exit", "Frayed sling"],
}
for d in days():
    for area in AREAS:
        for etype, rate in ehs_rates.items():
            rate = rate if is_working(d) else rate * 0.3
            while random.random() < rate:
                shift = pick_shift()
                ts = stamp(d, shift)
                contained = ""
                status = "Open"
                if etype == "Hazard" and random.random() < 0.85:
                    contained = fmt(ts + timedelta(minutes=random.randint(10, 300)))
                    status = "Contained"
                elif etype != "Hazard" and d < END - timedelta(days=3):
                    status = "Closed"
                ehs.append([f"EHS-{n}", fmt(ts), area, etype, status, contained,
                            random.choice(ehs_text[etype]), random.choice(["J.Smith", "A.Patel", "M.Jones", "K.Lee"])])
                n += 1
                rate *= 0.5
write("ehs_events.csv", ["EventID", "EventDateTime", "Area", "EventType", "Status", "ContainedDateTime", "Description", "ReportedBy"], ehs)

# ---------------------------------------------------------------- QMS
qms, n = [], 5000
qms_rates = {"Product Safety Report": 0.01, "Escape": 0.03, "Concession": 0.08, "NCR": 0.35}
for d in days():
    if not is_working(d):
        continue
    for area in AREAS:
        for rtype, rate in qms_rates.items():
            while random.random() < rate:
                shift = pick_shift()
                qms.append([f"{ {'Product Safety Report': 'PSR', 'Escape': 'ESC', 'Concession': 'CON', 'NCR': 'NCR'}[rtype]}-{n}",
                            rtype, fmt(stamp(d, shift)), area, f"PN-{random.randint(1000, 1099)}",
                            random.choice(["Dimension out of tolerance", "Surface finish", "Missing fastener", "Wrong label", "Hardness low"]),
                            "Open" if d > END - timedelta(days=5) else "Closed"])
                n += 1
                rate *= 0.4
write("qms_records.csv", ["RecordID", "RecordType", "RaisedDateTime", "Area", "PartNumber", "Description", "Status"], qms)

# ---------------------------------------------------------------- Test / MES
tests, sn = [], 200000
stage_area = {"Verify": "Assembly", "System": "Test", "Final": "Test"}
stage_fail = {"Verify": 0.04, "System": 0.06, "Final": 0.03}
for d in days():
    if not is_working(d):
        continue
    bad_day = random.random() < 0.15
    for _ in range(random.randint(25, 40)):
        sn += 1
        shift = pick_shift()
        ts = stamp(d, shift)
        for stage in ["Verify", "System", "Final"]:
            attempt = 1
            p_fail = stage_fail[stage] * (2.5 if bad_day else 1)
            while True:
                result = "FAIL" if random.random() < p_fail and attempt < 3 else "PASS"
                tests.append([f"SN{sn}", stage, fmt(ts), stage_area[stage], attempt, result])
                ts += timedelta(minutes=random.randint(5, 40))
                if result == "PASS":
                    break
                attempt += 1
            ts += timedelta(minutes=random.randint(10, 60))
write("test_results.csv", ["SerialNumber", "TestStage", "TestDateTime", "Area", "AttemptNo", "Result"], tests)

# ---------------------------------------------------------------- Thermal logger
thermal, n = [], 1
for d in days():
    while random.random() < (0.12 if is_working(d) else 0.04):
        shift = pick_shift()
        sp = random.choice([180, 420, 860])
        thermal.append([f"TD-{n}", random.choice(["FURN-01", "FURN-02", "OVEN-03"]), fmt(stamp(d, shift)), "Heat Treat",
                        random.choice(["Soak temperature", "Ramp rate", "Quench delay"]), sp,
                        round(sp * random.uniform(1.02, 1.08), 1), random.randint(2, 25)])
        n += 1
write("thermal_deviations.csv", ["DeviationID", "EquipmentID", "StartDateTime", "Area", "Parameter", "Setpoint", "Actual", "DurationMins"], thermal)

# ---------------------------------------------------------------- Andon
andon, n = [], 1
for d in days():
    if not is_working(d):
        continue
    for area in AREAS:
        for _ in range(random.randint(0, 5)):
            shift = pick_shift()
            ts = stamp(d, shift)
            wait = max(1, int(random.expovariate(1 / (12 if shift == "Night" else 6))))
            andon.append([f"AND-{n}", fmt(ts), area, f"ST-{random.randint(1, 12):02d}",
                          random.choice(["Material shortage", "Quality query", "Machine fault", "Tooling", "Engineering support"]),
                          fmt(ts + timedelta(minutes=wait))])
            n += 1
write("andon_calls.csv", ["CallID", "CallDateTime", "Area", "Station", "Reason", "ResponseDateTime"], andon)

# ---------------------------------------------------------------- ERP scrap & rework
erp, n = [], 900000
for d in days():
    if not is_working(d):
        continue
    for area in AREAS:
        for shift in SHIFT_STARTS:
            if random.random() < 0.55:
                qty = random.randint(1, 6)
                erp.append([n, d.isoformat(), area, shift, "SCRAP", f"PN-{random.randint(1000, 1099)}", qty,
                            round(qty * random.uniform(15, 90), 2), "", random.choice(["S01 Damage", "S02 Dimensional", "S03 Material"])])
                n += 1
            if random.random() < 0.6:
                erp.append([n, d.isoformat(), area, shift, "REWORK", f"PN-{random.randint(1000, 1099)}", random.randint(1, 4),
                            "", round(random.uniform(0.25, 3.5), 2), random.choice(["R01 Re-machine", "R02 Re-test", "R03 Re-assemble"])])
                n += 1
write("erp_scrap_rework.csv", ["TransactionID", "PostingDate", "Area", "Shift", "TransType", "PartNumber", "Qty", "Value_GBP", "Hours", "ReasonCode"], erp)

# ---------------------------------------------------------------- Visits register (includes the next 14 days)
visits, n = [], 1
d = START
while d <= END + timedelta(days=14):
    if is_working(d) and random.random() < 0.2:
        visits.append([f"V-{n}", d.isoformat(), random.choice(["Customer A", "Customer B", "Regulator", "Customer C"]),
                       random.choice(AREAS), random.choice(["Source inspection", "Audit", "Programme review", "First article"]),
                       random.choice(["Site Lead", "Quality Manager", "Programme Manager"])])
        n += 1
    d += timedelta(days=1)
write("customer_visits.csv", ["VisitID", "VisitDate", "Customer", "Area", "Purpose", "Host"], visits)

# ---------------------------------------------------------------- Tier 1 action log
actions = []
issues = [("Safety", "Repeat oil spills at Machining cell 3", "Fit drip tray and add to TPM check"),
          ("Quality", "Escape: missing fastener at customer", "Add torque-count poka-yoke at ST-07"),
          ("Delivery", "RFT System below target 3 days", "Fixture calibration and 5-why on top failure mode"),
          ("Delivery", "Night shift stop call waits >20 min", "Add team leader rota for night andon response"),
          ("Cost", "Scrap spike on PN-1042", "Check material cert and first-off approval"),
          ("People", "Customer A source inspection Thursday", "5S audit of Test area Wednesday PM"),
          ("Quality", "Concession trend on hardness", "Review furnace FURN-02 profile with Process Eng"),
          ("Safety", "Near miss: load swung near operator", "Re-brief lifting plan; exclusion zone marking")]
for i, (pillar, issue, cm) in enumerate(issues, 1):
    raised = END - timedelta(days=random.randint(0, 12))
    due = raised + timedelta(days=random.randint(2, 10))
    status = random.choice(["Open", "Open", "In Progress", "Closed"])
    actions.append([f"ACT-{i:03d}", raised.isoformat(), pillar, random.choice(AREAS), issue, cm,
                    random.choice(["J.Smith", "A.Patel", "M.Jones", "K.Lee"]), due.isoformat(), status])
write("actions.csv", ["ActionID", "DateRaised", "Pillar", "Area", "Issue", "Countermeasure", "Owner", "DueDate", "Status"], actions)
