from pathlib import Path
import yaml


def load_config(filename):
    path = Path(filename)
    if not path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {path}. "
            "Copy config.yaml.example to config.yaml and edit it."
        )

    with path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f) or {}

    return config
