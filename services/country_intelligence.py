from __future__ import annotations

from dataclasses import dataclass
from typing import Any


SUPPORTED_COUNTRIES = [
    "India",
    "Germany",
    "USA",
    "Canada",
    "Australia",
    "United Kingdom",
    "Singapore",
    "UAE",
    "Japan",
    "France",
    "Netherlands",
]


CAREER_CATEGORY_KEYWORDS = {
    "AI": ["ai", "machine learning", "ml engineer", "deep learning", "llm"],
    "Data": ["data", "analyst", "scientist", "analytics"],
    "Cybersecurity": ["cyber", "security"],
    "Cloud": ["cloud", "devops", "sre"],
    "Software": ["developer", "software", "backend", "frontend", "full stack", "mobile"],
    "Product": ["product manager", "ai product"],
    "Design": ["ux", "designer"],
    "Finance": ["finance", "accounting", "banking", "investment", "valuation"],
    "Marketing": ["marketing", "seo", "content", "brand", "ads", "campaign"],
    "Law": ["law", "lawyer", "legal", "compliance", "contract"],
    "Healthcare": ["health", "medical", "nursing", "pharmacy", "clinical", "public health"],
    "Education": ["teacher", "teaching", "education", "curriculum"],
    "Engineering": ["mechanical", "civil", "electrical", "electronics", "architecture", "agriculture"],
    "Government": ["government", "civil services", "policy", "public administration"],
}


