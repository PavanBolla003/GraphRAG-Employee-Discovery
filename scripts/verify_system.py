"""
System verification script.
Run after all setup steps to confirm every component is working correctly.
Usage: python scripts/verify_system.py
"""
import os, sys, json

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

PASS = "\033[92m[PASS]\033[0m"
FAIL = "\033[91m[FAIL]\033[0m"
SKIP = "\033[93m[SKIP]\033[0m"
INFO = "\033[94m[INFO]\033[0m"

results = []

def check(name, fn):
    try:
        msg = fn()
        print(f"  {PASS} {name}" + (f": {msg}" if msg else ""))
        results.append((name, True))
    except Exception as e:
        print(f"  {FAIL} {name}: {e}")
        results.append((name, False))

print("\n=== GraphRAG Employee Resource Discovery — System Verification ===\n")

# 1. CSV files
print("1. Data Files")
def check_csvs():
    files = ["employees.csv","skills.csv","domains.csv","projects.csv",
             "certifications.csv","employee_skills.csv","employee_projects.csv",
             "employee_certifications.csv","employee_domains.csv","project_skills.csv"]
    missing = [f for f in files if not os.path.exists(os.path.join("data", f))]
    if missing:
        raise FileNotFoundError(f"Missing: {missing}")
    import csv
    with open("data/employees.csv") as f:
        cnt = sum(1 for _ in csv.DictReader(f))
    return f"{cnt} employees"

check("CSV files present", check_csvs)

def check_profiles():
    profile_dir = "data/profiles"
    if not os.path.exists(profile_dir):
        raise FileNotFoundError("data/profiles/ missing")
    count = len([f for f in os.listdir(profile_dir) if f.endswith(".txt")])
    if count < 900:
        raise ValueError(f"Only {count} profiles found (expected ~1000)")
    return f"{count} profile files"

check("Employee text profiles", check_profiles)

# 2. FAISS index
print("\n2. FAISS Vector Store")
def check_faiss_index():
    import faiss
    index_path   = "embeddings/employee_index.bin"
    mapping_path = "embeddings/employee_ids.json"
    if not os.path.exists(index_path):
        raise FileNotFoundError("embeddings/employee_index.bin not found — run create_embeddings.py")
    if not os.path.exists(mapping_path):
        raise FileNotFoundError("embeddings/employee_ids.json not found")
    idx = faiss.read_index(index_path)
    with open(mapping_path) as f:
        ids = json.load(f)
    if idx.ntotal != len(ids):
        raise ValueError(f"Mismatch: {idx.ntotal} vectors vs {len(ids)} IDs")
    return f"{idx.ntotal} vectors, dim={idx.d}"

check("FAISS index loaded", check_faiss_index)

def check_vector_search():
    from embeddings.vector_store import VectorStore
    vs = VectorStore()
    if not vs.load():
        raise RuntimeError("VectorStore.load() returned False")
    results = vs.search("Python developer Machine Learning", top_k=3)
    if not results:
        raise ValueError("Search returned no results")
    return f"top result: {results[0]['emp_id']} (score={results[0]['score']:.3f})"

check("FAISS semantic search", check_vector_search)

# 3. HugeGraph connectivity
print("\n3. Apache HugeGraph")
def check_hugegraph_connection():
    from pyhugegraph.client import PyHugeClient
    client = PyHugeClient("127.0.0.1", "8081", user="admin", pwd="admin", graph="hugegraph")
    result = client.gremlin().exec("g.V().count()")

    return f"connected, vertex count={result[0]}"

check("HugeGraph Server reachable", check_hugegraph_connection)

def check_hugegraph_data():
    from pyhugegraph.client import PyHugeClient
    client = PyHugeClient("127.0.0.1", "8081", user="admin", pwd="admin", graph="hugegraph")

    emp_count  = client.gremlin().exec("g.V().hasLabel('Employee').count()")[0]
    skill_count = client.gremlin().exec("g.V().hasLabel('Skill').count()")[0]
    edge_count  = client.gremlin().exec("g.E().count()")[0]
    if emp_count < 900:
        raise ValueError(f"Only {emp_count} employees in graph — run ingest_hugegraph.py")
    return f"{emp_count} employees, {skill_count} skills, {edge_count} edges"

check("HugeGraph data ingested", check_hugegraph_data)

def check_graph_queries():
    from graph_queries import HugeGraphQueries
    q = HugeGraphQueries()
    bench = q.find_bench_employees()
    if not bench:
        raise ValueError("No BENCH employees found")
    python_devs = q.find_employees_by_skill("Python")
    gap = q.analyze_skill_gap(bench[0], "P001")
    return f"{len(bench)} bench, {len(python_devs)} Python devs, gap keys: {list(gap.keys())}"

check("Gremlin traversals (bench, skill, gap)", check_graph_queries)

# 4. RAG Pipeline
print("\n4. Hybrid GraphRAG Pipeline")
def check_rag_intent():
    from rag.rag_pipeline import GraphRAGPipeline
    pl = GraphRAGPipeline()
    intent = pl.extract_intent_fallback("Find bench developers with Python and Machine Learning in Banking")
    if "Python" not in intent["skills"]:
        raise ValueError(f"Skill extraction failed: {intent}")
    return f"skills={intent['skills']}, domain={intent['domain']}, status={intent['status']}"

check("Intent extraction (fallback)", check_rag_intent)

def check_rag_pipeline():
    from rag.rag_pipeline import GraphRAGPipeline
    pl = GraphRAGPipeline()
    result = pl.run_pipeline("Find bench employees with Python skills", api_key=None, top_n=3)
    if not result.get("candidates"):
        raise ValueError("Pipeline returned no candidates")
    return f"{len(result['candidates'])} candidates, explanation length={len(result['explanation'])}"

check("Full GraphRAG pipeline (no LLM)", check_rag_pipeline)

# 5. Summary
print("\n" + "=" * 55)
passed = sum(1 for _, ok in results if ok)
total  = len(results)
print(f"  Result: {passed}/{total} checks passed")
if passed == total:
    print("  ✅ ALL SYSTEMS OPERATIONAL — ready to launch!")
    print("     streamlit run app.py")
else:
    print("  ⚠️  Some checks failed. Review the output above.")
print("=" * 55 + "\n")
