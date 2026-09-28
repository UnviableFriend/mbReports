from framework.models import Column, ReportResult
from framework.cells import Link, LinkGroup


class Report:
    id = "release_streaming_on_wrong_format"
    title = "Streaming Links on Non-Digital Releases"
    filename = "release_streaming_on_wrong_format.html"
    category = "Releases"

    description = (
        "This report highlights streaming links found on media types that "
        "shouldn't have them, such as CDs. It could be someone who added "
        "streaming links to the wrong release, or a release with an incorrect "
        "media format. Check the edit history to determine what fix would be best."
    )

    query = """
    SELECT
        a.name AS artist_name,
        a.gid AS artist_mbid,
        release.name AS release_name,
        release.gid AS release_mbid,
        array_agg(DISTINCT url.url ORDER BY url.url) AS streaming_links,
        medium_format.name AS format
    FROM musicbrainz.url
    LEFT JOIN musicbrainz.l_release_url lru
        ON url.id = lru.entity1
    LEFT JOIN musicbrainz.release release
        ON lru.entity0 = release.id
    LEFT JOIN musicbrainz.artist_credit_name acn
        ON release.artist_credit = acn.artist_credit
    LEFT JOIN musicbrainz.artist a
        ON acn.artist = a.id
    LEFT JOIN musicbrainz.medium
        ON release.id = medium.release
    LEFT JOIN musicbrainz.medium_format
        ON medium.format = medium_format.id
    LEFT JOIN musicbrainz.area ar
        ON a.area = ar.id
    LEFT JOIN musicbrainz.area bar
        ON a.begin_area = bar.id
    WHERE
        (ar.name = 'South Korea' OR bar.name = 'South Korea')
        AND medium_format.name != 'Digital Media'
        AND url.url SIMILAR TO '%(spotify|deezer|apple|tidal|naver|bugs|melon|genie|music-flo).(com|co.kr)%'
        AND url.url NOT LIKE 'https://shop.spotify.com%'
    GROUP BY
        a.name,
        a.gid,
        release.name,
        release.gid,
        medium_format.name
    ORDER BY
        a.name,
        release.name;
    """

    def generate(self, context):
        rows = context.db.fetchall(self.query)

        report_rows = []

        for (
            artist_name,
            artist_mbid,
            release_name,
            release_mbid,
            streaming_links,
            release_format,
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
                    "release": (
                        Link(
                            text=str(release_name),
                            url=f"https://musicbrainz.org/release/{release_mbid}",
                        )
                        if release_mbid
                        else str(release_name or "")
                    ),
                    "streaming_links": LinkGroup(
                        [
                            Link(
                                text=str(url),
                                url=str(url),
                            )
                            for url in (streaming_links or [])
                        ]
                    ),
                    "format": str(release_format or ""),
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
                Column("streaming_links", "Streaming Links"),
                Column("format", "Format"),
            ],
            rows=report_rows,
        )
