from framework.models import Column, ReportResult
from framework.cells import Link, LinkGroup


class Report:
    id = "release_generasia"
    title = "Generasia Links on Releases"
    filename = "release_generasia.html"
    category = "Releases"

    description = (
        "Lists Generasia links attached to releases. Generasia links should "
        "usually be on release groups rather than individual releases."
    )

    query = """
    SELECT
        r.name AS release_name,
        r.gid AS release_mbid,
        acn.name AS artist_name,
        array_agg(DISTINCT u.url ORDER BY u.url) AS urls
    FROM musicbrainz.release r
    JOIN musicbrainz.l_release_url lru
        ON r.id = lru.entity0
    JOIN musicbrainz.url u
        ON lru.entity1 = u.id
    LEFT JOIN musicbrainz.artist_credit ac
        ON r.artist_credit = ac.id
    LEFT JOIN musicbrainz.artist_credit_name acn
        ON ac.id = acn.artist_credit
    WHERE LOWER(u.url) LIKE '%generasia.com%'
    GROUP BY
        r.name,
        r.gid,
        acn.name
    ORDER BY
        LOWER(acn.name),
        LOWER(r.name);
    """

    def generate(self, context):
        rows = context.db.fetchall(self.query)

        report_rows = []

        for release_name, release_mbid, artist_name, urls in rows:
            report_rows.append(
                {
                    "artist": str(artist_name or ""),
                    "release": Link(
                        text=str(release_name),
                        url=f"https://musicbrainz.org/release/{release_mbid}",
                    ),
                    "generasia": LinkGroup(
                        [
                            Link(text=str(url), url=str(url))
                            for url in (urls or [])
                        ]
                    ),
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
                Column("release", "Release"),
                Column("generasia", "Generasia Links"),
            ],
            rows=report_rows,
        )
