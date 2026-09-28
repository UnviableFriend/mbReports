# MusicBrainz Reports

A reusable framework for generating MusicBrainz data-quality and maintenance
reports from a shared PostgreSQL connection and shared artist collection data.

## Quick start

```bash
cp config.yaml.example config.yaml
# edit config.yaml

pip install -r requirements.txt

python reports.py --list
python reports.py
```

Generated HTML is written to the configured output directory.

The initial repository includes the converted Duplicate ISRC report as a
reference implementation.

See `REPORT_MODULE_GUIDE.md` for the module contract used when creating new
reports.
