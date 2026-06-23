import os
import sys
import json
import re

# Add root folder to sys.path to allow importing graph_queries and embeddings
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from graph_queries import HugeGraphQueries
from embeddings.vector_store import VectorStore

class GraphRAGPipeline:
    def __init__(self, host="127.0.0.1", port="8080", graph="hugegraph"):
        self.queries = HugeGraphQueries(host, port, graph)
        self.vector_store = VectorStore()
        # Attempt to load the FAISS vector store
        self.vector_store.load()
        
        # Define search vocabularies for regex fallback
        self.skills_list = [
            "Python", "Java", "React", "NodeJS", "AWS", "Azure", 
            "Machine Learning", "Deep Learning", "SQL", "Power BI", 
            "Spark", "Kafka", "Docker", "Kubernetes", "Data Engineering", 
            "MLOps", "GenAI", "TensorFlow", "PyTorch", "Snowflake"
        ]
        self.domains_list = [
            "Banking", "Insurance", "Retail", "Healthcare", 
            "Telecom", "Manufacturing", "Automotive", "Logistics"
        ]
        self.certs_list = [
            "AWS Associate", "Azure Fundamentals", "Databricks Associate", 
            "Google Cloud Engineer", "Snowflake Associate"
        ]

    def _get_llm_client(self, api_key=None):
        """Initializes and returns the Google GenAI client if API key is provided."""
        if not api_key:
            api_key = os.environ.get("GEMINI_API_KEY")
            
        if not api_key:
            return None
            
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            return client
        except Exception as e:
            print(f"[-] Failed to initialize Gemini Client: {e}")
            return None

    def extract_intent_fallback(self, query_text):
        """
        Regex-based fallback parser to extract skills, domains, status, and certs 
        from the query when LLM is unavailable.
        """
        extracted_skills = []
        extracted_domain = None
        extracted_certs = []
        extracted_status = None
        
        query_lower = query_text.lower()
        
        # 1. Match skills (case insensitive)
        for skill in self.skills_list:
            # Word boundary check for short skill names (e.g. 'SQL', 'Java')
            pattern = rf"\b{re.escape(skill.lower())}\b"
            # Special check for skills with symbols (e.g. NodeJS, Power BI)
            if skill.lower() in query_lower or re.search(pattern, query_lower):
                if skill not in extracted_skills:
                    extracted_skills.append(skill)
                    
        # 2. Match domains
        for domain in self.domains_list:
            if domain.lower() in query_lower:
                extracted_domain = domain
                break
                
        # 3. Match certifications
        for cert in self.certs_list:
            if cert.lower() in query_lower:
                extracted_certs.append(cert)
                
        # 4. Match status (bench / available)
        bench_keywords = ["bench", "available", "immediately", "free", "idle"]
        if any(keyword in query_lower for keyword in bench_keywords):
            extracted_status = "BENCH"
            
        return {
            "skills": extracted_skills,
            "domain": extracted_domain,
            "certifications": extracted_certs,
            "status": extracted_status
        }

    def extract_intent(self, query_text, api_key=None):
        """Extracts search filters from query using Gemini LLM, with regex fallback."""
        client = self._get_llm_client(api_key)
        
        if not client:
            print("[*] No LLM client. Using regex intent extraction fallback...")
            return self.extract_intent_fallback(query_text)
            
        prompt = f"""
        Analyze the following manager request for finding employees in a company.
        Extract the filtering criteria into a JSON object with the following keys:
        - "skills": List of skills requested (Must strictly match items from this list: {self.skills_list})
        - "domain": The industry domain requested (Must strictly match one from: {self.domains_list}, or null if not specified)
        - "certifications": List of certifications requested (Must strictly match items from: {self.certs_list})
        - "status": The availability status requested. Return "BENCH" if words like "bench", "available", "immediately", or "free" are used. Return null if not specified.
        
        Request: "{query_text}"
        
        Return ONLY the valid JSON block.
        """
        try:
            # Using gemini-2.5-flash as the standard fast LLM
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config={'response_mime_type': 'application/json'}
            )
            data = json.loads(response.text.strip())
            return {
                "skills": data.get("skills", []),
                "domain": data.get("domain"),
                "certifications": data.get("certifications", []),
                "status": data.get("status")
            }
        except Exception as e:
            print(f"[-] Gemini intent extraction failed: {e}. Falling back to regex parser...")
            return self.extract_intent_fallback(query_text)

    def retrieve_candidates(self, query_text, intent, top_k=15):
        """
        Retrieves candidates from HugeGraph (Gremlin) and FAISS, then fuses them.
        """
        skills = intent.get("skills", [])
        domain = intent.get("domain")
        certs = intent.get("certifications", [])
        status = intent.get("status")
        
        # 1. Graph Retrieval (Hard constraints matching)
        graph_emp_ids = []
        try:
            graph_emp_ids = self.queries.find_employees_hybrid_filters(
                skills=skills,
                domain=domain,
                certs=certs,
                status=status
            )
        except Exception as e:
            print(f"[-] Graph retrieval failed: {e}. Using empty graph matches.")
            
        # 2. Vector Retrieval (Semantic matching)
        vector_results = self.vector_store.search(query_text, top_k=top_k)
        
        # 3. Hybrid Fusion
        fused_candidates = {}
        
        # Add all vector matches first
        for item in vector_results:
            emp_id = item["emp_id"]
            fused_candidates[emp_id] = {
                "emp_id": emp_id,
                "vector_score": item["score"],
                "graph_match": emp_id in graph_emp_ids,
                "match_type": "Vector Match"
            }
            
        # Add graph matches that were not caught in the top_k of vector search
        for emp_id in graph_emp_ids:
            if emp_id not in fused_candidates:
                fused_candidates[emp_id] = {
                    "emp_id": emp_id,
                    "vector_score": 0.5,  # Base default score
                    "graph_match": True,
                    "match_type": "Graph Match"
                }
                
        # Calculate hybrid boosted score
        for emp_id, cand in fused_candidates.items():
            boost = 0.5 if cand["graph_match"] else 0.0
            cand["hybrid_score"] = cand["vector_score"] + boost
            if cand["graph_match"] and cand["match_type"] == "Vector Match":
                cand["match_type"] = "Hybrid Match"
                
        # Sort candidates by hybrid score descending
        sorted_candidates = sorted(fused_candidates.values(), key=lambda x: x["hybrid_score"], reverse=True)
        return sorted_candidates

    def generate_recommendations_fallback(self, query_text, candidates, intent):
        """Generates a structured candidate summary locally in Python if Gemini is offline."""
        output = []
        output.append(f"### Hybrid RAG Recommendations (Local Fallback Summary)")
        output.append(f"Query: \"{query_text}\"")
        output.append(f"Extracted Constraints: Skills: {intent.get('skills')}, Domain: {intent.get('domain')}, Status: {intent.get('status')}")
        output.append("")
        output.append("Here is the list of top candidates ranked by similarity and constraint matching:")
        output.append("")
        
        for idx, cand in enumerate(candidates[:5]):
            emp_id = cand["emp_id"]
            details = self.queries.get_employee_details(emp_id)
            if not details:
                # If HugeGraph is down, fall back to basic details
                output.append(f"{idx+1}. **Employee {emp_id}** - Score: {cand['hybrid_score']:.3f} [{cand['match_type']}]")
                continue
                
            match_str = f"[{cand['match_type']}] Score: {cand['hybrid_score']:.3f}"
            output.append(f"{idx+1}. **{details['name']}** ({emp_id}) - {details['designation']} - {match_str}")
            output.append(f"   * Experience: {details['experience_years']} years | Status: {details['status']} | Location: {details['location']}")
            output.append(f"   * Domain: {details['domain']}")
            output.append(f"   * Skills: {', '.join(details['skills'])}")
            if details['certifications']:
                output.append(f"   * Certifications: {', '.join(details['certifications'])}")
            
            # Analyze match gap
            req_skills = set(intent.get("skills", []))
            emp_skills = set(details["skills"])
            matched = req_skills.intersection(emp_skills)
            missing = req_skills - emp_skills
            
            output.append(f"   * Matching requested skills: {', '.join(matched) if matched else 'None'}")
            if missing:
                output.append(f"   * Missing requested skills: {', '.join(missing)}")
            output.append("")
            
        return "\n".join(output)

    def run_pipeline(self, query_text, api_key=None, top_n=5):
        """
        Runs the full Hybrid GraphRAG pipeline:
        Intent Extraction -> Hybrid Retrieval -> LLM Ranking & Explanation.
        """
        # Step 1: Intent Extraction
        intent = self.extract_intent(query_text, api_key)
        
        # Step 2 & 3: Retrieve and Fuse candidates
        candidates = self.retrieve_candidates(query_text, intent, top_k=15)
        
        # Get details for the top candidates
        top_candidates = []
        for cand in candidates[:top_n]:
            details = self.queries.get_employee_details(cand["emp_id"])
            if details:
                # Combine graph properties and scores
                details.update(cand)
                top_candidates.append(details)
                
        # If no candidates found, return empty info
        if not top_candidates:
            return {
                "intent": intent,
                "candidates": [],
                "explanation": "No matching candidates found in either the Graph database or Vector store."
            }
            
        # Step 4: Send context to LLM for final generation
        client = self._get_llm_client(api_key)
        if not client:
            print("[*] No LLM client. Using fallback ranking generator...")
            explanation = self.generate_recommendations_fallback(query_text, candidates, intent)
            return {
                "intent": intent,
                "candidates": top_candidates,
                "explanation": explanation
            }
            
        # Construct LLM prompt
        candidates_context = []
        for idx, c in enumerate(top_candidates):
            c_info = (
                f"Candidate {idx+1}: {c['name']} (ID: {c['emp_id']})\n"
                f"Designation: {c['designation']}, Experience: {c['experience_years']} years\n"
                f"Availability Status: {c['status']}, Location: {c['location']}\n"
                f"Domain Specialization: {c['domain']}\n"
                f"Skills: {', '.join(c['skills'])}\n"
                f"Certifications: {', '.join(c['certifications'])}\n"
                f"Match Type: {c['match_type']}, Hybrid Fusion Score: {c['hybrid_score']:.3f}\n"
            )
            candidates_context.append(c_info)
            
        candidates_str = "\n---\n".join(candidates_context)
        
        prompt = f"""
        You are a senior recruitment manager staffing a project.
        A manager asked this question: "{query_text}"
        
        We extracted the following search intent from their query:
        - Required Skills: {intent.get('skills')}
        - Domain: {intent.get('domain')}
        - Required Status: {intent.get('status')}
        
        Here are the top candidates retrieved by our Hybrid RAG system (combining Graph exact filters and vector semantic similarities):
        
        {candidates_str}
        
        Please provide a professional response that:
        1. Ranks these candidates in order of suitability for this specific request.
        2. Explains the reasoning behind the ranking.
        3. Mentions each candidate's key strengths (e.g. experience, domain specialization, matching skills, certifications).
        4. Identifies any skill gaps or missing skills relative to the query requirements.
        5. Concludes with a brief recommendation of who to contact or staff immediately.
        
        Write in clear Markdown format with headings.
        """
        
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt
            )
            return {
                "intent": intent,
                "candidates": top_candidates,
                "explanation": response.text.strip()
            }
        except Exception as e:
            print(f"[-] Gemini generation failed: {e}. Falling back to Python generator...")
            explanation = self.generate_recommendations_fallback(query_text, candidates, intent)
            return {
                "intent": intent,
                "candidates": top_candidates,
                "explanation": explanation
            }
