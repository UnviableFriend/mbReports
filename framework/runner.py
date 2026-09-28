from datetime import datetime, timezone
from pathlib import Path
import traceback

from framework.database import Database
from framework.collections import load_collections
from framework.renderer import render_report, render_index


REPLICATION_QUERY = """
SELECT last_replication_date
FROM musicbrainz.replication_control;
"""


class ReportContext:
    def __init__(self, config, db, collection_data, replication_date):
        self.config = config
        self.db = db
        self.collection_data = collection_data
        self.replication_date = replication_date

    @property
    def collections(self):
        return self.collection_data.get("collections", {})


class ReportRunner:
    def __init__(self, config, reports):
        self.config = config
        self.reports = reports

    def run(self, report_ids=None, category=None):
        selected = self.reports

        if report_ids:
            wanted = set(report_ids)
            selected = [r for r in selected if r.id in wanted]

        if category:
            selected = [r for r in selected if r.category == category]

        if not selected:
            print("No reports selected.")
            return

        output_dir = Path(self.config["output"]["directory"])
        if not output_dir.is_absolute():
            output_dir = Path.cwd() / output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        db = Database(self.config["database"] if "database" in self.config else self.config)
        # Database expects the full config.
        db = Database(self.config)
        generated_at = datetime.now(timezone.utc)

        results = []
        failures = []

        try:
            print("Connecting to MusicBrainz database...")
            db.connect()

            print("Loading artist collections...")
            collection_data = load_collections(
                db,
                self.config["collections"]["file"],
            )

            replication = db.fetchone(REPLICATION_QUERY)
            replication_date = replication[0] if replication else None

            context = ReportContext(
                self.config,
                db,
                collection_data,
                replication_date,
            )

            print(f"Running {len(selected)} report(s)...")

            for report in selected:
                print(f"  {report.id}: {report.title}")
                try:
                    result = report.generate(context)
                    if not result.filename:
                        result.filename = f"{report.id}.html"
                    results.append(result)
                    print(f"    OK ({len(result.rows)} rows)")
                except Exception as exc:
                    failures.append((report, exc))
                    print(f"    FAILED: {exc}")
                    traceback.print_exc()

            for result in results:
                destination = output_dir / result.filename
                destination.write_text(
                    render_report(result, generated_at, replication_date),
                    encoding="utf-8",
                )

            index_path = output_dir / "index.html"
            index_path.write_text(
                render_index(
                    results,
                    generated_at,
                    replication_date,
                    self.config.get("site", {}).get(
                        "title", "MusicBrainz Reports"
                    ),
                    failures,
                ),
                encoding="utf-8",
            )

        finally:
            db.close()

        print(f"Generated {len(results)} report(s) in {output_dir}")
        if failures:
            print(f"{len(failures)} report(s) failed.")
