#!/bin/sh
echo "=== Starting GraphRAG Stack ==="

# 1. Initialize hugegraph-llm library configuration
echo "[*] Initializing hugegraph-llm config..."
python scripts/initialize_config.py

# 2. Initialize HugeGraph database store (rocksdb)
echo "[*] Initializing HugeGraph database store..."
cd /home/user/app/hugegraph-server
./bin/init-store.sh

# 3. Start HugeGraph Server in daemon mode
echo "[*] Starting HugeGraph Server..."
./bin/start-hugegraph.sh

# Go back to app root
cd /home/user/app

# 4. Wait for HugeGraph Server REST API to be fully online (port 8081)
echo "[*] Waiting for HugeGraph Server to start on port 8081..."
until curl -s http://127.0.0.1:8081/status > /dev/null; do
    echo "    HugeGraph REST API is not ready yet... retrying in 2 seconds"
    sleep 2
done
echo "[+] HugeGraph Server is online!"

# 5. Run data ingestion and embedding generation
echo "[*] Ingesting schema and data into HugeGraph..."
python ingest_hugegraph.py

echo "[*] Generating text profiles..."
python create_profiles.py

echo "[*] Generating FAISS embeddings..."
python create_embeddings.py

# 6. Run system verification to confirm health
echo "[*] Running system verification..."
python scripts/verify_system.py

# 7. Start FastAPI Backend in background
echo "[*] Starting FastAPI Backend on port 8000..."
python -m uvicorn api.app:app --host 0.0.0.0 --port 8000 &

# 8. Start Streamlit Frontend in foreground on port 7860 (Hugging Face standard)
echo "[*] Starting Streamlit Frontend on port 7860..."
python -m streamlit run app.py --server.port 7860 --server.address 0.0.0.0 --server.enableCORS false --server.enableXsrfProtection false
