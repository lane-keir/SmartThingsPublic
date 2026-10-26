// Query name: stg_People   (disable load)
// PEOPLE - Customer Visits
// Source: visits register (customer_visits.csv) - ideally a Microsoft List in
// the Operations Teams site so the site lead can maintain it from Teams:
//   SharePoint.Tables(pSharePointSite, [Implementation = "2.0", ViewMode = "All"]){[Title = "Customer Visits"]}[Items]
// Visits are day-level so Shift is left blank.
let
    Source = fnReadCsv("customer_visits.csv"),
    Typed = Table.TransformColumnTypes(Source, {{"VisitDate", type date}}, "en-GB"),
    WithCode = Table.AddColumn(Typed, "KPI_Code", each "P01", type text),
    WithValue = Table.AddColumn(WithCode, "Value", each 1, type number),
    WithDen = Table.AddColumn(WithValue, "Denominator", each null, type number),
    WithShift = Table.AddColumn(WithDen, "Shift", each null, type text),
    WithDesc = Table.AddColumn(WithShift, "Description", each [Customer] & " - " & [Purpose] & " (host: " & [Host] & ")", type text),
    Renamed = Table.RenameColumns(WithDesc, {{"VisitID", "SourceRef"}, {"VisitDate", "ProductionDate"}}),
    Standard = fnToStandard(Renamed, "Visits Register", "Visits")
in
    Standard
