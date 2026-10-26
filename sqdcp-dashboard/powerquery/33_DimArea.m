// Query name: DimArea   (LOAD)
// Built from every area seen in the sources so a new cell/line appears automatically.
// Replace with a maintained list if you need area owners, value streams, ordering.
let
    Areas = List.Distinct(List.RemoveNulls(List.Combine({FactKPI[Area], FactActions[Area]}))),
    Sorted = List.Sort(Areas),
    AsTable = Table.FromList(Sorted, Splitter.SplitByNothing(), type table [Area = text])
in
    AsTable