COUNTRY_MARKET_DATA = {
    "India": {
        "currency": "INR",
        "salary_suffix": "LPA",
        "visa_difficulty": "Low",
        "market_growth": "Very High",
        "remote_jobs": "High",
        "top_hiring_companies": ["TCS", "Infosys", "Wipro", "Accenture", "Fractal", "Razorpay"],
        "interview_process": ["Online assessment", "Technical interview", "Managerial round", "HR round"],
        "future_demand": "Very high over the next 5-10 years as AI, cloud, and digital transformation hiring expands.",
        "certifications": ["AWS Cloud Practitioner", "Google Data Analytics", "Microsoft Azure Fundamentals", "NPTEL / IIT role courses"],
        "programming_languages": ["Python", "Java", "SQL", "JavaScript"],
        "frameworks": ["FastAPI", "React", "Spring Boot", "TensorFlow"],
        "country_skills": ["Cloud Deployment", "DSA", "System Design"],
        "categories": {
            "AI": {"demand": "Very High", "entry": "6-10", "mid": "14-25", "senior": "30-55"},
            "Data": {"demand": "High", "entry": "5-9", "mid": "12-22", "senior": "25-45"},
            "Cybersecurity": {"demand": "High", "entry": "5-8", "mid": "12-22", "senior": "25-42"},
            "Cloud": {"demand": "Very High", "entry": "6-10", "mid": "15-28", "senior": "32-60"},
            "Software": {"demand": "High", "entry": "4-8", "mid": "12-24", "senior": "28-55"},
            "Product": {"demand": "High", "entry": "8-14", "mid": "20-35", "senior": "45-80"},
            "Design": {"demand": "Medium", "entry": "4-7", "mid": "10-18", "senior": "22-38"},
        },
    },
    "Germany": {
        "currency": "EUR",
        "salary_suffix": "k",
        "visa_difficulty": "Medium",
        "market_growth": "High",
        "remote_jobs": "Medium",
        "top_hiring_companies": ["SAP", "Siemens", "Bosch", "BMW", "Zalando", "Celonis"],
        "interview_process": ["Recruiter screen", "Technical interview", "Practical task", "Team fit interview"],
        "future_demand": "High future demand, especially for AI, cloud, cybersecurity, and industrial software roles.",
        "certifications": ["AWS Solutions Architect", "Azure AI Engineer", "Google Professional ML Engineer", "German B1"],
        "programming_languages": ["Python", "Java", "SQL", "TypeScript"],
        "frameworks": ["FastAPI", "Spring Boot", "React", "Docker"],
        "country_skills": ["German B1", "EU Work Culture", "Cloud Basics"],
        "categories": {
            "AI": {"demand": "Very High", "entry": "55-65", "mid": "70-90", "senior": "95-125"},
            "Data": {"demand": "High", "entry": "50-62", "mid": "65-85", "senior": "90-115"},
            "Cybersecurity": {"demand": "Very High", "entry": "52-65", "mid": "70-92", "senior": "95-130"},
            "Cloud": {"demand": "Very High", "entry": "55-68", "mid": "75-95", "senior": "100-135"},
            "Software": {"demand": "High", "entry": "50-62", "mid": "68-88", "senior": "90-120"},
            "Product": {"demand": "Medium", "entry": "55-70", "mid": "78-100", "senior": "105-140"},
            "Design": {"demand": "Medium", "entry": "42-55", "mid": "58-75", "senior": "78-100"},
        },
    },
    "USA": {
        "currency": "USD",
        "salary_suffix": "k",
        "visa_difficulty": "High",
        "market_growth": "Very High",
        "remote_jobs": "Very High",
        "top_hiring_companies": ["Google", "Microsoft", "Amazon", "Meta", "NVIDIA", "OpenAI"],
        "interview_process": ["Recruiter screen", "Coding / technical rounds", "System design", "Behavioral interview"],
        "future_demand": "Very high future demand for AI, platform engineering, cybersecurity, data, and cloud roles.",
        "certifications": ["AWS Solutions Architect", "Google Professional ML Engineer", "CKA", "Security+"],
        "programming_languages": ["Python", "Java", "Go", "TypeScript"],
        "frameworks": ["React", "FastAPI", "Kubernetes", "TensorFlow"],
        "country_skills": ["Cloud Scale", "System Design", "Interview Readiness"],
        "categories": {
            "AI": {"demand": "Very High", "entry": "105-140", "mid": "150-210", "senior": "220-320"},
            "Data": {"demand": "High", "entry": "85-115", "mid": "120-165", "senior": "175-240"},
            "Cybersecurity": {"demand": "Very High", "entry": "90-120", "mid": "125-175", "senior": "185-260"},
            "Cloud": {"demand": "Very High", "entry": "95-130", "mid": "135-190", "senior": "200-285"},
            "Software": {"demand": "High", "entry": "90-125", "mid": "130-185", "senior": "190-280"},
            "Product": {"demand": "High", "entry": "105-140", "mid": "150-210", "senior": "220-330"},
            "Design": {"demand": "Medium", "entry": "75-105", "mid": "110-150", "senior": "155-220"},
        },
    },
    "Canada": {
        "currency": "CAD",
        "salary_suffix": "k",
        "visa_difficulty": "Medium",
        "market_growth": "High",
        "remote_jobs": "High",
        "top_hiring_companies": ["Shopify", "RBC", "TD", "Microsoft Canada", "Amazon Canada", "Cohere"],
        "interview_process": ["Recruiter screen", "Technical round", "Project discussion", "Behavioral interview"],
        "future_demand": "High future demand in AI, fintech, cloud, cybersecurity, and analytics.",
        "certifications": ["AWS Cloud Practitioner", "Azure Fundamentals", "Google Data Analytics", "Security+"],
        "programming_languages": ["Python", "Java", "SQL", "JavaScript"],
        "frameworks": ["React", "FastAPI", "Django", "Docker"],
        "country_skills": ["Cloud Basics", "Communication", "Portfolio Projects"],
        "categories": {
            "AI": {"demand": "High", "entry": "75-95", "mid": "100-135", "senior": "140-190"},
            "Data": {"demand": "High", "entry": "65-85", "mid": "90-120", "senior": "125-165"},
            "Cybersecurity": {"demand": "High", "entry": "70-90", "mid": "95-130", "senior": "135-180"},
            "Cloud": {"demand": "High", "entry": "75-98", "mid": "105-140", "senior": "145-195"},
            "Software": {"demand": "High", "entry": "70-92", "mid": "95-130", "senior": "135-185"},
            "Product": {"demand": "Medium", "entry": "80-105", "mid": "110-150", "senior": "155-210"},
            "Design": {"demand": "Medium", "entry": "58-78", "mid": "82-110", "senior": "115-150"},
        },
    },
    "Australia": {
        "currency": "AUD",
        "salary_suffix": "k",
        "visa_difficulty": "Medium",
        "market_growth": "High",
        "remote_jobs": "High",
        "top_hiring_companies": ["Atlassian", "Canva", "Telstra", "Commonwealth Bank", "REA Group", "Xero"],
        "interview_process": ["Recruiter screen", "Technical interview", "Case/project round", "Culture interview"],
        "future_demand": "High future demand, led by cloud, cybersecurity, data, AI adoption, and product engineering.",
        "certifications": ["AWS Solutions Architect", "Azure Administrator", "Google Data Analytics", "Security+"],
        "programming_languages": ["Python", "JavaScript", "Java", "SQL"],
        "frameworks": ["React", "Node.js", "FastAPI", "Docker"],
        "country_skills": ["Cloud Platforms", "Communication", "Local Market Projects"],
        "categories": {
            "AI": {"demand": "High", "entry": "85-110", "mid": "120-155", "senior": "165-220"},
            "Data": {"demand": "High", "entry": "75-95", "mid": "105-135", "senior": "145-190"},
            "Cybersecurity": {"demand": "Very High", "entry": "85-110", "mid": "120-160", "senior": "170-230"},
            "Cloud": {"demand": "Very High", "entry": "90-115", "mid": "125-165", "senior": "175-240"},
            "Software": {"demand": "High", "entry": "75-100", "mid": "105-145", "senior": "150-210"},
            "Product": {"demand": "Medium", "entry": "95-120", "mid": "130-170", "senior": "180-240"},
            "Design": {"demand": "Medium", "entry": "70-90", "mid": "95-125", "senior": "130-170"},
        },
    },
}


