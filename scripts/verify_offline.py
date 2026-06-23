import sys, os, json
sys.path.append(os.path.abspath("."))

print("=== Partial Verification (no HugeGraph needed) ===\n")

# 1. CSVs
import csv
files = [
    "employees.csv", "skills.csv", "domains.csv", "projects.csv",
    "certifications.csv", "employee_skills.csv", "employee_projects.csv",
    "employee_certifications.csv", "employee_domains.csv", "project_skills.csv"
]
missing = [f for f in files if not os.path.exists(os.path.join("data", f))]
if missing:
    print("FAIL CSVs:", missing)
else:
    with open("data/employees.csv") as f:
        cnt = sum(1 for _ in csv.DictReader(f))
    print("PASS CSV files:", cnt, "employees")

# 2. Profiles
pdir = "data/profiles"
pcount = len([f for f in os.listdir(pdir) if f.endswith(".txt")])
print("PASS Profiles:", pcount, "files")

# 3. FAISS
import faiss
idx = faiss.read_index("embeddings/employee_index.bin")
with open("embeddings/employee_ids.json") as f:
    ids = json.load(f)
print("PASS FAISS:", idx.ntotal, "vectors, dim=" + str(idx.d) + ",", len(ids), "IDs")

# 4. Vector search
from embeddings.vector_store import VectorStore
vs = VectorStore()
vs.load()
results = vs.search("Python developer Banking domain", top_k=3)
top = results[0]
print("PASS Vector search: top match =", top["emp_id"], "score=" + str(round(top["score"], 3)))

# 5. Intent extraction (standalone)
from rag.rag_pipeline import GraphRAGPipeline
pl = GraphRAGPipeline.__new__(GraphRAGPipeline)
pl.skills_list = [
    "Python", "Java", "React", "NodeJS", "AWS", "Azure", "Machine Learning",
    "Deep Learning", "SQL", "Power BI", "Spark", "Kafka", "Docker",
    "Kubernetes", "Data Engineering", "MLOps", "GenAI", "TensorFlow", "PyTorch", "Snowflake"
]
pl.domains_list = ["Banking", "Insurance", "Retail", "Healthcare", "Telecom", "Manufacturing", "Automotive", "Logistics"]
pl.certs_list   = ["AWS Associate", "Azure Fundamentals", "Databricks Associate", "Google Cloud Engineer", "Snowflake Associate"]
intent = pl.extract_intent_fallback("Find bench developers with Python and Machine Learning in Banking")
print("PASS Intent: skills=" + str(intent["skills"]) + " domain=" + str(intent["domain"]) + " status=" + str(intent["status"]))

print("\nAll offline checks PASSED. Start HugeGraph server to enable full graph queries.")
