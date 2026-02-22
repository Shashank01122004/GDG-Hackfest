"""
Full pipeline: extract metadata → profile → AI summaries → save artifacts (JSON + Markdown).
Optionally exports table row data to JSON (see EXPORT_TABLE_DATA).
"""
import os
from pathlib import Path
from config import ARTIFACTS_DIR
from storage import load_json, save_json
from metadata_extractor import extract_metadata, run_and_save as extract_and_save
from profiler import profile_all, run_and_save as profile_and_save
from ai_engine import generate_table_summary
from doc_generator import run_and_save as docs_save


def run_pipeline():
    """Run full pipeline and save all artifacts."""
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Extract metadata
    meta = extract_metadata()
    save_json(meta, ARTIFACTS_DIR / "metadata.json")
    print("Saved metadata.json")

    # 2. Profile all tables
    profiles = profile_and_save(meta)
    # profiles already saved by profile_and_save

    # 3. AI summaries per table
    tables = meta.get("tables", meta)
    summaries = {}
    for table_name, columns in tables.items():
        profile = profiles.get(table_name, {})
        summaries[table_name] = generate_table_summary(table_name, columns, profile)
    save_json(summaries, ARTIFACTS_DIR / "summaries.json")
    print("Saved summaries.json")

    # 4. Markdown documentation
    docs_save(meta, profiles, summaries)

    # 5. Optional: export table row data to JSON (set EXPORT_TABLE_DATA=1 to enable)
    if os.getenv("EXPORT_TABLE_DATA", "").strip() in ("1", "true", "yes"):
        try:
            from export_table_data import export_table_data_to_json
            export_table_data_to_json(one_file=False)
            print("Saved artifacts/table_data/*.json")
        except Exception as e:
            print(f"Table data export skipped: {e}")

    print("Pipeline complete.")
    return meta, profiles, summaries


if __name__ == "__main__":
    run_pipeline()
