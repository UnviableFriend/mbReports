from framework.models import Column, ReportResult
from framework.cells import Link


class Report:
    id = "artist_invalid_korean_alias_sort"
    title = "Invalid Korean Alias Sort Names"
    filename = "artist_invalid_korean_alias_sort.html"
    category = "Artists"

    description = (
        "These aliases are in Hangul, but their sort names are Latinized "
        "(incorrect per MusicBrainz guidelines)."
    )

    query = """
    SELECT
        a.name AS artist_name,
        a.gid AS mbid,
        aa.name AS alias_name,
        aa.sort_name AS alias_sort_name,
        aa.locale
    FROM musicbrainz.artist_alias aa
    JOIN musicbrainz.artist a
        ON aa.artist = a.id
    WHERE
        -- Focus on Korean aliases
        (aa.locale = 'ko' OR aa.name ~ '[가-힣]')
        -- Ensure the alias itself is in Hangul
        AND aa.name ~ '[가-힣]'
        -- Sort name contains no Hangul
        AND aa.sort_name !~ '[가-힣]'
        -- Exclude empty or null sort names
        AND aa.sort_name IS NOT NULL
        AND aa.sort_name != ''
    ORDER BY
        a.name;
    """

    def generate(self, context):
        rows = context.db.fetchall(self.query)

        report_rows = []

        for (
            artist_name,
            artist_mbid,
            alias_name,
            alias_sort_name,
            locale,
        ) in rows:
            report_rows.append(
                {
                    "artist": (
                        Link(
                            text=str(artist_name),
                            url=f"https://musicbrainz.org/artist/{artist_mbid}",
                        )
                        if artist_mbid
                        else str(artist_name or "")
                    ),
                    "alias": str(alias_name or ""),
                    "sort_name": str(alias_sort_name or ""),
                }
            )

        return ReportResult(
            report_id=self.id,
            title=self.title,
            description=self.description,
            category=self.category,
            filename=self.filename,
            columns=[
                Column("artist", "Artist"),
                Column("alias", "Hangul Alias"),
                Column("sort_name", "Incorrect Latin Sort"),
            ],
            rows=report_rows,
        )
