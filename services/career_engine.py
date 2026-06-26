from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from models.user import UserProfile


CAREERS_PATH = Path(__file__).resolve().parent.parent / "data" / "careers.json"


def load_careers() -> dict[str, dict[str, Any]]:
    with CAREERS_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def normalize_skill(skill: str) -> str:
    return skill.strip().casefold()


def split_multiline_or_csv(value: str) -> list[str]:
    if not value:
        return []
    normalized = value.replace("\n", ",")
    return [item.strip() for item in normalized.split(",") if item.strip()]


def calculate_readiness(profile: UserProfile, career: dict[str, Any]) -> dict[str, Any]:
    required = career.get("required_skills", [])
    user_skills = {normalize_skill(skill) for skill in profile.skills}
    matched = [skill for skill in required if normalize_skill(skill) in user_skills]
    missing = [skill for skill in required if normalize_skill(skill) not in user_skills]

    skill_score = (len(matched) / len(required)) * 70 if required else 0
    project_score = min(profile.project_count, 3) / 3 * 10
    internship_score = min(profile.internship_count, 2) / 2 * 10
    certification_score = min(profile.certification_count, 2) / 2 * 5
    study_score = min(profile.weekly_study_hours, 20) / 20 * 5

    score = round(skill_score + project_score + internship_score + certification_score + study_score)
    return {
        "score": max(0, min(score, 100)),
        "matched_skills": matched,
        "missing_skills": missing,
        "required_skills": required,
    }


def calculate_success_probability(profile: UserProfile, readiness_score: int, missing_count: int) -> int:
    probability = readiness_score

    if profile.weekly_study_hours >= 12:
        probability += 8
    elif profile.weekly_study_hours < 5:
        probability -= 8

    if profile.gpa >= 8:
        probability += 5
    elif profile.gpa < 6:
        probability -= 5

    if profile.project_count >= 2:
        probability += 6
    if profile.internship_count >= 1:
        probability += 6
    if missing_count >= 5:
        probability -= 8

    return max(5, min(round(probability), 98))


