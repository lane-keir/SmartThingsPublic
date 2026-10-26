// Query name: stg_Quality   (disable load)
// QUALITY - Product Safety Reports, Escapes, Concessions, NCRs
// Source: QMS export (qms_records.csv)
// Live alternative (SharePoint list):
//   SharePoint.Tables(pSharePointSite, [Implementation = "2.0", ViewMode = "All"]){[Title = "NCR Log"]}[Items]
let
    Source = fnReadCsv("qms_records.csv"),
    Typed = Table.TransformColumnTypes(Source, {{"RaisedDateTime", type datetime}}, "en-GB"),
    KpiMap = [#"Product Safety Report" = "Q01", Escape = "Q02", Concession = "Q03", NCR = "Q04"],
    WithCode = Table.AddColumn(Typed, "KPI_Code", each Record.FieldOrDefault(KpiMap, [RecordType], null), type text),
    Mapped = Table.SelectRows(WithCode, each [KPI_Code] <> null),
    WithValue = Table.AddColumn(Mapped, "Value", each 1, type number),
    WithDen = Table.AddColumn(WithValue, "Denominator", each null, type number),
    WithPart = Table.AddColumn(WithDen, "Desc2", each [PartNumber] & " - " & [Description], type text),
    Cleaned = Table.RenameColumns(
        Table.RemoveColumns(WithPart, {"Description"}),
        {{"RecordID", "SourceRef"}, {"RaisedDateTime", "EventDateTime"}, {"Desc2", "Description"}}
    ),
    Standard = fnToStandard(Cleaned, "QMS", "QMS")
in
    Standard
