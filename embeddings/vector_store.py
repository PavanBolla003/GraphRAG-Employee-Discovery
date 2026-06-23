import os
import json
import numpy as np

class VectorStore:
    def __init__(self, index_path="embeddings/employee_index.bin", mapping_path="embeddings/employee_ids.json", model_name="all-MiniLM-L6-v2"):
        self.index_path = index_path
        self.mapping_path = mapping_path
        self.model_name = model_name
        self.model = None
        self.index = None
        self.emp_ids = []
        
    def _lazy_init_model(self):
        """Lazily load the SentenceTransformer model to speed up initialization."""
        if self.model is None:
            print(f"[*] Loading SentenceTransformer model '{self.model_name}'...")
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)
            print("[+] Model loaded.")

    def add_profiles(self, emp_ids, profiles):
        """
        Generates embeddings for employee profiles and adds them to the FAISS index.
        """
        import faiss
        self._lazy_init_model()
        
        print(f"[*] Generating embeddings for {len(profiles)} profiles...")
        embeddings = self.model.encode(profiles, show_progress_bar=True, convert_to_numpy=True)
        embeddings = np.array(embeddings).astype("float32")
        
        # L2 normalization for Cosine Similarity (IndexFlatIP with normalized vectors)
        # We will use IndexFlatL2 for standard L2 distance search (or IndexFlatIP for cosine)
        dimension = embeddings.shape[1]
        print(f"[*] Embedding dimension: {dimension}")
        
        if self.index is None:
            self.index = faiss.IndexFlatL2(dimension)
            self.emp_ids = []
            
        self.index.add(embeddings)
        self.emp_ids.extend(emp_ids)
        print(f"[+] Added {len(emp_ids)} vectors to FAISS index.")

    def save(self):
        """Saves the FAISS index and employee ID mapping to disk."""
        import faiss
        if self.index is None:
            print("[-] No index to save.")
            return
            
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.mapping_path), exist_ok=True)
        
        faiss.write_index(self.index, self.index_path)
        with open(self.mapping_path, "w", encoding="utf-8") as f:
            json.dump(self.emp_ids, f, indent=2)
        print(f"[+] Saved FAISS index to {self.index_path} and mappings to {self.mapping_path}.")

    def load(self):
        """Loads the FAISS index and employee ID mapping from disk."""
        import faiss
        if not os.path.exists(self.index_path) or not os.path.exists(self.mapping_path):
            print(f"[-] Index files not found. Search not initialized.")
            return False
            
        try:
            self.index = faiss.read_index(self.index_path)
            with open(self.mapping_path, "r", encoding="utf-8") as f:
                self.emp_ids = json.load(f)
            print(f"[+] Loaded FAISS index from {self.index_path} with {len(self.emp_ids)} items.")
            return True
        except Exception as e:
            print(f"[-] Failed to load FAISS index: {e}")
            return False

    def search(self, query, top_k=5):
        """
        Searches the FAISS index for semantically similar employee profiles.
        Returns a list of dicts: [{'emp_id': 'E001', 'score': 0.123}, ...]
        """
        self._lazy_init_model()
        if self.index is None:
            if not self.load():
                return []
                
        # Generate query embedding
        query_vector = self.model.encode([query], convert_to_numpy=True).astype("float32")
        
        # Search index
        distances, indices = self.index.search(query_vector, top_k)
        
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0 or idx >= len(self.emp_ids):
                continue
            # For IndexFlatL2, lower distance is more similar.
            # Convert L2 distance to a pseudo-similarity score (e.g. 1 / (1 + dist))
            score = float(1 / (1 + dist))
            results.append({
                "emp_id": self.emp_ids[idx],
                "score": score,
                "l2_distance": float(dist)
            })
            
        return results
