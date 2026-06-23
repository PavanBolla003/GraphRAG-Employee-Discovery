"""
Smoke test for the GraphRAG pipeline.
Run from the project root: python scripts/smoke_test.py
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rag.rag_pipeline import GraphRAGPipeline

print("[*] Initializing GraphRAGPipeline...")
pipe = GraphRAGPipeline(host="127.0.0.1", port="8081", graph="hugegraph")
print("[+] Pipeline initialized successfully.")

print("[*] Testing intent extraction (no LLM)...")
intent = pipe.extract_intent_fallback("Find bench employees with Python and Machine Learning skills")
print(f"[+] Intent: {intent}")

print("[*] Testing graph query (bench employees with Python)...")
ids = pipe.queries.find_employees_hybrid_filters(skills=["Python"], status="BENCH")
print(f"[+] Found {len(ids)} bench employees with Python skill.")

print("[*] Testing employee details retrieval...")
if ids:
    details = pipe.queries.get_employee_details(ids[0])
    print(f"[+] Sample employee: {details['name']} - {details['designation']}")
    print(f"    Skills: {details['skills']}")
    print(f"    Certifications: {details['certifications']}")

print("[*] Testing FAISS vector search...")
results = pipe.vector_store.search("Python Machine Learning expert", top_k=3)
emp_ids = [r["emp_id"] for r in results]
print(f"[+] Vector search returned {len(results)} results: {emp_ids}")

print("[*] Testing similar employees...")
if ids:
    similar = pipe.queries.find_similar_employees(ids[0], limit=3)
    print(f"[+] Found {len(similar)} similar employees.")

print("")
print("=" * 50)
print("[SUCCESS] All system components are healthy!")
print("=" * 50)
