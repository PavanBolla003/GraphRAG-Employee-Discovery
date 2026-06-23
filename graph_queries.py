import re
from pyhugegraph.client import PyHugeClient

class HugeGraphQueries:
    def __init__(self, host="127.0.0.1", port="8081", graph="hugegraph"):
        self.client = PyHugeClient(host, port, user="admin", pwd="admin", graph=graph)

        
    def _parse_id(self, raw_id):
        """
        Parses the raw ID returned by HugeGraph (which might be formatted like '1:Employee:E001' or 'E001')
        to extract the pure custom string ID (e.g. 'E001').
        """
        if not isinstance(raw_id, str):
            raw_id = str(raw_id)
        if ":" in raw_id:
            return raw_id.split(":")[-1]
        return raw_id

    def execute_gremlin(self, query):
        """Executes a raw Gremlin query and returns the 'data' list of results."""
        try:
            res = self.client.gremlin().exec(query)
            if isinstance(res, dict) and "data" in res:
                return res["data"]
            return res
        except Exception as e:
            print(f"[-] Gremlin execution error for query '{query}': {e}")
            return []


    def get_employee_details(self, emp_id):
        """Fetches all attributes and connections for a single employee."""
        emp_id_clean = self._parse_id(emp_id)
        
        # Get employee vertex properties
        emp_query = f"g.V('{emp_id_clean}').valueMap(true)"
        emp_res = self.execute_gremlin(emp_query)
        if not emp_res:
            return None
            
        emp_props = emp_res[0]
        
        # Format properties (HugeGraph returns values as lists by default in valueMap)
        properties = {}
        for k, v in emp_props.items():
            if isinstance(v, list) and len(v) > 0:
                properties[k] = v[0]
            else:
                properties[k] = v
                
        # Resolve ID and label
        properties["emp_id"] = emp_id_clean
        properties["name"] = properties.get("name", "Unknown")
        properties["experience_years"] = int(properties.get("experience_years", 0))
        properties["location"] = properties.get("location", "Unknown")
        properties["status"] = properties.get("status", "Unknown")
        properties["designation"] = properties.get("designation", "Unknown")
        
        # Get Skills
        skills_query = f"g.V('{emp_id_clean}').out('HAS_SKILL').values('name')"
        properties["skills"] = self.execute_gremlin(skills_query)
        
        # Get Previous Projects
        projects_query = f"g.V('{emp_id_clean}').out('WORKED_ON').values('name')"
        properties["projects"] = self.execute_gremlin(projects_query)
        
        # Get Certifications
        certs_query = f"g.V('{emp_id_clean}').out('HAS_CERTIFICATION').values('name')"
        properties["certifications"] = self.execute_gremlin(certs_query)
        
        # Get Domain
        domain_query = f"g.V('{emp_id_clean}').out('BELONGS_TO_DOMAIN').values('name')"
        domains = self.execute_gremlin(domain_query)
        properties["domain"] = domains[0] if domains else "General"
        
        return properties

    def find_bench_employees(self):
        """Finds all employees whose status is BENCH."""
        query = "g.V().hasLabel('Employee').has('status', 'BENCH').id()"
        res = self.execute_gremlin(query)
        return [self._parse_id(eid) for eid in res]

    def find_employees_by_skill(self, skill_name):
        """Finds employees with a specific skill."""
        query = f"g.V().hasLabel('Skill').has('name', '{skill_name}').in('HAS_SKILL').id()"
        res = self.execute_gremlin(query)
        return [self._parse_id(eid) for eid in res]

    def find_employees_by_skills(self, skill_names, status=None):
        """
        Finds employees possessing ALL of the specified skills.
        Optionally filters by availability status (e.g. 'BENCH').
        """
        if not skill_names:
            if status:
                return [self._parse_id(eid) for eid in self.execute_gremlin(f"g.V().hasLabel('Employee').has('status', '{status}').id()")]
            return [self._parse_id(eid) for eid in self.execute_gremlin("g.V().hasLabel('Employee').id()")]
            
        query = "g.V().hasLabel('Employee')"
        if status:
            query += f".has('status', '{status}')"
            
        for skill in skill_names:
            query += f".where(out('HAS_SKILL').has('name', '{skill}'))"
            
        query += ".id()"
        res = self.execute_gremlin(query)
        return [self._parse_id(eid) for eid in res]

    def find_employees_by_domain(self, domain_name):
        """Finds employees specializing in a given domain."""
        query = f"g.V().hasLabel('Employee').where(out('BELONGS_TO_DOMAIN').has('name', '{domain_name}')).id()"
        res = self.execute_gremlin(query)
        return [self._parse_id(eid) for eid in res]

    def find_employees_by_certification(self, cert_name):
        """Finds employees holding a given certification."""
        query = f"g.V().hasLabel('Employee').where(out('HAS_CERTIFICATION').has('name', '{cert_name}')).id()"
        res = self.execute_gremlin(query)
        return [self._parse_id(eid) for eid in res]

    def find_similar_employees(self, emp_id, limit=5):
        """
        Finds other employees who share the most skills with the target employee.
        Returns a list of tuples: (employee_id, shared_skill_count)
        
        Note: HugeGraph's Groovy 2.x does not support order(local).by(values, desc)
        on groupCount maps, so we retrieve the raw map and sort in Python.
        """
        emp_id_clean = self._parse_id(emp_id)
        # Gremlin: traverse to skills, then back to other employees, then groupCount
        query = (
            f"g.V('{emp_id_clean}').as('e').out('HAS_SKILL').in('HAS_SKILL')"
            f".where(neq('e')).groupCount()"
        )
        res = self.execute_gremlin(query)
        
        if not res:
            return []
            
        # HugeGraph returns groupCount results inside a single map: [{id1: count1, id2: count2, ...}]
        raw_map = res[0] if isinstance(res, list) and len(res) > 0 else {}
        
        similar = []
        for raw_k, count in raw_map.items():
            similar.append((self._parse_id(raw_k), count))
            
        # Sort by shared skill count descending and limit
        similar.sort(key=lambda x: x[1], reverse=True)
        return similar[:limit]

    def analyze_skill_gap(self, emp_id, project_id):
        """
        Compares employee skills with project requirements.
        Returns a dict containing:
        - employee_skills: list of employee skill names
        - required_skills: list of project required skill names
        - matching_skills: list of intersection skill names
        - missing_skills: list of required skills not possessed by the employee
        """
        emp_id_clean = self._parse_id(emp_id)
        proj_id_clean = self._parse_id(project_id)
        
        # Get employee skills
        emp_skills_query = f"g.V('{emp_id_clean}').out('HAS_SKILL').values('name')"
        emp_skills = self.execute_gremlin(emp_skills_query)
        
        # Get project required skills
        proj_skills_query = f"g.V('{proj_id_clean}').out('REQUIRES_SKILL').values('name')"
        proj_skills = self.execute_gremlin(proj_skills_query)
        
        emp_set = set(emp_skills)
        proj_set = set(proj_skills)
        
        matching = list(emp_set.intersection(proj_set))
        missing = list(proj_set - emp_set)
        
        return {
            "employee_skills": list(emp_skills),
            "required_skills": list(proj_skills),
            "matching_skills": matching,
            "missing_skills": missing
        }
        
    def find_employees_hybrid_filters(self, skills=None, domain=None, certs=None, status=None):
        """
        Filters employees based on multiple criteria: skills (AND match), domain, certification, status.
        """
        query = "g.V().hasLabel('Employee')"
        if status:
            query += f".has('status', '{status}')"
        if domain:
            query += f".where(out('BELONGS_TO_DOMAIN').has('name', '{domain}'))"
        if certs:
            for cert in certs:
                query += f".where(out('HAS_CERTIFICATION').has('name', '{cert}'))"
        if skills:
            for skill in skills:
                query += f".where(out('HAS_SKILL').has('name', '{skill}'))"
                
        query += ".id()"
        res = self.execute_gremlin(query)
        return [self._parse_id(eid) for eid in res]
