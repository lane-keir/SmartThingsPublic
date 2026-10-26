# 1. KPI definitions & standard work

The single source of truth for names, targets and RAG rules is
[`sample-data/kpi_master.csv`](../sample-data/kpi_master.csv) (load it as `DimKPI`).
Move it to an Excel table or Microsoft List owned by the Ops Manager so targets can
be changed without editing the report.

## RAG rules (applied in DAX, driven by the KPI master)

| Polarity | Green | Amber | Red |
|---|---|---|---|
| `LowerIsBetter` | Actual ≤ Target | Actual ≤ Target + Tolerance | Above that |
| `HigherIsBetter` | Actual ≥ Target | Actual ≥ Target − Tolerance | Below that |
| `Info` | Shown blue: tracked, no target | | |

* Count / £ / hours / minutes targets are **per day, site level**, and scale with the
  number of days in view (Monday's review of Fri–Sun is judged against 3× the daily target).
* Ratio (RFT) targets do not scale.
* A pillar's colour for a day is the **worst** status of its KPIs (one red KPI = red letter).

## The KPIs

| Code | KPI | Calculation | Polarity / default target | Source |
|---|---|---|---|---|
| **S01** | Accidents | Count of EHS events type *Accident* (beyond first aid / lost time) | Lower, 0 | EHS system |
| **S02** | Incidents | Count of *Incident* (first aid, property, environmental) | Lower, 0 | EHS system |
| **S03** | Near Misses | Count of *Near Miss* reports | Info: a leading indicator. More reporting is healthy, so never set a "≤" target | EHS system |
| **S04** | Hazards Contained | Count of *Hazard* records with status *Contained* | Info: a leading indicator | EHS system |
| **Q01** | Product Safety Reports | Count of PSR records raised | Lower, 0 | QMS |
| **Q02** | Escapes | Count of defects found past the point of manufacture | Lower, 0 | QMS |
| **Q03** | Concessions | Count of concessions raised | Lower, 0 (amber 1) | QMS |
| **Q04** | NCRs | Count of NCRs raised | Lower, 1 (amber 2) | QMS |
| **D01** | RFT Final | Units passing Final **on attempt 1** ÷ units presented to Final | Higher, 95 % (amber 92 %) | MES / test |
| **D02** | RFT Verify | Same at Verify | Higher, 95 % | MES / test |
| **D03** | RFT System | Same at System test | Higher, 95 % | MES / test |
| **D04** | Thermal Deviations | Count of excursions outside the validated thermal profile | Lower, 0 (amber 1) | Thermal logger |
| **D05** | Stop Call Waits | Total minutes from stop call to response (open calls count to refresh time) | Lower, 30 min/day (amber 45) | Andon |
| **C01** | Scrap | £ value of scrap transactions | Lower, £500/day (amber £750) | ERP |
| **C02** | Rework | Hours booked to rework | Lower, 8 h/day (amber 12) | ERP |
| **P01** | Customer Visits | Count of visits on the day; the board also shows **visits in the next 7 days** | Info | Visits register |

Supporting measures are also provided: days since last accident and incident, stop
calls (count), average and longest stop-call wait, units presented, rolled
throughput yield (Verify × System × Final), open and overdue actions.

## Time rules

* **Production day & shift.** Early 06–14, Late 14–22, Night 22–06. Night shift is
  credited to the day it **started**, so a 02:00 Tuesday event counts as Monday nights.
  The boundaries are set in `powerquery/03_fnShift.m` and `32_DimShift.m`.
* **Review period** (`DimDate[IsReportDay]`). Tuesday to Friday it is yesterday. On
  Monday it is Friday plus the weekend.

## Lean notes for the meeting

* Stick to a **15-minute, stand-up, same-time-same-place** Tier 1. Go round
  S → Q → D → C → P and only discuss **reds and ambers**. Greens get a nod.
* Every red needs an **owner, a countermeasure and a date** in the action log, not a
  discussion. Problem-solving happens after the meeting.
* Celebrate near misses and hazards contained. If those counts fall to zero, people
  have usually stopped reporting, not stopped having near misses.
* Review the action log every day and escalate overdue items to Tier 2.
* Review targets each quarter in the KPI master. When a KPI is green every day for
  a month, tighten it.
