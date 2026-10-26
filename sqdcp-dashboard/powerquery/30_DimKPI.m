// Query name: DimKPI   (LOAD)
// KPI master: names, pillar, units, polarity and targets. Keep this as an Excel
// table or Microsoft List owned by the Ops Manager so targets can change without
// touching the report.
let
    Source = fnReadCsv("kpi_master.csv"),
    Typed = Table.TransformColumnTypes(
        Source,
        {
            {"PillarOrder", Int64.Type}, {"KPIOrder", Int64.Type},
            {"DailyTarget", type number}, {"AmberTolerance", type number}
        },
        "en-GB"
    ),
    WithLetter = Table.AddColumn(Typed, "PillarLetter", each Text.Start([Pillar], 1), type text),
    WithSort = Table.AddColumn(WithLetter, "KPISort", each [PillarOrder] * 100 + [KPIOrder], Int64.Type),
    WithLabel = Table.AddColumn(WithSort, "KPI_Label", each [PillarLetter] & " | " & [KPI_Name], type text)
in
    WithLabel
