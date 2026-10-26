// Query name: fnReadCsv   (function - disable load)
// Reads one CSV extract from the folder or SharePoint library chosen by pSourceMode.
// When a pillar moves to a live connection (SQL, SharePoint list, API) you replace
// the fnReadCsv(...) call in that staging query - see docs/02-data-sources.md.
(fileName as text) as table =>
let
    Content =
        if pSourceMode = "SharePoint" then
            let
                Files = SharePoint.Files(pSharePointSite, [ApiVersion = 15]),
                Match = Table.SelectRows(
                    Files,
                    each [Name] = fileName and Text.Contains([Folder Path], pSharePointFolder)
                )
            in
                Match{0}[Content]
        else
            File.Contents(pLocalFolder & fileName),
    Csv = Csv.Document(Content, [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Csv, [PromoteAllScalars = true])
in
    Promoted
