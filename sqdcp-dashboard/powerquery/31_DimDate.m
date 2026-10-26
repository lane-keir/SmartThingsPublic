// Query name: DimDate   (LOAD, then Table tools > Mark as date table > Date)
// IsReportDay flags the period the start-of-shift meeting reviews:
//   Tue-Fri -> yesterday;  Monday -> Friday + the weekend.
let
    Today = Date.From(DateTimeZone.SwitchZone(DateTimeZone.UtcNow(), pUtcOffsetHours)),
    FirstData = List.Min(FactKPI[ProductionDate]),
    StartDate = Date.StartOfMonth(if FirstData = null then Date.AddDays(Today, -90) else FirstData),
    EndDate = Date.EndOfMonth(Date.AddDays(Today, 31)),
    Dates = List.Dates(StartDate, Duration.Days(EndDate - StartDate) + 1, #duration(1, 0, 0, 0)),
    LastWeek = List.Dates(Date.AddDays(Today, -7), 7, #duration(1, 0, 0, 0)),
    PrevWorkingDay = List.Last(List.Select(LastWeek, each Date.DayOfWeek(_, Day.Monday) < 5)),
    Base = Table.FromList(Dates, Splitter.SplitByNothing(), type table [Date = date]),
    Cols = Table.AddColumn(Base, "Attrs", each
        let d = [Date], offset = Duration.Days(d - Today) in
        [
            Year = Date.Year(d),
            MonthNo = Date.Month(d),
            Month = Date.ToText(d, [Format = "MMM yyyy", Culture = "en-GB"]),
            MonthStart = Date.StartOfMonth(d),
            DayOfMonth = Date.Day(d),
            DayName = Date.ToText(d, [Format = "ddd", Culture = "en-GB"]),
            DayLabel = Date.ToText(d, [Format = "ddd dd", Culture = "en-GB"]),
            WeekStart = Date.StartOfWeek(d, Day.Monday),
            IsWorkingDay = Date.DayOfWeek(d, Day.Monday) < 5,
            DayOffset = offset,
            IsFuture = offset > 0,
            IsReportDay = d >= PrevWorkingDay and offset < 0,
            IsCurrentMonth = Date.StartOfMonth(d) = Date.StartOfMonth(Today)
        ]
    ),
    Expanded = Table.ExpandRecordColumn(Cols, "Attrs",
        {"Year", "MonthNo", "Month", "MonthStart", "DayOfMonth", "DayName", "DayLabel", "WeekStart",
         "IsWorkingDay", "DayOffset", "IsFuture", "IsReportDay", "IsCurrentMonth"}),
    Typed = Table.TransformColumnTypes(Expanded, {
        {"Year", Int64.Type}, {"MonthNo", Int64.Type}, {"Month", type text}, {"MonthStart", type date},
        {"DayOfMonth", Int64.Type}, {"DayName", type text}, {"DayLabel", type text}, {"WeekStart", type date},
        {"IsWorkingDay", type logical}, {"DayOffset", Int64.Type}, {"IsFuture", type logical},
        {"IsReportDay", type logical}, {"IsCurrentMonth", type logical}})
in
    Typed
