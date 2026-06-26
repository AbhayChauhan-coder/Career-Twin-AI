from __future__ import annotations

from typing import Any


def build_mentor_context(
    *,
    profile: Any,
    resume: Any,
    github_analysis: Any,
    country_intelligence: Any,
    roadmap: list[dict[str, Any]],
    missing_skills: list[str],
    resume_match: Any,
) -> dict[str, Any]:
    return {
        "name": getattr(profile, "name", "") or "there",
        "career_goal": getattr(profile, "career_goal", "") or "your target career",
        "country": getattr(profile, "target_country", "") or "your target country",
        "weekly_study_hours": getattr(profile, "weekly_study_hours", 0) or 0,
        "resume_strength": getattr(resume, "strength_score", None),
        "resume_skills": getattr(resume, "skills", []) if resume else getattr(profile, "skills", []),
        "projects": getattr(resume, "projects", []) if resume else getattr(profile, "projects", []),
        "experience": getattr(resume, "experience", []) if resume else getattr(profile, "internships", []),
        "certifications": getattr(resume, "certifications", []) if resume else getattr(profile, "certifications", []),
        "github_score": getattr(github_analysis, "github_score", None),
        "github_recommendations": getattr(github_analysis, "recommendations", []) if github_analysis else [],
        "country_demand": getattr(country_intelligence, "demand_level", ""),
        "country_skills": getattr(country_intelligence, "most_required_skills", []) if country_intelligence else [],
        "roadmap": roadmap,
        "missing_skills": missing_skills,
        "resume_match": getattr(resume_match, "overall_match", None),
        "critical_missing": getattr(resume_match, "critical_missing_skills", []) if resume_match else missing_skills[:3],
        "important_skills": getattr(resume_match, "important_skills", []) if resume_match else missing_skills[3:7],
        "match_suggestions": getattr(resume_match, "improvement_suggestions", []) if resume_match else [],
    }


def answer_mentor_question(question: str, context: dict[str, Any], history: list[dict[str, str]] | None = None) -> str:
    normalized = question.casefold()
    history = history or []

    if any(term in normalized for term in ["review my resume", "resume review", "review resume"]):
        return resume_review(context)
    if any(term in normalized for term in ["learn next", "next learn", "what should i learn", "learn now"]):
        return learning_advice(context)
    if any(term in normalized for term in ["certification", "certificate", "cert"]):
        return certification_advice(context)
    if any(term in normalized for term in ["interview", "questions", "prepare"]):
        return interview_questions(context)
    if "github" in normalized:
        return github_advice(context)
    if any(term in normalized for term in ["resume match", "match score", "increase my score", "increase score"]):
        return match_score_advice(context)
    if any(term in normalized for term in ["roadmap", "plan", "weeks", "month"]):
        return roadmap_advice(context)

    return general_answer(context, history)


def resume_review(context: dict[str, Any]) -> str:
    score = context.get("resume_strength")
    match = context.get("resume_match")
    projects = context.get("projects", [])
    experience = context.get("experience", [])
    certifications = context.get("certifications", [])
    missing = context.get("critical_missing", [])

    lines = [
        f"For {context['career_goal']} in {context['country']}, your resume is strongest where it shows concrete skills and proof of work.",
    ]
    if score is not None:
        lines.append(f"Resume Strength: {score}%.")
    if match is not None:
        lines.append(f"Resume Match Score: {match}%.")
    if projects:
        lines.append("Your projects help, but make sure each one states the problem, stack, and measurable result.")
    else:
        lines.append("Your biggest resume gap is project proof. Add at least one role-specific project.")
    if not experience:
        lines.append("Experience is not clearly visible, so add internships, freelance, lab, or volunteer work if available.")
    if not certifications:
        lines.append("Certifications are not prominent. A targeted certificate can improve credibility.")
    if missing:
        lines.append("Critical missing skills to address: " + ", ".join(missing[:4]) + ".")
    return "\n\n".join(lines)


