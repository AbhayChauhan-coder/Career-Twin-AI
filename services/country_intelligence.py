from __future__ import annotations

from dataclasses import dataclass
from typing import Any


SUPPORTED_COUNTRIES = ["India", "Germany", "USA", "Canada", "Australia"]


CAREER_CATEGORY_KEYWORDS = {
    "AI": ["ai", "machine learning", "ml engineer", "deep learning", "llm"],
    "Data": ["data", "analyst", "scientist", "analytics"],
    "Cybersecurity": ["cyber", "security"],
    "Cloud": ["cloud", "devops", "sre"],
    "Software": ["developer", "software", "backend", "frontend", "full stack", "mobile"],
    "Product": ["product manager", "ai product"],
    "Design": ["ux", "designer"],
}


COUNTRY_MARKET_DATA = {
    "India": {
        "currency": "₹",
        "salary_suffix": "LPA",
        "visa_difficulty": "Low",
        "market_growth": "Very High",
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
        "currency": "€",
        "salary_suffix": "k",
        "visa_difficulty": "Medium",
        "market_growth": "High",
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
        "currency": "$",
        "salary_suffix": "k",
        "visa_difficulty": "High",
        "market_growth": "Very High",
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
        "currency": "C$",
        "salary_suffix": "k",
        "visa_difficulty": "Medium",
        "market_growth": "High",
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
        "currency": "A$",
        "salary_suffix": "k",
        "visa_difficulty": "Medium",
        "market_growth": "High",
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


@dataclass
class CountryCareerIntelligence:
    country: str
    career: str
    demand_level: str
    entry_salary: str
    mid_level_salary: str
    senior_salary: str
    most_required_skills: list[str]
    visa_difficulty: str
    market_growth: str
    insights: list[str]


def get_country_career_intelligence(
    career_name: str,
    country: str,
    career_definition: dict[str, Any],
) -> CountryCareerIntelligence:
    selected_country = country if country in COUNTRY_MARKET_DATA else "India"
    country_data = COUNTRY_MARKET_DATA[selected_country]
    category = categorize_career(career_name)
    market = country_data["categories"].get(category, country_data["categories"]["Software"])
    required_skills = career_definition.get("required_skills", [])
    most_required_skills = (required_skills[:4] + country_data["country_skills"])[:7]

    intelligence = CountryCareerIntelligence(
        country=selected_country,
        career=career_name,
        demand_level=market["demand"],
        entry_salary=format_salary(country_data, market["entry"]),
        mid_level_salary=format_salary(country_data, market["mid"]),
        senior_salary=format_salary(country_data, market["senior"]),
        most_required_skills=most_required_skills,
        visa_difficulty=country_data["visa_difficulty"],
        market_growth=country_data["market_growth"],
        insights=[],
    )
    intelligence.insights = build_country_insights(intelligence, category)
    return intelligence


def categorize_career(career_name: str) -> str:
    normalized = career_name.casefold()
    for category, keywords in CAREER_CATEGORY_KEYWORDS.items():
        if any(keyword in normalized for keyword in keywords):
            return category
    return "Software"


def format_salary(country_data: dict[str, Any], salary_range: str) -> str:
    if "-" in salary_range:
        low, high = salary_range.split("-", 1)
        suffix = country_data["salary_suffix"]
        return f"{country_data['currency']}{low}{suffix} - {country_data['currency']}{high}{suffix}"
    return f"{country_data['currency']}{salary_range}{country_data['salary_suffix']}"


def build_country_insights(intelligence: CountryCareerIntelligence, category: str) -> list[str]:
    insights = [
        f"{intelligence.career} in {intelligence.country} has {intelligence.demand_level.lower()} demand with {intelligence.market_growth.lower()} market growth.",
        f"Focus on {', '.join(intelligence.most_required_skills[:3])} first to improve local market fit.",
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
