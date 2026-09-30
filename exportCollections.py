import time
import json
import requests
import random
from datetime import datetime, timezone


OUTPUT_FILE = "artist_collections.json"

HEADERS = {
    "User-Agent": "CollectionExportScript/1.0"
}


# Add your collection MBIDs here.
# Each label can contain one or more collections.
COLLECTIONS = {
    "KPopGroups": [
        "b1ed9262-1a52-41e5-8f58-b3e14da9e429"
    ],
    "KPersons": [
        "dec8e348-6420-44ae-a979-c35eaacf80a9"
    ]
}

MAX_RETRIES = 8


def request_with_backoff(url, params):
    """
    Make a MusicBrainz request with retry handling.
    """

    for attempt in range(MAX_RETRIES):

        try:
            response = requests.get(
                url,
                params=params,
                headers=HEADERS,
                timeout=30
            )

        except requests.exceptions.RequestException as e:
            wait = min(300, (2 ** attempt) * 5)
            wait += random.uniform(0, 5)

            print(
                f"Network error: {e}"
            )
            print(
                f"Waiting {wait:.1f} seconds before retry..."
            )

            time.sleep(wait)
            continue


        # Successful request
        if response.status_code == 200:
            return response


        # Temporary server/rate-limit errors
        if response.status_code in (
            429,
            500,
            502,
            503,
            504
        ):

            retry_after = response.headers.get(
                "Retry-After"
            )

            if retry_after:
                wait = int(retry_after)
            else:
                wait = min(
                    300,
                    (2 ** attempt) * 10
                )

            wait += random.uniform(0, 5)

            print(
                f"MusicBrainz returned HTTP {response.status_code}"
            )
            print(
                f"Retry {attempt + 1}/{MAX_RETRIES}. "
                f"Waiting {wait:.1f} seconds..."
            )

            time.sleep(wait)
            continue


        # Permanent errors
        print(
            f"Non-retryable HTTP error: {response.status_code}"
        )
        print(response.text)

        return None


    print(
        "Maximum retries exceeded."
    )

    return None


def fetch_collection_artists(collection_ids):

    base_url = "https://musicbrainz.org/ws/2/artist"

    limit = 100
    offset = 0

    artists = {}

    collection_param = ",".join(collection_ids)


    while True:

        params = {
            "collection": collection_param,
            "limit": limit,
            "offset": offset,
            "fmt": "json"
        }


        print(
            f"Fetching artists {offset}-{offset + limit}"
        )


        response = request_with_backoff(
            base_url,
            params
        )


        if response is None:
            break


        data = response.json()

        batch = data.get(
            "artists",
            []
        )


        if not batch:
            break


        for artist in batch:
            mbid = artist.get("id")

            if mbid:
                artists[mbid] = artist


        total = data.get(
            "artist-count",
            0
        )


        print(
            f"Captured {len(artists)} of {total} artists"
        )


        if len(batch) < limit or len(artists) >= total:
            break


        offset += limit


        # Normal pacing between successful requests
        time.sleep(
            2 + random.uniform(0, 2)
        )


    return artists


def main():

    output = {
        "generated": datetime.now(
            timezone.utc
        ).isoformat(),

        "source": "MusicBrainz Collections API",

        "collections": {}
    }


    for label, collection_ids in COLLECTIONS.items():

        print()
        print("=" * 50)
        print(f"Exporting {label}")
        print("=" * 50)


        artists = fetch_collection_artists(
            collection_ids
        )


        output["collections"][label] = {
            "collection_ids": collection_ids,
            "count": len(artists),
            "artists": artists
        }


        print(
            f"{label}: {len(artists)} artists"
        )


    with open(
        OUTPUT_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            output,
            f,
            indent=4,
            ensure_ascii=False
        )


    print(
        "Finished."
    )


if __name__ == "__main__":
    main()
