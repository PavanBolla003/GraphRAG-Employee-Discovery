"""
Extract the HugeGraph server tarball and create startup batch files.
Run this after hugegraph.tar.gz is already downloaded.
"""
import os
import tarfile
import shutil
import subprocess
import sys

WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TAR_FILE_PATH = os.path.join(WORKSPACE_DIR, "hugegraph.tar.gz")
SERVER_DIR    = os.path.join(WORKSPACE_DIR, "hugegraph-server")
TEMP_DIR      = os.path.join(WORKSPACE_DIR, "temp_extract")

def check_java():
    try:
        r = subprocess.run(["java", "-version"], stderr=subprocess.PIPE, text=True)
        print("[+] Java found:", r.stderr.strip().split("\n")[0])
        return True
    except FileNotFoundError:
        print("[-] Java not found! Install Java 11 or 17 first.")
        return False

def extract_and_setup():
    if not check_java():
        sys.exit(1)

    if os.path.exists(SERVER_DIR):
        print("[+] hugegraph-server directory already exists — skipping extraction.")
    else:
        if not os.path.exists(TAR_FILE_PATH):
            print(f"[-] {TAR_FILE_PATH} not found. Run setup_hugegraph.py first.")
            sys.exit(1)

        print(f"[*] Extracting {TAR_FILE_PATH}  (this takes ~30 s) ...")
        os.makedirs(TEMP_DIR, exist_ok=True)
        with tarfile.open(TAR_FILE_PATH, "r:gz") as tar:
            tar.extractall(path=TEMP_DIR)

        # Move extracted folder to final destination
        entries = os.listdir(TEMP_DIR)
        if not entries:
            print("[-] Extraction produced no files.")
            sys.exit(1)
        source = os.path.join(TEMP_DIR, entries[0])
        shutil.move(source, SERVER_DIR)
        shutil.rmtree(TEMP_DIR, ignore_errors=True)
        print(f"[+] Server installed at: {SERVER_DIR}")

    # Create convenient Windows batch files
    run_init_bat   = os.path.join(SERVER_DIR, "run_init.bat")
    run_server_bat = os.path.join(SERVER_DIR, "run_server.bat")

    with open(run_init_bat, "w") as f:
        f.write("@echo off\n")
        f.write("echo Initializing HugeGraph Database (runs once) ...\n")
        f.write('java -cp "lib/*" org.apache.hugegraph.cmd.InitServer'
                " conf/gremlin-server.yaml conf/rest-server.properties\n")
        f.write("echo Done! You can close this window.\npause\n")

    with open(run_server_bat, "w") as f:
        f.write("@echo off\n")
        f.write("echo Starting HugeGraph Server on http://localhost:8080 ...\n")
        f.write('java -cp "lib/*" org.apache.hugegraph.HugeGraphServer'
                " conf/gremlin-server.yaml conf/rest-server.properties\n")
        f.write("pause\n")

    print("[+] Batch files created:")
    print(f"    {run_init_bat}")
    print(f"    {run_server_bat}")
    print()
    print("=" * 60)
    print("  Next steps:")
    print(f"  1.  cd {SERVER_DIR}")
    print("  2.  run_init.bat    (first time only)")
    print("  3.  run_server.bat  (keep open — server runs on port 8080)")
    print()
    print("  Then back in your project root run:")
    print("    python ingest_hugegraph.py")
    print("    streamlit run app.py")
    print("=" * 60)

if __name__ == "__main__":
    extract_and_setup()
