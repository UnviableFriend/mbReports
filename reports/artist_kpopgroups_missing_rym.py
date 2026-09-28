from framework.models import Column, ReportResult
from framework.cells import Link


class Report:
    id = "artist_kpopgroups_missing_rym"
    title = "KPop Groups Missing Rate Your Music URLs"
    filename = "artist_kpopgroups_missing_rym.html"
    category = "Artists"

    description = (
        "Lists artists in the KPopGroups collection that do not have a "
        "Rate Your Music (rateyourmusic.com) artist URL in MusicBrainz."
    )

    query = """
    SELECT
        a.name AS artist_name,
        a.gid AS artist_mbid
    FROM report_collection_artists rca
    JOIN musicbrainz.artist a
        ON a.gid = rca.artist_gid
    WHERE rca.collection_name = 'KPopGroups'
      AND NOT EXISTS (
          SELECT 1
          FROM musicbrainz.l_artist_url lau
          JOIN musicbrainz.url u
              ON u.id = lau.entity1
          WHERE lau.entity0 = a.id
            AND u.url ILIKE '%rateyourmusic.com%'
      )
    ORDER BY LOWER(a.name), a.gid;
    """

    def generate(self, context):
        rows = context.db.fetchall(self.query)

        report_rows = [
            {
                "artist": Link(
                    text=str(artist_name),
                    url=f"https://musicbrainz.org/artist/{artist_mbid}",
                ),
            }
            for artist_name, artist_mbid in rows
        ]

        return ReportResult(
            report_id=self.id,
            title=self.title,
            description=self.description,
            category=self.category,
            filename=self.filename,
            columns=[
                Column("artist", "Artist"),
            ],
            rows=report_rows,
        )