DEFAULT_CATEGORY_MARKETS = {
    "Finance": {"demand": "High", "entry": "45-65", "mid": "70-105", "senior": "115-170"},
    "Marketing": {"demand": "High", "entry": "40-58", "mid": "65-95", "senior": "105-150"},
    "Law": {"demand": "Medium", "entry": "45-70", "mid": "75-120", "senior": "130-220"},
    "Healthcare": {"demand": "High", "entry": "42-62", "mid": "70-105", "senior": "115-180"},
    "Education": {"demand": "Medium", "entry": "35-52", "mid": "55-82", "senior": "90-135"},
    "Engineering": {"demand": "High", "entry": "45-65", "mid": "70-105", "senior": "115-170"},
    "Government": {"demand": "Medium", "entry": "35-55", "mid": "60-95", "senior": "100-160"},
    "General": {"demand": "Medium", "entry": "38-58", "mid": "62-92", "senior": "100-150"},
}


ADDITIONAL_COUNTRY_DATA = {
    "United Kingdom": {
        "currency": "GBP",
        "salary_suffix": "k",
        "visa_difficulty": "Medium",
        "market_growth": "High",
        "remote_jobs": "High",
        "cost_of_living": "High",
        "language_requirements": ["English professional fluency"],
        "top_hiring_companies": ["BBC", "NHS", "Barclays", "Deloitte UK", "Google UK", "Rolls-Royce"],
        "interview_process": ["Recruiter screen", "Competency interview", "Role task or case", "Panel interview"],
        "future_demand": "Strong demand across AI, healthcare, finance, public services, education, and creative technology.",
        "certifications": ["Role-specific UK certificate", "Google Project Management", "AWS Cloud Practitioner", "CIPD for HR"],
        "programming_languages": ["Python", "SQL", "JavaScript", "R"],
        "frameworks": ["React", "Django", "Power BI", "Figma"],
        "country_skills": ["English Communication", "UK Work Culture", "Portfolio Evidence"],
        "categories": {
            "AI": {"demand": "Very High", "entry": "45-60", "mid": "65-90", "senior": "95-140"},
            "Data": {"demand": "High", "entry": "38-52", "mid": "58-78", "senior": "85-120"},
            "Software": {"demand": "High", "entry": "40-55", "mid": "60-85", "senior": "90-135"},
            "Product": {"demand": "High", "entry": "48-65", "mid": "75-105", "senior": "115-170"},
            "Design": {"demand": "Medium", "entry": "35-48", "mid": "55-75", "senior": "82-115"},
            **DEFAULT_CATEGORY_MARKETS,
        },
    },
    "Singapore": {
        "currency": "SGD",
        "salary_suffix": "k",
        "visa_difficulty": "Medium",
        "market_growth": "Very High",
        "remote_jobs": "Medium",
        "cost_of_living": "Very High",
        "language_requirements": ["English professional fluency"],
        "top_hiring_companies": ["Grab", "DBS", "Shopee", "GovTech", "Sea Group", "Accenture"],
        "interview_process": ["Recruiter screen", "Technical or case round", "Business round", "Leadership interview"],
        "future_demand": "Very strong demand in finance, AI, cybersecurity, logistics, healthcare, and regional business roles.",
        "certifications": ["AWS Solutions Architect", "Google Data Analytics", "CFA Level 1", "Project Management"],
        "programming_languages": ["Python", "SQL", "Java", "JavaScript"],
        "frameworks": ["React", "Spring Boot", "Power BI", "Docker"],
        "country_skills": ["Regional Business Context", "English Communication", "Cross-cultural Collaboration"],
        "categories": {
            "AI": {"demand": "Very High", "entry": "70-95", "mid": "105-150", "senior": "165-240"},
            "Data": {"demand": "High", "entry": "60-82", "mid": "90-125", "senior": "135-190"},
            "Software": {"demand": "High", "entry": "65-90", "mid": "95-140", "senior": "150-220"},
            "Product": {"demand": "High", "entry": "80-110", "mid": "125-175", "senior": "190-280"},
            "Design": {"demand": "Medium", "entry": "55-75", "mid": "82-115", "senior": "125-175"},
            **DEFAULT_CATEGORY_MARKETS,
        },
    },
    "UAE": {
        "currency": "AED",
        "salary_suffix": "k",
        "visa_difficulty": "Medium",
        "market_growth": "Very High",
        "remote_jobs": "Medium",
        "cost_of_living": "High",
        "language_requirements": ["English professional fluency", "Arabic helpful for public-facing roles"],
        "top_hiring_companies": ["Emirates", "Etisalat", "Careem", "ADNOC", "PwC Middle East", "Dubai Government"],
        "interview_process": ["Recruiter screen", "Manager interview", "Case or portfolio round", "HR and offer discussion"],
        "future_demand": "High demand in finance, tourism, construction, AI, cybersecurity, healthcare, and government digital services.",
        "certifications": ["PMP", "AWS Cloud Practitioner", "CFA Level 1", "Google Ads"],
        "programming_languages": ["Python", "SQL", "JavaScript", "Java"],
        "frameworks": ["Power BI", "React", "Django", "Figma"],
        "country_skills": ["Business Communication", "Gulf Market Awareness", "Client Management"],
        "categories": {
            "AI": {"demand": "Very High", "entry": "150-220", "mid": "240-360", "senior": "400-650"},
            "Data": {"demand": "High", "entry": "120-180", "mid": "200-300", "senior": "330-520"},
            "Software": {"demand": "High", "entry": "120-190", "mid": "210-320", "senior": "350-560"},
            "Product": {"demand": "High", "entry": "160-240", "mid": "270-420", "senior": "460-720"},
            "Design": {"demand": "Medium", "entry": "100-150", "mid": "170-260", "senior": "280-430"},
            **DEFAULT_CATEGORY_MARKETS,
        },
    },
    "Japan": {
        "currency": "JPY",
        "salary_suffix": "m",
        "visa_difficulty": "Medium",
        "market_growth": "High",
        "remote_jobs": "Medium",
        "cost_of_living": "High in Tokyo, medium elsewhere",
        "language_requirements": ["Japanese N3-N2 preferred", "English for global teams"],
        "top_hiring_companies": ["Rakuten", "Sony", "Toyota", "LINE Yahoo", "Mercari", "SoftBank"],
        "interview_process": ["Recruiter screen", "Technical or role round", "Culture fit", "Final manager interview"],
        "future_demand": "Strong future demand in robotics, software, automotive, healthcare, data, and bilingual business roles.",
        "certifications": ["JLPT N3/N2", "AWS Cloud Practitioner", "Data Analytics certificate"],
        "programming_languages": ["Python", "Java", "SQL", "JavaScript"],
        "frameworks": ["React", "Spring Boot", "Django", "TensorFlow"],
        "country_skills": ["Japanese Language", "Process Discipline", "Documentation"],
        "categories": {
            "AI": {"demand": "High", "entry": "5-7", "mid": "8-12", "senior": "13-20"},
            "Data": {"demand": "High", "entry": "4-6", "mid": "7-10", "senior": "11-16"},
            "Software": {"demand": "High", "entry": "4-7", "mid": "7-11", "senior": "12-18"},
            "Product": {"demand": "Medium", "entry": "6-8", "mid": "9-14", "senior": "15-22"},
            "Design": {"demand": "Medium", "entry": "4-6", "mid": "7-10", "senior": "11-15"},
            **DEFAULT_CATEGORY_MARKETS,
        },
    },
    "France": {
        "currency": "EUR",
        "salary_suffix": "k",
        "visa_difficulty": "Medium",
        "market_growth": "High",
        "remote_jobs": "Medium",
        "cost_of_living": "High in Paris, medium elsewhere",
        "language_requirements": ["French B1-B2 preferred", "English for international teams"],
        "top_hiring_companies": ["Dassault Systemes", "Capgemini", "L'Oreal", "BNP Paribas", "Airbus", "Mistral AI"],
        "interview_process": ["Recruiter screen", "Role interview", "Case or technical task", "Team fit interview"],
        "future_demand": "High demand in AI, aerospace, luxury, finance, healthcare, public tech, and design.",
        "certifications": ["French B1", "AWS Cloud Practitioner", "Google Data Analytics", "Role-specific certificate"],
        "programming_languages": ["Python", "SQL", "Java", "JavaScript"],
        "frameworks": ["React", "Django", "Docker", "Power BI"],
        "country_skills": ["French Language", "EU Work Culture", "Portfolio Evidence"],
        "categories": {
            "AI": {"demand": "Very High", "entry": "42-55", "mid": "60-82", "senior": "88-125"},
            "Data": {"demand": "High", "entry": "38-50", "mid": "55-75", "senior": "80-110"},
            "Software": {"demand": "High", "entry": "38-52", "mid": "58-80", "senior": "85-120"},
            "Product": {"demand": "Medium", "entry": "45-60", "mid": "68-95", "senior": "105-145"},
            "Design": {"demand": "Medium", "entry": "34-46", "mid": "50-68", "senior": "75-100"},
            **DEFAULT_CATEGORY_MARKETS,
        },
    },
    "Netherlands": {
        "currency": "EUR",
        "salary_suffix": "k",
        "visa_difficulty": "Medium",
        "market_growth": "High",
        "remote_jobs": "High",
        "cost_of_living": "High in Amsterdam, medium-high elsewhere",
        "language_requirements": ["English professional fluency", "Dutch helpful for public-facing roles"],
        "top_hiring_companies": ["ASML", "Booking.com", "Philips", "Adyen", "ING", "TomTom"],
        "interview_process": ["Recruiter screen", "Role task", "Team interview", "Culture interview"],
        "future_demand": "High demand in semiconductors, AI, data, logistics, finance, design, and sustainability careers.",
        "certifications": ["AWS Solutions Architect", "Scrum.org PSM", "Dutch A2 helpful", "Google Data Analytics"],
        "programming_languages": ["Python", "SQL", "Java", "TypeScript"],
        "frameworks": ["React", "Django", "Docker", "Kubernetes"],
        "country_skills": ["English Communication", "EU Collaboration", "Portfolio Evidence"],
        "categories": {
            "AI": {"demand": "Very High", "entry": "50-65", "mid": "72-95", "senior": "105-145"},
            "Data": {"demand": "High", "entry": "45-58", "mid": "65-85", "senior": "92-125"},
            "Software": {"demand": "High", "entry": "48-62", "mid": "68-90", "senior": "98-140"},
            "Product": {"demand": "High", "entry": "58-75", "mid": "85-115", "senior": "125-175"},
            "Design": {"demand": "Medium", "entry": "42-55", "mid": "60-78", "senior": "85-115"},
            **DEFAULT_CATEGORY_MARKETS,
        },
    },
}


