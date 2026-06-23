"""
Automated downloader, installer, and runner for ngrok on Windows.
Runs from the workspace root.
"""
import os
import sys
import zipfile
import urllib.request
import subprocess
import json
import time

NGROK_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "ngrok_bin"))
NGROK_ZIP = os.path.join(NGROK_DIR, "ngrok.zip")
NGROK_EXE = os.path.join(NGROK_DIR, "ngrok.exe")
DOWNLOAD_URL = "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip"

def download_and_extract():
    if not os.path.exists(NGROK_DIR):
        os.makedirs(NGROK_DIR)
        
    if not os.path.exists(NGROK_EXE):
        print(f"[*] Downloading ngrok from {DOWNLOAD_URL}...")
        try:
            # Add User-Agent header to avoid HTTP 403 Forbidden
            req = urllib.request.Request(
                DOWNLOAD_URL, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            with urllib.request.urlopen(req) as response, open(NGROK_ZIP, 'wb') as out_file:
                out_file.write(response.read())
            print("[+] Download complete. Extracting zip...")
            with zipfile.ZipFile(NGROK_ZIP, 'r') as zip_ref:
                zip_ref.extractall(NGROK_DIR)
            print("[+] Extraction complete.")
            if os.path.exists(NGROK_ZIP):
                os.remove(NGROK_ZIP)
        except Exception as e:
            print(f"[-] Error downloading/extracting ngrok: {e}")
            sys.exit(1)
    else:
        print("[+] ngrok.exe is already present.")

def configure_token(authtoken):
    print("[*] Configuring ngrok authtoken...")
    try:
        cmd = [NGROK_EXE, "config", "add-authtoken", authtoken]
        subprocess.run(cmd, check=True, capture_output=True)
        print("[+] Authtoken configured successfully.")
    except Exception as e:
        print(f"[-] Error configuring authtoken: {e}")
        sys.exit(1)

def run_ngrok():
    print("[*] Starting ngrok tunnel on port 8501...")
    try:
        # Start ngrok in background
        proc = subprocess.Popen(
            [NGROK_EXE, "http", "8501", "--log", "stdout"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Give ngrok some time to establish connection
        time.sleep(5)
        
        # Read the public URL from ngrok's local API
        try:
            api_url = "http://127.0.0.1:4040/api/tunnels"
            req = urllib.request.urlopen(api_url)
            tunnels = json.loads(req.read().decode())
            if tunnels.get("tunnels"):
                public_url = tunnels["tunnels"][0]["public_url"]
                print("=" * 60)
                print(f"[SUCCESS] ngrok tunnel is live!")
                print(f"Public URL: {public_url}")
                print("=" * 60)
                # Keep script running to maintain the process
                proc.wait()
            else:
                print("[-] No active tunnels found in ngrok API.")
        except Exception as e:
            print(f"[-] Could not query ngrok local API: {e}")
            print("[*] Dumping initial ngrok stdout:")
            # Read whatever output is available
            stdout_lines = []
            for _ in range(10):
                line = proc.stdout.readline()
                if line:
                    print(line.strip())
            
    except Exception as e:
        print(f"[-] Error running ngrok: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python start_ngrok.py <authtoken>")
        sys.exit(1)
        
    token = sys.argv[1]
    download_and_extract()
    configure_token(token)
    run_ngrok()
