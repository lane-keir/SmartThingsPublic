// Query name: DimShift   (LOAD) - keep in step with the boundaries in fnShift
#table(
    type table [Shift = text, ShiftOrder = Int64.Type, StartTime = text, EndTime = text],
    {
        {"Early", 1, "06:00", "14:00"},
        {"Late",  2, "14:00", "22:00"},
        {"Night", 3, "22:00", "06:00"}
    }
)
