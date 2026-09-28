from framework.models import Column, ReportResult, Stat
from framework.cells import Link, LinkGroup


class Report:
    id = "release_missing_kr_streaming"
    title = "Releases Missing KR URLs"
    filename = "release_missing_kr_streaming.html"
    category = "Releases"

    description = (
        "<strong>Warning:</strong> This report is a simple URL-coverage check. "
        "It does not know which releases should have these relationships. "
        "It finds digital releases with at least one of the three targeted "
        "Korean streaming services (Bugs, Melon, or Genie) and lists those "
        "missing one or more of them. Verify that the release should have "
        "the missing service before adding it."
    )

    query = """
    WITH release_urls AS (
        SELECT
            r.id AS release_id,
            r.gid AS release_mbid,
            r.name AS release_name,
            a.name AS artist_name,
            a.gid AS artist_mbid,
            array_agg(DISTINCT u.url ORDER BY u.url) AS urls
        FROM musicbrainz.release r
        JOIN musicbrainz.artist_credit ac
            ON r.artist_credit = ac.id
        JOIN musicbrainz.artist_credit_name acn
            ON ac.id = acn.artist_credit
        JOIN musicbrainz.artist a
            ON acn.artist = a.id
        JOIN musicbrainz.medium m
            ON r.id = m.release
        JOIN musicbrainz.medium_format mf
            ON m.format = mf.id
        JOIN musicbrainz.l_release_url lru
            ON r.id = lru.entity0
        JOIN musicbrainz.url u
            ON lru.entity1 = u.id
        WHERE mf.name ILIKE 'digital media'
          AND (
              u.url ILIKE '%bugs.co.kr%'
              OR u.url ILIKE '%melon.com%'
              OR u.url ILIKE '%genie.co.kr%'
          )
        GROUP BY
            r.id,
            r.gid,
            r.name,
            a.id,
            a.gid,
            a.name
    )
    SELECT
        artist_name,
        artist_mbid,
        release_mbid,
        release_name,
        urls
    FROM release_urls
    WHERE NOT (
        EXISTS (
            SELECT 1
            FROM unnest(urls) u
            WHERE u ILIKE '%bugs.co.kr%'
        )
        AND EXISTS (
            SELECT 1
            FROM unnest(urls) u
            WHERE u ILIKE '%melon.com%'
        )
        AND EXISTS (
            SELECT 1
            FROM unnest(urls) u
            WHERE u ILIKE '%genie.co.kr%'
        )
    )
    ORDER BY
        LOWER(artist_name),
        LOWER(release_name);
    """

    domain_count_query = """
    SELECT
        domain,
        COUNT(*)
    FROM (
        SELECT
            CASE
                WHEN url ILIKE '%bugs.co.kr%' THEN 'bugs.co.kr'
                WHEN url ILIKE '%melon.com%' THEN 'melon.com'
                WHEN url ILIKE '%genie.co.kr%' THEN 'genie.co.kr'
                WHEN url ILIKE '%vibe.naver.com%' THEN 'vibe.naver.com'
                WHEN url ILIKE '%music-flo.com%' THEN 'music-flo.com'
                ELSE NULL
            END AS domain
        FROM musicbrainz.url
    ) AS domain_urls
    WHERE domain IS NOT NULL
    GROUP BY domain
    ORDER BY domain;
    """

    def generate(self, context):
        rows = context.db.fetchall(self.query)
        domain_counts = dict(context.db.fetchall(self.domain_count_query))

        report_rows = []

        for artist_name, artist_mbid, release_mbid, release_name, urls in rows:
            report_rows.append(
                {
                    "artist": Link(
                        text=str(artist_name),
                        url=f"https://musicbrainz.org/artist/{artist_mbid}",
                    ),
                    "release": Link(
                        text=str(release_name),
                        url=f"https://musicbrainz.org/release/{release_mbid}",
                    ),
                    "urls": LinkGroup(
                        [
                            Link(text=str(url), url=str(url))
                            for url in (urls or [])
                        ]
                    ),
                }
            )

        stats = [
            Stat("Bugs URLs", domain_counts.get("bugs.co.kr", 0)),
            Stat("Melon URLs", domain_counts.get("melon.com", 0)),
            Stat("Genie URLs", domain_counts.get("genie.co.kr", 0)),
            Stat("VIBE URLs", domain_counts.get("vibe.naver.com", 0)),
            Stat("FLO URLs", domain_counts.get("music-flo.com", 0)),
            Stat("Releases Missing Targeted URLs", len(report_rows)),
        ]

        return ReportResult(
            report_id=self.id,
            title=self.title,
            description=self.description,
            category=self.category,
            filename=self.filename,
            columns=[
                Column("artist", "Artist"),
                Column("release", "Release"),
                Column("urls", "URLs"),
            ],
            rows=report_rows,
            stats=stats,
        )
