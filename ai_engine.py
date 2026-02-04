"""
AI-enhanced business summaries and natural language answers.
Uses OpenAI when OPENAI_API_KEY is set; otherwise template-based fallbacks.
"""
import json
from config import OPENAI_API_KEY, OPENAI_MODEL


def _template_summary(table_name, columns, profile):
    """Generate a business-friendly summary without API."""
    cols_desc = ", ".join(
        f"{c['column_name']} ({c['data_type']})"
        for c in columns[:10]
    )
    if len(columns) > 10:
        cols_desc += f" and {len(columns) - 10} more"
    row_count = profile.get("total_rows", 0)
    comp = profile.get("columns", {})
    avg_comp = sum(c.get("completeness_pct", 0) for c in comp.values()) / len(comp) if comp else 0
    summary = (
        f"The table **{table_name}** stores {row_count} rows with columns: {cols_desc}. "
        f"Average data completeness is {avg_comp:.1f}%."
    )
    recs = [
        "Use this table for reporting and analytics on the entities it represents.",
        "Check key_health in the profile for primary key integrity.",
    ]
    if profile.get("freshness"):
        recs.append("Review freshness metrics for date columns to ensure data is up to date.")
    return {"summary": summary, "recommendations": recs}


def generate_table_summary(table_name, columns, profile):
    """
    Generate business-friendly summary and usage recommendations for a table.
    Returns: { "summary": str, "recommendations": list[str] }
    """
    if OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            prompt = f"""You are a data steward. For this table, write a short business-friendly summary (2-3 sentences) and 2-3 usage recommendations (one line each).
Table: {table_name}
Columns: {json.dumps(columns, indent=2)}
Data quality profile: total_rows={profile.get('total_rows')}, key_health={profile.get('key_health')}. Column sample: {json.dumps(list(profile.get('columns', {}).items())[:5])}
Respond in JSON only: {{ "summary": "...", "recommendations": ["...", "..."] }}"""
            resp = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            text = resp.choices[0].message.content.strip()
            if text.startswith("```"):
                text = text.split("```")[1].replace("json", "").strip()
            return json.loads(text)
        except Exception as e:
            return _template_summary(table_name, columns, profile)
    return _template_summary(table_name, columns, profile)


def answer_question(question, metadata, profiles, summaries):
    """
    Answer a natural language question about the database using metadata, profiles, and AI summaries.
    Returns a string answer.
    """
    context = {
        "metadata": metadata,
        "profiles": profiles,
        "summaries": summaries,
    }
    context_str = json.dumps(context, indent=2)[:12000]  # cap size for API

    if OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            resp = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": "You are a helpful data dictionary assistant. Answer the user's question about the database schema and data quality using only the provided context. Be concise and business-friendly."},
                    {"role": "user", "content": f"Context:\n{context_str}\n\nQuestion: {question}"},
                ],
                temperature=0.2,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            return _keyword_answer(question, metadata, profiles, summaries)
    return _keyword_answer(question, metadata, profiles, summaries)


def _keyword_answer(question, metadata, profiles, summaries):
    """Simple keyword-based answer when no API key."""
    q = question.lower()
    tables = metadata.get("tables", metadata)
    if isinstance(tables, dict):
        table_names = list(tables.keys())
    else:
        table_names = []
    if "table" in q or "schema" in q or "column" in q:
        lines = ["**Tables in this database:**"]
        for t in table_names:
            cols = tables.get(t, [])
            if isinstance(cols, list):
                col_list = [c.get("column_name", c) if isinstance(c, dict) else c for c in cols[:15]]
                lines.append(f"- **{t}**: " + ", ".join(str(c) for c in col_list))
        if summaries:
            for t, s in summaries.items():
                if isinstance(s, dict) and s.get("summary"):
                    lines.append(f"\n**{t}**: {s['summary']}")
        return "\n".join(lines)
    if "relationship" in q or "foreign" in q or "link" in q:
        rels = metadata.get("relationships", [])
        if not rels:
            return "No foreign key relationships extracted for this database."
        lines = ["**Relationships:**"]
        for r in rels:
            lines.append(f"- {r.get('table')}.{r.get('column')} → {r.get('ref_table')}.{r.get('ref_column')}")
        return "\n".join(lines)
    if "quality" in q or "completeness" in q:
        lines = ["**Data quality (sample):**"]
        for t, p in list(profiles.items())[:5]:
            total = p.get("total_rows", 0)
            kh = p.get("key_health", {})
            lines.append(f"- **{t}**: {total} rows; key health: null_pks={kh.get('null_pks', 0)}, duplicate_pks={kh.get('duplicate_pks', 0)}")
        return "\n".join(lines)
    # Friendly fallback with example questions
    return (
        "I'm your **data dictionary assistant**. I can answer questions about:\n\n"
        "- **Tables & schema** — e.g. *\"What tables exist?\"* or *\"What is the schema?\"*\n"
        "- **Relationships** — e.g. *\"How are orders linked to customers?\"* or *\"Show relationships\"*\n"
        "- **Data quality** — e.g. *\"What is data quality like?\"* or *\"Summarize data quality\"*\n\n"
        "Try one of the questions above, or set **OPENAI_API_KEY** in your environment for full natural language answers to any question."
    )
