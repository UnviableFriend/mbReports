# MusicBrainz Report Module Guide

This document is the contract for creating reports for the MusicBrainz Reports
framework.

The goal is that a new report should normally be a single Python file in
`reports/`. The framework handles PostgreSQL connections, collection loading,
replication metadata, HTML generation, CSS, JavaScript, and output paths.

## 1. Minimal module

A report module contains a `Report` class:

```python
from framework.models import Column, ReportResult

class Report:
    id = "my_report"
    title = "My Report"
    filename = "my_report.html"
    category = "Artists"
    description = "What this report identifies."

    query = """
    SELECT ...
    """

    def generate(self, context):
        rows = context.db.fetchall(self.query)

        return ReportResult(
            report_id=self.id,
            title=self.title,
            description=self.description,
            category=self.category,
            filename=self.filename,
            columns=[
                Column("name", "Name"),
            ],
            rows=[
                {"name": row[0]}
                for row in rows
            ],
        )
```

## 2. Required metadata

Every report must define:

- `id`: unique machine-readable identifier. Prefer `snake_case`.
- `title`: human-readable title.
- `filename`: output HTML filename.
- `category`: category shown on the generated index.
- `description`: explanation of what the report finds.

The `ReportResult` should normally use the same metadata.

## 3. Report context

`generate(context)` receives a shared `ReportContext`.

Available values:

### `context.db`

The single PostgreSQL database wrapper used for the entire run.

Useful methods:

```python
context.db.fetchall(query, params)
context.db.fetchone(query, params)
context.db.execute(query, params)
context.db.conn
```

Do NOT create another PostgreSQL connection.

### `context.config`

The complete configuration loaded from `config.yaml`.

### `context.collection_data`

The original parsed `artist_collections.json` structure.

### `context.collections`

Convenience access to:

```python
context.collections["KPopGroups"]
```

### `context.replication_date`

The MusicBrainz `last_replication_date` value obtained once at startup.

## 4. Collection staging table

The framework loads all collections into a temporary PostgreSQL table:

```text
report_collection_artists
```

Important columns include:

```text
collection_name
artist_gid
artist_name
sort_name
artist_type
country
area_gid
area_name
begin_area_gid
begin_area_name
begin_date
end_date
ended
disambiguation
```

Example:

```sql
SELECT *
FROM report_collection_artists
WHERE collection_name = 'KPopGroups';
```

Do not create your own copy of the collection table.

## 5. Returning data

Reports should return structured data, not HTML.

Do NOT do this:

```python
return "<tr><td>...</td></tr>"
```

Do this instead:

```python
return ReportResult(
    ...
    rows=[
        {
            "artist": "Example",
            "count": 3,
        }
    ],
)
```

The framework renders the result.

## 6. Columns

Define columns using `Column`:

```python
Column("artist", "Artist")
Column("count", "Count")
```

The first argument is the row dictionary key. The second is the visible heading.

## 7. Statistics

Statistics are optional.

```python
from framework.models import Stat

stats=[
    Stat("Total Artists", 1259),
    Stat("Artists with Problems", 42),
    Stat("Missing", "12.5%"),
]
```

The framework renders these consistently above the table.

## 8. MusicBrainz links

Use the supplied cell helpers instead of manually generating HTML.

```python
from framework.cells import mbid, link

{
    "mbid": mbid("08bc1626-aa7b-4daa-9a2a-caeb87987712", "artist")
}
```

For arbitrary external URLs:

```python
{
    "url": link("Bugs", "https://music.bugs.co.kr/...")
}
```

The renderer handles escaping and target attributes.

## 9. Multiple links in one cell

Use `LinkGroup` when a cell contains several links:

```python
from framework.cells import LinkGroup, link

{
    "releases": LinkGroup([
        link("Release A", "..."),
        link("Release B", "..."),
    ])
}
```

This is intended for reports such as URL reports where one URL can occur on
multiple releases.

## 10. Direct HTML

Avoid returning HTML from reports.

If a report genuinely needs a presentation that cannot be expressed by the
common cell model, that is a signal that the report may need a framework
extension or may be better kept as a specialized report.

Do not silently introduce report-specific CSS or JavaScript.

## 11. Database connections

Never do:

```python
psycopg2.connect(...)
```

inside a report.

The runner creates one connection and gives it to every report.

## 12. Collections JSON

Never parse `artist_collections.json` in a report.

The runner loads it once before any reports execute.

Use either:

```python
context.collection_data
```

or the PostgreSQL staging table:

```sql
report_collection_artists
```

For SQL-heavy reports, prefer the staging table.

## 13. Replication date

Do not query `musicbrainz.replication_control` in individual reports.

The framework queries it once and exposes:

```python
context.replication_date
```

The common template automatically displays it.

## 14. Output

Do not open output files from a report.

The report specifies:

```python
filename = "my_report.html"
```

and the framework writes it into the configured output directory.

## 15. JavaScript filtering

All standard table reports automatically receive the common table filter.

Reports should not implement their own filtering unless they require functionality
that the common framework does not provide.

Future framework functionality may add sorting, column filters, or other
features without requiring report changes.

## 16. Categories

Use a sensible broad category, such as:

- Artists
- Groups
- Aliases
- Releases
- Release Groups
- Recordings
- Relationships
- URLs
- Collections
- Metadata
- Discovery

The exact category list is not currently enforced.

## 17. Existing report conversion

When converting an old standalone report:

### Remove

- configuration constants for DB connection
- configuration constants for output path
- JSON loading
- collection temporary-table creation
- replication queries
- database connection/close code
- HTML/CSS generation
- output-file writing

### Keep

- the report-specific SQL
- report-specific calculations
- report-specific interpretation of the results

### Replace

Old:

```python
df = pd.read_sql_query(QUERY, conn)
```

New:

```python
rows = context.db.fetchall(QUERY)
```

Old HTML generation becomes structured `ReportResult` rows.

## 18. Design principle

A good module should mostly answer:

1. What data am I looking for?
2. How do I identify it?
3. What columns should the user see?
4. What optional statistics are useful?

Everything else belongs to the framework.

## 19. When NOT to use this framework

Do not force a report into this architecture if it fundamentally requires:

- a graph/network visualization
- a map
- a large interactive application
- complex custom JavaScript
- fundamentally different page structure
- substantial client-side computation

Those can remain specialized applications.

The framework is primarily intended for MusicBrainz reports that can reasonably be
represented as metadata + statistics + a structured table.
