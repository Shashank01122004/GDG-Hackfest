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


def _compute_layered_positions(tables, relationships, x_gap=480, y_gap=380):
    """Place tables in layers by FK dependency so edges flow left→right and cross less."""
    table_names = list(tables.keys())
    if not table_names:
        return {}
    # refs[t] = set of tables that t references (t has FK → ref_table)
    refs = {t: set() for t in table_names}
    for r in relationships:
        if not isinstance(r, dict):
            continue
        fr, to = r.get("table"), r.get("ref_table")
        if fr and to and fr in refs and to in refs and fr != to:
            refs[fr].add(to)
    # layer[t] = 0 if never a "from", else 1 + max(layer of refs)
    layer = {}
    for t in table_names:
        if not refs[t]:
            layer[t] = 0
        else:
            layer[t] = 1 + max(layer.get(r, 0) for r in refs[t])
    # Resolve in dependency order so refs are computed before dependents
    for _ in range(len(table_names) + 1):
        for t in table_names:
            if refs[t]:
                layer[t] = 1 + max(layer.get(r, 0) for r in refs[t])
    # Group by layer and assign (x, y): same layer = same x, spread y
    by_layer = {}
    for t, lv in layer.items():
        by_layer.setdefault(lv, []).append(t)
    for lv in by_layer:
        by_layer[lv].sort()
    origin_x, origin_y = 360, 380
    positions = {}
    for lv in sorted(by_layer.keys()):
        names = by_layer[lv]
        n = len(names)
        for row, name in enumerate(names):
            x = 180 + lv * x_gap
            y = 180 + row * y_gap
            positions[name] = (x, y)
    return positions


def build_er_diagram(tables, relationships):
    if not tables:
        return None
    table_names = list(tables.keys())
    positions   = _compute_layered_positions(tables, relationships)

    # Map "table|col" → color for FK columns
    col_colors: dict[str, str] = {}
    for idx, r in enumerate(relationships):
        if not isinstance(r, dict):
            continue
        fr, col = r.get("table"), r.get("column")
        if fr and col:
            col_colors[f"{fr}|{col}"] = RELATIONSHIP_COLORS[idx % len(RELATIONSHIP_COLORS)]

    # We build a full custom HTML page instead of relying on pyvis HTML labels
    # This gives us 100% control over node rendering
    
    # Connected tables per table (names only, no full detail of connected tables)
    connected_names: dict[str, set[str]] = {t: set() for t in table_names}
    for r in relationships:
        if not isinstance(r, dict):
            continue
        fr, to = r.get("table"), r.get("ref_table")
        if fr and to and fr in connected_names and to in connected_names and fr != to:
            connected_names[fr].add(to)
            connected_names[to].add(fr)

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
        node_data[table] = {"cols": col_rows, "pos": positions[table], "connected": sorted(connected_names.get(table, []))}

    # Build edge data
    edge_data = []
    for idx, r in enumerate(relationships):
        if not isinstance(r, dict):
            continue
        fr, to, col = r.get("table"), r.get("ref_table"), r.get("column")
        if not fr or not to:
            continue
        color = RELATIONSHIP_COLORS[idx % len(RELATIONSHIP_COLORS)]
        edge_data.append({
            "from": fr,
            "to":   to,
            "label": col or "",
            "color": color,
        })

    # Serialize for JS
    import json

    nodes_js = []
    for table, data in node_data.items():
        x, y = data["pos"]
        # Show only table name + key columns (PK/FK) in box for readability; max 6 lines
        key_cols = [c for c in data["cols"] if c["bold"]]  # PK and FK
        other_cols = [c for c in data["cols"] if not c["bold"]]
        display_cols = key_cols if key_cols else data["cols"][:5]  # fallback: first 5
        lines = [table, "─" * min(len(table), 20)]
        for c in display_cols[:6]:
            prefix = (c["icon"] + " ") if c["icon"] else "  "
            lines.append(prefix + c["name"])
        if (key_cols and len(other_cols) > 0) or len(data["cols"]) > 6:
            lines.append("  … hover for all")
        label = "\n".join(lines)

        # Plain-text tooltip: this table's columns + connected table names only (no full detail of connected tables)
        col_list = "\n".join(
            (c["icon"] + " " if c["icon"] else "  ") + c["name"] for c in data["cols"]
        )
        conn = data.get("connected", [])
        if conn:
            title_plain = f"{table}\n─────────────\n{col_list}\n─────────────\nConnected tables: {', '.join(conn)}"
        else:
            title_plain = f"{table}\n─────────────\n{col_list}"

        nodes_js.append({
            "id":    table,
            "label": label,
            "title": title_plain,
            "x":     x,
            "y":     y,
            "physics": False,
            "font": {
                "size": 15,
                "face": "monospace",
                "color": "#f0f6fc",
                "multi": False,
            },
            "color": {
                "background": "#161b22",
                "border":     "#58a6ff",
                "highlight":  {"background": "#21262d", "border": "#79c0ff"},
                "hover":      {"background": "#21262d", "border": "#79c0ff"},
            },
            "shape":       "box",
            "borderWidth": 2,
            "margin":      {"top": 14, "right": 18, "bottom": 14, "left": 18},
            "widthConstraint": {"minimum": 200, "maximum": 280},
        })

    edges_js = []
    for e in edge_data:
        edges_js.append({
            "from":   e["from"],
            "to":     e["to"],
            "label":  e["label"],
            "color":  {"color": e["color"], "highlight": e["color"], "hover": e["color"]},
            "font":   {
                "size": 12,
                "color": e["color"],
                "strokeWidth": 2,
                "strokeColor": "#0d1117",
                "face": "monospace",
                "align": "middle",
                "background": "rgba(13,17,23,0.85)",
            },
            "arrows": {"to": {"enabled": True, "scaleFactor": 1.0}},
            "smooth": {"type": "curvedCW", "roundness": 0.25},
            "width":  2,
        })

    nodes_json = json.dumps(nodes_js)
    edges_json = json.dumps(edges_js)

    # Embed local vis-network so diagram works inside Streamlit iframe (CDN often blocked)
    vis_lib_dir = PROJECT_ROOT / "lib" / "vis-9.1.2"
    vis_js_inline = ""
    vis_css_inline = ""
    if (vis_lib_dir / "vis-network.min.js").exists():
        raw = (vis_lib_dir / "vis-network.min.js").read_text(encoding="utf-8", errors="replace")
        vis_js_inline = raw.replace("</script>", "<\\/script>")
    if (vis_lib_dir / "vis-network.css").exists():
        vis_css_inline = (vis_lib_dir / "vis-network.css").read_text(encoding="utf-8", errors="replace")

    # If local lib missing, fall back to CDN
    if not vis_js_inline:
        vis_script_tag = '<script src="https://unpkg.com/vis-network@9.1.2/standalone/umd/vis-network.min.js"></script>'
        vis_css_inline = '<link href="https://unpkg.com/vis-network@9.1.2/dist/vis-network.min.css" rel="stylesheet"/>'
    else:
        vis_script_tag = "<script>\n" + vis_js_inline + "\n</script>"

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: #0d1117; overflow: hidden; }}
  #er-graph {{ width: 100%; height: 864px; border: none; background: #0d1117; }}
  #er-toolbar {{ padding: 8px 12px; background: #161b22; border-bottom: 1px solid #30363d; font-family: sans-serif; font-size: 13px; color: #8b949e; }}
  #er-toolbar button {{ background: #21262d; color: #58a6ff; border: 1px solid #30363d; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 12px; }}
  #er-toolbar button:hover {{ background: #30363d; border-color: #58a6ff; }}
  #er-toolbar .hint {{ margin-left: 12px; }}
  {vis_css_inline}
