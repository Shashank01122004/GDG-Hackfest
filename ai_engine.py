import json
import os
from google import genai

MODEL = "models/gemini-2.5-flash"
API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=API_KEY)


# ---------------------------
# Template fallback
# ---------------------------

def _template_summary(table_name, columns, profile):
    cols = ", ".join(c["column_name"] for c in columns[:6])
    if len(columns) > 6:
        cols += f" + {len(columns)-6} more"

    rows = profile.get("total_rows", 0)

    summary = f"{table_name} contains {rows} records describing {cols}."
    recs = [
        "Use for analytics and reporting",
        "Validate keys before joins",
        "Monitor data quality regularly"
    ]
    return {"summary": summary, "recommendations": recs}


# ---------------------------
# AI Summary Generator
# ---------------------------

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

    except Exception:
        return _template_summary(table_name, columns, profile)


# ---------------------------
# Natural Language QA
# ---------------------------

def answer_question(question, metadata, profiles, summaries):

    context = json.dumps({
        "metadata": metadata,
        "profiles": profiles,
        "summaries": summaries
    })[:12000]

    prompt = f"""
You are an intelligent data dictionary assistant.

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

    except Exception:
        return "Unable to answer right now — please try again."