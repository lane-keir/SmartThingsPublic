// Query name: stg_Safety   (disable load)
// SAFETY - Accidents, Incidents, Near Misses, Hazards Contained
// Source: EHS system export (ehs_events.csv)
// Live alternative (SQL):  Sql.Database("ehs-sql01", "EHS", [Query = "SELECT EventID, EventDateTime, Area, EventType, Status, ContainedDateTime, Description FROM dbo.vw_Events WHERE EventDateTime >= DATEADD(day,-400,GETDATE())"])
let
    Source = fnReadCsv("ehs_events.csv"),
    Typed = Table.TransformColumnTypes(
        Source,
        {{"EventDateTime", type datetime}, {"ContainedDateTime", type datetime}},
        "en-GB"
    ),
    // Hazards only count once they are contained
    Relevant = Table.SelectRows(
        Typed,
        each [EventType] <> "Hazard" or [Status] = "Contained" or [ContainedDateTime] <> null
    ),
    KpiMap = [Accident = "S01", Incident = "S02", #"Near Miss" = "S03", Hazard = "S04"],
    WithCode = Table.AddColumn(Relevant, "KPI_Code", each Record.FieldOrDefault(KpiMap, [EventType], null), type text),
    Mapped = Table.SelectRows(WithCode, each [KPI_Code] <> null),
    WithValue = Table.AddColumn(Mapped, "Value", each 1, type number),
    WithDen = Table.AddColumn(WithValue, "Denominator", each null, type number),
    Renamed = Table.RenameColumns(WithDen, {{"EventID", "SourceRef"}}),
    Standard = fnToStandard(Renamed, "EHS System", "EHS")
in
    Standard