COUNTRY_MARKET_DATA.update(ADDITIONAL_COUNTRY_DATA)
COUNTRY_CATEGORY_DEFAULTS = {
    "India": {
        "Finance": {"demand": "High", "entry": "4-8", "mid": "10-18", "senior": "22-45"},
        "Marketing": {"demand": "High", "entry": "3-6", "mid": "8-16", "senior": "18-35"},
        "Law": {"demand": "Medium", "entry": "4-8", "mid": "10-22", "senior": "25-60"},
        "Healthcare": {"demand": "High", "entry": "3-7", "mid": "8-18", "senior": "20-45"},
        "Education": {"demand": "Medium", "entry": "2-5", "mid": "6-12", "senior": "15-30"},
        "Engineering": {"demand": "High", "entry": "4-8", "mid": "10-20", "senior": "24-45"},
        "Government": {"demand": "Medium", "entry": "4-8", "mid": "9-16", "senior": "18-35"},
        "General": {"demand": "Medium", "entry": "3-6", "mid": "8-15", "senior": "18-32"},
    },
    "Japan": {
        "Finance": {"demand": "High", "entry": "4-6", "mid": "7-11", "senior": "12-18"},
        "Marketing": {"demand": "Medium", "entry": "3-5", "mid": "6-9", "senior": "10-15"},
        "Law": {"demand": "Medium", "entry": "4-7", "mid": "8-13", "senior": "14-22"},
        "Healthcare": {"demand": "High", "entry": "4-6", "mid": "7-11", "senior": "12-18"},
        "Education": {"demand": "Medium", "entry": "3-5", "mid": "5-8", "senior": "9-13"},
        "Engineering": {"demand": "High", "entry": "4-6", "mid": "7-11", "senior": "12-18"},
        "Government": {"demand": "Medium", "entry": "3-5", "mid": "6-9", "senior": "10-14"},
        "General": {"demand": "Medium", "entry": "3-5", "mid": "6-9", "senior": "10-15"},
    },
    "UAE": {
        "Finance": {"demand": "High", "entry": "90-150", "mid": "180-300", "senior": "350-600"},
        "Marketing": {"demand": "High", "entry": "70-120", "mid": "150-240", "senior": "280-450"},
        "Law": {"demand": "Medium", "entry": "100-180", "mid": "220-380", "senior": "450-750"},
        "Healthcare": {"demand": "High", "entry": "80-140", "mid": "170-280", "senior": "320-520"},
        "Education": {"demand": "Medium", "entry": "60-110", "mid": "120-200", "senior": "230-360"},
        "Engineering": {"demand": "High", "entry": "90-150", "mid": "180-300", "senior": "350-580"},
        "Government": {"demand": "Medium", "entry": "80-140", "mid": "160-260", "senior": "300-480"},
        "General": {"demand": "Medium", "entry": "70-120", "mid": "140-230", "senior": "260-420"},
    },
}
for _country_data in COUNTRY_MARKET_DATA.values():
    _country_data.setdefault("cost_of_living", "Medium")
    _country_data.setdefault("language_requirements", ["English helpful for global roles"])
