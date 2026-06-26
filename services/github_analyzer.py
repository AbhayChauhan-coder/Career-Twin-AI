from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import requests


AI_KEYWORDS = {
    "ai",
    "artificial-intelligence",
    "chatbot",
    "computer-vision",
    "deep-learning",
    "gemini",
    "langchain",
    "llm",
    "machine-learning",
    "ml",
    "nlp",
    "neural",
    "tensorflow",
    "pytorch",
}

WEB_KEYWORDS = {
    "api",
    "backend",
    "css",
    "dashboard",
    "django",
    "fastapi",
    "frontend",
    "fullstack",
    "html",
    "javascript",
    "next",
    "react",
    "streamlit",
    "typescript",
    "web",
}

LANGUAGE_TO_SKILLS = {
    "CSS": ["CSS", "Frontend"],
    "Dart": ["Flutter", "Mobile Development"],
    "HTML": ["HTML", "Frontend"],
    "Java": ["Java"],
    "JavaScript": ["JavaScript", "Web Development"],
    "Jupyter Notebook": ["Python", "Machine Learning", "Data Analysis"],
    "Python": ["Python"],
    "R": ["Statistics", "Data Analysis"],
    "SQL": ["SQL", "Data Analysis"],
    "TypeScript": ["TypeScript", "React"],
}


@dataclass
class GitHubRepoSummary:
    name: str
    description: str
    language: str
    stars: int
    topics: list[str] = field(default_factory=list)
    updated_at: str = ""
    url: str = ""
    project_type: str = "General"
    quality_score: int = 0


@dataclass
class GitHubAnalysis:
    username: str
    repository_count: int
    total_stars: int
    language_counts: dict[str, int]
    top_skills: list[str]
    ai_ml_projects: list[GitHubRepoSummary]
    web_projects: list[GitHubRepoSummary]
    activity_level: str
    github_score: int
    project_quality_score: int
    portfolio_strength: str
    recommendations: list[str]
    repos: list[GitHubRepoSummary]


def analyze_github_profile(username: str) -> GitHubAnalysis:
    username = username.strip()
    if not username:
        raise RuntimeError("Enter a GitHub username.")

    repos = fetch_public_repos(username)
    summaries = [summarize_repo(repo) for repo in repos]
    language_counts = count_languages(summaries)
    ai_projects = [repo for repo in summaries if repo.project_type == "AI/ML"]
    web_projects = [repo for repo in summaries if repo.project_type == "Web Development"]
    total_stars = sum(repo.stars for repo in summaries)
    activity_level = calculate_activity_level(summaries)
    project_quality_score = calculate_project_quality_score(summaries)
    github_score = calculate_github_score(
        repo_count=len(summaries),
        stars=total_stars,
        language_count=len(language_counts),
        ai_project_count=len(ai_projects),
        web_project_count=len(web_projects),
        activity_level=activity_level,
        project_quality_score=project_quality_score,
    )
    top_skills = extract_skills(summaries, language_counts)

    return GitHubAnalysis(
        username=username,
        repository_count=len(summaries),
        total_stars=total_stars,
        language_counts=language_counts,
        top_skills=top_skills,
        ai_ml_projects=ai_projects,
        web_projects=web_projects,
        activity_level=activity_level,
        github_score=github_score,
        project_quality_score=project_quality_score,
        portfolio_strength=portfolio_strength(github_score),
        recommendations=build_recommendations(
            summaries=summaries,
            ai_project_count=len(ai_projects),
            web_project_count=len(web_projects),
            activity_level=activity_level,
            top_skills=top_skills,
        ),
        repos=sorted(summaries, key=lambda repo: (repo.quality_score, repo.stars), reverse=True)[:6],
    )


def fetch_public_repos(username: str) -> list[dict[str, Any]]:
    url = f"https://api.github.com/users/{username}/repos"
    response = requests.get(
        url,
        params={"per_page": 100, "sort": "updated", "type": "owner"},
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "Career-Twin-AI",
        },
        timeout=15,
    )
    if response.status_code == 404:
        raise RuntimeError("GitHub user not found.")
    if response.status_code == 403:
        raise RuntimeError("GitHub API rate limit reached. Try again later.")
    if response.status_code >= 400:
        raise RuntimeError("Could not fetch this GitHub profile.")
    return response.json()


