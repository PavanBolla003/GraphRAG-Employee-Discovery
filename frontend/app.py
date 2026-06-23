"""
frontend/app.py — Streamlit dashboard entry point.
Delegates to the root app.py so both locations work.
Usage: streamlit run frontend/app.py
       streamlit run app.py         (preferred)
"""
import subprocess, sys, os

root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.exit(subprocess.call([sys.executable, "-m", "streamlit", "run",
                          os.path.join(root, "app.py")] + sys.argv[1:]))
