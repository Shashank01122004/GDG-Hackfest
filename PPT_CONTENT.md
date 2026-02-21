# Intelligent Data Dictionary Agent — PPT Content

Use this for your presentation slides. Copy the sections you need.

---

## Slide 1: Title

**Intelligent Data Dictionary Agent**

- Hackathon: GDG Hackfest (Problem Statement 11)
- Team / Your Name
- One-line: *Automated, AI-enhanced data dictionaries with natural language chat*

---

## Slide 2: The Problem

**Why we built this**

- Database documentation is often **outdated, incomplete, or missing**
- Technical metadata (columns, types) has **no business context**
- Analysts and business users struggle to:
  - Understand what each table and column means
  - See how tables are related (e.g. orders → customers)
  - Know data quality (completeness, freshness, key health)
- Result: **slower analytics, wrong assumptions, duplicated effort**

---

## Slide 3: Our Solution

**Intelligent Data Dictionary Agent**

- **Connects** to your database (SQLite, PostgreSQL, SQL Server)
- **Extracts** full schema: tables, columns, relationships (foreign keys)
- **Profiles** data quality: completeness %, freshness, key health
- **Generates** business-friendly documentation (JSON + Markdown)
- **AI-enhanced** table summaries and usage recommendations
- **Chat interface**: ask questions in plain language and get answers about schema, relationships, and data quality

---

## Slide 4: Key Features

| Feature | What it does |
|--------|----------------|
| **Multi-DB support** | SQLite (demo), PostgreSQL, SQL Server via config |
| **Schema extraction** | Tables, columns, types, nullability, primary keys, **relationships (FKs)** |
| **Data quality** | Completeness %, uniqueness, **freshness** (date min/max), **key health** (null/duplicate PKs) |
| **AI summaries** | Business description + usage tips per table (OpenAI or template) |
| **Documentation** | JSON + **Markdown** data dictionary in `artifacts/` |
| **Natural language chat** | Ask “What tables exist?”, “How are orders linked to customers?”, “Data quality?” — get direct answers |

---

## Slide 5: High-Level Architecture

```
[ Your Database ]  →  [ Connector ]  →  [ Metadata Extractor ]  →  [ Profiler ]
         ↓                    ↓                     ↓                      ↓
    demo.db / PG / SS     config.py         tables, columns,         completeness,
                                              relationships           freshness, key health
         ↓
[ AI Engine ]  ←  metadata + profiles
     ↓
 summaries (per table) + NL answers in chat
     ↓
[ Doc Generator ]  →  artifacts/metadata.json, profiles.json, summaries.json, data_dictionary.md
     ↓
[ Streamlit Chat UI ]  →  User asks questions → Answers from metadata + profiles + summaries (or OpenAI)
```

---

## Slide 6: Tech Stack

- **Language:** Python 3.9+
- **DB:** SQLite (default), PostgreSQL, SQL Server
- **UI:** Streamlit (chat interface)
- **AI:** OpenAI API (optional) for summaries and free-form Q&A; template/keyword fallback without API key
- **Config:** `.env` (python-dotenv) for DB connection and `OPENAI_API_KEY`
- **Output:** JSON + Markdown artifacts

---

## Slide 7: End-to-End Flow

1. **Setup:** Configure DB (or use demo SQLite DB) and optionally `OPENAI_API_KEY`.
2. **Create DB:** Run `create_db.py` to create/reset demo DB (customers, orders).
3. **Pipeline:** Run `pipeline.py`:
   - Extract metadata (schema + relationships)
   - Profile all tables (quality metrics)
   - Generate AI/template summaries per table
   - Write JSON + Markdown to `artifacts/`
4. **Chat:** Run `streamlit run frontend/app.py` → users ask questions in natural language and get answers from metadata, profiles, and summaries (or OpenAI when key is set).

---

## Slide 8: What Gets Generated (Artifacts)

| File | Content |
|------|--------|
| `metadata.json` | Tables, columns (name, type, nullable, PK), relationships (FKs) |
| `profiles.json` | Per-table: row count, per-column completeness & unique count, freshness (date min/max), key health (null/duplicate PKs) |
| `summaries.json` | Per-table: business summary + usage recommendations (AI or template) |
| `data_dictionary.md` | Full data dictionary in Markdown (schema + quality + summaries) |

---

## Slide 9: Demo — Chat Examples

**User asks:** “What tables exist?”  
**Answer:** List of tables (e.g. customers, orders) with columns.

**User asks:** “How are orders linked to customers?”  
**Answer:** Relationships, e.g. `orders.customer_id` → `customers.id`.

**User asks:** “What is data quality like?”  
**Answer:** Row counts, key health (null_pks, duplicate_pks) per table.

With **OPENAI_API_KEY:** Any free-form question (e.g. “Explain the customers table”) gets an AI-generated answer using the same context.

---

## Slide 10: Project Structure (Key Files)

- `config.py` — DB type, path/URI, OpenAI key, artifacts dir
- `db_connector.py` — Connection for SQLite / Postgres / SQL Server
- `metadata_extractor.py` — Schema + relationships → `artifacts/metadata.json`
- `profiler.py` — Data quality → `artifacts/profiles.json`
- `ai_engine.py` — Table summaries + NL answers (OpenAI or template)
- `doc_generator.py` — Markdown data dictionary
- `pipeline.py` — One command: extract → profile → AI → save all artifacts
- `frontend/app.py` — Streamlit chat UI
- `create_db.py` — Demo SQLite DB (customers, orders)

---

## Slide 11: Optional / Future Enhancements

- Incremental updates when schema changes are detected
- Data lineage and table relationship diagrams
- SQL query suggestions based on user questions
- Data quality alerts and trend monitoring
- Support for Snowflake and more DBs

---

## Slide 12: Summary

- **Problem:** Missing or unclear database documentation; no business context.
- **Solution:** Automated extraction + profiling + AI summaries + Markdown docs + **natural language chat**.
- **Outcome:** One pipeline generates metadata, quality metrics, and docs; users ask questions in plain language and get immediate answers about schema, relationships, and data quality.

---

## One-liners for speaker notes

- “We connect to your database once, run a pipeline, and get a full data dictionary plus a chat where you ask things like ‘What tables exist?’ or ‘How are orders linked to customers?’.”
- “Without an API key we use templates and keyword matching; with OpenAI we generate business summaries and answer any natural language question about your schema and data quality.”
- “Everything is stored in `artifacts/` as JSON and Markdown so you can version and share the documentation.”
