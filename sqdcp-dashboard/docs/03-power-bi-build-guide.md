# 3. Power BI build guide

Allow about 2–3 hours for the first build. Everything below runs on the sample data,
so you can build and test the whole report before any live system is connected.

## Step 1: Get the files

Copy the `sqdcp-dashboard` folder to `C:\SQDCP\`, or upload `sample-data/` to a
SharePoint library such as `Operations > Shared Documents > SQDCP Data`.
To refresh the sample dates so they end yesterday, run
`python3 tools/generate_sample_data.py`.

## Step 2: Queries

In Power BI Desktop go to **Transform data**, then **New Source > Blank Query** for
each file in `powerquery/`, in number order. Open the **Advanced Editor**, paste the
file, and rename the query to the name in its header comment.

| Order | Query | Load? |
|---|---|---|
| 00 | `pSourceMode`, `pLocalFolder`, `pSharePointSite`, `pSharePointFolder`, `pUtcOffsetHours`: one parameter each (the file has five blocks) | – |
| 01–04 | `SourceLinks`, `fnReadCsv`, `fnShift`, `fnToStandard` | **Disable load** |
| 10–16 | `stg_Safety` … `stg_People` | **Disable load** |
| 20–21 | `FactKPI`, `FactActions` | Load |
| 30–34 | `DimKPI`, `DimDate`, `DimShift`, `DimArea`, `_Measures` | Load |

To disable load, right-click the query and untick **Enable load**. Set the
parameters to your folder or SharePoint path, then **Close & Apply**.

## Step 3: Model

**Model view > Manage relationships.** All relationships are many-to-one and single direction.

| From (many) | To (one) |
|---|---|
| `FactKPI[ProductionDate]` | `DimDate[Date]` |
| `FactKPI[KPI_Code]` | `DimKPI[KPI_Code]` |
| `FactKPI[Shift]` | `DimShift[Shift]` |
| `FactKPI[Area]` | `DimArea[Area]` |
| `FactActions[Area]` | `DimArea[Area]` |

Then:

* Select `DimDate` and choose **Mark as date table**, using `Date`.
* **Sort by column**:
  * `DimKPI[KPI_Name]` and `DimKPI[KPI_Label]` by `KPISort`
  * `DimKPI[Pillar]` by `PillarOrder`
  * `DimDate[Month]` by `MonthStart`
  * `DimDate[DayLabel]` by `Date`
  * `DimShift[Shift]` by `ShiftOrder`
* Set `FactKPI[SourceURL]` and `FactActions[SourceURL]` to **Data category: Web URL**.
* Hide the `_Measures[Placeholder]` column, the fact keys and the sort columns.

## Step 4: Measures

Open **DAX query view**, paste all of [`dax/measures.dax`](../dax/measures.dax) and
click **Run**. The test query returns one row per KPI for the review period, and
the values should match the mockup (`python3 tools/build_mockup.py` prints the
same numbers). Then click **Update model: Add new measures**. Finally set formats:
`RFT …` measures to `0.0%`, `Scrap £` to `£#,0`, `Rework Hrs` to `0.0`.

## Step 5: Theme

**View > Themes > Browse for themes** and choose `theme/sqdcp-theme.json`.
Use a 16:9 canvas, which suits a Teams tab and a shopfloor TV.

## Step 6: Pages

Use [`mockup/sqdcp-board.html`](../mockup/sqdcp-board.html) as the layout reference
for page 1.

### Page 1: Start of Shift (the meeting page)

* **Page filter:** `DimDate[IsReportDay] = True`. Monday then shows Fri–Sun
  automatically, and nobody touches a date slicer.
* **Header:** a card with `[Report Period Label]` and a small card with `[Data Freshness Label]`.
* **Slicers** (dropdown, top right): `DimArea[Area]`, `DimShift[Shift]`.
* **Banner cards:** `[Days Since Last Accident]`, `[Open Actions]`,
  `[Overdue Actions]` (red font if > 0), `[Customer Visits Next 7 Days]`.
