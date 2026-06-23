import os
import sys
import streamlit as st
import streamlit.components.v1 as components
import networkx as nx
from pyvis.network import Network

# Add root folder to sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Page configuration — must be the very first Streamlit call
st.set_page_config(
    page_title="GraphRAG Employee Resource Discovery",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Premium CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&family=Space+Grotesk:wght@400;600&display=swap');

html, body, [class*="css"] { font-family: 'Outfit', sans-serif; }
h1, h2, h3 { font-family: 'Space Grotesk', sans-serif; font-weight: 700; letter-spacing: -0.5px; }

.glass-card {
    background: rgba(17,25,40,0.75);
    backdrop-filter: blur(16px) saturate(180%);
    border: 1px solid rgba(255,255,255,0.075);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 16px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.37);
}
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.82rem;
    font-weight: 600;
    margin: 2px 4px 2px 0;
}
.badge-hybrid  { background:rgba(29,185,84,0.15);  color:#1DB954; border:1px solid #1DB954; }
.badge-graph   { background:rgba(0,191,255,0.15);  color:#00BFFF; border:1px solid #00BFFF; }
.badge-vector  { background:rgba(147,112,219,0.15); color:#9370DB; border:1px solid #9370DB; }
.badge-skill   { background:rgba(255,165,0,0.12);  color:#FFA500; border:1px solid #FFA500; }
.badge-bench   { background:rgba(255,165,0,0.15);  color:#FFA500; border:1px solid #FFA500; }
.badge-proj    { background:rgba(128,128,128,0.15); color:#aaa;    border:1px solid #555; }
.main-title {
    background: linear-gradient(135deg,#00C6FF 0%,#0072FF 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    font-size: 2.6rem; margin-bottom: 6px;
}
.cand-card {
    border-left: 4px solid #0072FF;
    background: rgba(0,114,255,0.05);
    border-radius: 0 8px 8px 0;
    padding: 12px 16px;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# ── Session State ────────────────────────────────────────────────────────────
if "gemini_key" not in st.session_state:
    st.session_state["gemini_key"] = os.environ.get("GEMINI_API_KEY", "")
if "pipeline_ready" not in st.session_state:
    st.session_state["pipeline_ready"] = False

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🕸️ GraphRAG Settings")
    host = st.text_input("HugeGraph Host", value="127.0.0.1")
    port = st.text_input("HugeGraph Port", value="8081")

    graph = st.text_input("Graph Name", value="hugegraph")

    api_key_input = st.text_input(
        "🔑 Google Gemini API Key",
        value=st.session_state["gemini_key"],
        type="password",
        help="Paste your Gemini API key here. Without it, RAG uses a smart keyword fallback."
    )
    if api_key_input:
        st.session_state["gemini_key"] = api_key_input

    st.markdown("---")
    st.markdown("""
### ⚡ Quick Setup
1. Start HugeGraph server (see README)
2. `python ingest_hugegraph.py`
3. `python create_embeddings.py`
4. `streamlit run app.py`
    """)
    st.markdown("---")
    st.info("FastAPI docs: `http://127.0.0.1:8000/docs`\n\nStart with: `uvicorn api.app:app`")

# ── Pipeline init (cached) ────────────────────────────────────────────────────
@st.cache_resource(show_spinner="Connecting to GraphRAG pipeline…")
def load_pipeline(h, p, g):
    from rag.rag_pipeline import GraphRAGPipeline
    try:
        pl = GraphRAGPipeline(host=h, port=p, graph=g)
        return pl, None
    except Exception as e:
        return None, str(e)

pipeline, pipeline_err = load_pipeline(host, port, graph)

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("<h1 class='main-title'>Employee Resource Discovery System</h1>", unsafe_allow_html=True)
st.markdown(
    "<p style='font-size:1.1rem;color:#888;margin-top:-8px;'>"
    "Intelligent GraphRAG talent matching · Apache HugeGraph · FAISS · Google Gemini"
    "</p>",
    unsafe_allow_html=True
)

if pipeline is None:
    st.error(
        f"❌ **GraphRAG Pipeline offline.** Error: `{pipeline_err}`\n\n"
        "Make sure Apache HugeGraph Server is running and you have run `ingest_hugegraph.py` "
        "and `create_embeddings.py`. See the sidebar for the quick-start guide."
    )
    st.stop()

st.success("✅ Pipeline connected to HugeGraph & FAISS index loaded.", icon="✅")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🔍 AI Employee Search",
    "👤 Profile & Graph View",
    "⚖️ Skill Gap Analyzer",
    "📋 Project Staffing"
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — AI NATURAL LANGUAGE SEARCH
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("### 🔍 Natural Language Talent Query")
    st.write(
        "Describe what you need in plain English. The system extracts intent, "
        "filters the graph, searches FAISS embeddings, fuses results, and generates an AI report."
    )

    query = st.text_input(
        "Manager Query",
        value="Find available developers with Python and Machine Learning skills",
        placeholder="e.g. Who are bench employees with Banking domain and AWS certification?"
    )
    col_n, _, col_btn = st.columns([1, 3, 1])
    with col_n:
        top_n = st.slider("Top N Candidates", 1, 10, 5)
    with col_btn:
        st.write("")
        search_btn = st.button("⚡ Run Hybrid GraphRAG", type="primary", use_container_width=True)

    if search_btn and query.strip():
        with st.spinner("Running Hybrid GraphRAG pipeline…"):
            result = pipeline.run_pipeline(
                query_text=query,
                api_key=st.session_state["gemini_key"] or None,
                top_n=top_n
            )

        intent = result.get("intent", {})
        candidates = result.get("candidates", [])
        explanation = result.get("explanation", "")

        # Intent badges
        st.markdown("#### ⚡ Extracted Query Intent")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.caption("Required Skills")
            for s in (intent.get("skills") or []):
                st.markdown(f"<span class='badge badge-skill'>{s}</span>", unsafe_allow_html=True)
            if not intent.get("skills"):
                st.markdown("_None detected_")
        with c2:
            st.caption("Domain Focus")
            dom = intent.get("domain") or "Any"
            st.markdown(f"<span class='badge badge-hybrid'>{dom}</span>", unsafe_allow_html=True)
        with c3:
            st.caption("Availability Filter")
            sta = intent.get("status") or "Any"
            st.markdown(f"<span class='badge badge-bench'>{sta}</span>", unsafe_allow_html=True)
        with c4:
            st.caption("Certifications")
            for c in (intent.get("certifications") or []):
                st.markdown(f"<span class='badge badge-graph'>{c}</span>", unsafe_allow_html=True)
            if not intent.get("certifications"):
                st.markdown("_None detected_")

        st.markdown("---")

        # LLM report
        st.markdown("#### 📄 AI Talent Acquisition Report")
        st.markdown(explanation)

        # Candidate cards
        if candidates:
            st.markdown("#### 👥 Matched Candidate Details")
            for cand in candidates:
                mt = cand.get("match_type", "Vector Match")
                badge_cls = "badge-hybrid" if "Hybrid" in mt else ("badge-graph" if "Graph" in mt else "badge-vector")
                status_cls = "badge-bench" if cand.get("status") == "BENCH" else "badge-proj"

                with st.expander(
                    f"**{cand.get('name','?')}** ({cand.get('emp_id','?')}) "
                    f"— {cand.get('designation','?')} "
                    f"| Score: {cand.get('hybrid_score',0):.3f} [{mt}]"
                ):
                    ca, cb = st.columns(2)
                    with ca:
                        st.markdown(f"**Experience:** {cand.get('experience_years','?')} years")
                        st.markdown(f"**Location:** {cand.get('location','?')}")
                        st.markdown(f"**Domain:** {cand.get('domain','?')}")
                        st.markdown(
                            f"**Status:** <span class='badge {status_cls}'>{cand.get('status','?')}</span>",
                            unsafe_allow_html=True
                        )
                    with cb:
                        st.markdown(f"**Skills:** {', '.join(cand.get('skills',[]))}")
                        if cand.get("certifications"):
                            st.markdown(f"**Certifications:** {', '.join(cand['certifications'])}")
                        if cand.get("projects"):
                            st.markdown(f"**Past Projects:** {', '.join(cand['projects'])}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — PROFILE & PYVIS GRAPH
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### 👤 Employee Profile Viewer & Network Graph")

    # Get all employee IDs for selector
    try:
        raw_ids = pipeline.queries.execute_gremlin("g.V().hasLabel('Employee').id()")
        emp_options = sorted([pipeline.queries._parse_id(x) for x in raw_ids])
    except Exception:
        emp_options = [f"E{i:04d}" for i in range(1, 1001)]

    selected_emp = st.selectbox("Select Employee", emp_options)

    if selected_emp:
        details = pipeline.queries.get_employee_details(selected_emp)
        if not details:
            st.warning(f"Could not fetch details for {selected_emp}. Is HugeGraph running?")
        else:
            left, right = st.columns([1, 1.2])

            with left:
                status_cls = "badge-bench" if details["status"] == "BENCH" else "badge-proj"
                st.markdown(f"### {details['name']} `{details['emp_id']}`")
                st.markdown(
                    f"**Designation:** {details['designation']} &nbsp;|&nbsp; "
                    f"**Experience:** {details['experience_years']} yrs &nbsp;|&nbsp; "
                    f"**Location:** {details['location']}",
                    unsafe_allow_html=True
                )
                st.markdown(
                    f"**Status:** <span class='badge {status_cls}'>{details['status']}</span>",
                    unsafe_allow_html=True
                )
                st.markdown(f"**Domain Specialization:** {details['domain']}")

                st.markdown("**Skills:**")
                skill_badges = "".join(
                    f"<span class='badge badge-skill'>{s}</span>" for s in details["skills"]
                )
                st.markdown(skill_badges or "_None_", unsafe_allow_html=True)

                if details["certifications"]:
                    st.markdown("**Certifications:**")
                    cert_badges = "".join(
                        f"<span class='badge badge-graph'>{c}</span>" for c in details["certifications"]
                    )
                    st.markdown(cert_badges, unsafe_allow_html=True)

                if details["projects"]:
                    st.markdown("**Previous Projects:**")
                    for proj in details["projects"]:
                        st.markdown(f"- {proj}")

                st.markdown("---")
                st.markdown("##### 👥 Top Similar Employees (by shared skills)")
                try:
                    similar = pipeline.queries.find_similar_employees(selected_emp, limit=3)
                    if similar:
                        for sim_id, cnt in similar:
                            sd = pipeline.queries.get_employee_details(sim_id)
                            if sd:
                                st.markdown(
                                    f"- **{sd['name']}** `{sim_id}` — {sd['designation']} "
                                    f"({cnt} shared skills)"
                                )
                    else:
                        st.write("No similar employees found.")
                except Exception as e:
                    st.write(f"Could not fetch similar employees: {e}")

            with right:
                st.markdown("#### 🕸️ Local Neighborhood Graph")

                # Build graph
                G = nx.Graph()
                EMP_CLR  = "#FFD700"
                SKILL_CLR = "#FF6B6B"
                PROJ_CLR  = "#A29BFE"
                DOM_CLR   = "#55E6C1"
                CERT_CLR  = "#F3A683"

                G.add_node(
                    details["emp_id"],
                    label=details["name"],
                    title=f"Employee · {details['designation']}",
                    color=EMP_CLR, size=28
                )
                # Domain
                if details["domain"]:
                    G.add_node(details["domain"], label=details["domain"],
                               title="Domain", color=DOM_CLR, size=18)
                    G.add_edge(details["emp_id"], details["domain"], label="BELONGS_TO_DOMAIN")
                # Skills
                for sk in details["skills"]:
                    G.add_node(sk, label=sk, title="Skill", color=SKILL_CLR, size=14)
                    G.add_edge(details["emp_id"], sk, label="HAS_SKILL")
                # Certs
                for ct in details["certifications"]:
                    G.add_node(ct, label=ct, title="Certification", color=CERT_CLR, size=14)
                    G.add_edge(details["emp_id"], ct, label="HAS_CERTIFICATION")
                # Projects
                for pr in details["projects"]:
                    G.add_node(pr, label=pr, title="Project", color=PROJ_CLR, size=14)
                    G.add_edge(details["emp_id"], pr, label="WORKED_ON")

                net = Network(height="480px", width="100%", bgcolor="#0F172A", font_color="#FFFFFF")
                net.from_nx(G)
                net.set_options("""
{
  "physics": {
    "barnesHut": {
      "gravitationalConstant": -3500,
      "centralGravity": 0.3,
      "springLength": 100
    },
    "minVelocity": 0.75
  }
}
""")
                os.makedirs("temp", exist_ok=True)
                html_path = os.path.join("temp", f"graph_{selected_emp}.html")
                net.save_graph(html_path)
                with open(html_path, "r", encoding="utf-8") as f:
                    html_str = f.read()
                components.html(html_str, height=490)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — SKILL GAP ANALYZER
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### ⚖️ Project Skill Gap Analyzer")
    st.write("Select an employee and a project to see which required skills they have and which are missing.")

    sg_col1, sg_col2 = st.columns(2)
    with sg_col1:
        sg_emp = st.selectbox("Select Employee", [f"E{i:04d}" for i in range(1, 1001)], key="sg_emp")
    with sg_col2:
        sg_proj = st.selectbox("Select Project", [f"P{i:03d}" for i in range(1, 51)], key="sg_proj")

    if sg_emp and sg_proj:
        gap = pipeline.queries.analyze_skill_gap(sg_emp, sg_proj)
        emp_det = pipeline.queries.get_employee_details(sg_emp)

        # Get project name
        try:
            pnames = pipeline.queries.execute_gremlin(f"g.V('{sg_proj}').values('name')")
            pname = pnames[0] if pnames else sg_proj
        except Exception:
            pname = sg_proj

        emp_name = emp_det["name"] if emp_det else sg_emp
        st.markdown(f"#### Gap Analysis: **{emp_name}** vs **{pname}**")

        total_req = len(gap["required_skills"])
        matched   = len(gap["matching_skills"])
        pct = (matched / total_req * 100) if total_req > 0 else 100.0

        m1, m2, m3 = st.columns(3)
        m1.metric("Required Skills", total_req)
        m2.metric("Skills Matched", matched)
        m3.metric("Coverage", f"{pct:.1f}%")

        st.progress(int(pct))

        g1, g2, g3 = st.columns(3)
        with g1:
            st.markdown("##### ✅ Matching Skills")
            if gap["matching_skills"]:
                for s in gap["matching_skills"]:
                    st.markdown(f"<span class='badge badge-hybrid'>{s}</span>", unsafe_allow_html=True)
            else:
                st.info("None match")
        with g2:
            st.markdown("##### ❌ Missing Skills")
            if gap["missing_skills"]:
                for s in gap["missing_skills"]:
                    st.markdown(f"<span class='badge badge-skill'>{s}</span>", unsafe_allow_html=True)
            else:
                st.success("100% coverage — no gaps!")
        with g3:
            st.markdown("##### 📋 All Employee Skills")
            for s in gap["employee_skills"]:
                st.markdown(f"- {s}")

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 — PROJECT STAFFING
# ═══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("### 📋 Automated Project Staffing")
    st.write(
        "Use hard graph filters (skills AND domain AND certifications AND availability) "
        "to find exact matching employees for a new project."
    )

    sf1, sf2 = st.columns(2)
    with sf1:
        sel_skills = st.multiselect("Required Skills (all must match)", pipeline.skills_list)
        sel_domain = st.selectbox("Domain Focus", [None] + pipeline.domains_list, format_func=lambda x: x or "Any")
    with sf2:
        sel_certs  = st.multiselect("Required Certifications", pipeline.certs_list)
        bench_only = st.checkbox("Bench employees only (immediately available)", value=True)

    run_staffing = st.button("🔎 Search Staffing Database", type="primary")

    if run_staffing:
        status_val = "BENCH" if bench_only else None
        with st.spinner("Querying HugeGraph…"):
            matched_ids = pipeline.queries.find_employees_hybrid_filters(
                skills=sel_skills or None,
                domain=sel_domain,
                certs=sel_certs or None,
                status=status_val
            )

        st.markdown(f"#### Found **{len(matched_ids)}** employees matching all filters")

        if matched_ids:
            for idx, eid in enumerate(matched_ids[:10]):
                det = pipeline.queries.get_employee_details(eid)
                if not det:
                    continue
                sc = "🟠" if det["status"] == "BENCH" else "🔘"
                with st.expander(f"{idx+1}. {det['name']} ({eid}) — {det['designation']} {sc}"):
                    ca, cb = st.columns(2)
                    with ca:
                        st.write(f"**Experience:** {det['experience_years']} yrs")
                        st.write(f"**Location:** {det['location']}")
                        st.write(f"**Domain:** {det['domain']}")
                        st.write(f"**Status:** {det['status']}")
                    with cb:
                        st.write(f"**Skills:** {', '.join(det['skills'])}")
                        if det["certifications"]:
                            st.write(f"**Certifications:** {', '.join(det['certifications'])}")
                        if det["projects"]:
                            st.write(f"**Past Projects:** {', '.join(det['projects'])}")
        else:
            st.warning(
                "No candidates match all filters simultaneously. "
                "Try relaxing constraints (e.g. remove a skill or allow on-project employees)."
            )