</style>
{vis_script_tag}
</head>
<body>
<div id="er-graph"></div>
<script>
  (function() {{
    if (typeof vis === "undefined") {{
      document.getElementById("er-graph").innerHTML = "<div style=\\"padding:20px;color:#8b949e;font-family:sans-serif;\\">Diagram library could not load. Refresh the page or check the console.</div>";
      return;
    }}
    var nodes = new vis.DataSet({nodes_json});
    var edges = new vis.DataSet({edges_json});
    var allNodes = nodes.get().slice();
    var allEdges = edges.get().slice();

    var container = document.getElementById("er-graph");
    var data = {{ nodes: nodes, edges: edges }};
    var options = {{
      interaction: {{
        dragNodes: false,
        dragView: true,
        zoomView: true,
        hover: true,
        selectable: true,
        selectConnectedEdges: true,
        navigationButtons: true,
        keyboard: false,
        tooltipDelay: 100
      }},
      physics: {{ enabled: false }},
      edges: {{ smooth: {{ type: "curvedCW", roundness: 0.2 }} }}
    }};

    var network = new vis.Network(container, data, options);

    // Fit view to all nodes so the diagram is visible (not blank)
    network.on("afterDrawing", function() {{
      network.fit({{ animation: {{ duration: 300 }} }});
    }});
    setTimeout(function() {{ network.fit({{ animation: {{ duration: 300 }} }}); }}, 100);

    function showOnlyConnected(nodeId) {{
      var connectedIds = new Set([nodeId]);
      allEdges.forEach(function(e) {{
        if (e.from === nodeId || e.to === nodeId) {{
          connectedIds.add(e.from);
          connectedIds.add(e.to);
        }}
      }});
      var filteredNodes = allNodes.filter(function(n) {{ return connectedIds.has(n.id); }});
      var filteredEdges = allEdges.filter(function(e) {{ return connectedIds.has(e.from) && connectedIds.has(e.to); }});
      nodes.clear();
      nodes.add(filteredNodes);
      edges.clear();
      edges.add(filteredEdges);
      network.fit({{ animation: {{ duration: 250 }} }});
    }}

    function showAll() {{
      nodes.clear();
      nodes.add(allNodes);
      edges.clear();
      edges.add(allEdges);
      network.fit({{ animation: {{ duration: 250 }} }});
    }}

    network.on("click", function(params) {{
      if (params.nodes.length > 0) showOnlyConnected(params.nodes[0]);
    }});
    network.on("doubleClick", function() {{ showAll(); }});
  }})();
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
tables_dict = metadata.get("tables", {})
if not isinstance(tables_dict, dict):
    tables_dict = {k: v for k, v in (metadata.items() if isinstance(metadata, dict) else []) if isinstance(v, list)}
