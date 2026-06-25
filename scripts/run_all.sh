#!/bin/sh
echo "=== Starting GraphRAG Stack ==="

# Get the directory where run_all.sh is located, and go up one level to the project root
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# 1. Initialize hugegraph-llm library configuration
echo "[*] Initializing hugegraph-llm config..."
cd "$APP_DIR"
python scripts/initialize_config.py

# 2. Download and extract HugeGraph Server if not present
echo "[*] Downloading and extracting HugeGraph Server..."
python scripts/setup_hugegraph.py

# 3. Install runtime dependencies that require build environment or are heavy
echo "[*] Installing faiss-cpu and sentence-transformers at runtime..."
pip install --user faiss-cpu sentence-transformers

# 4. Initialize HugeGraph database store (rocksdb)
echo "[*] Initializing HugeGraph database store..."
cd "$APP_DIR/hugegraph-server"
./bin/init-store.sh

# 5. Start HugeGraph Server in daemon mode
echo "[*] Starting HugeGraph Server..."
./bin/start-hugegraph.sh

# Go back to app root
cd "$APP_DIR"

# 6. Wait for HugeGraph Server REST API to be fully online (port 8081)
echo "[*] Waiting for HugeGraph Server to start on port 8081..."
until curl -s http://127.0.0.1:8081/status > /dev/null; do
    echo "    HugeGraph REST API is not ready yet... retrying in 2 seconds"
    sleep 2
done
echo "[+] HugeGraph Server is online!"

# 7. Run data ingestion and embedding generation
echo "[*] Ingesting schema and data into HugeGraph..."
python ingest_hugegraph.py

echo "[*] Generating text profiles..."
python create_profiles.py

echo "[*] Generating FAISS embeddings..."
python create_embeddings.py

# 8. Run system verification to confirm health
echo "[*] Running system verification..."
python scripts/verify_system.py

# 9. Start FastAPI Backend in background
echo "[*] Starting FastAPI Backend on port 8000..."
python -m uvicorn api.app:app --host 0.0.0.0 --port 8000 &

# 10. Start Streamlit Frontend in foreground on port 7860 (Hugging Face standard)
echo "[*] Starting Streamlit Frontend on port 7860..."
python -m streamlit run app.py --server.port 7860 --server.address 0.0.0.0 --server.enableCORS false --server.enableXsrfProtection false