def learning_advice(context: dict[str, Any]) -> str:
    roadmap = context.get("roadmap", [])
    critical = context.get("critical_missing", [])
    weekly_hours = context.get("weekly_study_hours", 0)
    first_focus = roadmap[0]["focus"] if roadmap else (critical[0] if critical else "portfolio building")
    second_focus = roadmap[1]["focus"] if len(roadmap) > 1 else None

    answer = [
        f"Learn **{first_focus}** next because it is closest to your current {context['career_goal']} gap.",
        f"With {weekly_hours} study hours per week, keep the plan focused: learn, build, then document proof.",
    ]
    if second_focus:
        answer.append(f"After that, move to **{second_focus}** so your roadmap progresses without repeating topics.")
    if critical:
        answer.append("Do not skip these critical gaps: " + ", ".join(critical[:3]) + ".")
    return "\n\n".join(answer)


def certification_advice(context: dict[str, Any]) -> str:
    goal = context["career_goal"].casefold()
    country = context["country"]
    if "ai" in goal or "machine learning" in goal:
        certs = ["Google Professional Machine Learning Engineer", "AWS Machine Learning Specialty", "DeepLearning.AI Machine Learning Specialization"]
    elif "data" in goal:
        certs = ["Google Data Analytics", "Microsoft PL-300 Power BI", "IBM Data Analyst"]
    elif "cloud" in goal or "devops" in goal:
        certs = ["AWS Solutions Architect Associate", "Certified Kubernetes Application Developer", "Terraform Associate"]
    elif "cyber" in goal or "security" in goal:
        certs = ["CompTIA Security+", "Certified Ethical Hacker", "Google Cybersecurity Certificate"]
    else:
        certs = ["AWS Cloud Practitioner", "Google Project Management", "role-specific portfolio certification"]

    if country == "Germany":
        certs.append("German B1 language certification")
    return "Best certification path:\n\n" + "\n".join(f"- {cert}" for cert in certs[:4])


def interview_questions(context: dict[str, Any]) -> str:
    skills = context.get("critical_missing", []) + context.get("resume_skills", [])[:4]
    questions = [
        f"Tell me about a project that proves you are ready for {context['career_goal']}.",
        "Which technical decision did you make in a project, and why?",
        "What was the hardest bug or blocker you solved?",
        f"How would you improve your profile for the {context['country']} market?",
    ]
    questions.extend(f"Explain {skill} with a practical example." for skill in skills[:4])
    return "Practice these interview questions:\n\n" + "\n".join(f"- {question}" for question in questions)


def github_advice(context: dict[str, Any]) -> str:
    score = context.get("github_score")
    recommendations = context.get("github_recommendations", [])
    lines = []
    if score is not None:
        lines.append(f"Your GitHub Score is {score}%.")
    if recommendations:
        lines.append("Highest-impact GitHub fixes:\n" + "\n".join(f"- {item}" for item in recommendations[:4]))
    else:
        lines.append("Improve GitHub by pinning 3 strong repositories, adding READMEs, screenshots, setup steps, and deployed demos.")
    lines.append(f"Build one flagship {context['career_goal']} project and make the README recruiter-friendly.")
    return "\n\n".join(lines)


def match_score_advice(context: dict[str, Any]) -> str:
    suggestions = context.get("match_suggestions", [])
    critical = context.get("critical_missing", [])
    lines = []
    if context.get("resume_match") is not None:
        lines.append(f"Your current Resume Match Score is {context['resume_match']}%.")
    if suggestions:
        lines.append("To raise it fastest:")
        lines.extend(f"- {item['suggestion']} Why: {item['why']}" for item in suggestions[:5])
    elif critical:
        lines.append("Add proof for these critical missing skills: " + ", ".join(critical[:4]) + ".")
    else:
        lines.append("Improve match score by adding measurable project outcomes and exact target-role keywords.")
    return "\n".join(lines)


def roadmap_advice(context: dict[str, Any]) -> str:
    roadmap = context.get("roadmap", [])
    if not roadmap:
        return "I need a generated roadmap first. Create your Career Twin, then I can explain the next steps."
    lines = [f"Here is your current roadmap for {context['career_goal']}:"]
    for item in roadmap[:6]:
        lines.append(f"- {item['month']}: {item['focus']}")
    return "\n".join(lines)


def general_answer(context: dict[str, Any], history: list[dict[str, str]]) -> str:
    memory_note = ""
    if history:
        memory_note = "I am using our previous messages in this session, plus your current dashboard context.\n\n"
    return (
        memory_note
        + f"You are targeting **{context['career_goal']}** in **{context['country']}**. "
        + "Ask me to review your resume, improve your GitHub, plan certifications, prepare interviews, or raise your Resume Match Score."
    )
