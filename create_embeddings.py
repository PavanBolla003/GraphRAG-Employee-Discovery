import os
import sys

# Add root folder to sys.path to allow imports from embeddings/
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from embeddings.vector_store import VectorStore

def main():
    print("[*] Running embedding generation for employee profiles...")
    
    profiles_dir = "data/profiles"
    if not os.path.exists(profiles_dir):
        print(f"[-] Profiles directory '{profiles_dir}' not found. Please run 'create_profiles.py' first.")
        sys.exit(1)
        
    emp_ids = []
    profiles = []
    
    # Load all txt profiles
    for filename in sorted(os.listdir(profiles_dir)):
        if filename.endswith(".txt") and filename.startswith("E"):
            emp_id = os.path.splitext(filename)[0]
            filepath = os.path.join(profiles_dir, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                profile_text = f.read()
            emp_ids.append(emp_id)
            profiles.append(profile_text)
            
    if not emp_ids:
        print("[-] No employee profiles found in data/profiles/. Run 'create_profiles.py' first.")
        sys.exit(1)
        
    print(f"[+] Loaded {len(emp_ids)} employee profiles.")
    
    # Initialize and populate vector store
    store = VectorStore()
    store.add_profiles(emp_ids, profiles)
    store.save()
    
    print("[+] Embeddings creation and FAISS indexing complete!")

if __name__ == "__main__":
    main()
