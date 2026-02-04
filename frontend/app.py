"""
Intelligent Data Dictionary Agent — Chat UI.
Natural language Q&A over schema, data quality, and AI-generated summaries.
"""
import streamlit as st
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
METADATA_PATH = ARTIFACTS_DIR / "metadata.json"
PROFILES_PATH = ARTIFACTS_DIR / "profiles.json"
SUMMARIES_PATH = ARTIFACTS_DIR / "summaries.json"


def ensure_artifacts():
    """If artifacts missing, run pipeline to generate metadata, profiles, summaries."""
    if METADATA_PATH.exists() and PROFILES_PATH.exists():
        return
    sys.path.insert(0, str(PROJECT_ROOT))
    from pipeline import run_pipeline
    run_pipeline()


def load_artifacts():
    """Load metadata, profiles, summaries from artifacts (or run pipeline once)."""
    ensure_artifacts()
    from storage import load_json  # noqa: E402
    metadata = load_json(METADATA_PATH)
    profiles = load_json(PROFILES_PATH) if PROFILES_PATH.exists() else {}
    summaries = load_json(SUMMARIES_PATH) if SUMMARIES_PATH.exists() else {}
    return metadata, profiles, summaries


st.set_page_config(page_title="Data Dictionary Agent", layout="wide")
st.title("Intelligent Data Dictionary Agent")
st.caption("Ask questions about your database schema, relationships, and data quality in plain language.")

metadata, profiles, summaries = load_artifacts()

# Example questions so users know what to ask
with st.expander("Try asking:", expanded=False):
    st.markdown("""
    - **What tables exist?** — List tables and columns  
    - **What is the schema?** — Same as above  
    - **How are orders linked to customers?** — Show relationships (foreign keys)  
    - **What is data quality like?** — Row counts and key health  
    """)

with st.sidebar:
    st.header("Actions")
    if st.button("Refresh documentation"):
        sys.path.insert(0, str(PROJECT_ROOT))
        from pipeline import run_pipeline
        run_pipeline()
        st.success("Documentation refreshed.")
        st.rerun()
    st.divider()
    st.subheader("Artifacts")
    if (ARTIFACTS_DIR / "data_dictionary.md").exists():
        with open(ARTIFACTS_DIR / "data_dictionary.md") as f:
            st.download_button("Download Markdown", f.read(), file_name="data_dictionary.md", mime="text/markdown")
    st.divider()
    st.subheader("Tables")
    tables = metadata.get("tables", metadata)
    for t in (tables.keys() if isinstance(tables, dict) else []):
        st.text(t)

question = st.chat_input("Ask about your database (e.g. What tables exist? How are orders linked to customers?)")
if question:
    sys.path.insert(0, str(PROJECT_ROOT))
    from ai_engine import answer_question
    answer = answer_question(question, metadata, profiles, summaries)
    with st.chat_message("user"):
        st.write(question)
    with st.chat_message("assistant"):
        st.markdown(answer)
