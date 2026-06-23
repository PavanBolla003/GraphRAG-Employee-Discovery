import os
import sys
from typing import List, Optional
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException

# Add root folder to sys.path to allow importing from rag and graph_queries
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from rag.rag_pipeline import GraphRAGPipeline

app = FastAPI(
    title="GraphRAG Employee Resource Discovery System API",
    description="APIs for discovering employees, calculating skill gaps, and generating recommendations using Apache HugeGraph and FAISS.",
    version="1.0.0"
)

# Initialize the pipeline
pipeline = None

def get_pipeline():
    global pipeline
    if pipeline is None:
        try:
            # Assumes server runs on localhost:8081 by default
            pipeline = GraphRAGPipeline(host="127.0.0.1", port="8081", graph="hugegraph")

        except Exception as e:
            print(f"[-] Warning: Pipeline initialization failed: {e}. Some endpoints may fail if databases are not running.")
    return pipeline

# Pydantic schemas for request validation
class SearchRequest(BaseModel):
    query: str
    api_key: Optional[str] = None
    top_n: Optional[int] = 5

class RecommendationRequest(BaseModel):
    skills: List[str]
    domain: Optional[str] = None
    certifications: Optional[List[str]] = []
    status: Optional[str] = None
    api_key: Optional[str] = None
    top_n: Optional[int] = 5

class SkillGapRequest(BaseModel):
    emp_id: str
    project_id: str

class SimilarEmployeeRequest(BaseModel):
    emp_id: str
    limit: Optional[int] = 5

@app.get("/")
def read_root():
    return {"status": "online", "message": "GraphRAG Employee Discovery API is active."}

@app.post("/search_employee")
def search_employee(req: SearchRequest):
    pipe = get_pipeline()
    if not pipe:
        raise HTTPException(status_code=503, detail="RAG Pipeline is unavailable. Ensure HugeGraph and FAISS are initialized.")
    try:
        result = pipe.run_pipeline(query_text=req.query, api_key=req.api_key, top_n=req.top_n)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/recommend_employee")
def recommend_employee(req: RecommendationRequest):
    pipe = get_pipeline()
    if not pipe:
        raise HTTPException(status_code=503, detail="RAG Pipeline is unavailable.")
    try:
        # Construct intent dictionary matching the pipeline structure
        intent = {
            "skills": req.skills,
            "domain": req.domain,
            "certifications": req.certifications,
            "status": req.status
        }
        # Run hybrid retrieval
        candidates = pipe.retrieve_candidates(
            query_text=f"Find staffing for domain {req.domain} and skills {', '.join(req.skills)}",
            intent=intent,
            top_k=req.top_n * 2
        )
        
        # Populate candidate details
        top_candidates = []
        for cand in candidates[:req.top_n]:
            details = pipe.queries.get_employee_details(cand["emp_id"])
            if details:
                details.update(cand)
                top_candidates.append(details)
                
        return {"intent": intent, "candidates": top_candidates}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {str(e)}")

@app.post("/skill_gap")
def skill_gap(req: SkillGapRequest):
    pipe = get_pipeline()
    if not pipe:
        raise HTTPException(status_code=503, detail="RAG Pipeline is unavailable.")
    try:
        # Check if employee exists
        details = pipe.queries.get_employee_details(req.emp_id)
        if not details:
            raise HTTPException(status_code=404, detail=f"Employee {req.emp_id} not found in the graph.")
            
        gap = pipe.queries.analyze_skill_gap(req.emp_id, req.project_id)
        return {
            "emp_id": req.emp_id,
            "project_id": req.project_id,
            "employee_skills": gap["employee_skills"],
            "required_skills": gap["required_skills"],
            "matching_skills": gap["matching_skills"],
            "missing_skills": gap["missing_skills"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Skill gap analysis failed: {str(e)}")

@app.post("/similar_employee")
def similar_employee(req: SimilarEmployeeRequest):
    pipe = get_pipeline()
    if not pipe:
        raise HTTPException(status_code=503, detail="RAG Pipeline is unavailable.")
    try:
        similar = pipe.queries.find_similar_employees(req.emp_id, req.limit)
        results = []
        for sim_id, count in similar:
            details = pipe.queries.get_employee_details(sim_id)
            if details:
                details["shared_skills_count"] = count
                results.append(details)
        return {"target_employee": req.emp_id, "similar_employees": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Similar employee search failed: {str(e)}")
