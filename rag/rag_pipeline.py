import os
import sys
import json
import re
from typing import Optional, List, Dict, Any, Callable

# Add root folder to sys.path to allow importing graph_queries and embeddings
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from graph_queries import HugeGraphQueries
from embeddings.vector_store import VectorStore

from hugegraph_llm.llms.base import BaseLLM
from google import genai

# Custom LLM Wrapper for Google Gemini to integrate with hugegraph-llm
class GeminiLLM(BaseLLM):
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.model_name = model_name
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is not set.")
        self.client = genai.Client(api_key=self.api_key)

    def generate(self, messages: Optional[List[Dict[str, Any]]] = None, prompt: Optional[str] = None) -> str:
        if messages is None:
            assert prompt is not None, "Prompt or messages must be provided."
            contents = prompt
        else:
            # Format messages as single prompt string
            parts = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                parts.append(f"{role.capitalize()}: {content}")
            contents = "\n".join(parts)
            
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents
            )
            return response.text.strip()
        except Exception as e:
            print(f"[-] Gemini generation error: {e}")
            return f"Error: {e}"

    def generate_streaming(
        self,
        messages: Optional[List[Dict[str, Any]]] = None,
        prompt: Optional[str] = None,
        on_token_callback: Callable = None,
    ) -> str:
        res = self.generate(messages, prompt)
        if on_token_callback:
            on_token_callback({"choices": [{"delta": {"content": res}}]})
        return res

    def num_tokens_from_string(self, string: str) -> int:
        return len(string.split())

    def max_allowed_token_length(self) -> int:
        return 1000000

    def get_llm_type(self) -> str:
        return "gemini"


# Local Regex-based Fallback LLM Wrapper to allow offline operations
class FallbackLLM(BaseLLM):
    def __init__(self, skills_list: List[str], domains_list: List[str], certs_list: List[str]):
        self.skills_list = skills_list
        self.domains_list = domains_list
        self.certs_list = certs_list

    def generate(self, messages: Optional[List[Dict[str, Any]]] = None, prompt: Optional[str] = None) -> str:
        text = prompt or ""
        if messages:
            text += "\n" + "\n".join(m.get("content", "") for m in messages)
            
        text_lower = text.lower()
        
        # 1. Keyword extraction prompt
        if "extract" in text_lower and "keywords from the text" in text_lower:
            extracted = []
            
            # Match skills
            for skill in self.skills_list:
                pattern = rf"\b{re.escape(skill.lower())}\b"
                if skill.lower() in text_lower or re.search(pattern, text_lower):
                    if skill not in extracted:
                        extracted.append(skill)
                        
            # Match domains
            for domain in self.domains_list:
                if domain.lower() in text_lower:
                    if domain not in extracted:
                        extracted.append(domain)
                        
            # Match certifications
            for cert in self.certs_list:
                if cert.lower() in text_lower:
                    if cert not in extracted:
                        extracted.append(cert)
                        
            # Match status keywords
            bench_keywords = ["bench", "available", "immediately", "free", "idle"]
            if any(kw in text_lower for kw in bench_keywords):
                extracted.append("BENCH")
                
            return f"KEYWORDS: {', '.join(extracted)}"
            
        # 2. Synonym expansion prompt
        elif "expand synonyms" in text_lower or "synonyms:" in text_lower:
            return "SYNONYMS: "
            
        # 3. Answer synthesis prompt
        else:
            return (
                "### 🕸️ GraphRAG Recommendations (Local Fallback Summary)\n\n"
                "The system is currently running in **Offline Fallback Mode** (no LLM key provided).\n\n"
                "Here are the top candidates matched by search parameters and traversed subgraph paths:\n\n"
                f"{text}\n"
            )

    def generate_streaming(
        self,
        messages: Optional[List[Dict[str, Any]]] = None,
        prompt: Optional[str] = None,
        on_token_callback: Callable = None,
    ) -> str:
        res = self.generate(messages, prompt)
        if on_token_callback:
            on_token_callback({"choices": [{"delta": {"content": res}}]})
        return res

    def num_tokens_from_string(self, string: str) -> int:
        return len(string.split())

    def max_allowed_token_length(self) -> int:
        return 1000000

    def get_llm_type(self) -> str:
        return "fallback"


