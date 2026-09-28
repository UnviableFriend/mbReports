from framework.models import Column, ReportResult, Stat
from framework.cells import mbid


class Report:
    id = "recordings_dupe_isrcs"
    title = "KPop Groups - Duplicate ISRCs"
    filename = "recordings_dupe_isrcs.html"
    category = "Recordings"

    description = (
        "Identifies ISRCs that are attached to more than one recording for the "
        "same artist in the KPopGroups collection. A duplicate ISRC is a "
        "potential data-quality issue, but does not automatically mean the "
        "recordings should be merged."
    )

    query = """
    WITH collection_artists AS (
        SELECT
            a.id AS artist_id,
            a.gid AS artist_gid,
            a.name AS artist_name
        FROM musicbrainz.artist a
        JOIN report_collection_artists rca
            ON rca.artist_gid = a.gid
        WHERE rca.collection_name = 'KPopGroups'
    ),

    artist_recordings AS (
        SELECT DISTINCT
            ca.artist_id,
            ca.artist_gid,
            ca.artist_name,
            r.id AS recording_id,
            i.isrc
        FROM collection_artists ca
        JOIN musicbrainz.artist_credit_name acn
            ON acn.artist = ca.artist_id
        JOIN musicbrainz.recording r
            ON r.artist_credit = acn.artist_credit
        JOIN musicbrainz.isrc i
            ON i.recording = r.id
    ),

    duplicate_isrcs AS (
        SELECT
            artist_id,
            artist_gid,
            artist_name,
            isrc
        FROM artist_recordings
        GROUP BY
            artist_id,
            artist_gid,
            artist_name,
            isrc
        HAVING COUNT(DISTINCT recording_id) > 1
    )

    SELECT
        artist_name AS artist,
        artist_gid::text AS mbid,
        COUNT(*) AS duplicate_isrcs
    FROM duplicate_isrcs
    GROUP BY
        artist_id,
        artist_gid,
        artist_name
    ORDER BY
        COUNT(*) DESC,
        artist_name;
    """

    def generate(self, context):
        rows = context.db.fetchall(self.query)

        collection_count = sum(
            1
            for collection in context.collection_data.get("collections", {}).values()
            if collection.get("artists")
        )

        report_rows = [
            {
                "artist": artist,
                "mbid": mbid(mbid_value, "artist"),
                "duplicate_isrcs": int(count),
            }
            for artist, mbid_value, count in rows
        ]

        duplicate_artist_count = len(report_rows)
        total_duplicate_isrcs = sum(r["duplicate_isrcs"] for r in report_rows)

        return ReportResult(
            report_id=self.id,
            title=self.title,
            description=self.description,
            category=self.category,
            filename=self.filename,
            columns=[
                Column("artist", "Artist"),
                Column("mbid", "MBID"),
                Column("duplicate_isrcs", "Duplicate ISRCs"),
            ],
            rows=report_rows,
            stats=[
                Stat("KPopGroups Collection Artists", collection_count),
                Stat("Artists with Duplicate ISRCs", duplicate_artist_count),
                Stat("Total Duplicate ISRCs", total_duplicate_isrcs),
            ],
        )
