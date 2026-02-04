"""
Generate documentation: Markdown data dictionary from metadata, profiles, and summaries.
"""
from pathlib import Path
from config import ARTIFACTS_DIR


def build_markdown(metadata, profiles, summaries):
    """Build a single Markdown document and per-table snippets."""
    tables = metadata.get("tables", metadata)
    rels = metadata.get("relationships", [])
    lines = [
        "# Data Dictionary",
        "",
        "## Overview",
        "This document describes the database schema, data quality metrics, and business context.",
        "",
        "## Relationships",
    ]
    if rels:
        for r in rels:
            lines.append(f"- `{r.get('table')}.{r.get('column')}` → `{r.get('ref_table')}.{r.get('ref_column')}`")
    else:
        lines.append("- No foreign key relationships extracted.")
    lines.extend(["", "---", ""])

    for table_name, columns in tables.items():
        profile = profiles.get(table_name, {})
        summary_block = summaries.get(table_name, {})
        summary = summary_block.get("summary", "") if isinstance(summary_block, dict) else ""
        recs = summary_block.get("recommendations", []) if isinstance(summary_block, dict) else []

        lines.append(f"## Table: `{table_name}`")
        lines.append("")
        if summary:
            lines.append(summary)
            lines.append("")
        lines.append("### Columns")
        lines.append("")
        lines.append("| Column | Type | Nullable | PK | Completeness | Unique |")
        lines.append("|--------|------|----------|-----|--------------|--------|")
        col_stats = profile.get("columns", {})
        for c in columns:
            cn = c.get("column_name", c)
            typ = c.get("data_type", "")
            null = "YES" if c.get("nullable") else "NO"
            pk = "✓" if c.get("primary_key") else ""
            st = col_stats.get(cn, {})
            comp = st.get("completeness_pct", "")
            uniq = st.get("unique_count", "")
            lines.append(f"| {cn} | {typ} | {null} | {pk} | {comp} | {uniq} |")
        lines.append("")
        if profile.get("total_rows") is not None:
            lines.append(f"**Total rows:** {profile['total_rows']}")
        kh = profile.get("key_health", {})
        if kh:
            lines.append(f"**Key health:** null_pks={kh.get('null_pks', 0)}, duplicate_pks={kh.get('duplicate_pks', 0)}")
        if recs:
            lines.append("**Recommendations:**")
            for r in recs:
                lines.append(f"- {r}")
        lines.append("")
        lines.append("---")
        lines.append("")

    return "\n".join(lines)


def run_and_save(metadata, profiles, summaries):
    """Write Markdown to artifacts/data_dictionary.md."""
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    md = build_markdown(metadata, profiles, summaries)
    path = ARTIFACTS_DIR / "data_dictionary.md"
    path.write_text(md, encoding="utf-8")
    print(f"Saved {path}")
    return path
