# 2. Data sources: linking each KPI to its original system

## Architecture

```
 EHS system ──┐
 QMS ─────────┤                 Power Query                      Power BI model
 MES / test ──┤   stg_* queries (one per source, disable load)
 Thermal ─────┼──►  map to KPI codes + fnShift (day/shift)  ──►  FactKPI ─┬─ DimKPI  (targets)
 Andon ───────┤     fnToStandard (one schema + deep link)                 ├─ DimDate (review day)
 ERP ─────────┤                                                           ├─ DimShift
 Visits list ─┘                                                           └─ DimArea
 Tier1 Actions list ───────────────────────────────────────►  FactActions ───┘
```

Every staging query outputs the same columns:

| Column | Meaning |
|---|---|
| ProductionDate, Shift, Area | When and where (from `fnShift` if the source only has a timestamp) |
| KPI_Code | Joins to `DimKPI` |
| Value | 1 per event, or minutes, £, hours, or a 1/0 first-pass flag |
| Denominator | Units presented (RFT), 1 per stop call, otherwise blank |
| SourceSystem, SourceRef | System name and the record's own ID |
| SourceURL | **Deep link that opens the original record** (from `SourceLinks`) |
| Description, EventDateTime | Detail shown on drill-through |

Because each row keeps `SourceRef` and `SourceURL`, a team leader can click any
number on the board and open the actual NCR, EHS report, serial-number history or
andon call in the originating system.

## Source register (fill this in for your site)

| KPIs | Staging query | Sample extract | Recommended live connection | Gateway? | Owner |
|---|---|---|---|---|---|
| S01–S04 | `stg_Safety` | `ehs_events.csv` | EHS database view (SQL) or EHS API / OData export | SQL on-prem: yes | EHS Manager |
| Q01–Q04 | `stg_Quality` | `qms_records.csv` | QMS database view, or SharePoint list if NCRs are logged in Lists | SQL: yes. SharePoint: no | Quality Manager |
| D01–D03 | `stg_RFT` | `test_results.csv` | MES / test-station database: `AttemptNo = 1` rows only | yes | Production Manager |
| D04 | `stg_Thermal` | `thermal_deviations.csv` | Furnace SCADA / historian alarm table, or a scheduled CSV drop to SharePoint | usually yes | Process Engineer |
| D05 | `stg_StopCalls` | `andon_calls.csv` | Andon system database or export | yes | Production Manager |
| C01–C02 | `stg_Cost` | `erp_scrap_rework.csv` | ERP view or OData (SAP: CDS view / BW query) | depends | Finance / Ops |
| P01 | `stg_People` | `customer_visits.csv` | Microsoft List **Customer Visits** in the Ops Teams site | no | Site Lead |
| Actions | `FactActions` | `actions.csv` | Microsoft List **Tier1 Actions** in the Ops Teams site | no | Shift Leads |
| Targets | `DimKPI` | `kpi_master.csv` | Excel table in SharePoint, or a Microsoft List | no | Ops Manager |

## Moving one source from a CSV to a live connection

You can connect each pillar live on its own schedule. Until then the dashboard runs
on file drops.

1. Open the staging query, e.g. `stg_Safety`, in the Advanced Editor.
2. Replace **only** the `Source = fnReadCsv("…")` line with the live connector. A
   commented example is at the top of each staging query, for example:
   ```m
   Source = Sql.Database("ehs-sql01", "EHS",
       [Query = "SELECT EventID, EventDateTime, Area, EventType, Status, ContainedDateTime, Description
                 FROM dbo.vw_Events WHERE EventDateTime >= DATEADD(day,-400,GETDATE())"]),
   ```
3. If the live system uses different column names or codes, rename them or extend
   the `KpiMap` record in that query. The rest of the query stays as it is.
4. Put the system's record-view URL in `SourceLinks` so drill-through opens the record.
5. Refresh and check the result against the system's own report for one day.

Good practice:

* Ask IT for a **read-only database view** per system, not direct table access. Then
  a schema change in the source cannot break the dashboard silently.
* Filter at source to about 13 months (`DATEADD(day,-400,…)`) so refreshes stay fast
  and query folding works.
* For SharePoint lists, use `Implementation = "2.0"` (shown in the comments). It is
  much faster.
* Keep area names identical across systems, or add a mapping table. `DimArea` is
  built from whatever names the sources use.

## Data capture where no system exists

If a KPI is still on a whiteboard, such as hazards contained or customer visits,
create a **Microsoft List** in the Operations team. Add it as a Teams tab next to
the dashboard, or put a **Microsoft Forms** / **Power Apps** front end on it for
shopfloor tablets. Point the staging query at the list with `SharePoint.Tables(...)`.
The data then reaches the dashboard at the next refresh, with no re-keying.

## Refresh & gateway

* **Cloud sources** (SharePoint, Lists, Excel in SharePoint, cloud ERP): set the
  credentials in the Power BI service. No gateway is needed.
* **On-premises sources** (SQL, file shares, historians): install the **On-premises
  data gateway** (standard mode) on an always-on server. Add each data source to the
  gateway and map the dataset to it.
* **Schedule.** Pro licences allow up to 8 refreshes a day and Premium/Fabric up to
  48. Set one about **45 minutes before each shift meeting**, for example 05:15,
  13:15 and 21:15, plus others during the day as needed.
* Turn on refresh-failure emails to the dashboard owner. The report shows a "Latest
  source record" timestamp so a stale refresh is visible in the meeting.
* `pUtcOffsetHours`: the service runs in UTC. Set it to 1 during BST, or your site's
  offset, so "yesterday" rolls over at local midnight.