* **Five pillar blocks** (S, Q, D, C, P), one **table** each:
  * Filter: `DimKPI[Pillar]` = that pillar.
  * Columns: `DimKPI[KPI_Name]`, `[KPI Display]` (Actual), `[KPI Target Display]`
    (Target), `[KPI Actual MTD]`, `[KPI Trend Arrow]`.
  * Conditional formatting:
    * `[KPI Display]` **Background colour**, *Format style: Field value*, `[KPI Status Colour]`.
    * The same column's **Font colour**, *Field value*, `[KPI Status Font Colour]`.
    * `[KPI Trend Arrow]` **Font colour**, *Field value*, `[KPI Trend Colour]`.
  * Above each table, add a card showing `[Pillar Status]`, filtered to the pillar,
    with the pillar name as its title, e.g. "S – Safety". Set its background to
    `[Pillar Status Colour]` under **Format > Effects > Background > fx**. The header
    then turns red, amber or green.
  * Cards are an alternative to tables. The **new card visual** can show many KPIs
    with reference labels for Target and MTD, and accent colours by `[KPI Status Colour]`.
* **Open actions table** from `FactActions`, filtered to `Status <> Closed` and
  sorted by DueDate. Row font colour comes from a rule on `IsOverdue`. Show
  `SourceURL` as a link icon (**Format > Cell elements > URL icon**).

### Page 2: SQDCP Calendar (letter calendar)

* Slicer: `DimDate[Month]`, single select, defaulting to the current month.
* **Pillar letter calendar:** a matrix with rows `DimKPI[Pillar]`, columns
  `DimDate[DayOfMonth]` and value `[Pillar Status]`. Set Background and Font colour
  to `[Pillar Status Colour]` (same colour, so the cell is solid). This is the
  digital version of the paper S/Q/D/C/P letter calendar.
* **KPI calendar:** a matrix with rows `DimKPI[KPI_Label]`, columns
  `DimDate[DayOfMonth]` and value `[KPI Display]`. Set Background to
  `[KPI Status Colour]` and Font to `[KPI Status Font Colour]`. Turn off totals.
* Optional: for a true "S"-shaped safety cross, use the Deneb custom visual with
  `[Safety Day Colour]` per day.

### Page 3: Trends (30 days)

* Page filter: `DimDate[Date]` relative date, **in the last 30 days**.
* Line chart with X `DimDate[Date]`, Y `[KPI Actual]` and `[KPI Target]`, and
  **small multiples** by `DimKPI[KPI_Name]`. Add a pillar slicer.
* Column chart of `[Stop Call Wait Mins]` by `DimShift[Shift]`, to check whether
  nights are under-supported.
* Column chart of `[Scrap £]` by `DimArea[Area]`.

### Page 4: Event Detail (drill-through, linked to source records)

* **Drill-through fields:** `DimKPI[KPI_Name]` and `DimDate[Date]`. Keep "all filters" on.
* Table with `FactKPI` columns ProductionDate, Shift, Area, SourceSystem, SourceRef,
  Description, EventDateTime and SourceURL (as a URL icon).
* From any number on pages 1–3, right-click and choose **Drill through > Event
  Detail**. Then click the link to open the NCR, EHS report or andon call in its
  own system.

### Mobile layout

Under **View > Mobile layout**, place the page 1 banner and pillar tables so the
board also works in the Teams mobile app on the shopfloor.

## Step 7: Optional hardening

* **Row-level security:** give an `Area Lead` role a rule on `DimArea[Area]` if
  leads should only see their own area.
* **Incremental refresh:** when RFT history gets large, add `RangeStart` and
  `RangeEnd` parameters and filter `FactKPI` on `ProductionDate`.
* **Data alerts:** pin the `[Accidents]` and `[Escapes]` cards to a Power BI
  dashboard and set an alert at > 0. A Power Automate flow (*When a data driven
  alert is triggered*, then *Post message in a chat or channel*) pushes it into the
  Teams channel straight away.

## Step 8: Publish

Save as `SQDCP Start of Shift.pbix` (or as a `.pbip` project so it can be version
controlled here). Publish to a workspace such as **Operations – SQDCP**. Then
follow [04-teams-deployment.md](04-teams-deployment.md).
