// Query name: fnShift   (function - disable load)
// Converts a timestamp into the production day and shift it belongs to.
// Night shift (22:00-06:00) is credited to the day the shift STARTED, so an
// event at 02:00 on Tuesday is reported against Monday night shift.
// Edit the boundaries below to match your shift pattern.
(dt as nullable datetime) as record =>
let
    EarlyStart = 6,
    LateStart  = 14,
    NightStart = 22,
    h = if dt = null then null else Time.Hour(DateTime.Time(dt)),
    Shift =
        if h = null then null
        else if h >= EarlyStart and h < LateStart then "Early"
        else if h >= LateStart and h < NightStart then "Late"
        else "Night",
    ProductionDate =
        if dt = null then null
        else if h < EarlyStart then Date.AddDays(DateTime.Date(dt), -1)
        else DateTime.Date(dt)
in
    [ProductionDate = ProductionDate, Shift = Shift]
