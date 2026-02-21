""" Intelligent Data Dictionary Agent — Chat UI. Natural language Q&A over schema, data quality, and AI-generated summaries. """
import streamlit as st
import sys
from pathlib import Path
import tempfile
from pyvis.network import Network

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
METADATA_PATH = ARTIFACTS_DIR / "metadata.json"
PROFILES_PATH = ARTIFACTS_DIR / "profiles.json"
SUMMARIES_PATH = ARTIFACTS_DIR / "summaries.json"

RELATIONSHIP_COLORS = [
    "#FF6B00",  # vivid orange
    "#FF2D78",  # hot pink
    "#00E676",  # bright green
    "#FFEA00",  # vivid yellow
    "#00B0FF",  # sky blue
    "#FF1744",  # bright red
    "#D500F9",  # vivid purple
    "#00E5FF",  # cyan
    "#76FF03",  # lime
    "#FF9100",  # amber
    "#F50057",  # deep pink
    "#651FFF",  # deep purple
]


def ensure_artifacts():
    if METADATA_PATH.exists() and PROFILES_PATH.exists():
        return
    from pipeline import run_pipeline
    run_pipeline()


def load_artifacts():
    ensure_artifacts()
    from storage import load_json
    metadata  = load_json(METADATA_PATH)
    profiles  = load_json(PROFILES_PATH)  if PROFILES_PATH.exists()  else {}
    summaries = load_json(SUMMARIES_PATH) if SUMMARIES_PATH.exists() else {}
    return metadata, profiles, summaries


def compute_grid_positions(table_names, cols_per_row=3, x_gap=550, y_gap=420):
    positions = {}
    for i, name in enumerate(table_names):
        col = i % cols_per_row
        row = i // cols_per_row
        positions[name] = (col * x_gap + 100, row * y_gap + 100)
    return positions


def build_er_diagram(tables, relationships):
    table_names = list(tables.keys())
    positions   = compute_grid_positions(table_names, cols_per_row=3)

    # Map "table|col" → color for FK columns
    col_colors: dict[str, str] = {}
    for idx, r in enumerate(relationships):
        color = RELATIONSHIP_COLORS[idx % len(RELATIONSHIP_COLORS)]
        col_colors[f"{r['table']}|{r['column']}"] = color

    # We build a full custom HTML page instead of relying on pyvis HTML labels
    # This gives us 100% control over node rendering
    
    # Collect node data for custom rendering
    node_data = {}
    for table, cols in tables.items():
        col_rows = []
        for c in cols:
            col_key = f"{table}|{c['column_name']}"
            color   = col_colors.get(col_key, "#cccccc")
            if c["primary_key"]:
                col_rows.append({"name": c["column_name"], "color": "#FFD700", "icon": "🔑", "bold": True})
            elif col_key in col_colors:
                col_rows.append({"name": c["column_name"], "color": color, "icon": "⬡", "bold": True})
            else:
                col_rows.append({"name": c["column_name"], "color": "#aaaaaa", "icon": "", "bold": False})
        node_data[table] = {"cols": col_rows, "pos": positions[table]}

    # Build edge data
    edge_data = []
    for idx, r in enumerate(relationships):
        color = RELATIONSHIP_COLORS[idx % len(RELATIONSHIP_COLORS)]
        edge_data.append({
            "from": r["table"],
            "to":   r["ref_table"],
            "label": r["column"],
            "color": color,
        })

    # Serialize for JS
    import json

    nodes_js = []
    for table, data in node_data.items():
        x, y = data["pos"]
        # Build label as plain multiline text — pyvis handles this correctly
        lines = [table]
        lines.append("─" * max(len(table), 16))
        for c in data["cols"]:
            prefix = c["icon"] + " " if c["icon"] else "  "
            lines.append(prefix + c["name"])
        label = "\n".join(lines)

        # Per-column color info passed as title (tooltip) for reference
        col_html = "".join(
            f'<div style="color:{c["color"]};font-family:monospace;font-size:13px;">'
            f'{"<b>" if c["bold"] else ""}{c["icon"]} {c["name"]}{"</b>" if c["bold"] else ""}</div>'
            for c in data["cols"]
        )
        title_html = f'<div style="background:#1a2a3a;padding:8px;border-radius:6px;"><b style="color:#7ec8f7;font-size:14px;">{table}</b><hr style="border-color:#4a90d9;margin:4px 0"/>{col_html}</div>'

        nodes_js.append({
            "id":    table,
            "label": label,
            "title": title_html,
            "x":     x,
            "y":     y,
            "physics": False,
            "font": {
                "size": 14,
                "face": "monospace",
                "color": "#ffffff",
                "multi": False,
            },
            "color": {
                "background": "#1a2a3a",
                "border":     "#4a90d9",
                "highlight":  {"background": "#1a2a3a", "border": "#4a90d9"},
                "hover":      {"background": "#1a2a3a", "border": "#4a90d9"},
            },
            "shape":       "box",
            "borderWidth": 2,
            "margin":      {"top": 10, "right": 14, "bottom": 10, "left": 14},
            "widthConstraint": {"minimum": 180, "maximum": 260},
        })

    edges_js = []
    for e in edge_data:
        edges_js.append({
            "from":  e["from"],
            "to":    e["to"],
            "color": {"color": e["color"], "highlight": e["color"], "hover": e["color"]},
            "font":  {"size": 12, "color": e["color"], "strokeWidth": 0, "face": "monospace", "align": "middle"},
            "arrows": {"to": {"enabled": True, "scaleFactor": 1.0}},
            "smooth": {"type": "curvedCW", "roundness": 0.25},
            "width": 2,
        })

    nodes_json = json.dumps(nodes_js)
    edges_json = json.dumps(edges_js)

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: #0d1117; overflow: hidden; }}
  #er-graph {{ width: 100%; height: 880px; border: none; }}
