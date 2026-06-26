from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from models.user import UserProfile
from services.github_analyzer import GitHubAnalysis
from services.resume_parser import ResumeParseResult, build_skill_bank, detect_skills


STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "be",
    "for",
    "in",
    "of",
    "on",
    "or",
    "our",
    "the",
    "to",
    "with",
    "you",
    "your",
}


@dataclass
class ResumeMatchAnalysis:
    overall_match: int
    weighted_scores: dict[str, int]
    strengths: list[str]
    weaknesses: list[str]
    critical_missing_skills: list[str]
    important_skills: list[str]
    nice_to_have_skills: list[str]
    improvement_suggestions: list[dict[str, str]]


@dataclass
class JobDescriptionMatch:
    keyword_match: int
    semantic_match: int
    matched_keywords: list[str]
    missing_keywords: list[str]
    experience_match: int
    education_match: int
    certification_match: int
    technical_match: int
    hiring_recommendation: str
    highlighted_missing_keywords: list[str] = field(default_factory=list)


def analyze_resume_match(
    resume: ResumeParseResult,
    profile: UserProfile,
    career_definition: dict[str, Any],
    github_analysis: GitHubAnalysis | None = None,
) -> ResumeMatchAnalysis:
    required_skills = career_definition.get("required_skills", [])
    resume_skills = set(normalize(skill) for skill in resume.skills or profile.skills)
    required_skill_set = set(normalize(skill) for skill in required_skills)
    matched_required = required_skill_set & resume_skills
    missing_required = [skill for skill in required_skills if normalize(skill) not in resume_skills]

    technical = percent(len(matched_required), len(required_skill_set))
    soft = soft_skill_score(resume)
    projects = min(len(resume.structured_projects or resume.projects), 3) / 3 * 100
    experience = min(len(resume.structured_experience or resume.experience), 2) / 2 * 100
    internships = 100 if any("intern" in item.casefold() for item in resume.experience) else 0
    education = 100 if resume.degree or resume.education else 0
    certifications = min(len(resume.structured_certifications or resume.certifications), 2) / 2 * 100
    github = github_analysis.github_score if github_analysis else 0
    ats = resume.ats_readiness_score
    industry = resume.industry_readiness_score

    weighted_scores = {
        "Technical Skills": round(technical),
        "Soft Skills": round(soft),
        "Projects": round(projects),
        "Experience": round(experience),
        "Internships": round(internships),
        "Education": round(education),
        "Certifications": round(certifications),
        "GitHub": round(github),
        "ATS Compatibility": round(ats),
        "Industry Readiness": round(industry),
    }
    weights = {
        "Technical Skills": 0.22,
        "Soft Skills": 0.06,
        "Projects": 0.14,
        "Experience": 0.12,
        "Internships": 0.06,
        "Education": 0.08,
        "Certifications": 0.07,
        "GitHub": 0.05,
        "ATS Compatibility": 0.10,
        "Industry Readiness": 0.10,
    }
    overall = round(sum(weighted_scores[key] * weights[key] for key in weights))

    critical, important, nice = split_missing_skills(missing_required)
    strengths = build_strengths(weighted_scores, matched_required, required_skills)
    weaknesses = build_weaknesses(weighted_scores, missing_required)
    suggestions = build_suggestions(weighted_scores, critical, important, nice, profile.career_goal)

    return ResumeMatchAnalysis(
        overall_match=max(0, min(overall, 100)),
        weighted_scores=weighted_scores,
        strengths=strengths,
        weaknesses=weaknesses,
        critical_missing_skills=critical,
        important_skills=important,
        nice_to_have_skills=nice,
        improvement_suggestions=suggestions,
    )


def compare_resume_to_job_description(
    resume: ResumeParseResult,
    job_description_text: str,
    careers: dict[str, dict[str, Any]],
) -> JobDescriptionMatch:
    normalized_jd = normalize_text(job_description_text)
    if not normalized_jd:
        return JobDescriptionMatch(0, 0, [], [], 0, 0, 0, 0, "Needs Improvement", [])

    skill_bank = build_skill_bank(careers)
    jd_skills = detect_skills(normalized_jd, skill_bank)
    resume_skill_set = {normalize(skill) for skill in resume.skills}
    matched_keywords = [skill for skill in jd_skills if normalize(skill) in resume_skill_set]
    missing_keywords = [skill for skill in jd_skills if normalize(skill) not in resume_skill_set]

    keyword_match = percent(len(matched_keywords), len(jd_skills))
    semantic_match = semantic_overlap(resume.text, normalized_jd)
    experience_match = section_match(resume.experience, normalized_jd, ["experience", "intern", "years", "worked", "responsible"])
    education_match = section_match(resume.education + [resume.degree, resume.branch], normalized_jd, ["degree", "bachelor", "master", "education", "graduate"])
    certification_match = section_match(resume.certifications, normalized_jd, ["certification", "certificate", "certified"])
    technical_match = keyword_match
    recommendation = hiring_recommendation(keyword_match, semantic_match, experience_match, education_match, technical_match)

    return JobDescriptionMatch(
        keyword_match=keyword_match,
        semantic_match=semantic_match,
        matched_keywords=matched_keywords,
        missing_keywords=missing_keywords,
        experience_match=experience_match,
        education_match=education_match,
        certification_match=certification_match,
        technical_match=technical_match,
        hiring_recommendation=recommendation,
        highlighted_missing_keywords=missing_keywords[:12],
    )


