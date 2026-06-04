import os
from flask import Flask, request, jsonify, render_template
from werkzeug.utils import secure_filename
import pdfplumber
import docx

app = Flask(__name__)

# Ensure the uploads directory exists to prevent FileNotFoundError
UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Expanded IT Job Roles Catalog
job_roles = {
    "cloud_engineer": ["python", "aws", "cloud", "linux", "sql", "terraform", "docker", "kubernetes", "devops", "azure"],
    "java_developer": ["java", "spring", "hibernate", "sql", "oop", "maven", "microservices", "rest api", "git", "junit"],
    "data_scientist": ["python", "machine learning", "statistics", "sql", "pandas", "numpy", "scikit-learn", "deep learning", "r", "tableau"],
    "frontend_developer": ["html", "css", "javascript", "react", "vue", "angular", "typescript", "tailwind", "sass", "git"],
    "backend_developer": ["python", "node.js", "express", "django", "postgresql", "mongodb", "restful api", "redis", "docker", "graphql"],
    "devops_engineer": ["linux", "bash", "docker", "kubernetes", "jenkins", "ci/cd", "ansible", "terraform", "aws", "prometheus"],
    "cybersecurity_analyst": ["wireshark", "linux", "siem", "firewall", "network security", "pentesting", "metasploit", "cryptography", "owasp", "incident response"],
    "qa_automation_engineer": ["selenium", "cucumber", "testng", "java", "python", "playwright", "automation", "api testing", "jira", "postman"]
}

def extract_text(file_path):
    text = ""
    if file_path.endswith(".pdf"):
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() or ""
    elif file_path.endswith(".docx"):
        doc = docx.Document(file_path)
        for para in doc.paragraphs:
            text += para.text + " "
    return text.lower()

# Recruiter-focused role evaluations
role_suggestions = {
    "cloud_engineer": [
        "Verify hands-on experience with multi-region AWS/Azure infrastructure deployments.",
        "Check if candidate holds active Cloud certifications (AWS Solutions Architect, Terraform Associate).",
        "Test knowledge of Infrastructure as Code (IaC) and containerization during technical screening."
    ],
    "java_developer": [
        "Assess familiarity with Spring Boot microservices and REST API design patterns.",
        "Query code testing practices (JUnit/Mockito) to verify commit quality.",
        "Verify database integration experience with SQL databases and caching layers (Redis)."
    ],
    "data_scientist": [
        "Assess candidate's knowledge of machine learning model metrics (F1-score, ROC-AUC) during technical review.",
        "Query the business impact and scale of data in prior analytical projects.",
        "Verify Python library capabilities (Pandas/NumPy) and data storytelling skills."
    ],
    "frontend_developer": [
        "Request live portfolio links or inspect Git repositories to assess code structure.",
        "Evaluate knowledge of modern state management (Redux, Context API) and UI load optimization.",
        "Check experience with responsive layouts and front-end test automation tools."
    ],
    "backend_developer": [
        "Test database design proficiency (SQL/NoSQL) and optimization capabilities.",
        "Inquire about backend API security policies (OAuth, JWT) and microservices experience.",
        "Evaluate familiarity with message brokers (Kafka/RabbitMQ) for asynchronous architecture."
    ],
    "devops_engineer": [
        "Verify pipeline automation depth using Jenkins/GitHub Actions and containerization tools.",
        "Assess experience setting up performance telemetry monitors (Prometheus, Grafana).",
        "Evaluate automated configuration setup experience (Ansible, Chef) during screening."
    ],
    "cybersecurity_analyst": [
        "Check familiarity with threat hunting frameworks and vulnerability scanners (Nessus, Wireshark).",
        "Ask candidate about experience managing compliance standards (SOC 2, ISO 27001).",
        "Verify active certifications (Security+, CEH, CISSP) during interview screening."
    ],
    "qa_automation_engineer": [
        "Evaluate framework architecture design skills (Selenium, Playwright, or Cypress).",
        "Assess integration of automation scripts into CI/CD pipelines.",
        "Quantify candidate's impact on automation test coverage and error reduction rates."
    ]
}

def analyze_structure_and_format(text, file_path):
    sections = {
        "experience": ["experience", "work history", "employment", "professional history"],
        "education": ["education", "academic", "university", "college"],
        "skills": ["skills", "technical skills", "technologies", "expertise"],
        "projects": ["projects", "personal projects", "academic projects"],
        "summary": ["summary", "objective", "profile", "professional summary"]
    }
    
    found_sections = []
    missing_sections = []
    
    for section_name, keywords in sections.items():
        if any(kw in text for kw in keywords):
            found_sections.append(section_name)
        else:
            missing_sections.append(section_name)
            
    # Calculate score weights
    file_ext = os.path.splitext(file_path)[1].lower()
    format_score = 10 if file_ext in [".pdf", ".docx"] else 5
    
    section_score = (len(found_sections) / len(sections)) * 30
    
    return {
        "found": found_sections,
        "missing": missing_sections,
        "format_score": format_score,
        "section_score": section_score
    }

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    role = request.form.get("role", "")
    use_sample = request.form.get("use_sample", "false") == "true"
    
    if use_sample:
        filename = "resume.pdf"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(file_path):
            return jsonify({"error": "Sample resume not found on server"}), 404
    else:
        # Defensive check: ensure the file exists in the request
        if "resume" not in request.files or request.files["resume"].filename == '':
            return jsonify({"error": "No resume file uploaded"}), 400
            
        file = request.files["resume"]
        filename = secure_filename(file.filename)
        if not filename:
            filename = "uploaded_resume"
            
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

    resume_text = extract_text(file_path)
    required_skills = job_roles.get(role, [])
    
    # Calculate structure and format
    structure_info = analyze_structure_and_format(resume_text, file_path)
    
    # Keyword extraction math
    matched = [skill for skill in required_skills if skill in resume_text]
    missing = [skill for skill in required_skills if skill not in matched]
    
    keyword_ratio = len(matched) / len(required_skills) if required_skills else 0
    keyword_score = keyword_ratio * 60
    
    ats_score = keyword_score + structure_info["section_score"] + structure_info["format_score"]
    status = "Eligible" if ats_score >= 60 else "Requires Review"

    # Build recommendations list
    suggestions = []
    
    # Skill gap recommendations
    if missing:
        suggestions.append(f"Candidate is missing core competencies: {', '.join(missing[:4])}. Flag this for interview verification.")
        
    # Section gap recommendations
    for m_sec in structure_info["missing"]:
        suggestions.append(f"Dedicated '{m_sec.capitalize()}' section was not detected in the document structure.")
        
    # Role-specific recommendations
    role_tips = role_suggestions.get(role, [])
    suggestions.extend(role_tips[:2]) # Take 2 role tips
    
    # General recommendations based on score
    if ats_score < 50:
        suggestions.append("Profile shows low alignment metrics. A thorough technical phone screening is strongly advised.")
    elif ats_score < 80:
        suggestions.append("Candidate demonstrates average keyword overlap. Standard technical rounds recommended.")
    else:
        suggestions.append("Candidate displays excellent keyword matching. Proceed directly to final round hiring manager review.")

    return jsonify({
        "role": role, 
        "skills_found": matched, 
        "skills_missing": missing, 
        "percentage": keyword_ratio * 100, 
        "ats_score": int(ats_score),
        "status": status,
        "suggestions": suggestions
    })

if __name__ == "__main__":
    app.run(debug=True)
