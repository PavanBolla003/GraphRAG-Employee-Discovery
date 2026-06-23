import os
import csv
import random

# Ensure data directory exists
os.makedirs("data", exist_ok=True)

# Define constants
SKILLS = [
    "Python", "Java", "React", "NodeJS", "AWS", "Azure", 
    "Machine Learning", "Deep Learning", "SQL", "Power BI", 
    "Spark", "Kafka", "Docker", "Kubernetes", "Data Engineering", 
    "MLOps", "GenAI", "TensorFlow", "PyTorch", "Snowflake"
]

DOMAINS = [
    "Banking", "Insurance", "Retail", "Healthcare", 
    "Telecom", "Manufacturing", "Automotive", "Logistics"
]

CERTIFICATIONS = [
    "AWS Associate", "Azure Fundamentals", "Databricks Associate", 
    "Google Cloud Engineer", "Snowflake Associate"
]

LOCATIONS = ["Chennai", "Bangalore", "Hyderabad", "Pune", "Mumbai", "Delhi"]
STATUSES = ["ON_PROJECT", "BENCH"]

PROJECT_TEMPLATES = [
    ("Fraud Detection System", "Banking"),
    ("Risk Analytics Platform", "Banking"),
    ("Credit Scoring Engine", "Banking"),
    ("Algorithmic Trading Dashboard", "Banking"),
    ("Insurance Claims Engine", "Insurance"),
    ("Customer Churn Predictor", "Telecom"),
    ("Retail Analytics Platform", "Retail"),
    ("Supply Chain Optimizer", "Logistics"),
    ("Predictive Maintenance Hub", "Manufacturing"),
    ("Patient Health Tracker", "Healthcare"),
    ("Automotive Telematics Platform", "Automotive"),
    ("Inventory Forecasting Engine", "Retail"),
    ("Fraud Prevention Portal", "Insurance"),
    ("Billing & Invoice Manager", "Telecom"),
    ("Warehouse Automation API", "Logistics"),
    ("Medical Image Analyzer", "Healthcare"),
    ("Smart Grid Energy Analyst", "Manufacturing"),
    ("Fleet Routing System", "Logistics"),
    ("E-Commerce Recommendation Engine", "Retail"),
    ("Underwriting Automation Engine", "Insurance")
]

# Seed for reproducibility
random.seed(42)

def generate_first_names():
    return ["Aarav", "Aditi", "Amit", "Ananya", "Arjun", "Deepika", "Divya", "Ganesh", "Hari", "Ishaan", 
            "Kavita", "Kiran", "Madhav", "Meera", "Neha", "Nikhil", "Pooja", "Rahul", "Rohan", "Sanjay", 
            "Shreya", "Siddharth", "Sneha", "Vikram", "Yash", "Alexander", "Emily", "Michael", "Sarah", "David",
            "James", "John", "Patricia", "Robert", "Jennifer", "Linda", "Elizabeth", "William", "Barbara", "Richard"]

def generate_last_names():
    return ["Sharma", "Patel", "Verma", "Gupta", "Kumar", "Singh", "Joshi", "Mehta", "Rao", "Nair",
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez",
            "Reddy", "Choudhury", "Bose", "Sen", "Deshmukh", "Kulkarni", "Prasad", "Iyer", "Pillai", "Das"]

def generate_skills_based_on_exp(exp, designation):
    # Architects/Leads have advanced skills (ML, GenAI, Kubernetes, Spark)
    # Trainees have foundational skills (Python, Java, React, SQL)
    advanced = ["Machine Learning", "Deep Learning", "Spark", "Kafka", "Kubernetes", "MLOps", "GenAI", "TensorFlow", "PyTorch", "Snowflake"]
    foundational = ["Python", "Java", "React", "NodeJS", "AWS", "Azure", "SQL", "Power BI", "Docker", "Data Engineering"]
    
    num_skills = random.randint(2, 5)
    if designation in ["Lead", "Architect"]:
        pool = advanced * 2 + foundational
    elif designation == "Senior Developer":
        pool = advanced + foundational
    else:
        pool = foundational * 2 + advanced
        
    return random.sample(list(set(pool)), min(num_skills, len(set(pool))))

