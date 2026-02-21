# Intelligent Data Dictionary Agent CHASERS

**Hackathon: Intelligent Data Dictionary Agent (ps11)**

A software-only solution that connects to databases (SQLite, PostgreSQL, SQL Server), extracts schema metadata, analyzes data quality, and produces AI-enhanced documentation. An interactive chat interface lets users query and understand the data in natural language.

---

## Features

- **Multi-database support**: SQLite (default), PostgreSQL, SQL Server via config/env
- **Schema extraction**: Tables, columns, data types, nullability, primary keys, and **relationships** (foreign keys)
- **Data quality profiling**: Completeness %, unique counts, **freshness** (min/max for date columns), **key health** (null PKs, duplicate PKs)
- **AI-enhanced summaries**: Business-friendly table descriptions and usage recommendations (OpenAI when `OPENAI_API_KEY` is set; template fallback otherwise)
- **Documentation**: JSON + **Markdown** data dictionary saved under `artifacts/`
- **Conversational chat**: Natural language questions about schema, relationships, and data quality (NL answers with OpenAI; keyword-based answers without)

---

## Quick Start

### 1. Clone and install

```bash
cd hackfest
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. (Optional) Configure database and AI

Copy `.env.example` to `.env` and edit:

- **DB**: Default is SQLite `demo.db` in the project root. For PostgreSQL/SQL Server, set `DB_TYPE` and the corresponding URI.
- **AI**: Set `OPENAI_API_KEY` for business summaries and natural language chat answers. Without it, template-based summaries and keyword answers are used.

### 3. Create demo database (if using SQLite default)

```bash
python3 create_db.py
```

### 4. Generate documentation (metadata + profiles + AI summaries + Markdown)

```bash
python3 pipeline.py
```

This writes:

- `artifacts/metadata.json` — schema and relationships  
- `artifacts/profiles.json` — data quality metrics  
- `artifacts/summaries.json` — AI/template table summaries  
- `artifacts/data_dictionary.md` — full data dictionary in Markdown  

### 5. Run the Streamlit chat app

```bash
streamlit run frontend/app.py
```

(If the command is not found, activate the venv first: `source venv/bin/activate`, or run `./venv/bin/streamlit run frontend/app.py`.)

Open the URL (e.g. http://localhost:8501). You can:

- **Ask in natural language**: e.g. “What tables exist?”, “How are orders linked to customers?”, “What is data quality like?”
- **Refresh documentation**: Sidebar → “Refresh documentation” (re-runs pipeline)
- **Download Markdown**: Sidebar → “Download Markdown” (data dictionary)

If `artifacts/` is empty, the app runs the pipeline once on first load.

---

## How to test the Streamlit app

1. **Start the app** (from project root):
   ```bash
   streamlit run frontend/app.py
   ```
   If `streamlit` is not found: `source venv/bin/activate` then run the command again, or use `./venv/bin/streamlit run frontend/app.py`.

2. **In the chat box at the bottom**, type one of these and press Enter:

   | What to type | What you should see |
   |--------------|----------------------|
   | `What tables exist?` | List of tables (e.g. customers, orders) and their columns. |
   | `What is the schema?` | Same: tables and columns. |
   | `How are orders linked to customers?` or `relationships` | Foreign key: `orders.customer_id` → `customers.id`. |
   | `What is data quality like?` or `data quality` | Row counts and key health (null_pks, duplicate_pks) per table. |

3. **Sidebar:** Use **Refresh documentation** to re-run the pipeline; use **Download Markdown** to get the data dictionary file.

4. **If the app shows errors:** Run `python3 create_db.py` and `python3 pipeline.py` from project root, then start the app again.

5. **With OpenAI:** Set `OPENAI_API_KEY` in `.env`, run `python3 pipeline.py`, then ask free-form questions (e.g. "Explain the customers table") for AI answers.

---

## How It Works

1. **Config** (`config.py`): DB type and path/URI, `OPENAI_API_KEY`, artifacts directory. Loads `.env` if `python-dotenv` is installed.

2. **DB connector** (`db_connector.py`): `get_connection()` returns a connection for the configured DB (SQLite by default; PostgreSQL/SQL Server when set and dependencies installed).

3. **Metadata extractor** (`metadata_extractor.py`): Reads tables, columns (name, type, nullable, PK), and **relationships** (FKs). Saves to `artifacts/metadata.json`.

4. **Profiler** (`profiler.py`): For each table: row count, per-column **completeness** and **unique count**, **freshness** (min/max for date-like columns), **key health** (null/duplicate PKs). Saves to `artifacts/profiles.json`.

5. **AI engine** (`ai_engine.py`):  
   - **Table summaries**: Business summary + recommendations per table (OpenAI or template).  
   - **Chat**: Answers natural language questions using metadata + profiles + summaries (OpenAI or keyword-based).

6. **Doc generator** (`doc_generator.py`): Builds a single Markdown data dictionary from metadata, profiles, and summaries; saved as `artifacts/data_dictionary.md`.

7. **Pipeline** (`pipeline.py`): Runs extract → profile → AI summaries → save JSON + Markdown. Single entry point for “refresh documentation”.

8. **Frontend** (`frontend/app.py`): Streamlit chat UI; loads artifacts (or runs pipeline once), then answers questions via `ai_engine.answer_question`.

---

## Project layout

```
hackfest/
├── config.py           # DB and OpenAI config
├── db_connector.py     # DB connection (SQLite / Postgres / SQL Server)
├── metadata_extractor.py  # Schema + relationships
├── profiler.py         # Data quality (completeness, freshness, key health)
├── ai_engine.py        # Table summaries + NL answers
├── doc_generator.py    # Markdown data dictionary
├── pipeline.py         # Full run: extract → profile → AI → docs
├── storage.py          # JSON read/write
├── create_db.py        # Demo SQLite DB (customers, orders)
├── frontend/
│   └── app.py          # Streamlit chat UI
├── artifacts/          # Generated (metadata, profiles, summaries, data_dictionary.md)
├── requirements.txt
├── .env.example
└── README.md
```

---

## Testing the flow

1. **Reset DB and regenerate everything**

   ```bash
   python3 create_db.py
   python3 pipeline.py
   ```

2. **Inspect artifacts**

   - `cat artifacts/metadata.json`
   - `cat artifacts/profiles.json`
   - `cat artifacts/data_dictionary.md`

3. **Chat**

   ```bash
   streamlit run frontend/app.py
   ```

   Try: “What tables are there?”, “How are customers and orders connected?”, “Summarize data quality.”

4. **Optional: OpenAI**

   Set `OPENAI_API_KEY` in `.env` and run the pipeline and chat again for AI-generated summaries and full natural language answers.

---

## Optional features (for extension)

- Incremental updates when schema changes are detected  
- Data lineage / table relationship visualizations  
- SQL query suggestions from user questions  
- Data quality alerts and trend monitoring  

---

## License

Use as per hackathon rules.
