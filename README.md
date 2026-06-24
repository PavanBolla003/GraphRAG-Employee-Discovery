# 🕸️ GraphRAG Employee Resource Discovery System

An intelligent **end-to-end GraphRAG** system for discovering and recommending employees in a large enterprise — built using the official **Apache HugeGraph-AI (`hugegraph-llm`)** toolkit, **FAISS**, **Sentence Transformers**, **FastAPI**, and **Streamlit**.

---

## 🏗️ Architecture

```
Manager Query (Natural Language)
        │
        ▼
   hugegraph-llm Pipeline
   ├── KeywordExtract (Extracts entity keywords using LLM/Regex)
   │    │
   │    ├──────────────────────┐
   │    ▼                      ▼
   │ GraphRAGQuery       FAISS Vector Store
   │ (Traverses Graph    (Semantic Search)
   │  Paths in DB)             │
   │    │                      │
   │    └──────────┬───────────┘
   │               ▼
   │         Hybrid Fusion
   │               │
   │               ▼
   └── AnswerSynthesize (Gemini LLM ranks and explains candidate fit)
                   │
                   ▼
             FastAPI  ◄──► Streamlit UI
```

---

## 🚀 Features

- **Natural Language Search**: Ask like a manager — "Find bench employees with Python and ML skills"
- **Official Apache HugeGraph-AI Integration**: Built using the `hugegraph-llm` package's operator-driven workflow (`KeywordExtract` -> `GraphRAGQuery` -> `AnswerSynthesize`)
- **Hybrid RAG**: Combines exact graph traversal subgraph paths with FAISS vector similarity (semantic match)
- **Interactive Graph Viewer**: Visualise an employee's neighbourhood using Pyvis
- **Skill Gap Analyzer**: Compare any employee vs a project's requirements
- **Project Staffing**: Multi-filter search (skills + domain + certs + availability)
- **Gemini & Offline Fallback**: Integrates Google Gemini 2.5 Flash via a custom `GeminiLLM` wrapper, falling back to a custom local `FallbackLLM` if no API key is present

---

## 📁 Project Structure

```
HugeGraph/
├── api/
│   └── app.py              # FastAPI backend (4 endpoints)
├── rag/
│   └── rag_pipeline.py     # Hybrid GraphRAG pipeline using hugegraph-llm operators
├── embeddings/
│   └── vector_store.py     # FAISS vector store wrapper
├── scripts/
│   ├── initialize_config.py # Configures hugegraph-llm's config.ini automatically
│   ├── smoke_test.py       # End-to-end pipeline test
│   ├── test_api.py         # FastAPI endpoint tests
│   ├── start_ngrok.py      # Auto-install & run ngrok tunnel
│   └── verify_system.py    # System health check
├── data/
│   ├── employees.csv       # 1000 synthetic employees
│   ├── skills.csv          # 20 skills
│   ├── domains.csv         # 8 industry domains
│   ├── certifications.csv  # 5 certifications
│   ├── projects.csv        # 50 projects
│   └── *.csv               # Relationship tables
├── app.py                  # Streamlit frontend
├── generate_data.py        # Synthetic dataset generator
├── ingest_hugegraph.py     # HugeGraph schema + data ingestion
├── create_profiles.py      # Employee text profile generator
├── create_embeddings.py    # FAISS index builder
├── graph_queries.py        # Gremlin query library
└── requirements.txt        # Python dependencies
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.9+
- Java 11 (required for HugeGraph)
- Apache HugeGraph Server 1.3.0

### 1. Install Python Dependencies
```bash
pip install -r requirements.txt
```

### 2. Download & Start HugeGraph Server
Download HugeGraph 1.3.0 from https://hugegraph.apache.org/docs/download/hugegraph/ and extract to `hugegraph-server/`.

Start the server (must use Java 11):
```powershell
& "C:\Program Files\Java\jdk-11\bin\java.exe" -cp "lib/*" org.apache.hugegraph.dist.HugeGraphServer conf/gremlin-server.yaml conf/rest-server.properties
```

### 3. Initialize hugegraph-llm Configuration
Run the configuration script to write port `8081` and database credentials to `config.ini` inside the installed package:
```bash
python scripts/initialize_config.py
```

### 4. Generate Synthetic Data & Ingest
```bash
python generate_data.py
python ingest_hugegraph.py
```

### 5. Build Text Profiles & FAISS Index
```bash
python create_profiles.py
python create_embeddings.py
```

### 6. Start the API + Frontend
```bash
# Terminal 1 — FastAPI backend
python -m uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2 — Streamlit frontend
python -m streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

Open **http://localhost:8501** in your browser.

---

## 🔑 Gemini API Key (Optional but Recommended)

Without a key, the system uses a regex-based fallback for intent extraction and a Python-based fallback for generating recommendations.  
With a key, it uses **Gemini 2.5 Flash** for both — giving much richer, more accurate responses.

Enter your key in the Streamlit sidebar, or set it as an environment variable:
```bash
set GEMINI_API_KEY=your_key_here
```

Get a free key at: https://aistudio.google.com/app/apikey

---

## 🌐 Public Access with ngrok

To expose the app to the internet:
```bash
python scripts/start_ngrok.py <your_ngrok_authtoken>
```

Get a free authtoken at: https://ngrok.com

## 🕸️ Graph Visualization with HugeGraph-Hubble

HugeGraph-Hubble is the official visual graph management and analysis platform for HugeGraph. You can use it to visualize and explore the schema and the ingested data.

### 1. Download and Set Up Hubble
Run the automated multi-threaded setup script to download and extract Hubble, and generate the Windows launcher:
```bash
python scripts/setup_hubble.py
```

### 2. Start Hubble
Run the generated launcher in the background:
```powershell
# Open a new terminal and run
cd hugegraph-hubble
.\run_hubble.bat
```

### 3. Connect to HugeGraph Server
1. Access the web UI at **http://localhost:8088** in your browser.
2. In the connection page, click **Create Connection** (or **New Graph**) and fill in the connection details:
   - **Host**: `localhost`
   - **Port**: `8081`
   - **Graph Name**: `hugegraph`
3. Click **Connect** to access the dashboard.
4. Go to **Graph Analysis** or **Schema Management** to explore the data dynamically reflecting from the database!

---

## 📊 Dataset Summary

| Entity       | Count |
|--------------|-------|
| Employees    | 1,000 |
| Skills       | 20    |
| Domains      | 8     |
| Certifications | 5   |
| Projects     | 50    |
| Graph Edges  | ~7,321|

---

## 🛠️ Tech Stack

| Component        | Technology                          |
|------------------|-------------------------------------|
| Graph Toolkit    | Apache HugeGraph-AI (hugegraph-llm) |
| Graph Database   | Apache HugeGraph 1.3.0 (Gremlin)   |
| Vector Search    | FAISS + sentence-transformers       |
| Embedding Model  | all-MiniLM-L6-v2                    |
| LLM              | Google Gemini 2.5 Flash             |
| Backend API      | FastAPI + Uvicorn                   |
| Frontend         | Streamlit + Pyvis + NetworkX        |
| Graph Client     | pyhugegraph                         |

---

## 📝 License

MIT License — free to use, modify, and distribute.
