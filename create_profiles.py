import os
import csv
import sys

# Ensure profiles directory exists
os.makedirs("data/profiles", exist_ok=True)

def build_profile_text(emp_id, name, designation, exp, skills, certifications, domain, projects, status):
    profile = []
    profile.append(f"Employee: {emp_id}")
    profile.append(f"Name: {name}")
    profile.append(f"Designation: {designation}")
    profile.append(f"Experience: {exp} years")
    profile.append(f"Status: {status}")
    profile.append("")
    
    profile.append("Skills:")
    if skills:
        for skill in skills:
            profile.append(f"- {skill}")
    else:
        profile.append("- None")
    profile.append("")
    
    profile.append("Certifications:")
    if certifications:
        for cert in certifications:
            profile.append(f"- {cert}")
    else:
        profile.append("- None")
    profile.append("")
    
    profile.append("Domain:")
    profile.append(f"- {domain}")
    profile.append("")
    
    profile.append("Previous Projects:")
    if projects:
        for proj in projects:
            profile.append(f"- {proj}")
    else:
        profile.append("- None")
        
    return "\n".join(profile)

def create_profiles_from_csv():
    print("[*] Reading data from CSV files to generate profiles...")
    
    # 1. Load entities
    skills_map = {}
    with open("data/skills.csv", "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            skills_map[row["skill_id"]] = row["name"]
            
    domains_map = {}
    with open("data/domains.csv", "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            domains_map[row["domain_id"]] = row["name"]
            
    certs_map = {}
    with open("data/certifications.csv", "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            certs_map[row["cert_id"]] = row["name"]
            
    projects_map = {}
    with open("data/projects.csv", "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            projects_map[row["project_id"]] = row["project_name"]
            
    # 2. Load relationships
    emp_skills = {}
    with open("data/employee_skills.csv", "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            emp_skills.setdefault(row["emp_id"], []).append(skills_map[row["skill_id"]])
            
    emp_certs = {}
    with open("data/employee_certifications.csv", "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            emp_certs.setdefault(row["emp_id"], []).append(certs_map[row["cert_id"]])
            
    emp_projects = {}
    with open("data/employee_projects.csv", "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            emp_projects.setdefault(row["emp_id"], []).append(projects_map[row["project_id"]])
            
    emp_domains = {}
    with open("data/employee_domains.csv", "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            emp_domains[row["emp_id"]] = domains_map[row["domain_id"]]
            
    # 3. Read employees and write profiles
    with open("data/employees.csv", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            emp_id = row["emp_id"]
            skills = emp_skills.get(emp_id, [])
            certs = emp_certs.get(emp_id, [])
            projects = emp_projects.get(emp_id, [])
            domain = emp_domains.get(emp_id, "General")
            
            profile_content = build_profile_text(
                emp_id=emp_id,
                name=row["name"],
                designation=row["designation"],
                exp=row["experience_years"],
                skills=skills,
                certifications=certs,
                domain=domain,
                projects=projects,
                status=row["status"]
            )
            
            profile_path = f"data/profiles/{emp_id}.txt"
            with open(profile_path, "w", encoding="utf-8") as pf:
                pf.write(profile_content)
            count += 1
            
    print(f"[+] Generated {count} employee profiles from CSV data.")

def create_profiles_from_graph():
    print("[*] Attempting to generate profiles using HugeGraph database...")
    try:
        from graph_queries import HugeGraphQueries
        queries = HugeGraphQueries()
        # Test connection
        queries.execute_gremlin("g.V().limit(1)")
        
        # Get all employee IDs from graph
        emp_ids = queries.execute_gremlin("g.V().hasLabel('Employee').id()")
        emp_ids = [queries._parse_id(eid) for eid in emp_ids]
        
        if not emp_ids:
            print("[-] No employee vertices found in the graph. Ingestion might be empty.")
            return False
            
        count = 0
        for emp_id in emp_ids:
            details = queries.get_employee_details(emp_id)
            if not details:
                continue
                
            profile_content = build_profile_text(
                emp_id=emp_id,
                name=details["name"],
                designation=details["designation"],
                exp=details["experience_years"],
                skills=details["skills"],
                certifications=details["certifications"],
                domain=details["domain"],
                projects=details["projects"],
                status=details["status"]
            )
            
            profile_path = f"data/profiles/{emp_id}.txt"
            with open(profile_path, "w", encoding="utf-8") as pf:
                pf.write(profile_content)
            count += 1
            
        print(f"[+] Generated {count} employee profiles from graph queries.")
        return True
    except Exception as e:
        print(f"[-] Could not connect or query graph: {e}")
        return False

def main():
    # Attempt graph queries first, fall back to CSV if graph server not available
    success = create_profiles_from_graph()
    if not success:
        create_profiles_from_csv()
    print("[+] Employee profile creation complete!")

if __name__ == "__main__":
    main()