def main():
    print("[*] Generating synthetic enterprise dataset...")
    
    # 1. Generate Skills
    skills_data = [{"skill_id": f"S{i+1:03d}", "name": skill} for i, skill in enumerate(SKILLS)]
    with open("data/skills.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["skill_id", "name"])
        writer.writeheader()
        writer.writerows(skills_data)
    print(f"[+] Generated {len(SKILLS)} skills.")
    
    # 2. Generate Domains
    domains_data = [{"domain_id": f"D{i+1:03d}", "name": domain} for i, domain in enumerate(DOMAINS)]
    with open("data/domains.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["domain_id", "name"])
        writer.writeheader()
        writer.writerows(domains_data)
    print(f"[+] Generated {len(DOMAINS)} domains.")
    
    # 3. Generate Certifications
    certifications_data = [{"cert_id": f"C{i+1:03d}", "name": cert} for i, cert in enumerate(CERTIFICATIONS)]
    with open("data/certifications.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["cert_id", "name"])
        writer.writeheader()
        writer.writerows(certifications_data)
    print(f"[+] Generated {len(CERTIFICATIONS)} certifications.")
    
    # 4. Generate 50 Projects
    projects_data = []
    project_skills = []
    
    # Pre-generate 50 projects
    for i in range(50):
        proj_id = f"P{i+1:03d}"
        if i < len(PROJECT_TEMPLATES):
            proj_name, domain = PROJECT_TEMPLATES[i]
        else:
            domain = random.choice(DOMAINS)
            proj_name = f"{domain} {random.choice(['Analytics Engine', 'Integration Hub', 'Intelligence API', 'Data Pipeline', 'Compliance Portal', 'Migration Tool'])}"
            
        required_skills = random.sample(SKILLS, random.randint(2, 5))
        projects_data.append({
            "project_id": proj_id,
            "project_name": proj_name,
            "domain": domain
        })
        
        # Save project_skills relationships
        for skill in required_skills:
            skill_id = next(s["skill_id"] for s in skills_data if s["name"] == skill)
            project_skills.append({
                "project_id": proj_id,
                "skill_id": skill_id
            })
            
    with open("data/projects.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["project_id", "project_name", "domain"])
        writer.writeheader()
        writer.writerows(projects_data)
        
    with open("data/project_skills.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["project_id", "skill_id"])
        writer.writeheader()
        writer.writerows(project_skills)
    print(f"[+] Generated 50 projects and required skills relationships.")
    
    # 5. Generate 1000 Employees & Employee Relationships
    first_names = generate_first_names()
    last_names = generate_last_names()
    
    employees_data = []
    emp_skills = []
    emp_projects = []
    emp_certs = []
    emp_domains = []
    
    for i in range(1000):
        emp_id = f"E{i+1:04d}"
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        exp = random.randint(1, 20)
        location = random.choice(LOCATIONS)
        status = random.choices(STATUSES, weights=[70, 30])[0] # 70% ON_PROJECT, 30% BENCH
        
        # Determine designation based on experience
        if exp <= 2:
            designation = "Trainee"
        elif exp <= 5:
            designation = "Developer"
        elif exp <= 8:
            designation = "Senior Developer"
        elif exp <= 12:
            designation = "Lead"
        else:
            designation = "Architect"
            
        employees_data.append({
            "emp_id": emp_id,
            "name": name,
            "experience_years": exp,
            "location": location,
            "status": status,
            "designation": designation
        })
        
        # Relationships: 2-5 skills
        assigned_skills = generate_skills_based_on_exp(exp, designation)
        for skill in assigned_skills:
            skill_id = next(s["skill_id"] for s in skills_data if s["name"] == skill)
            emp_skills.append({
                "emp_id": emp_id,
                "skill_id": skill_id
            })
            
        # Relationships: 0-3 previous projects
        num_proj = random.randint(0, 3)
        assigned_projs = random.sample(projects_data, num_proj)
        for proj in assigned_projs:
            emp_projects.append({
                "emp_id": emp_id,
                "project_id": proj["project_id"]
            })
            
        # Relationships: 0-2 certifications
        num_certs = random.randint(0, 2)
        assigned_certs = random.sample(certifications_data, num_certs)
        for cert in assigned_certs:
            emp_certs.append({
                "emp_id": emp_id,
                "cert_id": cert["cert_id"]
            })
            
        # Relationships: 1 domain specialization
        assigned_domain = random.choice(domains_data)
        emp_domains.append({
            "emp_id": emp_id,
            "domain_id": assigned_domain["domain_id"]
        })
        
    with open("data/employees.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["emp_id", "name", "experience_years", "location", "status", "designation"])
        writer.writeheader()
        writer.writerows(employees_data)
        
    with open("data/employee_skills.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["emp_id", "skill_id"])
        writer.writeheader()
        writer.writerows(emp_skills)
        
    with open("data/employee_projects.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["emp_id", "project_id"])
        writer.writeheader()
        writer.writerows(emp_projects)
        
    with open("data/employee_certifications.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["emp_id", "cert_id"])
        writer.writeheader()
        writer.writerows(emp_certs)
        
    with open("data/employee_domains.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["emp_id", "domain_id"])
        writer.writeheader()
        writer.writerows(emp_domains)
        
    print(f"[+] Generated 1000 employees and all their relationship files.")
    print("[+] Synthetic dataset generation complete! Files saved under the 'data/' directory.")

if __name__ == "__main__":
    main()