def normalize(value: str) -> str:
    return value.strip().casefold()


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def percent(numerator: int, denominator: int) -> int:
    if denominator <= 0:
        return 0
    return round(numerator / denominator * 100)


def soft_skill_score(resume: ResumeParseResult) -> int:
    soft_skills = resume.skill_categories.get("Soft Skills", [])
    return min(len(soft_skills), 4) * 25


def split_missing_skills(missing_skills: list[str]) -> tuple[list[str], list[str], list[str]]:
    return missing_skills[:3], missing_skills[3:7], missing_skills[7:]


def build_strengths(weighted_scores: dict[str, int], matched_required: set[str], required_skills: list[str]) -> list[str]:
    strengths = []
    if matched_required:
        strengths.append(f"Matches {len(matched_required)} target-career technical skill(s), which directly improves role fit.")
    for label, score in weighted_scores.items():
        if score >= 75:
            strengths.append(f"{label} is strong because the resume provides enough evidence in this area.")
    return strengths[:6] or ["The resume has enough structure to begin matching against the selected career."]


def build_weaknesses(weighted_scores: dict[str, int], missing_skills: list[str]) -> list[str]:
    weaknesses = []
    if missing_skills:
        weaknesses.append(f"{len(missing_skills)} required skill(s) are missing from the resume, reducing technical match.")
    for label, score in weighted_scores.items():
        if score < 45:
            weaknesses.append(f"{label} is weak because the resume has limited visible proof for this category.")
    return weaknesses[:6]


def build_suggestions(
    weighted_scores: dict[str, int],
    critical: list[str],
    important: list[str],
    nice: list[str],
    career_goal: str,
) -> list[dict[str, str]]:
    suggestions = []
    for skill in critical:
        suggestions.append(
            {
                "suggestion": f"Add a project or bullet proving {skill}.",
                "why": f"{skill} is a critical missing skill for {career_goal}, so adding proof will raise the technical match score.",
            }
        )
    if weighted_scores["Projects"] < 70:
        suggestions.append(
            {
                "suggestion": "Add one role-specific portfolio project with tools, problem, and measurable result.",
                "why": "Project evidence is weighted heavily because recruiters need proof that skills were applied.",
            }
        )
    if weighted_scores["ATS Compatibility"] < 70:
        suggestions.append(
            {
                "suggestion": "Use standard resume headings and include exact role keywords.",
                "why": "ATS compatibility is low when key sections or target keywords are hard to find.",
            }
        )
    if important:
        suggestions.append(
            {
                "suggestion": f"Add important supporting skills: {', '.join(important[:4])}.",
                "why": "These skills are not always blockers, but they improve shortlist probability.",
            }
        )
    if nice:
        suggestions.append(
            {
                "suggestion": f"Use nice-to-have skills as differentiators: {', '.join(nice[:4])}.",
                "why": "Nice-to-have skills help the resume stand out after core requirements are covered.",
            }
        )
    return suggestions[:8]


def semantic_overlap(resume_text: str, jd_text: str) -> int:
    resume_terms = meaningful_terms(resume_text)
    jd_terms = meaningful_terms(jd_text)
    if not jd_terms:
        return 0
    return percent(len(resume_terms & jd_terms), len(jd_terms))


def meaningful_terms(text: str) -> set[str]:
    terms = re.findall(r"[a-zA-Z][a-zA-Z+#.]{2,}", text.casefold())
    return {term for term in terms if term not in STOP_WORDS}


def section_match(resume_values: list[str], jd_text: str, jd_markers: list[str]) -> int:
    jd_lower = jd_text.casefold()
    if not any(marker in jd_lower for marker in jd_markers):
        return 100
    resume_text = " ".join(value for value in resume_values if value).casefold()
    if not resume_text:
        return 0
    return semantic_overlap(resume_text, jd_text)


def hiring_recommendation(*scores: int) -> str:
    average = round(sum(scores) / len(scores)) if scores else 0
    if average >= 80:
        return "Excellent"
    if average >= 65:
        return "Good"
    if average >= 45:
        return "Average"
    return "Needs Improvement"
