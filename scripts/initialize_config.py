"""
Script to initialize and update hugegraph-llm's config.ini settings.
Sets the HugeGraph server port to 8081 and other defaults.
"""
import os
import sys

def main():
    print("[*] Initializing hugegraph-llm library configuration...")
    try:
        from hugegraph_llm.utils.config import Config
        from hugegraph_llm.utils.constants import Constants
        
        # Configure HugeGraph section
        c_hg = Config(section=Constants.HUGEGRAPH_CONFIG)
        c_hg.update_config({
            "ip": "127.0.0.1",
            "port": "8081",
            "user": "admin",
            "pwd": "admin",
            "graph": "hugegraph"
        })
        print(f"[+] HugeGraph settings updated in: {c_hg.config_file}")
        
        # Configure LLM section with placeholders
        c_llm = Config(section=Constants.LLM_CONFIG)
        c_llm.update_config({
            "type": "openai",
            "api_key": "dummy_key",
            "model_name": "gpt-3.5-turbo",
            "max_token": "4000"
        })
        print(f"[+] LLM settings updated in: {c_llm.config_file}")
        
        print("[+] Configuration successfully initialized!")
    except Exception as e:
        print(f"[-] Failed to initialize configuration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
