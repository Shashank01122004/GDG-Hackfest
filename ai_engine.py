import json
import os
import sqlite3
from google import genai
from config import DB_PATH

# ===========================
# CONFIG
# ===========================

MODEL = "models/gemini-2.5-flash"  # ✅ correct model
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("❌ GEMINI_API_KEY not found in environment variables")

client = genai.Client(api_key=API_KEY)


# ===========================
# ERROR LOGGER
# ===========================

def log_error(where, err):
    print(f"\n[ERROR in {where}] {type(err).__name__}: {err}\n")


# ===========================
# TEMPLATE FALLBACK
# ===========================

def _template_summary(table_name, columns, profile):
    cols = ", ".join(c["column_name"] for c in columns[:6])
    if len(columns) > 6:
        cols += f" + {len(columns) - 6} more"

    rows = profile.get("total_rows", 0)

    summary = f"{table_name} contains {rows} records describing {cols}."
    recs = [
        "Use for analytics and reporting",
        "Validate keys before joins",
        "Monitor data quality regularly"
    ]

    return {"summary": summary, "recommendations": recs}


# ===========================
# AI TABLE SUMMARY
# ===========================

def generate_table_summary(table_name, columns, profile):

    prompt = f"""
You are a data governance expert.

Write:
1) A short business summary (2–3 sentences)
2) 2–3 usage recommendations

Table: {table_name}

Schema:
{json.dumps(columns, indent=2)}

Data quality:
{json.dumps(profile, indent=2)}

Return JSON exactly:
{{"summary": "...", "recommendations": ["...", "..."]}}
"""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )

        text = response.text.strip()

        if "```" in text:
            text = text.split("```")[1]

        return json.loads(text)

    except Exception as e:
        log_error("generate_table_summary", e)
        return _template_summary(table_name, columns, profile)


# ===========================
# NATURAL LANGUAGE QA
# ===========================

def answer_question(question, metadata, profiles, summaries):
    """Answer any user question about the database schema, relationships, data quality, or documentation."""

    context = json.dumps({
        "metadata": metadata,
        "profiles": profiles,
        "summaries": summaries
    })[:12000]   # avoid token overflow

    prompt = f"""
You are an intelligent data dictionary assistant. You answer any question about the database: schema, tables, columns, relationships (foreign keys), data quality, row counts, and AI-generated summaries.

Rules:
- Answer in clear, concise markdown. Use bullets or short paragraphs as appropriate.
- If the question is about schema/relationships/quality/docs, use the Context below to answer.
- If the question is unrelated to this database (e.g. general knowledge, other topics), reply briefly that you are focused on this database's schema and data dictionary only, and suggest rephrasing about tables, columns, or data quality.

Context:
{context}

User question:
{question}
"""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )

        return response.text.strip()

    except Exception as e:
        log_error("answer_question", e)
        return f"❌ AI error: {e}"


# ===========================
# SQL GENERATOR
# ===========================

def generate_sql(question, metadata):

    schema = {
        t: [c["column_name"] for c in cols]
        for t, cols in metadata["tables"].items()
    }

    prompt = f"""
You are an expert SQL generator.

Database schema:
{json.dumps(schema, indent=2)}

Write ONLY a valid SQL query.
No markdown.
No explanation.
No backticks.

Question:
{question}
"""

    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )

    sql = response.text.strip()

    # 🔥 CLEAN MARKDOWN IF PRESENT
    if "```" in sql:
        sql = sql.split("```")[1]
        sql = sql.replace("sql", "").strip()

    return sql

# ===========================
# SQL EXECUTOR
# ===========================

def execute_sql(sql):

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    try:
        cur.execute(sql)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]

        conn.close()
        return cols, rows

    except Exception as e:
        log_error("execute_sql", e)
        conn.close()
        return None, str(e)