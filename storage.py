import json

def save_metadata(metadata, file_name="metadata.json"):
    with open(file_name, "w") as f:
        json.dump(metadata, f, indent=4)