for _country_name, _country_data in COUNTRY_MARKET_DATA.items():
    _defaults = COUNTRY_CATEGORY_DEFAULTS.get(_country_name, DEFAULT_CATEGORY_MARKETS)
    _country_data["categories"] = {**_defaults, **_country_data.get("categories", {})}
    if _country_name in COUNTRY_CATEGORY_DEFAULTS:
        _country_data["categories"].update(COUNTRY_CATEGORY_DEFAULTS[_country_name])


@dataclass
class CountryCareerIntelligence:
    country: str
    career: str
    demand_level: str
    entry_salary: str
    mid_level_salary: str
    senior_salary: str
    remote_jobs: str
    top_hiring_companies: list[str]
    most_required_skills: list[str]
    most_valuable_certifications: list[str]
    most_valuable_programming_languages: list[str]
    most_valuable_frameworks: list[str]
    visa_difficulty: str
    market_growth: str
    interview_process: list[str]
    future_demand: str
    cost_of_living: str
    language_requirements: list[str]
    interview_style: str
    career_growth: str
    insights: list[str]


def get_country_career_intelligence(
    career_name: str,
    country: str,
    career_definition: dict[str, Any],
) -> CountryCareerIntelligence:
    selected_country = country if country in COUNTRY_MARKET_DATA else "India"
    country_data = COUNTRY_MARKET_DATA[selected_country]
    category = categorize_career(career_name)
    domain = career_definition.get("domain", "")
    market = country_data["categories"].get(
        category,
        country_data["categories"].get("General", country_data["categories"].get("Software")),
    )
    required_skills = career_definition.get("required_skills", [])
    most_required_skills = (required_skills[:4] + country_data["country_skills"])[:7]
    is_technology = domain == "Technology" or (not domain and category in {"AI", "Data", "Cybersecurity", "Cloud", "Software"})
    top_companies = career_definition.get("top_hiring_companies") or career_definition.get("hiring_companies") or country_data["top_hiring_companies"]
    certifications = (
        career_definition.get("certifications")
        or career_definition.get("preferred_certifications")
        or career_definition.get("recommended_certifications")
        or country_data["certifications"]
    )

    intelligence = CountryCareerIntelligence(
        country=selected_country,
        career=career_name,
        demand_level=market["demand"],
        entry_salary=format_salary(country_data, market["entry"]),
        mid_level_salary=format_salary(country_data, market["mid"]),
        senior_salary=format_salary(country_data, market["senior"]),
        remote_jobs=country_data["remote_jobs"],
        top_hiring_companies=top_companies,
        most_required_skills=most_required_skills,
        most_valuable_certifications=certifications,
        most_valuable_programming_languages=country_data["programming_languages"] if is_technology else [],
        most_valuable_frameworks=career_definition.get("frameworks", country_data["frameworks"] if is_technology else []),
        visa_difficulty=country_data["visa_difficulty"],
        market_growth=country_data["market_growth"],
        interview_process=country_data["interview_process"],
        future_demand=country_data["future_demand"],
        cost_of_living=country_data.get("cost_of_living", "Medium"),
        language_requirements=country_data.get("language_requirements", ["English helpful for global roles"]),
        interview_style=", ".join(country_data["interview_process"][:2]),
        career_growth=country_data.get("market_growth", "Medium"),
        insights=[],
    )
    intelligence.insights = build_country_insights(intelligence, category)
    return intelligence


