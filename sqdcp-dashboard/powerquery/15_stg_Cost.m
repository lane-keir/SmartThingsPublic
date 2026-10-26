// Query name: stg_Cost   (disable load)
// COST - Scrap (GBP) and Rework (hours)
// Source: ERP scrap / rework transactions (erp_scrap_rework.csv). ERP posts by
// date + shift, so no timestamp conversion is needed.
// Live alternative (SAP/ERP view via SQL or OData):
//   OData.Feed("https://erp.contoso.com/odata/ScrapRework?$filter=PostingDate ge 2025-01-01")
let
    Source = fnReadCsv("erp_scrap_rework.csv"),
    Typed = Table.TransformColumnTypes(
        Source,
        {{"PostingDate", type date}, {"Qty", type number}, {"Value_GBP", type number}, {"Hours", type number}},
        "en-GB"
    ),
    WithCode = Table.AddColumn(
        Typed, "KPI_Code",
        each if [TransType] = "SCRAP" then "C01" else if [TransType] = "REWORK" then "C02" else null,
        type text
    ),
    Mapped = Table.SelectRows(WithCode, each [KPI_Code] <> null),
    WithValue = Table.AddColumn(Mapped, "Value", each if [KPI_Code] = "C01" then [Value_GBP] else [Hours], type number),
    WithDen = Table.AddColumn(WithValue, "Denominator", each null, type number),
    WithDesc = Table.AddColumn(
        WithDen, "Description",
        each [PartNumber] & " x" & Number.ToText([Qty]) & " - " & [ReasonCode],
        type text
    ),
    Renamed = Table.RenameColumns(
        Table.TransformColumns(WithDesc, {{"TransactionID", Text.From, type text}}),
        {{"TransactionID", "SourceRef"}, {"PostingDate", "ProductionDate"}}
    ),
    Standard = fnToStandard(Renamed, "ERP", "ERP")
in
    Standard
