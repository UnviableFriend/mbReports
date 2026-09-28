from framework.models import Column, ReportResult
from framework.cells import Link, LinkGroup, mbid


class Report:
    id = "artist_missing_kr_streaming"
    title = "Artists Missing Korean Streaming URLs"
    filename = "artist_missing_kr_streaming.html"
    category = "Artists"

    description = (
        "Lists Korean artists that do not have artist URLs for all five "
        "specified Korean streaming services: Bugs, Melon, Genie, VIBE, and FLO."
    )

    query = """
    WITH RECURSIVE korean_areas AS (
        SELECT id
        FROM area
        WHERE id = 113

        UNION ALL

        SELECT DISTINCT laa.entity1
        FROM l_area_area laa
        JOIN link l
            ON laa.link = l.id
        JOIN link_type lt
            ON l.link_type = lt.id
        JOIN korean_areas ka
            ON laa.entity0 = ka.id
        WHERE lt.name = 'part of'
    ),
    korean_artists AS (
        SELECT
            artist.id AS artist_id,
            artist.name AS artist_name,
            artist.gid AS artist_mbid
        FROM artist
        WHERE artist.area IN (SELECT id FROM korean_areas)
           OR artist.begin_area IN (SELECT id FROM korean_areas)
    ),

    artist_urls AS (
        SELECT
            ka.artist_id,
            ka.artist_mbid,
            ka.artist_name,
            array_agg(DISTINCT url.url ORDER BY url.url) AS urls
        FROM korean_artists ka
        JOIN musicbrainz.l_artist_url
            ON ka.artist_id = l_artist_url.entity0
        JOIN musicbrainz.url
            ON l_artist_url.entity1 = url.id
        WHERE url.url ILIKE '%bugs.co.kr%'
           OR url.url ILIKE '%melon.com%'
           OR url.url ILIKE '%genie.co.kr%'
           OR url.url ILIKE '%vibe.naver.com%'
           OR url.url ILIKE '%music-flo.com%'
        GROUP BY
            ka.artist_id,
            ka.artist_mbid,
            ka.artist_name
    )

    SELECT
        artist_name,
        artist_mbid,
        urls
    FROM artist_urls
    WHERE NOT (
        EXISTS (
            SELECT 1 FROM unnest(urls) u
            WHERE u ILIKE '%bugs.co.kr%'
        )
        AND EXISTS (
            SELECT 1 FROM unnest(urls) u
            WHERE u ILIKE '%melon.com%'
        )
        AND EXISTS (
            SELECT 1 FROM unnest(urls) u
            WHERE u ILIKE '%genie.co.kr%'
        )
        AND EXISTS (
            SELECT 1 FROM unnest(urls) u
            WHERE u ILIKE '%vibe.naver.com%'
        )
        AND EXISTS (
            SELECT 1 FROM unnest(urls) u
            WHERE u ILIKE '%music-flo.com%'
        )
    )
    ORDER BY LOWER(artist_name);
    """

    def generate(self, context):
        rows = context.db.fetchall(self.query)

        report_rows = []

        for artist_name, artist_mbid, urls in rows:
            report_rows.append(
                {
                    "artist": Link(
                        text=str(artist_name),
                        url=f"https://musicbrainz.org/artist/{artist_mbid}",
                    ),
                    "urls": LinkGroup(
                        [Link(text=str(url), url=str(url)) for url in (urls or [])]
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
                Column("urls", "URLs"),
            ],
            rows=report_rows,
        )
