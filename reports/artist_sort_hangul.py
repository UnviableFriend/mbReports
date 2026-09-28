from framework.models import Column, ReportResult
from framework.cells import Link


class Report:
    id = "artist_sort_hangul"
    title = "Artist Sort Names Requiring Latinization"
    filename = "artist_sort_hangul.html"
    category = "Artists"

    description = (
        "The following South Korean artists have primary sort names in Hangul. "
        "Per MusicBrainz guidelines, these must be converted to Latin characters."
    )

    query = """
    WITH RECURSIVE korean_areas AS (
        SELECT id
        FROM musicbrainz.area
        WHERE id = 113

        UNION ALL

        SELECT DISTINCT laa.entity1
        FROM musicbrainz.l_area_area laa
        JOIN musicbrainz.link l
            ON laa.link = l.id
        JOIN musicbrainz.link_type lt
            ON l.link_type = lt.id
        JOIN korean_areas ka
            ON laa.entity0 = ka.id
        WHERE lt.name = 'part of'
    )
    SELECT
        a.name AS artist_name,
        a.sort_name AS current_sort_name,
        a.gid AS mbid
    FROM musicbrainz.artist a
    LEFT JOIN musicbrainz.area ar
        ON a.area = ar.id
    LEFT JOIN musicbrainz.area bar
        ON a.begin_area = bar.id
    WHERE
        -- Artist is associated with South Korea or a region within South Korea
        (
            a.area IN (SELECT id FROM korean_areas)
            OR a.begin_area IN (SELECT id FROM korean_areas)
        )
        -- Find cases where the sort_name contains Hangul characters
        AND a.sort_name ~ '[가-힣]'
    ORDER BY
        a.name;
    """

    def generate(self, context):
        rows = context.db.fetchall(self.query)

        report_rows = []

        for (
            artist_name,
            current_sort_name,
            artist_mbid,
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
                    "sort_name": str(current_sort_name or ""),
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
                Column("sort_name", "Invalid Hangul Sort Name"),
            ],
            rows=report_rows,
        )