class GraphRAGPipeline:
    def __init__(self, host="127.0.0.1", port="8081", graph="hugegraph"):
        self.queries = HugeGraphQueries(host, port, graph)
        self.vector_store = VectorStore()
        self.vector_store.load()
        
        # Define search vocabularies
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

    def _get_llm_client(self, api_key=None) -> BaseLLM:
        """Initializes and returns the appropriate LLM client (Gemini or Fallback)."""
        if not api_key:
            api_key = os.environ.get("GEMINI_API_KEY")
            
        if api_key and api_key != "dummy_key" and len(api_key.strip()) > 5:
            try:
                return GeminiLLM(api_key=api_key)
            except Exception as e:
                print(f"[-] Failed to initialize GeminiLLM: {e}. Falling back...")
                
        return FallbackLLM(self.skills_list, self.domains_list, self.certs_list)

    def extract_intent_from_keywords(self, keywords: List[str]) -> Dict[str, Any]:
        """Maps extracted keywords to structured search intent parameters."""
        extracted_skills = []
        extracted_domain = None
        extracted_certs = []
        extracted_status = None
        
        keywords_lower = [k.lower() for k in keywords]
        
        for skill in self.skills_list:
            if skill.lower() in keywords_lower:
                extracted_skills.append(skill)
                
        for domain in self.domains_list:
            if domain.lower() in keywords_lower:
                extracted_domain = domain
                
        for cert in self.certs_list:
            if cert.lower() in keywords_lower:
                extracted_certs.append(cert)
                
        if "bench" in keywords_lower:
            extracted_status = "BENCH"
            
        return {
            "skills": extracted_skills,
            "domain": extracted_domain,
            "certifications": extracted_certs,
            "status": extracted_status
        }

    def retrieve_candidates(self, query_text, intent, top_k=15):
        """Retrieves candidates from HugeGraph and FAISS, then fuses them."""
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
        for item in vector_results:
            emp_id = item["emp_id"]
            fused_candidates[emp_id] = {
                "emp_id": emp_id,
                "vector_score": item["score"],
                "graph_match": emp_id in graph_emp_ids,
                "match_type": "Vector Match"
            }
            
        for emp_id in graph_emp_ids:
            if emp_id not in fused_candidates:
                fused_candidates[emp_id] = {
                    "emp_id": emp_id,
                    "vector_score": 0.5,
                    "graph_match": True,
                    "match_type": "Graph Match"
                }
                
        for emp_id, cand in fused_candidates.items():
            boost = 0.5 if cand["graph_match"] else 0.0
            cand["hybrid_score"] = cand["vector_score"] + boost
            if cand["graph_match"] and cand["match_type"] == "Vector Match":
                cand["match_type"] = "Hybrid Match"
                
        sorted_candidates = sorted(fused_candidates.values(), key=lambda x: x["hybrid_score"], reverse=True)
        return sorted_candidates

    def run_pipeline(self, query_text, api_key=None, top_n=5):
        """Runs the GraphRAG pipeline using hugegraph-llm operators."""
        # 1. Initialize LLM
        llm_client = self._get_llm_client(api_key)
        
        # 2. Step 1: Keyword Extraction (using hugegraph-llm KeywordExtract operator)
        from hugegraph_llm.operators.llm_op.keyword_extract import KeywordExtract
        context = {"query": query_text, "llm": llm_client}
        op_kw = KeywordExtract()
        context = op_kw.run(context)
        
        # 3. Map keywords to structured intent
        intent = self.extract_intent_from_keywords(context.get("keywords", []))
        
        # 4. Retrieve candidates from Graph and Vector Store
        candidates = self.retrieve_candidates(query_text, intent, top_k=15)
        
        # Format top candidates to retrieve their full graph properties
        top_candidates = []
        candidates_context_list = []
        for idx, cand in enumerate(candidates[:top_n]):
            details = self.queries.get_employee_details(cand["emp_id"])
            if details:
                details.update(cand)
                top_candidates.append(details)
                
                c_info = (
                    f"Candidate {idx+1}: {details['name']} (ID: {details['emp_id']})\n"
                    f"Designation: {details['designation']}, Experience: {details['experience_years']} years\n"
                    f"Availability Status: {details['status']}, Location: {details['location']}\n"
                    f"Domain Specialization: {details['domain']}\n"
                    f"Skills: {', '.join(details['skills'])}\n"
                    f"Certifications: {', '.join(details['certifications'])}\n"
                    f"Match Type: {details['match_type']}, Hybrid Fusion Score: {details['hybrid_score']:.3f}\n"
                )
                candidates_context_list.append(c_info)
                
        candidates_context_str = "\n---\n".join(candidates_context_list)
        
        # 5. Step 2: Query Graph for RAG (using hugegraph-llm GraphRAGQuery operator)
        from hugegraph_llm.operators.hugegraph_op.graph_rag_query import GraphRAGQuery
        # GraphRAGQuery automatically initializes PyHugeClient from config.ini
        op_query = GraphRAGQuery(max_deep=2, max_items=30)
        try:
            context = op_query.run(context)
        except Exception as e:
            print(f"[-] GraphRAGQuery failed: {e}")
            context["synthesize_context_body"] = []
            context["synthesize_context_head"] = ""

        # 6. Build the synthesis context (Combine subgraph facts and retrieved candidate info)
        graph_paths = context.get("synthesize_context_body", [])
        combined_context_body = []
        
        if graph_paths:
            combined_context_body.append("--- Traversed Graph Subgraph Paths ---")
            combined_context_body.extend(graph_paths)
            combined_context_body.append("")
            
        if candidates_context_str:
            combined_context_body.append("--- Retrieved Resource Candidate Details ---")
            combined_context_body.append(candidates_context_str)
            
        context["synthesize_context_body"] = combined_context_body
        context["synthesize_context_head"] = "The following is graph knowledge and resource candidate information retrieved from the database:"
        context["synthesize_context_tail"] = "Please rank these candidates and explain who is the most suitable resource to staff immediately."
        
        # 7. Step 3: Synthesize Answer (using hugegraph-llm AnswerSynthesize operator)
        from hugegraph_llm.operators.llm_op.answer_synthesize import AnswerSynthesize
        
        custom_prompt_template = """
        You are a senior staffing manager.
        The manager's request is: "{query_str}"
        
        Context information:
        {context_str}
        
        Please provide a professional response that:
        1. Ranks the candidates in order of suitability for this request.
        2. Explains the reasoning behind the ranking.
        3. Mentions each candidate's key strengths (experience, domain, matching skills, certifications).
        4. Identifies any skill gaps or missing skills relative to the query requirements.
        5. Concludes with a brief recommendation of who to contact or staff immediately.
        
        Write in clear Markdown format with headings.
        """
        
        op_synth = AnswerSynthesize(prompt_template=custom_prompt_template)
        explanation = op_synth.run(context)
        
        return {
            "intent": intent,
            "candidates": top_candidates,
            "explanation": explanation
        }
