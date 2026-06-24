"""
Download and extract Apache HugeGraph-Hubble 1.3.0 (from Toolchain).
Run once: python scripts/setup_hubble.py
"""
import os, sys, subprocess, shutil, tarfile, urllib.request, time, threading

WORKSPACE_DIR  = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TAR_FILE_PATH  = os.path.join(WORKSPACE_DIR, "toolchain.tar.gz")
HUBBLE_DIR     = os.path.join(WORKSPACE_DIR, "hugegraph-hubble")
TEMP_DIR       = os.path.join(WORKSPACE_DIR, "temp_extract_hubble")

# URLs for HugeGraph Toolchain 1.3.0
URLS = [
    "https://mirrors.tuna.tsinghua.edu.cn/apache/hugegraph/1.3.0/apache-hugegraph-toolchain-incubating-1.3.0.tar.gz",
    "https://mirrors.huaweicloud.com/apache/hugegraph/1.3.0/apache-hugegraph-toolchain-incubating-1.3.0.tar.gz",
    "https://mirrors.ustc.edu.cn/apache/hugegraph/1.3.0/apache-hugegraph-toolchain-incubating-1.3.0.tar.gz",
    "https://archive.apache.org/dist/incubator/hugegraph/1.3.0/apache-hugegraph-toolchain-incubating-1.3.0.tar.gz",
]

def check_java():
    try:
        r = subprocess.run(["java", "-version"], stderr=subprocess.PIPE, text=True)
        print("[+] Java:", r.stderr.strip().split("\n")[0])
        return True
    except FileNotFoundError:
        print("[-] Java not found. Install Java 11 or 17 and add to PATH.")
        return False

def download_chunk(url, start, end, chunk_file, thread_idx, retries=5):
    headers = {"Range": f"bytes={start}-{end}"}
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                with open(chunk_file, "wb") as f:
                    shutil.copyfileobj(response, f)
            return True
        except Exception as e:
            print(f"\n    [Thread {thread_idx}] Attempt {attempt+1} failed: {e}")
            time.sleep(2)
    return False

def download(url, dest, num_threads=8):
    print(f"[*] Downloading toolchain from:\n    {url}")
    print(f"[*] Fetching headers to determine file size...")
    try:
        req = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(req, timeout=15) as r:
            headers = r.info()
            total_size = int(headers.get("Content-Length", 0))
    except Exception as e:
        print(f"[-] HEAD request failed: {e}. Falling back to single-threaded download...")
        urllib.request.urlretrieve(url, dest)
        return

    if total_size <= 0:
        print("[-] Content-Length not found. Falling back to single-threaded download...")
        urllib.request.urlretrieve(url, dest)
        return

    print(f"[+] File size: {total_size / (1024*1024):.2f} MB")
    chunk_size = total_size // num_threads
    threads = []
    chunk_files = []
    
    start_time = time.time()
    
    for i in range(num_threads):
        start = i * chunk_size
        end = total_size - 1 if i == num_threads - 1 else (i + 1) * chunk_size - 1
        chunk_file = f"{dest}.part{i}"
        chunk_files.append(chunk_file)
        
        t = threading.Thread(target=download_chunk, args=(url, start, end, chunk_file, i))
        threads.append(t)
        t.start()
        
    while any(t.is_alive() for t in threads):
        downloaded = 0
        for f in chunk_files:
            if os.path.exists(f):
                downloaded += os.path.getsize(f)
        pct = (downloaded / total_size) * 100
        elapsed = time.time() - start_time
        speed = downloaded / max(1, elapsed) / 1024 / 1024
        print(f"    Downloaded: {downloaded / (1024*1024):.2f} MB / {total_size / (1024*1024):.2f} MB ({pct:.1f}%) | Speed: {speed:.2f} MB/s", end="\r")
        sys.stdout.flush()
        time.sleep(1)
        
    for t in threads:
        t.join()
        
    # Check if all chunks were downloaded successfully
    for chunk_file in chunk_files:
        if not os.path.exists(chunk_file) or os.path.getsize(chunk_file) == 0:
            raise RuntimeError(f"Download failed: missing or empty chunk: {chunk_file}")
        
    # Merge chunks
    print("\n[*] Merging chunks...")
    with open(dest, "wb") as outfile:
        for chunk_file in chunk_files:
            with open(chunk_file, "rb") as infile:
                shutil.copyfileobj(infile, outfile)
            os.remove(chunk_file)
            
    print(f"[+] Download complete: {dest}")

def extract():
    print(f"[*] Extracting {TAR_FILE_PATH} ...")
    os.makedirs(TEMP_DIR, exist_ok=True)
    with tarfile.open(TAR_FILE_PATH, "r:gz", errorlevel=0) as tar:
        tar.extractall(path=TEMP_DIR)
        
    # Toolchain has multiple sub-folders. We want to find the one starting with 'apache-hugegraph-hubble'
    toolchain_extracted_dir = os.path.join(TEMP_DIR, os.listdir(TEMP_DIR)[0])
    hubble_subfolders = [f for f in os.listdir(toolchain_extracted_dir) if "hubble" in f]
    
    if not hubble_subfolders:
        raise RuntimeError("No hubble subdirectory found in toolchain archive.")
        
    source = os.path.join(toolchain_extracted_dir, hubble_subfolders[0])
    
    if os.path.exists(HUBBLE_DIR):
        shutil.rmtree(HUBBLE_DIR)
        
    shutil.move(source, HUBBLE_DIR)
    shutil.rmtree(TEMP_DIR, ignore_errors=True)
    print(f"[+] Hubble installed at: {HUBBLE_DIR}")

def write_batch_files():
    run_hubble_bat = os.path.join(HUBBLE_DIR, "run_hubble.bat")
    
    # We will locate the jar file inside lib directory of hugegraph-hubble
    lib_dir = os.path.join(HUBBLE_DIR, "lib")
    jar_file = None
    if os.path.exists(lib_dir):
        jars = [f for f in os.listdir(lib_dir) if f.startswith("hugegraph-hubble") and f.endswith(".jar")]
        if jars:
            jar_file = jars[0]
            
    if not jar_file:
        jar_file = "hugegraph-hubble-1.3.0.jar"
        
    with open(run_hubble_bat, "w") as f:
        f.write("@echo off\n")
        f.write("echo Starting HugeGraph Hubble on http://localhost:8088 ...\n")
        f.write(f'java -cp "conf;lib/{jar_file};lib/*" org.apache.hugegraph.HubbleStart\n')
        f.write("pause\n")
        
    print(f"[+] Batch file created: run_hubble.bat")

def main():
    if not check_java():
        sys.exit(1)

    if os.path.exists(HUBBLE_DIR):
        print("[+] hugegraph-hubble already present — skipping download/extract.")
        write_batch_files()
    else:
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
    print("  HUGEGRAPH HUBBLE READY")
    print(f"  Location : {HUBBLE_DIR}")
    print()
    print("  To start Hubble:")
    print(f"    1. Open a new terminal")
    print(f"    2. cd {HUBBLE_DIR}")
    print(f"    3. .\\run_hubble.bat (keep it running)")
    print()
    print("  Access Hubble web UI at http://localhost:8088")
    print("=" * 62)

if __name__ == "__main__":
    main()
