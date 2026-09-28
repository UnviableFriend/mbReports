from datetime import datetime
from html import escape
from framework.cells import Link, MBID, LinkGroup


def _format_value(value):
    if value is None:
        return ""

    if isinstance(value, Link):
        target = ' target="_blank" rel="noopener"' if value.new_tab else ""
        return f'<a href="{escape(value.url, quote=True)}"{target}>{escape(value.text)}</a>'

    if isinstance(value, MBID):
        url = f"https://musicbrainz.org/{value.entity_type}/{value.value}"
        return (
            f'<a href="{escape(url, quote=True)}" target="_blank" '
            f'rel="noopener">{escape(value.value)}</a>'
        )

    if isinstance(value, LinkGroup):
        return "<div class=\"link-group\">" + "<br>".join(
            _format_value(item) for item in value.items
        ) + "</div>"

    return escape(str(value))

def _format_datetime(value):
    if value is None:
        return ""

    return (
        f'<time datetime="{escape(value.isoformat(), quote=True)}">'
        f'{escape(value.isoformat())}'
        f'</time>'
    )

def render_report(result, generated_at, replication_date):
    stats_html = ""
    if result.stats:
        stats_html = '<div class="stats">'
        for stat in result.stats:
            stats_html += (
                '<div class="stat">'
                f'<span class="stat-label">{escape(str(stat.label))}</span>'
                f'<span class="stat-value">{_format_value(stat.value)}</span>'
                '</div>'
            )
        stats_html += "</div>"

    description = (
        f'<div class="description">{result.description}</div>'
        if result.description
        else ""
    )

    headers = "".join(
        f'<th data-key="{escape(column.key)}">{escape(column.title)}</th>'
        for column in result.columns
    )

    rows_html = []
    for row in result.rows:
        cells = "".join(
            f'<td>{_format_value(row.get(column.key))}</td>'
            for column in result.columns
        )
        rows_html.append(f"<tr>{cells}</tr>")

    body = "\n".join(rows_html)

    generated = _format_datetime(generated_at)
    replication = _format_datetime(replication_date) if replication_date else "Unavailable"

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(result.title)}</title>
<link rel="stylesheet" href="static/report.css">
</head>
<body>
<div class="container">
<header>
  <h1>{escape(result.title)}</h1>
  {description}
  <div class="metadata">
    <span><strong>Report Generated:</strong> {generated}</span>
    <span><strong>Last Replication Date:</strong> {replication}</span>
  </div>
</header>

{stats_html}

<div class="table-tools">
  <input id="table-filter" type="search" placeholder="Filter table...">
  <span id="row-count">{len(result.rows)} rows</span>
</div>

<div class="table-wrapper">
<table id="report-table">
<thead><tr>{headers}</tr></thead>
<tbody>
{body}
</tbody>
</table>
</div>
</div>
<script src="static/report.js"></script>
</body>
</html>
"""


def render_index(results, generated_at, replication_date, site_title, failures):
    categories = {}
    for result in results:
        categories.setdefault(result.category, []).append(result)

    sections = []
    for category in sorted(categories):
        links = []
        for result in sorted(categories[category], key=lambda r: r.title.lower()):
            links.append(
                f'<li><a href="{escape(result.filename, quote=True)}">'
                f'{escape(result.title)}</a>'
                f'<span class="index-count">{len(result.rows)} rows</span></li>'
            )
        sections.append(
            f'<section><h2>{escape(category)}</h2><ul>{"".join(links)}</ul></section>'
        )

    failure_html = ""
    if failures:
        failure_html = (
            "<section><h2>Failed Reports</h2><ul>"
            + "".join(
                f"<li>{escape(report.title)}: {escape(str(exc))}</li>"
                for report, exc in failures
            )
            + "</ul></section>"
        )

    generated = _format_datetime(generated_at)
    replication = _format_datetime(replication_date) if replication_date else "Unavailable"

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(site_title)}</title>
<link rel="stylesheet" href="static/report.css">
</head>
<body>
<div class="container">
<header>
  <h1>{escape(site_title)}</h1>
  <div class="metadata">
    <span><strong>Generated:</strong> {generated}</span>
    <span><strong>Last Replication Date:</strong> {replication}</span>
  </div>
</header>
{"".join(sections)}
{failure_html}
</div>
</body>
</html>
"""
