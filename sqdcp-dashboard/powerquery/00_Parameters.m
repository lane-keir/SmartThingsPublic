// ============================================================================
// PARAMETERS  -  create each as a Power Query parameter
// (Home > Manage Parameters > New Parameter) or paste each block into a
// Blank Query via the Advanced Editor and rename the query to the name shown.
// ============================================================================

// ---- Query name: pSourceMode   (Text; allowed values: Folder, SharePoint)
// "Folder"     = read the extracts from a local / network folder (needs gateway once published)
// "SharePoint" = read the extracts from a SharePoint document library (cloud refresh, no gateway)
"Folder" meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true, List = {"Folder", "SharePoint"}, DefaultValue = "Folder"]

// ---- Query name: pLocalFolder   (Text) - must end with a backslash
"C:\SQDCP\sample-data\" meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true]

// ---- Query name: pSharePointSite   (Text) - the SITE url, not the library url
"https://contoso.sharepoint.com/sites/Operations" meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true]

// ---- Query name: pSharePointFolder   (Text) - library + folder path, forward slashes, trailing slash
"Shared Documents/SQDCP Data/" meta [IsParameterQuery = true, Type = "Text", IsParameterQueryRequired = true]

// ---- Query name: pUtcOffsetHours   (Decimal) - the Power BI service refreshes in UTC.
// Set 0 for GMT, 1 during BST (or your site's offset) so "yesterday" is correct.
0 meta [IsParameterQuery = true, Type = "Number", IsParameterQueryRequired = true]