def categorize_career(career_name: str) -> str:
    normalized = career_name.casefold()
    priority_categories = ["Finance", "Marketing", "Law", "Healthcare", "Education", "Engineering", "Government"]
    for category in priority_categories:
        if any(keyword in normalized for keyword in CAREER_CATEGORY_KEYWORDS.get(category, [])):
            return category
    for category, keywords in CAREER_CATEGORY_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return category
    try:
        from services.career_knowledge import get_career_knowledge

        domain = get_career_knowledge(career_name).get("domain", "")
        return {
            "Technology": "Software",
            "Creative": "Design",
            "Business": "Product",
        }.get(domain, domain or "General")
    except Exception:
        return "General"


def format_salary(country_data: dict[str, Any], salary_range: str) -> str:
    if "-" in salary_range:
        low, high = salary_range.split("-", 1)
        suffix = country_data["salary_suffix"]
        return f"{country_data['currency']} {low}{suffix} - {country_data['currency']} {high}{suffix}"
    return f"{country_data['currency']} {salary_range}{country_data['salary_suffix']}"


def salary_midpoint(value: str) -> int:
    import re

    numbers = [int(part) for part in re.findall(r"\d+", value)]
    if len(numbers) >= 2:
        return round(sum(numbers[:2]) / 2)
    return numbers[0] if numbers else 0


def build_country_insights(intelligence: CountryCareerIntelligence, category: str) -> list[str]:
    insights = [
        f"{intelligence.career} in {intelligence.country} has {intelligence.demand_level.lower()} demand with {intelligence.market_growth.lower()} market growth.",
        f"Remote job availability is {intelligence.remote_jobs.lower()}, so portfolio proof and communication skills affect opportunity quality.",
        f"Focus on {', '.join(intelligence.most_required_skills[:3])} first to improve local market fit.",
        f"Future demand: {intelligence.future_demand}",
    ]
    if intelligence.visa_difficulty == "High":
        insights.append("Visa difficulty is high, so strong portfolio proof and employer sponsorship readiness matter.")
    elif intelligence.visa_difficulty == "Medium":
        insights.append("Visa difficulty is manageable, but local language, documentation, and relevant experience improve outcomes.")
    else:
        insights.append("Visa difficulty is low for local candidates, so skills and portfolio quality become the main differentiators.")
    if category == "AI":
        insights.append("A deployed AI project with API, model evaluation, and clear business use case will stand out.")
    return insights