relationships_list = metadata.get("relationships", [])
n_tables = len(tables_dict)
n_rels = len(relationships_list)

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
    rels = metadata.get("relationships", [])
    table_names = list(tables_sidebar.keys()) if isinstance(tables_sidebar, dict) else []
    # Connected tables per table (direct relationships)
    connected = {}
    for r in rels:
        t1, t2 = r.get("table"), r.get("ref_table")
        if t1 and t2:
            connected.setdefault(t1, set()).add(t2)
            connected.setdefault(t2, set()).add(t1)
    # FK column -> ref_table
    fk_ref = {(r.get("table"), r.get("column")): r.get("ref_table") for r in rels if r.get("table") and r.get("column") and r.get("ref_table")}

    if table_names:
        selected = st.selectbox("Select a table", ["—"] + table_names, key="sidebar_table_select", label_visibility="collapsed")
        if selected and selected != "—":
            cols = tables_sidebar.get(selected, [])
            st.markdown("**Columns**")
            for c in cols:
                name = c.get("column_name", c.get("name", ""))
                pk = c.get("primary_key", c.get("pk", False))
                ref = fk_ref.get((selected, name))
                if pk and not ref:
                    st.caption(f"🔑 {name} (PK)")
                elif ref:
                    st.caption(f"⬡ {name} (FK → {ref})")
                else:
                    st.caption(f"  {name}")
            conn = sorted(connected.get(selected, []))
            if conn:
                st.markdown("**Connected tables** (names only)")
                st.caption(", ".join(conn))
    else:
        for t in table_names:
            st.text(t)

# ── Tabs: Chatbot | ER Diagram | SQL ──────────────────────────────────────────
tab_chat, tab_er, tab_sql = st.tabs(["💬 Chatbot", "📊 ER Diagram", "🔍 SQL Query"])

with tab_chat:
    st.subheader("Ask about your database")
    st.caption("Schema, relationships, data quality, documentation.")
    # Form: Enter key or Ask button both submit
    with st.form("chat_form", clear_on_submit=False):
        question = st.text_input("Your question", placeholder="e.g. What tables exist? How are orders linked to customers?", key="chat_question")
        col_ask, _ = st.columns([1, 4])
        with col_ask:
            submitted = st.form_submit_button("Ask")
    # Suggestions below the input
    with st.expander("💡 Try asking:", expanded=False):
        st.markdown("""
        - **What tables exist?** — List tables and columns
        - **What is the schema?** — Same as above
        - **How are orders linked to customers?** — Show relationships (foreign keys)
        - **What is data quality like?** — Row counts and key health
        """)
    if submitted and question:
        from ai_engine import answer_question
        answer = answer_question(question.strip(), metadata, profiles, summaries)
        with st.chat_message("user"):
            st.write(question)
        with st.chat_message("assistant"):
            st.markdown(answer)

with tab_er:
    st.subheader("Database ER Diagram")
    # Use metadata directly so ER diagram always gets the same tables as the rest of the app
    tables_raw = metadata.get("tables", {})
    if not isinstance(tables_raw, dict):
        tables_raw = {}
    rels_er = metadata.get("relationships", [])
    tables_for_er = {}
    for tname, cols in tables_raw.items():
        if not isinstance(cols, list):
            continue
        tables_for_er[tname] = [
            {
                "column_name": c.get("column_name") or c.get("name", ""),
                "primary_key": c.get("primary_key") if "primary_key" in c else c.get("pk", False),
            }
            for c in cols
        ]
    n_er_tables = len(tables_for_er)
    st.caption(f"Showing **{n_er_tables}** tables and **{len(rels_er)}** relationships. Click a table to show only it and connected tables; pan and zoom to explore.")
    st.caption("After adding or removing tables in the database, click **Refresh documentation** in the sidebar to update this diagram.")
    if n_er_tables == 0:
        st.info("No table metadata available. Click **Refresh documentation** in the sidebar to generate schema and then reload.")
    else:
        html_path = build_er_diagram(tables_for_er, rels_er)
        if html_path:
            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            st.components.v1.html(html_content, height=900, scrolling=False)
        else:
            st.warning("Could not generate the diagram.")

with tab_sql:
    st.subheader("Ask in English → Get SQL Result")
    st.caption("Describe what you want; the app will generate and run SQL. DROP/DELETE/TRUNCATE and other destructive commands are blocked from execution to prevent data loss (SQL is still shown).")
    nl_query = st.text_input("Ask a data question", placeholder="e.g. most frequent product, total revenue, average price", key="nl_sql_input")
    if nl_query:
        from ai_engine import generate_sql, execute_sql
        sql = generate_sql(nl_query, metadata)
        st.code(sql, language="sql")
        cols, rows = execute_sql(sql)
        if isinstance(rows, str):
            st.error(rows)
        else:
            st.dataframe(rows, use_container_width=True)