</style>
<script src="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.js"></script>
<link  href="https://cdnjs.cloudflare.com/ajax/libs/vis/4.21.0/vis.min.css" rel="stylesheet"/>
</head>
<body>
<div id="er-graph"></div>
<script>
  var nodes = new vis.DataSet({nodes_json});
  var edges = new vis.DataSet({edges_json});

  var container = document.getElementById("er-graph");
  var data      = {{ nodes: nodes, edges: edges }};
  var options   = {{
    interaction: {{
      dragNodes:            false,
      dragView:             false,
      zoomView:             false,
      hover:                true,
      selectable:           false,
      selectConnectedEdges: false,
      navigationButtons:    false,
      keyboard:             false,
      tooltipDelay:         100
    }},
    physics: {{
      enabled: false
    }},
    edges: {{
      smooth: {{
        type:      "curvedCW",
        roundness: 0.25
      }}
    }}
  }};

  var network = new vis.Network(container, data, options);
</script>
</body>
</html>
"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".html", mode="w", encoding="utf-8") as f:
        f.write(html)
        return f.name


# ── Page setup ─────────────────────────────────────────────────────────────────
st.set_page_config(page_title="Data Dictionary Agent", layout="wide")
st.title("Intelligent Data Dictionary Agent")
st.caption("Ask questions about your database schema, relationships, and data quality in plain language.")

metadata, profiles, summaries = load_artifacts()

with st.expander("Try asking:", expanded=False):
    st.markdown("""
    - **What tables exist?** — List tables and columns
    - **What is the schema?** — Same as above
    - **How are orders linked to customers?** — Show relationships (foreign keys)
    - **What is data quality like?** — Row counts and key health
    """)

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Actions")
    if st.button("Refresh documentation"):
        from pipeline import run_pipeline
        run_pipeline()
        st.success("Documentation refreshed.")
        st.rerun()

    st.divider()
    st.subheader("Artifacts")
    if (ARTIFACTS_DIR / "data_dictionary.md").exists():
        with open(ARTIFACTS_DIR / "data_dictionary.md") as f:
            st.download_button(
                "Download Markdown", f.read(),
                file_name="data_dictionary.md", mime="text/markdown"
            )

    st.divider()
    st.subheader("Tables")
    tables_sidebar = metadata.get("tables", metadata)
    for t in (tables_sidebar.keys() if isinstance(tables_sidebar, dict) else []):
        st.text(t)

# ── Chat ───────────────────────────────────────────────────────────────────────
question = st.chat_input("Ask about your database...")
if question:
    from ai_engine import answer_question
    answer = answer_question(question, metadata, profiles, summaries)
    with st.chat_message("user"):
        st.write(question)
    with st.chat_message("assistant"):
        st.markdown(answer)

# ── ER Diagram ─────────────────────────────────────────────────────────────────
st.subheader("📊 Database ER Diagram")

tables        = metadata.get("tables", {})
relationships = metadata.get("relationships", [])

html_path = build_er_diagram(tables, relationships)
with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

st.components.v1.html(html_content, height=900, scrolling=False)

st.subheader("🧠 Ask in English → Get SQL Result")

nl_query = st.text_input("Ask a data question (e.g. most frequent product, total revenue, average price)")

if nl_query:
    from ai_engine import generate_sql, execute_sql

    sql = generate_sql(nl_query, metadata)

    st.code(sql, language="sql")

    cols, rows = execute_sql(sql)

    if isinstance(rows, str):
        st.error(rows)
    else:
        st.dataframe(rows, use_container_width=True)