def career_matches(profile: UserProfile, careers: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    matches = []
    for name, career in careers.items():
        readiness = calculate_readiness(profile, career)
        probability = calculate_success_probability(
            profile,
            readiness["score"],
            len(readiness["missing_skills"]),
        )
        matches.append(
            {
                "career": name,
                "score": readiness["score"],
                "probability": probability,
                "missing_skills": readiness["missing_skills"],
                "matched_skills": readiness["matched_skills"],
            }
        )
    return sorted(matches, key=lambda item: (item["probability"], item["score"]), reverse=True)


def fallback_roadmap(
    missing_skills: list[str],
    career_goal: str,
    country: str = "",
    weekly_study_hours: int = 0,
) -> list[dict[str, Any]]:
    focus = adaptive_learning_sequence(career_goal, missing_skills, country)
    difficulty = "light" if weekly_study_hours < 6 else "balanced" if weekly_study_hours < 14 else "intensive"

    return [
        {
            "month": f"Month {index + 1}",
            "focus": skill,
            "tasks": [
                monthly_learning_task(skill, difficulty),
                monthly_project_task(skill, career_goal, country),
            ],
            "outcome": f"Create a portfolio artifact proving {skill} for {career_goal}.",
        }
        for index, skill in enumerate(focus[:6])
    ]


def fallback_future(profile: UserProfile, readiness_score: int) -> list[dict[str, str]]:
    if readiness_score >= 75:
        one_year = "Strong internship or junior role candidate"
        three_year = profile.career_goal or "Specialist contributor"
        five_year = f"Senior {profile.career_goal}" if profile.career_goal else "Senior specialist"
    elif readiness_score >= 45:
        one_year = "Portfolio-ready learner with early applications"
        three_year = f"Junior {profile.career_goal}" if profile.career_goal else "Junior professional"
        five_year = profile.career_goal or "Mid-level professional"
    else:
        one_year = "Foundation-building learner"
        three_year = "Entry-level candidate with targeted projects"
        five_year = f"Growing {profile.career_goal}" if profile.career_goal else "Growing professional"

    return [
        {"label": "Current", "title": profile.current_year or "Starting point", "detail": "Your present profile and skill base."},
        {"label": "1 Year", "title": one_year, "detail": "Depends heavily on weekly consistency and portfolio completion."},
        {"label": "3 Years", "title": three_year, "detail": "Likely path if missing skills are closed and real projects are shipped."},
        {"label": "5 Years", "title": five_year, "detail": "A realistic upside path with internships, networking, and applied experience."},
    ]


def fallback_action_plan(
    missing_skills: list[str],
    career_goal: str = "",
    weekly_study_hours: int = 0,
    country: str = "",
) -> list[dict[str, str]]:
    focus = adaptive_learning_sequence(career_goal, missing_skills, country)
    weekly_focus = []
    for skill in focus[:3]:
        weekly_focus.append(f"Learn the core concepts of {skill}.")
        weekly_focus.append(f"Build a small {skill} exercise for your portfolio.")
    weekly_focus.extend(
        [
            "Improve resume bullets with measurable project outcomes.",
            f"Prepare interview answers for {career_goal or 'your target role'}.",
        ]
    )

    return [
        {"week": f"Week {index + 1}", "task": focus}
        for index, focus in enumerate(weekly_focus[:8])
    ]


def adaptive_learning_sequence(career_goal: str, missing_skills: list[str], country: str = "") -> list[str]:
    goal = career_goal.casefold()
    if "data analyst" in goal or ("analyst" in goal and "business" not in goal):
        base = ["Advanced Excel", "SQL", "Power BI", "Statistics", "Python", "Portfolio Dashboard"]
    elif "data scientist" in goal:
        base = ["Statistics", "Python", "Machine Learning", "SQL", "Data Visualization", "Portfolio Case Study"]
    elif "ai" in goal or "machine learning" in goal or "ml engineer" in goal:
        base = ["Python Advanced", "Machine Learning", "Deep Learning", "Computer Vision or NLP", "Docker", "Deployment"]
    elif "backend" in goal:
        base = ["Python", "FastAPI", "Databases", "Docker", "Cloud", "System Design"]
    elif "frontend" in goal:
        base = ["JavaScript", "React", "TypeScript", "Testing", "Design Systems", "Deployment"]
    elif "cyber" in goal or "security" in goal:
        base = ["Networking", "Linux", "Security Fundamentals", "SIEM", "Incident Response", "Cloud Security"]
    elif "cloud" in goal or "devops" in goal:
        base = ["Linux", "Docker", "Kubernetes", "CI/CD", "Terraform", "Monitoring"]
    else:
        base = ["Core Role Skills", "Portfolio Project", "Tools Practice", "Deployment", "Interview Prep", "Applications"]

    sequence = []
    for skill in missing_skills + base:
        if skill and skill not in sequence:
            sequence.append(skill)
    if country == "Germany" and "German B1" not in sequence:
        sequence.append("German B1")
    while len(sequence) < 6:
        filler = f"{career_goal or 'Career'} Portfolio"
        if filler not in sequence:
            sequence.append(filler)
        else:
            sequence.append(f"Interview Practice {len(sequence) + 1}")
    return sequence[:6]


def monthly_learning_task(skill: str, difficulty: str) -> str:
    if difficulty == "light":
        return f"Study {skill} for 3 focused sessions each week."
    if difficulty == "intensive":
        return f"Complete an advanced {skill} module and document key notes."
    return f"Complete a structured learning path for {skill}."


def monthly_project_task(skill: str, career_goal: str, country: str) -> str:
    country_context = f" for {country}" if country else ""
    return f"Apply {skill} in a {career_goal or 'career'} project{country_context}."
