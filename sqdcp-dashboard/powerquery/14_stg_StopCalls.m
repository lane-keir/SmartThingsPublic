// Query name: stg_StopCalls   (disable load)
// DELIVERY - Stop Call Waits
// Source: andon system call log (andon_calls.csv)
// Value = minutes the operator waited for a response; Denominator = 1 per call
// (so the model can also report number of calls and average wait).
// Calls with no response yet are measured up to the time of refresh.
let
    Source = fnReadCsv("andon_calls.csv"),
    Typed = Table.TransformColumnTypes(
        Source,
        {{"CallDateTime", type datetime}, {"ResponseDateTime", type datetime}},
        "en-GB"
    ),
    Now = DateTimeZone.RemoveZone(DateTimeZone.SwitchZone(DateTimeZone.UtcNow(), pUtcOffsetHours)),
    WithCode = Table.AddColumn(Typed, "KPI_Code", each "D05", type text),
    WithValue = Table.AddColumn(
        WithCode, "Value",
        each Number.Round(Duration.TotalMinutes((if [ResponseDateTime] = null then Now else [ResponseDateTime]) - [CallDateTime]), 1),
        type number
    ),
    WithDen = Table.AddColumn(WithValue, "Denominator", each 1, type number),
    WithDesc = Table.AddColumn(
        WithDen, "Description",
        each [Station] & " - " & [Reason] & (if [ResponseDateTime] = null then " (NO RESPONSE YET)" else ""),
        type text
    ),
    Renamed = Table.RenameColumns(WithDesc, {{"CallID", "SourceRef"}, {"CallDateTime", "EventDateTime"}}),
    Standard = fnToStandard(Renamed, "Andon", "Andon")
in
    Standard