def summarize_repo(repo: dict[str, Any]) -> GitHubRepoSummary:
    topics = repo.get("topics") or []
    language = repo.get("language") or "Unknown"
    text = " ".join(
        [
            repo.get("name") or "",
            repo.get("description") or "",
            language,
            " ".join(topics),
        ]
    ).casefold()
    project_type = classify_project(text)
    summary = GitHubRepoSummary(
        name=repo.get("name") or "Untitled repository",
        description=repo.get("description") or "No description provided.",
        language=language,
        stars=int(repo.get("stargazers_count") or 0),
        topics=topics,
        updated_at=repo.get("updated_at") or "",
        url=repo.get("html_url") or "",
        project_type=project_type,
    )
    summary.quality_score = repo_quality_score(summary)
    return summary


def classify_project(text: str) -> str:
    if any(keyword in text for keyword in AI_KEYWORDS):
        return "AI/ML"
    if any(keyword in text for keyword in WEB_KEYWORDS):
        return "Web Development"
    return "General"


def count_languages(repos: list[GitHubRepoSummary]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for repo in repos:
        if repo.language and repo.language != "Unknown":
            counts[repo.language] = counts.get(repo.language, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: item[1], reverse=True))


def extract_skills(repos: list[GitHubRepoSummary], language_counts: dict[str, int]) -> list[str]:
    skills = []
    for language in language_counts:
        skills.extend(LANGUAGE_TO_SKILLS.get(language, [language]))
    for repo in repos:
        text = f"{repo.name} {repo.description} {' '.join(repo.topics)}".casefold()
        if any(keyword in text for keyword in AI_KEYWORDS):
            skills.extend(["Machine Learning", "AI Projects"])
        if "fastapi" in text:
            skills.append("FastAPI")
        if "react" in text:
            skills.append("React")
        if "dashboard" in text:
            skills.append("Data Visualization")
    return dedupe(skills)[:10]


def repo_quality_score(repo: GitHubRepoSummary) -> int:
    score = 35
    if repo.description and repo.description != "No description provided.":
        score += 15
    if repo.topics:
        score += min(len(repo.topics), 5) * 4
    if repo.stars:
        score += min(repo.stars, 20)
    if repo.project_type in {"AI/ML", "Web Development"}:
        score += 15
    if repo.updated_at and days_since(repo.updated_at) <= 180:
        score += 10
    return max(0, min(score, 100))


def calculate_project_quality_score(repos: list[GitHubRepoSummary]) -> int:
    if not repos:
        return 0
    top_repos = sorted(repos, key=lambda repo: repo.quality_score, reverse=True)[:5]
    return round(sum(repo.quality_score for repo in top_repos) / len(top_repos))


def calculate_activity_level(repos: list[GitHubRepoSummary]) -> str:
    if not repos:
        return "No public activity"
    recent_count = sum(1 for repo in repos if repo.updated_at and days_since(repo.updated_at) <= 120)
    if recent_count >= 5:
        return "High"
    if recent_count >= 2:
        return "Medium"
    return "Low"


def calculate_github_score(
    repo_count: int,
    stars: int,
    language_count: int,
    ai_project_count: int,
    web_project_count: int,
    activity_level: str,
    project_quality_score: int,
) -> int:
    score = 0
    score += min(repo_count, 20) * 2
    score += min(stars, 50)
    score += min(language_count, 6) * 4
    score += min(ai_project_count, 3) * 7
    score += min(web_project_count, 3) * 5
    score += {"High": 20, "Medium": 12, "Low": 5}.get(activity_level, 0)
    score += round(project_quality_score * 0.25)
    return max(0, min(score, 100))


def portfolio_strength(score: int) -> str:
    if score >= 80:
        return "Strong"
    if score >= 55:
        return "Developing"
    if score >= 30:
        return "Early"
    return "Needs public proof of work"


def build_recommendations(
    summaries: list[GitHubRepoSummary],
    ai_project_count: int,
    web_project_count: int,
    activity_level: str,
    top_skills: list[str],
) -> list[str]:
    recommendations = []
    if ai_project_count == 0:
        recommendations.append("Build one production-level AI project with a clear README and deployed demo.")
    if web_project_count == 0:
        recommendations.append("Add one full-stack or API project to show product-building ability.")
    if activity_level != "High":
        recommendations.append("Update or publish projects consistently so recent activity is visible.")
    if summaries and any(repo.description == "No description provided." for repo in summaries[:5]):
        recommendations.append("Add descriptions and topics to your strongest repositories.")
    if not top_skills:
        recommendations.append("Use public repositories to demonstrate your strongest technical skills.")
    return recommendations[:4] or ["Your GitHub portfolio is strong. Add one polished flagship project to make it recruiter-ready."]


def days_since(iso_datetime: str) -> int:
    updated = datetime.fromisoformat(iso_datetime.replace("Z", "+00:00"))
    return (datetime.now(timezone.utc) - updated).days


def dedupe(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        key = item.casefold()
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result
