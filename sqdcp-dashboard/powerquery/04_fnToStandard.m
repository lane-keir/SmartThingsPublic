// Query name: fnToStandard   (function - disable load)
// Shapes any staging table into the single standard KPI-event schema used by
// FactKPI. Input must have: Area, KPI_Code, Value, Denominator, SourceRef,
// Description and EITHER EventDateTime (datetime) OR ProductionDate + Shift.
(t as table, system as text, linkKey as text) as table =>
let
    WithShift =
        if Table.HasColumns(t, {"ProductionDate", "Shift"}) then t
        else Table.ExpandRecordColumn(
            Table.AddColumn(t, "_shift", each fnShift([EventDateTime])),
            "_shift", {"ProductionDate", "Shift"}
        ),
    WithTime =
        if Table.HasColumns(WithShift, "EventDateTime") then WithShift
        else Table.AddColumn(WithShift, "EventDateTime", each null),
    WithSystem = Table.AddColumn(WithTime, "SourceSystem", each system, type text),
    LinkBase = Record.FieldOrDefault(SourceLinks, linkKey, ""),
    WithUrl = Table.AddColumn(
        WithSystem, "SourceURL",
        each if LinkBase = "" or [SourceRef] = null then null
             else LinkBase & Uri.EscapeDataString(Text.From([SourceRef])),
        type text
    ),
    Out = Table.SelectColumns(
        WithUrl,
        {"ProductionDate", "Shift", "Area", "KPI_Code", "Value", "Denominator",
         "SourceSystem", "SourceRef", "Description", "SourceURL", "EventDateTime"}
    )
in
    Out
