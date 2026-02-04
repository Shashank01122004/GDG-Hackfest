"""Save and load JSON artifacts."""
import json
from pathlib import Path


def save_json(data, path):
    """Write data as JSON to path (str or Path)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def load_json(path):
    """Load JSON from path (str or Path)."""
    with open(path) as f:
        return json.load(f)


def save_metadata(metadata, file_name="metadata.json"):
    """Legacy: save metadata dict to file_name (default metadata.json)."""
    path = Path(file_name)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(metadata, f, indent=2)
