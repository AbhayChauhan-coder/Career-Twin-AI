from __future__ import annotations

from dataclasses import dataclass

from models.user import UserProfile
from services.career_engine import load_careers
from services.career_knowledge import recommend_careers_for_profile
from services.resume_parser import parse_resume_text


@dataclass(frozen=True)
class ValidationResume:
    name: str
    text: str
    expected_terms: tuple[str, ...]


VALIDATION_RESUMES = [
    ValidationResume("Software Engineer", "Current Role: Software Engineer II\nBTech Computer Science\nSkills: Python Java Docker System Design Git\nExperience: Software Engineer at product company 3 years", ("Software", "Backend", "Engineer")),
    ValidationResume("Data Scientist", "Designation: Data Scientist\nMSc Statistics\nSkills: Python SQL Machine Learning Statistics Data Visualization\nExperience: Data Scientist 4 years", ("Data Scientist", "Machine Learning", "Analytics")),
    ValidationResume("AI Engineer", "Job Title: AI Engineer\nSkills: Python Deep Learning MLOps TensorFlow Docker\nExperience: AI Engineer 3 years", ("AI Engineer", "Machine Learning", "MLOps")),
    ValidationResume("Chartered Accountant", "Current Designation: Senior Audit Associate\nChartered Accountant with 4 years at Deloitte\nSkills: Accounting Financial Reporting Audit Taxation Risk Analysis Excel\nCertifications: CA", ("Audit Manager", "Finance Manager", "Finance Controller", "Corporate Finance")),
    ValidationResume("Finance Manager", "Role: Finance Manager\nMBA Finance\nSkills: Financial Modeling Budgeting Accounting Risk Analysis Excel\nExperience: Finance Manager 7 years", ("Finance Manager", "Finance Controller", "Finance Director")),
    ValidationResume("HR Manager", "Position: HR Manager\nMBA HR\nSkills: Recruitment HR Analytics Employee Relations Policy Writing\nExperience: HR Manager 6 years", ("HR", "People", "Talent")),
    ValidationResume("Marketing Manager", "Current Role: Marketing Manager\nSkills: SEO Brand Strategy Campaign Analytics Content Strategy Google Ads\nExperience: Marketing Manager 5 years", ("Marketing", "Brand", "Growth")),
    ValidationResume("Sales Executive", "Designation: Sales Executive\nSkills: CRM Negotiation Customer Relationship Sales Pipeline\nExperience: Sales Executive 2 years", ("Sales", "Account", "Business Development")),
    ValidationResume("Civil Engineer", "Role: Civil Engineer\nBTech Civil Engineering\nSkills: AutoCAD STAAD Pro Construction Management Site Planning\nExperience: Civil Engineer 4 years", ("Civil", "Construction", "Structural")),
    ValidationResume("Mechanical Engineer", "Current Role: Mechanical Engineer\nSkills: CAD SolidWorks Manufacturing Quality Control MATLAB\nExperience: Mechanical Engineer 4 years", ("Mechanical", "Manufacturing", "Quality")),
    ValidationResume("Electrical Engineer", "Designation: Electrical Engineer\nSkills: Circuit Design Power Systems MATLAB Safety\nExperience: Electrical Engineer 3 years", ("Electrical", "Power", "Instrumentation")),
    ValidationResume("Teacher", "Current Designation: Teacher\nBEd English\nSkills: Lesson Planning Curriculum Design Assessment Classroom Management\nExperience: Teacher 5 years", ("Teacher", "Academic", "Curriculum")),
    ValidationResume("Professor", "Position: Assistant Professor\nPhD Physics\nSkills: Research Methods Academic Writing Teaching Curriculum Design\nExperience: Assistant Professor 6 years", ("Professor", "Research", "Academic")),
    ValidationResume("Doctor", "Current Role: Medical Officer\nMBBS\nSkills: Patient Care Diagnosis Clinical Decision Making Medical Records\nExperience: Medical Officer 4 years", ("Medical Officer", "Doctor", "Healthcare")),
    ValidationResume("Nurse", "Designation: Nurse\nBSc Nursing\nSkills: Patient Care Clinical Documentation Medication Safety\nExperience: Nurse 3 years", ("Nurse", "Clinical", "Healthcare")),
    ValidationResume("Lawyer", "Current Designation: Legal Associate\nLLB Corporate Law\nSkills: Legal Research Contract Drafting Compliance Legal Writing\nExperience: Legal Associate 3 years", ("Legal", "Lawyer", "Counsel")),
    ValidationResume("Architect", "Role: Architect\nBArch\nSkills: AutoCAD Revit Building Codes Sustainable Design\nExperience: Architect 4 years", ("Architect", "BIM", "Design")),
    ValidationResume("Graphic Designer", "Current Role: Graphic Designer\nSkills: Figma Canva Adobe Photoshop Visual Design Portfolio Development\nExperience: Graphic Designer 3 years", ("Designer", "Creative", "Art")),
    ValidationResume("Product Manager", "Designation: Product Manager\nMBA\nSkills: Product Strategy User Research Analytics Roadmapping Stakeholder Management\nExperience: Product Manager 5 years", ("Product Manager", "Program", "Strategy")),
    ValidationResume("Business Analyst", "Current Role: Business Analyst\nSkills: Requirements Analysis Process Mapping Power BI Stakeholder Management\nExperience: Business Analyst 4 years", ("Business Analyst", "Operations", "Consultant")),
    ValidationResume("Hotel Manager", "Role: Hotel Manager\nHotel Management degree\nSkills: Guest Relations Hotel Operations Food Safety Event Planning\nExperience: Hotel Manager 5 years", ("Hotel", "Hospitality", "Restaurant")),
    ValidationResume("Supply Chain Manager", "Designation: Supply Chain Manager\nSkills: Logistics Procurement Vendor Management Operations\nExperience: Supply Chain Manager 6 years", ("Supply Chain", "Logistics", "Procurement")),
    ValidationResume("Pharmacist", "Current Role: Pharmacist\nBPharm\nSkills: Pharmacology Medication Counseling Drug Safety Patient Care\nExperience: Pharmacist 4 years", ("Pharmacist", "Pharmaceutical", "Drug Safety")),
    ValidationResume("Research Scientist", "Current Designation: Research Scientist\nPhD Biology\nSkills: Research Methods Laboratory Techniques Academic Writing Data Analysis\nExperience: Research Scientist 5 years", ("Research", "Scientist", "Biologist")),
    ValidationResume("Entrepreneur", "Role: Startup Founder\nSkills: Customer Discovery Sales Business Model Design Financial Planning Pitching\nExperience: Startup Founder 4 years", ("Founder", "Entrepreneur", "Business")),
]


