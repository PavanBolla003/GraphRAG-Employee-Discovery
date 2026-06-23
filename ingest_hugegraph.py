import os
import csv
import time
import sys
from pyhugegraph.client import PyHugeClient

def get_client(host="127.0.0.1", port="8081", graph="hugegraph", max_retries=10, delay=3):
    print(f"[*] Connecting to Apache HugeGraph Server at {host}:{port}...")

    for attempt in range(1, max_retries + 1):
        try:
            client = PyHugeClient(host, port, user="admin", pwd="admin", graph=graph)
            # Try a simple connection check
            client.gremlin().exec("g.V().limit(1)")
            print("[+] Successfully connected to HugeGraph Server!")
            return client
        except Exception as e:
            print(f"[-] Connection attempt {attempt}/{max_retries} failed: {e}")
            if attempt < max_retries:
                print(f"    Retrying in {delay} seconds...")
                time.sleep(delay)
    print("[-] Could not connect to HugeGraph Server. Please ensure it is running.")
    sys.exit(1)

def define_schema(client):
    print("[*] Defining HugeGraph schema...")
    schema = client.schema()
    
    # 1. Define Property Keys
    print("    - Creating Property Keys...")
    schema.propertyKey("name").asText().ifNotExist().create()
    schema.propertyKey("experience_years").asInt().ifNotExist().create()
    schema.propertyKey("location").asText().ifNotExist().create()
    schema.propertyKey("status").asText().ifNotExist().create()
    schema.propertyKey("designation").asText().ifNotExist().create()
    schema.propertyKey("domain").asText().ifNotExist().create()
    
    # 2. Define Vertex Labels (using CUSTOMIZE_STRING ID strategy)
    print("    - Creating Vertex Labels...")
    schema.vertexLabel("Employee") \
          .properties("name", "experience_years", "location", "status", "designation") \
          .useCustomizeStringId() \
          .ifNotExist().create()
          
    schema.vertexLabel("Skill") \
          .properties("name") \
          .useCustomizeStringId() \
          .ifNotExist().create()
          
    schema.vertexLabel("Project") \
          .properties("name", "domain") \
          .useCustomizeStringId() \
          .ifNotExist().create()
          
    schema.vertexLabel("Domain") \
          .properties("name") \
          .useCustomizeStringId() \
          .ifNotExist().create()
          
    schema.vertexLabel("Certification") \
          .properties("name") \
          .useCustomizeStringId() \
          .ifNotExist().create()
          
    # 3. Define Edge Labels
    print("    - Creating Edge Labels...")
    schema.edgeLabel("HAS_SKILL").sourceLabel("Employee").targetLabel("Skill").ifNotExist().create()
    schema.edgeLabel("WORKED_ON").sourceLabel("Employee").targetLabel("Project").ifNotExist().create()
    schema.edgeLabel("HAS_CERTIFICATION").sourceLabel("Employee").targetLabel("Certification").ifNotExist().create()
    schema.edgeLabel("BELONGS_TO_DOMAIN").sourceLabel("Employee").targetLabel("Domain").ifNotExist().create()
    schema.edgeLabel("REQUIRES_SKILL").sourceLabel("Project").targetLabel("Skill").ifNotExist().create()
    
    # 4. Define Index Labels (Important for property-based filtering)
    print("    - Creating Index Labels...")
    schema.indexLabel("employeeByStatus").onV("Employee").by("status").secondary().ifNotExist().create()
    schema.indexLabel("employeeByLocation").onV("Employee").by("location").secondary().ifNotExist().create()
    schema.indexLabel("employeeByDesignation").onV("Employee").by("designation").secondary().ifNotExist().create()
    schema.indexLabel("employeeByExperience").onV("Employee").by("experience_years").range().ifNotExist().create()
    schema.indexLabel("skillByName").onV("Skill").by("name").secondary().ifNotExist().create()
    schema.indexLabel("projectByName").onV("Project").by("name").secondary().ifNotExist().create()
    schema.indexLabel("domainByName").onV("Domain").by("name").secondary().ifNotExist().create()
    schema.indexLabel("certificationByName").onV("Certification").by("name").secondary().ifNotExist().create()
    
    print("[+] Schema definition completed.")

