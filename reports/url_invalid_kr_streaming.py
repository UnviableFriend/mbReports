import re

from framework.models import Column, ReportResult
from framework.cells import Link


VALIDATION_PATTERNS = {
    "music.bugs.co.kr": re.compile(
        r"^https://music\.bugs\.co\.kr/(album|artist|track|mv)/\d+$"
    ),
    "www.melon.com": re.compile(
        r"^https://www\.melon\.com/"
        r"(album|artist|song|video)/detail\.htm\?"
        r"(albumId|artistId|songId|mvId)=\d+$"
    ),
    "www.genie.co.kr": re.compile(
        r"^https://www\.genie\.co\.kr/detail/"
        r"(albumInfo|artistInfo|songInfo|mediaInfo)\?"
        r"(axnm|xxnm|xgnm|xvnm)=\d+$"
    ),
    "music.naver.com": re.compile(
        r"^https://music\.naver\.com/"
        r"(album/index\.nhn\?albumId=\d+"
        r"|artist/\w+\.nhn\?artistId=\d+"
        r"|video/\w+\.nhn\?videoId=\d+)$"
    ),
    "vibe.naver.com": re.compile(
        r"^https://vibe\.naver\.com/(album|artist|track|video)/\d+$"
    ),
    "www.music-flo.com": re.compile(
        r"^https://www\.music-flo\.com/detail/"
        r"(artist/\d+/album|album/\d+/albumtrack)$"
    ),
}


def is_valid_url(url):
    """Return True when the URL matches the expected MusicBrainz format."""

    domain = next(
        (domain for domain in VALIDATION_PATTERNS if domain in url),
        None,
    )

    if domain is None:
        return True

    match = VALIDATION_PATTERNS[domain].match(url)

    # Bugs: query strings are not valid.
    if domain == "music.bugs.co.kr" and "?" in url:
        return False

    # FLO has some additional URL restrictions.
    if domain == "www.music-flo.com":
        if "?" in url:
            return False

        # Artist URLs must point to the /album page.
        if re.match(
            r"^https://www\.music-flo\.com/detail/artist/\d+/$",
            url,
        ):
            return False

        # Album URLs must point to the /albumtrack page.
        if re.match(
            r"^https://www\.music-flo\.com/detail/album/\d+/$",
            url,
        ):
            return False

        # Track URLs are not valid for this service.
        if re.match(
            r"^https://www\.music-flo\.com/detail/track/\d+.*$",
            url,
        ):
            return False

    return match is not None


class Report:
    id = "url_invalid_kr_streaming"
    title = "Invalid KR Streaming Links"
    filename = "url_invalid_kr_streaming.html"
    category = "URLs"

    description = (
        "Lists Korean streaming service URLs that do not match the URL "
        "patterns used by MusicBrainz's URL cleanup/validation rules. "
        "These can include older URLs that predate MusicBrainz's cleanup "
        "code and therefore require manual correction."
        "<br><br>"
        'See <a href="https://tickets.metabrainz.org/browse/MBS-12667" '
        'target="_blank">MBS-12667</a> for Melon and Bugs, '
        '<a href="https://tickets.metabrainz.org/browse/MBS-13370" '
        'target="_blank">MBS-13370</a> for Genie, and '
        '<a href="https://tickets.metabrainz.org/browse/MBS-13922" '
        'target="_blank">MBS-13922</a> for Naver.'
    )

    query = """
    SELECT
        u.url,
        a.gid AS artist_mbid,
        a.name AS artist_name,
        r.gid AS release_mbid,
        r.name AS release_name,
        mf.name AS format
    FROM musicbrainz.url u
    LEFT JOIN musicbrainz.l_artist_url lau
        ON u.id = lau.entity1
    LEFT JOIN musicbrainz.artist a
        ON lau.entity0 = a.id
    LEFT JOIN musicbrainz.l_release_url lru
        ON u.id = lru.entity1
    LEFT JOIN musicbrainz.release r
        ON lru.entity0 = r.id
    LEFT JOIN musicbrainz.medium m
        ON r.id = m.release
    LEFT JOIN musicbrainz.medium_format mf
        ON m.format = mf.id
    WHERE u.url SIMILAR TO '%(naver|bugs|melon|genie|music-flo).(com|co.kr)%'
    ORDER BY u.url;
    """

    def generate(self, context):
        rows = context.db.fetchall(self.query)

        report_rows = []

        for url, artist_mbid, artist_name, release_mbid, release_name, release_format in rows:
            if is_valid_url(url):
                continue

            report_rows.append(
                {
                    "url": Link(
                        text=str(url),
                        url=str(url),
                    ),
                    "artist": (
                        Link(
                            text=str(artist_name),
                            url=f"https://musicbrainz.org/artist/{artist_mbid}",
                        )
                        if artist_mbid
                        else ""
                    ),
                    "release": (
                        Link(
                            text=str(release_name),
                            url=f"https://musicbrainz.org/release/{release_mbid}",
                        )
                        if release_mbid
                        else ""
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
                Column("url", "URL"),
                Column("artist", "Artist MBID"),
                Column("release", "Release MBID"),
                Column("format", "Format"),
            ],
            rows=report_rows,
        )