def run_validation_suite() -> dict[str, object]:
    careers = load_careers()
    failures = []
    results = []
    for sample in VALIDATION_RESUMES:
        resume = parse_resume_text(sample.text, careers)
        profile = UserProfile(
            name=sample.name,
            age=None,
            degree=resume.degree,
            branch=resume.branch,
            current_year="Professional",
            gpa=0.0,
            skills=resume.skills,
            projects=resume.projects,
            certifications=resume.certifications,
            internships=resume.experience,
            career_goal=sample.name,
            target_country="India",
        )
        recommendations = recommend_careers_for_profile(profile, resume, careers, limit=5)
        names = [item.career for item in recommendations]
        joined = " ".join(names).casefold()
        passed = any(term.casefold() in joined for term in sample.expected_terms)
        if not passed:
            failures.append({"resume": sample.name, "recommendations": names, "expected": sample.expected_terms})
        results.append({"resume": sample.name, "designation": resume.current_designation, "recommendations": names, "passed": passed})
    return {
        "total": len(VALIDATION_RESUMES),
        "passed": len(VALIDATION_RESUMES) - len(failures),
        "failed": len(failures),
        "failures": failures,
        "results": results,
    }


if __name__ == "__main__":
    import json

    print(json.dumps(run_validation_suite(), indent=2))
