// Query name: FactKPI   (LOAD)
// One row per KPI event / unit / transaction from every source, in one schema.
//   Value       - count (1), minutes, GBP, hours, or 1/0 pass flag for RFT
//   Denominator - units presented (RFT) or 1 per stop call; null otherwise
let
    Combined = Table.Combine({stg_Safety, stg_Quality, stg_RFT, stg_Thermal, stg_StopCalls, stg_Cost, stg_People}),
    Typed = Table.TransformColumnTypes(
        Combined,
        {
            {"ProductionDate", type date}, {"Shift", type text}, {"Area", type text},
            {"KPI_Code", type text}, {"Value", type number}, {"Denominator", type number},
            {"SourceSystem", type text}, {"SourceRef", type text}, {"Description", type text},
            {"SourceURL", type text}, {"EventDateTime", type datetime}
        }
    ),
    Valid = Table.SelectRows(Typed, each [ProductionDate] <> null)
in
    Valid
