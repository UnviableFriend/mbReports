import json
from pathlib import Path


COLLECTION_TABLE = "report_collection_artists"


def load_collections(db, filename):
    """
    Load artist_collections.json once into a temporary PostgreSQL table.

    The original JSON remains the source of truth. The temporary relational
    representation is deliberately flattened for convenient report queries.
    """
    path = Path(filename)

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    db.execute(f"""
        CREATE TEMP TABLE {COLLECTION_TABLE} (
            collection_name TEXT NOT NULL,
            artist_gid UUID NOT NULL,
            artist_name TEXT,
            sort_name TEXT,
            artist_type TEXT,
            country TEXT,
            area_gid UUID,
            area_name TEXT,
            begin_area_gid UUID,
            begin_area_name TEXT,
            begin_date TEXT,
            end_date TEXT,
            ended BOOLEAN,
            disambiguation TEXT,
            PRIMARY KEY (collection_name, artist_gid)
        );
    """)

    rows = []

    for collection_name, collection in data.get("collections", {}).items():
        for mbid, artist in collection.get("artists", {}).items():
            life_span = artist.get("life-span") or {}
            area = artist.get("area") or {}
            begin_area = artist.get("begin-area") or {}

            rows.append((
                collection_name,
                mbid,
                artist.get("name"),
                artist.get("sort-name"),
                artist.get("type"),
                artist.get("country"),
                area.get("id"),
                area.get("name"),
                begin_area.get("id"),
                begin_area.get("name"),
                life_span.get("begin"),
                life_span.get("end"),
                life_span.get("ended", False),
                artist.get("disambiguation", ""),
            ))

    with db.conn.cursor() as cur:
        cur.executemany(
            f"""
            INSERT INTO {COLLECTION_TABLE} (
                collection_name, artist_gid, artist_name, sort_name,
                artist_type, country, area_gid, area_name,
                begin_area_gid, begin_area_name, begin_date,
                end_date, ended, disambiguation
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            rows,
        )

    return data


def collection_counts(data):
    return {
        name: collection.get("count", len(collection.get("artists", {})))
        for name, collection in data.get("collections", {}).items()
    }
