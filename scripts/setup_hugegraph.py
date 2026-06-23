"""
Download and extract Apache HugeGraph Server 1.3.0.
Uses Python urllib with progress, then extracts with Python tarfile.
Run once: python scripts/setup_hugegraph.py
"""
import os, sys, subprocess, shutil, tarfile, urllib.request, time

WORKSPACE_DIR  = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TAR_FILE_PATH  = os.path.join(WORKSPACE_DIR, "hugegraph.tar.gz")
SERVER_DIR     = os.path.join(WORKSPACE_DIR, "hugegraph-server")
TEMP_DIR       = os.path.join(WORKSPACE_DIR, "temp_extract")

# Primary and fallback URLs for HugeGraph 1.3.0
URLS = [
    "https://archive.apache.org/dist/incubator/hugegraph/1.3.0/apache-hugegraph-incubating-1.3.0.tar.gz",
    "https://downloads.apache.org/incubator/hugegraph/1.3.0/apache-hugegraph-incubating-1.3.0.tar.gz",
]

def check_java():
    try:
        r = subprocess.run(["java", "-version"], stderr=subprocess.PIPE, text=True)
        print("[+] Java:", r.stderr.strip().split("\n")[0])
        return True
    except FileNotFoundError:
        print("[-] Java not found. Install Java 11 or 17 and add to PATH.")
        return False

def download(url, dest):
    print(f"[*] Downloading from:\n    {url}")
    last_printed = [0]
    start = time.time()

    def hook(count, block_size, total_size):
        if total_size <= 0:
            return
        downloaded = count * block_size
        pct = min(100, downloaded * 100 / total_size)
        now = time.time()
        if now - last_printed[0] >= 5 or pct >= 100:
            speed = downloaded / max(1, now - start) / 1024 / 1024
            print(f"    {pct:.1f}% ({downloaded/1024/1024:.1f} MB / {total_size/1024/1024:.1f} MB)  {speed:.2f} MB/s")
            last_printed[0] = now

    urllib.request.urlretrieve(url, dest, reporthook=hook)
    print("[+] Download complete.")

def extract():
    print(f"[*] Extracting {TAR_FILE_PATH} ...")
    os.makedirs(TEMP_DIR, exist_ok=True)
    with tarfile.open(TAR_FILE_PATH, "r:gz", errorlevel=0) as tar:
        tar.extractall(path=TEMP_DIR)
    entries = os.listdir(TEMP_DIR)
    if not entries:
        raise RuntimeError("Extraction produced no files.")
    source = os.path.join(TEMP_DIR, entries[0])
    if os.path.exists(SERVER_DIR):
        shutil.rmtree(SERVER_DIR)
    shutil.move(source, SERVER_DIR)
    shutil.rmtree(TEMP_DIR, ignore_errors=True)
    print(f"[+] Server installed at: {SERVER_DIR}")

def write_batch_files():
    run_init_bat   = os.path.join(SERVER_DIR, "run_init.bat")
    run_server_bat = os.path.join(SERVER_DIR, "run_server.bat")

    with open(run_init_bat, "w") as f:
        f.write("@echo off\n")
        f.write("echo Initializing HugeGraph DB (runs once)...\n")
        f.write('java -cp "lib/*" org.apache.hugegraph.cmd.InitServer'
                " conf/gremlin-server.yaml conf/rest-server.properties\n")
        f.write("echo Initialization done.\npause\n")

    with open(run_server_bat, "w") as f:
        f.write("@echo off\n")
        f.write("echo Starting HugeGraph Server on http://localhost:8080 ...\n")
        f.write('java -cp "lib/*" org.apache.hugegraph.HugeGraphServer'
                " conf/gremlin-server.yaml conf/rest-server.properties\n")
        f.write("pause\n")

    print(f"[+] Batch files created: run_init.bat, run_server.bat")

def main():
    if not check_java():
        sys.exit(1)

    if os.path.exists(SERVER_DIR):
        print("[+] hugegraph-server already present — skipping download/extract.")
        write_batch_files()
    else:
        # Download
        success = False
        for url in URLS:
            try:
                download(url, TAR_FILE_PATH)
                success = True
                break
            except Exception as e:
                print(f"[-] Download failed ({e}), trying next URL...")
                if os.path.exists(TAR_FILE_PATH):
                    os.remove(TAR_FILE_PATH)

        if not success:
            print("[-] All download URLs failed. Check your internet connection.")
            sys.exit(1)

        # Extract
        try:
            extract()
        except Exception as e:
            print(f"[-] Extraction error: {e}")
            sys.exit(1)
        finally:
            if os.path.exists(TAR_FILE_PATH):
                os.remove(TAR_FILE_PATH)
                print("[*] Cleaned up tar.gz")

        write_batch_files()

    print()
    print("=" * 62)
    print("  HUGEGRAPH SERVER READY")
    print(f"  Location : {SERVER_DIR}")
    print()
    print("  To start the server:")
    print(f"    1. Open a new terminal")
    print(f"    2. cd {SERVER_DIR}")
    print(f"    3. .\\run_init.bat   (first time only)")
    print(f"    4. .\\run_server.bat (keep it running)")
    print()
    print("  Then run in the project root:")
    print("    python ingest_hugegraph.py")
    print("    streamlit run app.py")
    print("=" * 62)

if __name__ == "__main__":
    main()
