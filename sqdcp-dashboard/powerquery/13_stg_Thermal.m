// Query name: stg_Thermal   (disable load)
// DELIVERY - Thermal Deviations
// Source: furnace / oven data-logger alarm export (thermal_deviations.csv)
let
    Source = fnReadCsv("thermal_deviations.csv"),
    Typed = Table.TransformColumnTypes(
        Source,
        {{"StartDateTime", type datetime}, {"Setpoint", type number}, {"Actual", type number}, {"DurationMins", type number}},
        "en-GB"
    ),
    WithCode = Table.AddColumn(Typed, "KPI_Code", each "D04", type text),
    WithValue = Table.AddColumn(WithCode, "Value", each 1, type number),
    WithDen = Table.AddColumn(WithValue, "Denominator", each null, type number),
    WithDesc = Table.AddColumn(
        WithDen, "Description",
        each [EquipmentID] & " " & [Parameter] & ": " & Number.ToText([Actual]) & " vs SP "
            & Number.ToText([Setpoint]) & " for " & Number.ToText([DurationMins]) & " min",
        type text
    ),
    Renamed = Table.RenameColumns(WithDesc, {{"DeviationID", "SourceRef"}, {"StartDateTime", "EventDateTime"}}),
    Standard = fnToStandard(Renamed, "Thermal Logger", "Thermal")
in
    Standard