def clear_graph_data(client):
    print("[*] Clearing existing graph data...")
    try:
        # Clear edges first
        client.gremlin().exec("g.E().drop()")
        # Clear vertices
        client.gremlin().exec("g.V().drop()")
        print("[+] Graph data cleared.")
    except Exception as e:
        print(f"[-] Warning: Failed to clear graph data: {e}")

def ingest_vertices(client):
    g = client.graph()
    
    # 1. Ingest Skills
    print("[*] Ingesting Skills...")
    with open("data/skills.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            g.addVertex("Skill", {"name": row["name"]}, id=row["skill_id"])
            
    # 2. Ingest Domains
    print("[*] Ingesting Domains...")
    with open("data/domains.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            g.addVertex("Domain", {"name": row["name"]}, id=row["domain_id"])
            
    # 3. Ingest Certifications
    print("[*] Ingesting Certifications...")
    with open("data/certifications.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            g.addVertex("Certification", {"name": row["name"]}, id=row["cert_id"])
            
    # 4. Ingest Projects
    print("[*] Ingesting Projects...")
    with open("data/projects.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            g.addVertex("Project", {"name": row["project_name"], "domain": row["domain"]}, id=row["project_id"])
            
    # 5. Ingest Employees
    print("[*] Ingesting Employees...")
    with open("data/employees.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            g.addVertex("Employee", {
                "name": row["name"],
                "experience_years": int(row["experience_years"]),
                "location": row["location"],
                "status": row["status"],
                "designation": row["designation"]
            }, id=row["emp_id"])
             
    print("[+] Vertices ingestion completed.")


def ingest_edges(client):
    g = client.graph()
    
    # 1. Ingest HAS_SKILL
    print("[*] Ingesting HAS_SKILL edges...")
    with open("data/employee_skills.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            g.addEdge("HAS_SKILL", row["emp_id"], row["skill_id"], {})
            
    # 2. Ingest WORKED_ON
    print("[*] Ingesting WORKED_ON edges...")
    with open("data/employee_projects.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            g.addEdge("WORKED_ON", row["emp_id"], row["project_id"], {})
            
    # 3. Ingest HAS_CERTIFICATION
    print("[*] Ingesting HAS_CERTIFICATION edges...")
    with open("data/employee_certifications.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            g.addEdge("HAS_CERTIFICATION", row["emp_id"], row["cert_id"], {})
            
    # 4. Ingest BELONGS_TO_DOMAIN
    print("[*] Ingesting BELONGS_TO_DOMAIN edges...")
    with open("data/employee_domains.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            g.addEdge("BELONGS_TO_DOMAIN", row["emp_id"], row["domain_id"], {})
            
    # 5. Ingest REQUIRES_SKILL
    print("[*] Ingesting REQUIRES_SKILL edges...")
    with open("data/project_skills.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            g.addEdge("REQUIRES_SKILL", row["project_id"], row["skill_id"], {})
            
    print("[+] Edges ingestion completed.")

def verify_ingestion(client):
    print("[*] Verifying ingestion counts...")
    time.sleep(1) # Let indices update
    
    # Helper to execute and safely get the list first element
    def get_count(query):
        res = client.gremlin().exec(query)
        if isinstance(res, dict) and "data" in res:
            return res["data"][0] if res["data"] else 0
        return res[0] if isinstance(res, list) else 0

    # Vertices
    v_count = get_count("g.V().count()")
    print(f"    - Total Vertices: {v_count}")
    
    labels = ["Employee", "Skill", "Project", "Domain", "Certification"]
    for label in labels:
        count = get_count(f"g.V().hasLabel('{label}').count()")
        print(f"      * {label}: {count}")
        
    # Edges
    e_count = get_count("g.E().count()")
    print(f"    - Total Edges: {e_count}")
    
    elabels = ["HAS_SKILL", "WORKED_ON", "HAS_CERTIFICATION", "BELONGS_TO_DOMAIN", "REQUIRES_SKILL"]
    for elabel in elabels:
        count = get_count(f"g.E().hasLabel('{elabel}').count()")
        print(f"      * {elabel}: {count}")


def main():
    client = get_client()
    define_schema(client)
    clear_graph_data(client)
    ingest_vertices(client)
    ingest_edges(client)
    verify_ingestion(client)
    print("[+] Ingestion successfully finished!")

if __name__ == "__main__":
    main()
