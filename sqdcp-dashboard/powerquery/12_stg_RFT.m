// Query name: stg_RFT   (disable load)
// DELIVERY - Right First Time Final / Verify / System
// Source: MES / test-station results (test_results.csv) - one row per test attempt.
// RFT = units that PASS on attempt 1 / units presented (attempt 1 rows).
// Live alternative (SQL):  Sql.Database("mes-sql01", "MES", [Query = "SELECT SerialNumber, TestStage, TestDateTime, Area, AttemptNo, Result FROM dbo.TestResults WHERE AttemptNo = 1 AND TestDateTime >= DATEADD(day,-400,GETDATE())"])
let
    Source = fnReadCsv("test_results.csv"),
    Typed = Table.TransformColumnTypes(
        Source,
        {{"TestDateTime", type datetime}, {"AttemptNo", Int64.Type}},
        "en-GB"
    ),
    FirstAttempt = Table.SelectRows(Typed, each [AttemptNo] = 1),
    KpiMap = [Final = "D01", Verify = "D02", System = "D03"],
    WithCode = Table.AddColumn(FirstAttempt, "KPI_Code", each Record.FieldOrDefault(KpiMap, [TestStage], null), type text),
    Mapped = Table.SelectRows(WithCode, each [KPI_Code] <> null),
    WithValue = Table.AddColumn(Mapped, "Value", each if Text.Upper([Result]) = "PASS" then 1 else 0, type number),
    WithDen = Table.AddColumn(WithValue, "Denominator", each 1, type number),
    WithDesc = Table.AddColumn(WithDen, "Description", each [TestStage] & " first attempt: " & [Result], type text),
    Renamed = Table.RenameColumns(WithDesc, {{"SerialNumber", "SourceRef"}, {"TestDateTime", "EventDateTime"}}),
    Standard = fnToStandard(Renamed, "MES / Test", "Test")
in
    Standard
