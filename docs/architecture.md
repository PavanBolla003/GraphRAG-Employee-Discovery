# System Architecture

The **GraphRAG Employee Resource Discovery System** uses a hybrid retrieval mechanism that combines structured graph queries with unstructured semantic vector search.

## Overview

Traditional RAG (Retrieval-Augmented Generation) systems search flat text databases (like document stores or vector databases) to find matching passages. However, they lack the ability to handle **complex relationships** (e.g., "Find an employee who worked on Project X AND has Skill Y AND is available").

A graph database can answer these relational queries with 100% precision. However, graph databases are rigid and struggle with **semantic queries** (e.g., "Find an expert in cloud migration" where the database only has the skill "AWS" or "Azure").

By combining **Apache HugeGraph** (graph) and **FAISS** (vector), our system offers:
1. **Hard Filtering Precision**: Filter candidates strictly by availability, locations, or certifications.
2. **Semantic Flexbility**: Find candidates whose profiles describe matching work experiences even if keywords don't match exactly.
3. **Structured Context for LLMs**: Fuses the structured connections (e.g., similar employees, worked-on projects) with textual profiles to generate high-quality recommendations.

---

## Technical Flow

### 1. Intent Extraction
The system receives a natural language query from a manager.
- It parses the query using Gemini (or a regex keyword fallback) to identify specific filters:
  - **Skills**: Python, ML, AWS, NodeJS...
  - **Domains**: Banking, Healthcare...
  - **Certifications**: AWS Associate...
  - **Availability**: BENCH / ON_PROJECT

### 2. Parallel Retrieval
- **Graph Path**: Converts the extracted intent into a Gremlin traversal. HugeGraph filters and returns employee IDs matching the constraints.
- **Vector Path**: Encodes the user query using `all-MiniLM-L6-v2`. Computes L2 similarity against the index of textual employee profiles in FAISS, returning the top 15 candidate IDs and distances.

### 3. Hybrid Fusion
- Normalizes FAISS L2 distances into similarity scores: $Score_{vector} = \frac{1}{1 + L2\_distance}$.
- Intersects the list of candidates.
- If a candidate returned by FAISS matches the Graph query, they get a boost: $Score_{hybrid} = Score_{vector} + 0.5$.
- Sorts candidates by their $Score_{hybrid}$ in descending order and returns the top 5.

### 4. LLM Generation
- Compiles the textual profiles of the top 5 candidates, their matching/missing skills, and the manager's query into a contextual prompt.
- Gemini ranks the candidates, writes a detailed summary of their strengths/weaknesses, and explains the reasoning.
- The Streamlit interface displays this report alongside interactive connection graphs.
