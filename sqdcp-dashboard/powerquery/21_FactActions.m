// Query name: FactActions   (LOAD)
// Tier 1 action / countermeasure log - the "so what" of the start-of-shift meeting.
// Recommended live source: a Microsoft List "Tier1 Actions" in the Operations
// Teams site (add it as a tab next to the dashboard so actions are raised in the meeting):
//   SharePoint.Tables(pSharePointSite, [Implementation = "2.0", ViewMode = "All"]){[Title = "Tier1 Actions"]}[Items]
let
    Source = fnReadCsv("actions.csv"),
    Typed = Table.TransformColumnTypes(Source, {{"DateRaised", type date}, {"DueDate", type date}}, "en-GB"),
    Today = Date.From(DateTimeZone.SwitchZone(DateTimeZone.UtcNow(), pUtcOffsetHours)),
    WithOverdue = Table.AddColumn(Typed, "IsOverdue", each [Status] <> "Closed" and [DueDate] <> null and [DueDate] < Today, type logical),
    WithDaysOpen = Table.AddColumn(WithOverdue, "DaysOpen", each if [Status] = "Closed" then null else Duration.Days(Today - [DateRaised]), Int64.Type),
    LinkBase = Record.FieldOrDefault(SourceLinks, "Actions", ""),
    WithUrl = Table.AddColumn(WithDaysOpen, "SourceURL", each if LinkBase = "" then null else LinkBase & Uri.EscapeDataString([ActionID]), type text)
in
    WithUrl
