from __future__ import annotations

import hashlib
import html
import re

import altair as alt
import pandas as pd
import streamlit as st

from database.db import recent_profiles, save_profile
from models.user import UserProfile
from services.career_engine import (
    calculate_readiness,
    calculate_success_probability,
    career_matches,
    fallback_action_plan,
    fallback_future,
    fallback_roadmap,
    load_careers,
    split_multiline_or_csv,
)
from services.gemini_service import (
    generate_explanation,
    generate_future_simulation,
    generate_roadmap,
)
from services.github_analyzer import GitHubAnalysis, analyze_github_profile
from services.country_intelligence import (
    SUPPORTED_COUNTRIES,
    CountryCareerIntelligence,
    get_country_career_intelligence,
)
from services.resume_parser import CONFIDENCE_LOW_MESSAGE, ResumeParseResult, parse_uploaded_resume
from services.resume_parser import extract_resume_text
from services.resume_matcher import (
    JobDescriptionMatch,
    ResumeMatchAnalysis,
    analyze_resume_match,
    compare_resume_to_job_description,
)
from services.ai_mentor import answer_mentor_question, build_mentor_context


HTML_TAG_RE = re.compile(r"</?[a-z][\s\S]*?>", re.IGNORECASE)
SCRIPT_STYLE_RE = re.compile(r"<(script|style)[\s\S]*?</\1>", re.IGNORECASE)


st.set_page_config(
    page_title="Career Twin AI",
    page_icon="CT",
    layout="wide",
    initial_sidebar_state="expanded",
)


def render_metric(label: str, value: str, note: str = "") -> None:
    with st.container(border=True):
        st.metric(label, value)
        if note:
            st.caption(note)


def render_ai_mentor_chat(context: dict[str, object]) -> None:
    st.session_state.setdefault("mentor_messages", [])

    with st.popover("AI Mentor Chat", use_container_width=True):
        st.caption("Personalized mentor using your resume, career goal, GitHub, country, roadmap, missing skills, and match scores.")
        quick_prompts = [
            "Review my resume.",
            "What should I learn next?",
            "Which certification should I do?",
            "Prepare interview questions.",
            "Improve my GitHub.",
            "How can I increase my Resume Match Score?",
        ]
        selected_prompt = st.selectbox("Quick question", [""] + quick_prompts, key="mentor_quick_prompt")
        custom_prompt = st.text_area("Ask your mentor", value="", height=90, key="mentor_custom_prompt")

        if st.button("Ask Mentor", use_container_width=True):
            question = custom_prompt.strip() or selected_prompt.strip()
            if question:
                st.session_state.mentor_messages.append({"role": "user", "content": question})
                answer = answer_mentor_question(question, context, st.session_state.mentor_messages)
                st.session_state.mentor_messages.append({"role": "assistant", "content": answer})

        if st.button("Clear Mentor Memory", use_container_width=True):
            st.session_state.mentor_messages = []

        for message in st.session_state.mentor_messages[-10:]:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])


def render_circular_score(label: str, score: int, note: str = "") -> None:
    st.markdown(
        f"""
        <div style="border:1px solid rgba(128,128,128,.25); border-radius:14px; padding:16px; text-align:center;">
            <div style="width:112px; height:112px; border-radius:50%; margin:0 auto 10px;
                background: conic-gradient(#4f8cff {score * 3.6}deg, rgba(128,128,128,.18) 0deg);
                display:flex; align-items:center; justify-content:center;">
                <div style="width:78px; height:78px; border-radius:50%; background:rgba(14,17,23,.96);
                    display:flex; align-items:center; justify-content:center; font-size:22px; font-weight:700;">
                    {score}%
                </div>
            </div>
            <div style="font-weight:700;">{label}</div>
            <div style="font-size:12px; opacity:.72;">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_progress_steps(current_step: int) -> None:
    steps = [
        "Step 1: Create Profile",
        "Step 2: Analyze Skills",
        "Step 3: Generate Career Twin",
        "Step 4: View Dashboard",
    ]
    st.progress(current_step / len(steps))
    columns = st.columns(len(steps))
    for index, (column, step) in enumerate(zip(columns, steps), start=1):
        with column:
            if index < current_step:
                st.success(step)
            elif index == current_step:
                st.info(step)
            else:
                st.caption(step)


def render_onboarding_intro(method: str) -> None:
    st.subheader("How would you like to create your Career Twin?")
    option_cols = st.columns(2)
    with option_cols[0]:
        with st.container(border=True):
            st.markdown("**Upload Resume**")
            st.caption("Recommended. Extract your profile from a PDF resume, then review and edit it before generating the dashboard.")
            if method == "Upload Resume":
                st.success("Selected")
    with option_cols[1]:
        with st.container(border=True):
            st.markdown("**Fill Manually**")
            st.caption("Enter your education, skills, projects, certifications, and experience yourself.")
            if method == "Fill Manually":
                st.success("Selected")


def render_pills(items: list[str]) -> None:
    if not items:
        st.success("No gaps found")
        return

    columns = st.columns(2)
    for index, item in enumerate(items):
        with columns[index % 2]:
            st.write(f"- {item}")


def render_skill_grid(skills: list[str]) -> None:
    if not skills:
        st.info("No skills detected yet.")
        return

    columns = st.columns(4)
    for index, skill in enumerate(skills):
        with columns[index % 4]:
            with st.container(border=True):
                st.caption(skill)


def display_value(value: object) -> str:
    if value in {None, "", "Unknown", "None", "Null", 0}:
        return "Not Specified"
    return str(value)


def confident_value(resume: ResumeParseResult, field: str, value: object) -> str:
    if resume.field_confidence.get(field, 0.0) < 0.6 or value in {None, "", "Unknown", "None", "Null"}:
        return CONFIDENCE_LOW_MESSAGE
    return str(value)


def confidence_pct(resume: ResumeParseResult, field: str) -> str:
    return f"{round(resume.field_confidence.get(field, 0.0) * 100)}%"


def render_resume_debug_panels(resume: ResumeParseResult) -> None:
    with st.expander("Extracted Resume Text"):
        if resume.text:
            st.text_area(
                "Raw text extracted by PyMuPDF",
                value=resume.text,
                height=320,
                disabled=True,
            )
        else:
            st.error("No text could be extracted from this resume.")

    with st.expander("Detected Skills"):
        if resume.skills:
            render_skill_grid(resume.skills)
        else:
            st.warning("No skills were detected.")


def render_extracted_fields(resume: ResumeParseResult) -> None:
    st.markdown("**Exact fields extracted from resume**")
    personal_cols = st.columns(2)
    with personal_cols[0]:
        st.write(f"Name: {confident_value(resume, 'name', resume.name)} ({confidence_pct(resume, 'name')})")
        st.write(f"Email: {confident_value(resume, 'email', resume.email)} ({confidence_pct(resume, 'email')})")
        st.write(f"Phone: {confident_value(resume, 'phone', resume.phone)} ({confidence_pct(resume, 'phone')})")
        st.write(f"Location: {confident_value(resume, 'location', resume.location)} ({confidence_pct(resume, 'location')})")
        st.write(f"Age: {display_value(resume.age)}")
    with personal_cols[1]:
        st.write(f"LinkedIn: {confident_value(resume, 'linkedin', resume.linkedin)} ({confidence_pct(resume, 'linkedin')})")
        st.write(f"GitHub: {confident_value(resume, 'github', resume.github)} ({confidence_pct(resume, 'github')})")
        st.write(f"Portfolio: {confident_value(resume, 'portfolio', resume.portfolio)} ({confidence_pct(resume, 'portfolio')})")
        st.write(f"Degree: {confident_value(resume, 'degree', resume.degree)} ({confidence_pct(resume, 'degree')})")
        st.write(f"Branch: {confident_value(resume, 'branch', resume.branch)} ({confidence_pct(resume, 'branch')})")
    st.write(f"University: {confident_value(resume, 'university', resume.university)} ({confidence_pct(resume, 'university')})")
    st.write(f"Education Years: {display_value(resume.start_year)} - {display_value(resume.graduation_year)}")
    st.write(f"Current Year: {confident_value(resume, 'current_year', resume.current_year)} ({confidence_pct(resume, 'current_year')})")
    st.write(f"CGPA: {confident_value(resume, 'cgpa', resume.gpa)} ({confidence_pct(resume, 'cgpa')})")


def render_resume_insights(resume: ResumeParseResult, missing_skills: list[str]) -> None:
    st.subheader("Resume Insights")
    metric_cols = st.columns(5)
    with metric_cols[0]:
        render_metric("Resume Strength", f"{resume.strength_score}%", "Based on skills, projects, education, certifications, and experience.")
        st.progress(resume.strength_score / 100)
    with metric_cols[1]:
        render_metric("Resume Completeness", f"{resume.completeness_score}%", "How many major resume sections were detected.")
    with metric_cols[2]:
        render_metric("Industry Readiness", f"{resume.industry_readiness_score}%", "Role proof from skills, projects, and experience.")
    with metric_cols[3]:
        render_metric("ATS Readiness", f"{resume.ats_readiness_score}%", "Keyword and section readiness.")
    with metric_cols[4]:
        render_metric("Overall Career Readiness", f"{resume.overall_career_readiness_score}%", "Combined resume readiness.")

    insight_cols = st.columns([1.2, 1])
    with insight_cols[0]:
        st.markdown("**Extracted Skills By Category**")
        for category, skills in resume.skill_categories.items():
            with st.expander(category, expanded=bool(skills)):
                render_skill_grid(skills)
    with insight_cols[1]:
        st.markdown("**Missing Skills For Selected Career**")
        render_pills(missing_skills)

    detail_cols = st.columns(3)
    with detail_cols[0]:
        with st.expander("Education", expanded=True):
            if resume.education:
                for item in resume.education:
                    st.write(f"- {item}")
                st.caption(f"Degree: {display_value(resume.degree)}")
                st.caption(f"Branch: {display_value(resume.branch)}")
                st.caption(f"University: {display_value(resume.university)}")
                st.caption(f"Current Year: {display_value(resume.current_year)}")
            else:
                st.warning("We couldn't confidently extract this section. Please review it manually.")
    with detail_cols[1]:
        with st.expander("Certifications", expanded=True):
            if resume.structured_certifications:
                for cert in resume.structured_certifications:
                    with st.container(border=True):
                        st.markdown(f"**{display_value(cert.get('name'))}**")
                        if cert.get("provider") or cert.get("completion_year"):
                            st.caption(f"{display_value(cert.get('provider'))} | {display_value(cert.get('completion_year'))}")
            else:
                st.warning("We couldn't confidently extract this section. Please review it manually.")
    with detail_cols[2]:
        with st.expander("Projects and Experience", expanded=True):
            if resume.structured_projects:
                st.markdown("**Projects**")
                for project in resume.structured_projects:
                    with st.container(border=True):
                        st.markdown(f"**{display_value(project.get('name'))}**")
                        st.caption(f"Stack: {display_value(project.get('tech_stack'))}")
                        st.write(display_value(project.get("description")))
                        if project.get("role"):
                            st.caption(f"Role: {project['role']}")
                        if project.get("impact"):
                            st.success(f"Impact: {project['impact']}")
            else:
                st.warning("We couldn't confidently extract Projects. Please review it manually.")
            if resume.structured_experience:
                st.markdown("**Experience**")
                for experience in resume.structured_experience:
                    with st.container(border=True):
                        st.markdown(f"**{display_value(experience.get('role'))}**")
                        st.caption(f"{display_value(experience.get('company'))} | {display_value(experience.get('duration'))}")
                        st.write(display_value(experience.get("responsibilities")))
                        if experience.get("skills_used"):
                            st.caption(f"Skills Used: {experience['skills_used']}")
                        if experience.get("achievements"):
                            st.success(f"Achievement: {experience['achievements']}")
            else:
                st.warning("We couldn't confidently extract Experience. Please review it manually.")

    with st.expander("Resume improvement notes"):
        for insight in resume.insights:
            st.write(f"- {insight}")

    render_extracted_fields(resume)
    render_resume_debug_panels(resume)


def render_github_analysis(analysis: GitHubAnalysis) -> None:
    st.subheader("GitHub Profile Analysis")
    st.caption(f"Public portfolio analysis for `{analysis.username}`.")

    metric_cols = st.columns(4)
    with metric_cols[0]:
        render_metric("GitHub Score", f"{analysis.github_score}%", "Repository depth, stars, skills, activity, and project quality.")
        st.progress(analysis.github_score / 100)
    with metric_cols[1]:
        render_metric("Repository Count", str(analysis.repository_count), "Public repositories analyzed.")
    with metric_cols[2]:
        render_metric("Project Quality", f"{analysis.project_quality_score}%", "Average quality of the strongest repositories.")
        st.progress(analysis.project_quality_score / 100)
    with metric_cols[3]:
        render_metric("Portfolio Strength", analysis.portfolio_strength, f"Activity level: {analysis.activity_level}")

    chart_cols = st.columns([1, 1])
    with chart_cols[0]:
        st.markdown("**Languages Used**")
        if analysis.language_counts:
            language_data = pd.DataFrame(
                [{"Language": language, "Repositories": count} for language, count in analysis.language_counts.items()]
            )
            chart = (
                alt.Chart(language_data)
                .mark_arc(innerRadius=55)
                .encode(
                    theta=alt.Theta("Repositories:Q"),
                    color=alt.Color("Language:N"),
                    tooltip=["Language", "Repositories"],
                )
            )
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No repository languages detected.")
    with chart_cols[1]:
        st.markdown("**Top Skills**")
        render_skill_grid(analysis.top_skills)

    project_cols = st.columns(2)
    with project_cols[0]:
        st.markdown("**AI/ML Projects**")
        render_project_summary_cards(analysis.ai_ml_projects[:3])
    with project_cols[1]:
        st.markdown("**Web Development Projects**")
        render_project_summary_cards(analysis.web_projects[:3])

    st.markdown("**Project Summary Cards**")
    render_project_summary_cards(analysis.repos)

    with st.expander("Recommendations", expanded=True):
        for recommendation in analysis.recommendations:
            st.write(f"- {recommendation}")


def render_project_summary_cards(repos: list[object]) -> None:
    if not repos:
        st.caption("No matching public repositories found.")
        return

    for repo in repos:
        with st.container(border=True):
            st.markdown(f"**{repo.name}**")
            st.caption(repo.project_type)
            st.write(repo.description)
            detail_cols = st.columns(3)
            with detail_cols[0]:
                st.metric("Stars", repo.stars)
            with detail_cols[1]:
                st.metric("Language", repo.language)
            with detail_cols[2]:
                st.metric("Quality", f"{repo.quality_score}%")
            if repo.url:
                st.link_button("Open repository", repo.url)


def render_resume_match_score(
    analysis: ResumeMatchAnalysis,
    resume: ResumeParseResult,
    careers: dict[str, dict],
) -> None:
    st.subheader("Resume Match Score")
    st.caption("Complete resume-to-career match intelligence for the selected target role.")

    render_circular_score("Overall Resume Match", analysis.overall_match, "Weighted fit across resume, ATS, GitHub, and role evidence.")

    score_items = list(analysis.weighted_scores.items())
    for start in range(0, len(score_items), 5):
        columns = st.columns(5)
        for column, (label, score) in zip(columns, score_items[start : start + 5]):
            with column:
                render_circular_score(label, score)

    summary_cols = st.columns(2)
    with summary_cols[0]:
        with st.expander("Strengths", expanded=True):
            for item in analysis.strengths:
                st.success(item)
        with st.expander("Critical Missing Skills", expanded=True):
            render_pills(analysis.critical_missing_skills)
        with st.expander("Important Skills"):
            render_pills(analysis.important_skills)
    with summary_cols[1]:
        with st.expander("Weaknesses", expanded=True):
            if analysis.weaknesses:
                for item in analysis.weaknesses:
                    st.warning(item)
            else:
                st.success("No major weaknesses detected for the selected career.")
        with st.expander("Nice-to-have Skills"):
            render_pills(analysis.nice_to_have_skills)
        with st.expander("Resume Improvement Suggestions", expanded=True):
            for suggestion in analysis.improvement_suggestions:
                with st.container(border=True):
                    st.markdown(f"**{suggestion['suggestion']}**")
                    st.caption(f"Why: {suggestion['why']}")

    st.markdown("**Resume vs Job Description**")
    jd_cols = st.columns([1, 1])
    with jd_cols[0]:
        jd_file = st.file_uploader("Upload PDF or DOCX Job Description", type=["pdf", "docx"], key="job_description_file")
    with jd_cols[1]:
        jd_text = st.text_area("Or paste Text Job Description", height=160, key="job_description_text")

    jd_source_text = ""
    if jd_file:
        try:
            jd_source_text = extract_resume_text(jd_file)
        except RuntimeError as exc:
            st.error(str(exc))
    elif jd_text.strip():
        jd_source_text = jd_text.strip()

    if jd_source_text:
        jd_match = compare_resume_to_job_description(resume, jd_source_text, careers)
        render_job_description_match(jd_match)


def render_job_description_match(match: JobDescriptionMatch) -> None:
    metric_cols = st.columns(4)
    with metric_cols[0]:
        render_circular_score("Keyword Match", match.keyword_match)
    with metric_cols[1]:
        render_circular_score("Semantic Match", match.semantic_match)
    with metric_cols[2]:
        render_circular_score("Technical Match", match.technical_match)
    with metric_cols[3]:
        render_metric("Hiring Recommendation", match.hiring_recommendation)

    detail_cols = st.columns(3)
    with detail_cols[0]:
        render_metric("Experience Match", f"{match.experience_match}%")
    with detail_cols[1]:
        render_metric("Education Match", f"{match.education_match}%")
    with detail_cols[2]:
        render_metric("Certification Match", f"{match.certification_match}%")

    keyword_cols = st.columns(2)
    with keyword_cols[0]:
        st.markdown("**Matched Keywords**")
        render_pills(match.matched_keywords)
    with keyword_cols[1]:
        st.markdown("**Missing Keywords**")
        render_pills(match.missing_keywords)

    if match.highlighted_missing_keywords:
        st.warning("Missing keywords to add or prove: " + ", ".join(match.highlighted_missing_keywords))


def render_country_intelligence(intelligence: CountryCareerIntelligence) -> None:
    st.subheader("Country Career Intelligence")
    st.caption(f"{intelligence.career} in {intelligence.country}")

    top_cols = st.columns(4)
    with top_cols[0]:
        render_metric("Demand Level", intelligence.demand_level, "Hiring appetite for this role.")
    with top_cols[1]:
        render_metric("Visa Difficulty", intelligence.visa_difficulty, "Directional mobility complexity.")
    with top_cols[2]:
        render_metric("Market Growth", intelligence.market_growth, "Expected sector momentum.")
    with top_cols[3]:
        render_metric("Entry Salary", intelligence.entry_salary, "Typical early-career range.")

    salary_cols = st.columns(3)
    with salary_cols[0]:
        render_metric("Entry Salary", intelligence.entry_salary)
    with salary_cols[1]:
        render_metric("Mid-Level Salary", intelligence.mid_level_salary)
    with salary_cols[2]:
        render_metric("Senior Salary", intelligence.senior_salary)

    detail_cols = st.columns([1, 1])
    with detail_cols[0]:
        st.markdown("**Most Required Skills**")
        render_skill_grid(intelligence.most_required_skills)
    with detail_cols[1]:
        st.markdown("**Market Insights**")
        for insight in intelligence.insights:
            st.write(f"- {insight}")
        st.caption("Salary and visa indicators are directional planning estimates, not legal or compensation advice.")


def clean_gemini_response(text: str | None) -> str:
    if not text:
        return ""

    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:html|markdown|md)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    cleaned = SCRIPT_STYLE_RE.sub("", cleaned)
    cleaned = cleaned.replace("\r\n", "\n")
    cleaned = html.unescape(cleaned)
    return cleaned.strip()


def html_to_markdown(text: str) -> str:
    converted = clean_gemini_response(text)
    replacements = [
        (r"<\s*br\s*/?\s*>", "\n"),
        (r"</\s*p\s*>", "\n\n"),
        (r"<\s*p[^>]*>", ""),
        (r"</\s*div\s*>", "\n"),
        (r"<\s*div[^>]*>", ""),
        (r"<\s*li[^>]*>", "- "),
        (r"</\s*li\s*>", "\n"),
        (r"</?\s*(ul|ol)[^>]*>", "\n"),
        (r"<\s*h[1-6][^>]*>", "### "),
        (r"</\s*h[1-6]\s*>", "\n\n"),
        (r"<\s*(strong|b)[^>]*>", "**"),
        (r"</\s*(strong|b)\s*>", "**"),
        (r"<\s*(em|i)[^>]*>", "*"),
        (r"</\s*(em|i)\s*>", "*"),
    ]
    for pattern, replacement in replacements:
        converted = re.sub(pattern, replacement, converted, flags=re.IGNORECASE)

    converted = HTML_TAG_RE.sub("", converted)
    converted = re.sub(r"\n{3,}", "\n\n", converted)
    return converted.strip()


def render_clean_response(text: str | None) -> None:
    cleaned = clean_gemini_response(text)
    if not cleaned:
        return

    if HTML_TAG_RE.search(cleaned):
        st.markdown(html_to_markdown(cleaned))
    else:
        st.markdown(cleaned)


def render_timeline(items: list[dict[str, str]]) -> None:
    columns = st.columns(len(items))
    for index, (column, item) in enumerate(zip(columns, items)):
        with column:
            with st.container(border=True):
                st.caption(item["label"])
                st.subheader(item["title"])
                st.write(item["detail"])
                if index < len(items) - 1:
                    st.caption("Next step ->")


def salary_range_for_stage(career_goal: str, stage_index: int) -> str:
    salary_bands = {
        "AI": ["Not applicable", "₹6-8 LPA", "₹12-18 LPA", "₹25-40 LPA"],
        "Data": ["Not applicable", "₹5-7 LPA", "₹10-16 LPA", "₹22-35 LPA"],
        "Cybersecurity": ["Not applicable", "₹5-8 LPA", "₹12-20 LPA", "₹24-38 LPA"],
        "Cloud": ["Not applicable", "₹6-9 LPA", "₹14-22 LPA", "₹28-45 LPA"],
        "DevOps": ["Not applicable", "₹6-9 LPA", "₹14-24 LPA", "₹30-48 LPA"],
        "Developer": ["Not applicable", "₹4-7 LPA", "₹10-18 LPA", "₹22-38 LPA"],
        "Product": ["Not applicable", "₹7-10 LPA", "₹16-28 LPA", "₹35-60 LPA"],
        "UX": ["Not applicable", "₹4-7 LPA", "₹10-16 LPA", "₹20-32 LPA"],
    }
    for keyword, bands in salary_bands.items():
        if keyword.casefold() in career_goal.casefold():
            return bands[stage_index]
    return ["Not applicable", "₹4-7 LPA", "₹10-18 LPA", "₹22-35 LPA"][stage_index]


def digital_twin_stages(profile: UserProfile, readiness: dict[str, object], probability: int) -> list[dict[str, object]]:
    missing_skills = list(readiness.get("missing_skills", []))
    matched_skills = list(readiness.get("matched_skills", []))
    career_goal = profile.career_goal or "Target Career"
    current_role = profile.current_year if profile.current_year not in {"Not specified", "Not Specified"} else "Current You"

    staged_skills = [
        matched_skills[:4] or profile.skills[:4],
        missing_skills[:3] or matched_skills[:3] or ["Portfolio Building"],
        (missing_skills[:5] + ["Real Projects"])[:5] if missing_skills else matched_skills[:5],
        (missing_skills + ["Leadership", "System Design", "Mentoring"])[:6],
    ]
    confidence_scores = [
        max(10, min(readiness["score"], 100)),
        max(20, min(readiness["score"] + 18, 100)),
        max(35, min(probability, 100)),
        max(45, min(probability + 12, 100)),
    ]

    return [
        {
            "label": "Current You",
            "role": current_role or "Student",
            "salary": salary_range_for_stage(career_goal, 0),
            "skills": staged_skills[0],
            "experience": "Foundation",
            "confidence": confidence_scores[0],
        },
        {
            "label": "1 Year Future",
            "role": f"{career_goal.split()[0]} Intern" if career_goal else "Career Intern",
            "salary": salary_range_for_stage(career_goal, 1),
            "skills": staged_skills[1],
            "experience": "Internship Ready",
            "confidence": confidence_scores[1],
        },
        {
            "label": "3 Year Future",
            "role": career_goal,
            "salary": salary_range_for_stage(career_goal, 2),
            "skills": staged_skills[2],
            "experience": "Early Professional",
            "confidence": confidence_scores[2],
        },
        {
            "label": "5 Year Future",
            "role": f"Senior {career_goal}",
            "salary": salary_range_for_stage(career_goal, 3),
            "skills": staged_skills[3],
            "experience": "Advanced Contributor",
            "confidence": confidence_scores[3],
        },
    ]


def render_digital_twin(profile: UserProfile, readiness: dict[str, object], probability: int) -> None:
    st.header("🚀 Your Digital Twin")
    st.caption("A projected career timeline based on your current profile, selected goal, skills, and readiness score.")

    stages = digital_twin_stages(profile, readiness, probability)
    for index, stage in enumerate(stages):
        with st.container(border=True):
            top_cols = st.columns([1.2, 2, 1])
            with top_cols[0]:
                st.caption(str(stage["label"]))
                st.subheader(str(stage["role"]))
            with top_cols[1]:
                st.markdown(f"**Salary Estimate:** {stage['salary']}")
                st.markdown(f"**Experience Level:** {stage['experience']}")
                skills = stage["skills"] or ["No skills detected yet"]
                st.markdown("**Skills Acquired:** " + ", ".join(str(skill) for skill in skills))
            with top_cols[2]:
                st.metric("Confidence Score", f"{stage['confidence']}%")
                st.progress(int(stage["confidence"]) / 100)

        if index < len(stages) - 1:
            arrow_cols = st.columns([1, 1, 1])
            with arrow_cols[1]:
                st.markdown("### ↓")


def render_roadmap(items: list[dict[str, object]]) -> None:
    for item in items:
        with st.expander(f"{item['month']}: {item['focus']}", expanded=item["month"] in {"Month 1", "Month 2"}):
            for task in item["tasks"]:
                st.write(f"- {task}")
            st.success(str(item["outcome"]))


def render_profile_form(careers: dict[str, dict], autofill: dict[str, object], submit_label: str) -> bool:
    career_options = sorted(careers.keys())
    default_career_index = career_options.index("AI Engineer") if "AI Engineer" in career_options else 0
    gpa_value = str(autofill.get("gpa") or "")
    current_year_options = ["Not Specified", "1st Year", "2nd Year", "3rd Year", "4th Year", "Graduate", "Professional"]
    autofill_current_year = str(autofill.get("current_year") or "Not Specified")
    current_year_index = current_year_options.index(autofill_current_year) if autofill_current_year in current_year_options else 0

    name = st.sidebar.text_input("Name", value=str(autofill.get("name") or ""))
    age_text = st.sidebar.text_input("Age", value=str(autofill.get("age") or ""), placeholder="Not Specified")
    degree = st.sidebar.text_input("Degree", value=str(autofill.get("degree") or ""))
    branch = st.sidebar.text_input("Branch", value=str(autofill.get("branch") or ""))
    current_year = st.sidebar.selectbox("Current Year", current_year_options, index=current_year_index)
    gpa_text = st.sidebar.text_input("GPA / CGPA", value=gpa_value, placeholder="Not Specified")
    skills = st.sidebar.text_area("Skills", value=str(autofill.get("skills") or ""), help="Use commas or new lines.")
    projects = st.sidebar.text_area("Projects", value=str(autofill.get("projects") or ""))
    certifications = st.sidebar.text_area("Certifications", value=str(autofill.get("certifications") or ""))
    internships = st.sidebar.text_area("Experience / Internships", value=str(autofill.get("internships") or ""))
    weekly_study_hours = st.sidebar.slider("Weekly Study Hours", min_value=0, max_value=40, value=0)
    career_goal = st.sidebar.selectbox("Career Goal", career_options, index=default_career_index)
    target_country = st.sidebar.selectbox("Target Country", SUPPORTED_COUNTRIES, index=0)
    submitted = st.sidebar.button(submit_label, use_container_width=True)

    age = int(age_text) if age_text.strip().isdigit() else None
    try:
        gpa = float(gpa_text) if gpa_text.strip() else 0.0
    except ValueError:
        gpa = 0.0
    should_update_profile = submitted or st.session_state.get("profile_created", False)
    if should_update_profile:
        st.session_state.profile = UserProfile(
            name=name.strip(),
            age=age,
            degree=degree.strip(),
            branch=branch.strip(),
            current_year=current_year,
            gpa=float(gpa),
            skills=split_multiline_or_csv(skills),
            projects=split_multiline_or_csv(projects),
            certifications=split_multiline_or_csv(certifications),
            internships=split_multiline_or_csv(internships),
            weekly_study_hours=int(weekly_study_hours),
            career_goal=career_goal,
            target_country=target_country.strip(),
        )
        if submitted:
            st.session_state.profile_created = True

    return submitted


def clear_resume_state(clear_profile: bool = True) -> None:
    keys = [
        "profile",
        "profile_created",
        "resume_parse",
        "resume_autofill",
        "resume_error",
        "resume_file_key",
    ]
    if not clear_profile:
        keys.remove("profile")
    for key in keys:
        st.session_state.pop(key, None)


def uploaded_file_key(uploaded_file: object) -> str:
    file_bytes = uploaded_file.getvalue()
    return hashlib.sha256(file_bytes).hexdigest()


def profile_form(careers: dict[str, dict]) -> UserProfile | None:
    st.sidebar.title("Career Twin AI")
    st.sidebar.caption("Build your profile, then generate the same dashboard from either path.")
    st.sidebar.subheader("How would you like to create your Career Twin?")

    method = st.sidebar.radio(
        "Creation method",
        ["Upload Resume", "Fill Manually"],
        index=0,
        captions=["Recommended. Fastest way to start.", "Enter every detail yourself."],
    )
    st.session_state.onboarding_method = method
    st.sidebar.divider()

    if method == "Upload Resume":
        st.sidebar.info("Upload Resume is recommended for faster profile creation.")
        uploaded_resume = st.sidebar.file_uploader("Upload resume", type=["pdf", "docx", "jpg", "jpeg", "png"])
        if uploaded_resume:
            current_file_key = uploaded_file_key(uploaded_resume)
            if st.session_state.get("resume_file_key") != current_file_key:
                clear_resume_state()
                st.session_state.resume_file_key = current_file_key

        if uploaded_resume and st.sidebar.button("Analyze Resume", use_container_width=True):
            try:
                current_file_key = uploaded_file_key(uploaded_resume)
                clear_resume_state()
                st.session_state.resume_file_key = current_file_key
                resume = parse_uploaded_resume(uploaded_resume, careers)
                st.session_state.resume_parse = resume
                if resume.extraction_status == "Failed":
                    st.session_state.resume_error = "Resume extraction failed. No usable fields were detected."
                    st.sidebar.error(st.session_state.resume_error)
                else:
                    st.session_state.resume_autofill = resume.autofill()
                    st.sidebar.success("Resume Analysis Complete")
                st.rerun()
            except RuntimeError as exc:
                clear_resume_state()
                st.session_state.resume_error = str(exc)
                st.sidebar.error(str(exc))
            except Exception:
                clear_resume_state()
                st.session_state.resume_error = "Could not read this PDF resume. Try another PDF file."
                st.sidebar.error(st.session_state.resume_error)

        if st.session_state.get("resume_error"):
            st.sidebar.error(st.session_state.resume_error)
        resume = st.session_state.get("resume_parse")
        if resume:
            if resume.extraction_status == "Success":
                st.sidebar.success("Extraction Status: Success")
            elif resume.extraction_status == "Partial":
                st.sidebar.warning("Extraction Status: Partial")
            else:
                st.sidebar.error("Extraction Status: Failed")
            st.sidebar.metric("Resume Strength", f"{resume.strength_score}%")
            st.sidebar.caption(f"{len(resume.skills)} skills detected")
            with st.sidebar.expander("Exact extracted fields", expanded=True):
                st.write(f"Name: {display_value(resume.name)}")
                st.write(f"Email: {display_value(resume.email)}")
                st.write(f"Phone: {display_value(resume.phone)}")
                st.write(f"LinkedIn: {display_value(resume.linkedin)}")
                st.write(f"GitHub: {display_value(resume.github)}")
                st.write(f"Portfolio: {display_value(resume.portfolio)}")
                st.write(f"Location: {display_value(resume.location)}")
                st.write(f"Age: {display_value(resume.age)}")
                st.write(f"Degree: {display_value(resume.degree)}")
                st.write(f"Branch: {display_value(resume.branch)}")
                st.write(f"University: {display_value(resume.university)}")
                st.write(f"Current Year: {display_value(resume.current_year)}")
                st.write(f"CGPA: {display_value(resume.gpa)}")
                st.write(f"Skills: {', '.join(resume.skills) if resume.skills else 'Not Specified'}")
                st.write(f"Education: {'; '.join(resume.education) if resume.education else 'Not Specified'}")
                st.write(f"Certifications: {'; '.join(resume.certifications) if resume.certifications else 'Not Specified'}")
                st.write(f"Projects: {'; '.join(resume.projects) if resume.projects else 'Not Specified'}")
                st.write(f"Experience: {'; '.join(resume.experience) if resume.experience else 'Not Specified'}")
            if resume.extraction_status != "Failed":
                with st.sidebar.expander("Edit extracted contact fields"):
                    resume.name = st.text_input("Extracted Name", value=resume.name)
                    resume.email = st.text_input("Extracted Email", value=resume.email)
                    resume.phone = st.text_input("Extracted Phone", value=resume.phone)
                    resume.linkedin = st.text_input("Extracted LinkedIn", value=resume.linkedin)
                    resume.github = st.text_input("Extracted GitHub", value=resume.github)
                    resume.portfolio = st.text_input("Extracted Portfolio", value=resume.portfolio)
                    resume.location = st.text_input("Extracted Location", value=resume.location)
                    st.session_state.resume_autofill["name"] = resume.name
                st.sidebar.subheader("Review and edit extracted data")
                render_profile_form(careers, st.session_state.get("resume_autofill", {}), "Generate Career Twin")
        else:
            st.sidebar.caption("The manual form will appear after resume analysis so you can review and edit extracted data.")

    else:
        clear_resume_state(clear_profile=False)
        st.sidebar.subheader("Manual Entry")
        render_profile_form(careers, {}, "Generate Career Twin")

    st.sidebar.divider()
    st.sidebar.subheader("GitHub Profile Analysis")
    github_username = st.sidebar.text_input("GitHub Username", value=st.session_state.get("github_username", ""))
    if st.sidebar.button("Analyze GitHub", use_container_width=True):
        try:
            analysis = analyze_github_profile(github_username)
            st.session_state.github_username = github_username.strip()
            st.session_state.github_analysis = analysis
            st.session_state.github_error = ""
            st.sidebar.success("GitHub analysis complete.")
        except RuntimeError as exc:
            st.session_state.github_error = str(exc)
            st.session_state.pop("github_analysis", None)
            st.sidebar.error(str(exc))
        except Exception:
            st.session_state.github_error = "Could not analyze this GitHub profile."
            st.session_state.pop("github_analysis", None)
            st.sidebar.error(st.session_state.github_error)

    if st.session_state.get("github_error"):
        st.sidebar.error(st.session_state.github_error)

    return st.session_state.get("profile")


def main() -> None:
    careers = load_careers()
    profile = profile_form(careers)

    st.title("Career Twin AI")
    st.caption(
        "See the future version of your career before you live it. Build a digital career twin, compare your current skills with your destination, and get the route forward."
    )
    render_progress_steps(4 if profile else 1)

    if profile is None:
        render_onboarding_intro(st.session_state.get("onboarding_method", "Upload Resume"))
        st.info("Choose Upload Resume or Fill Manually in the sidebar to create your profile.")
        return

    selected_career = careers[profile.career_goal]
    readiness = calculate_readiness(profile, selected_career)
    country_intelligence = get_country_career_intelligence(profile.career_goal, profile.target_country, selected_career)
    probability = calculate_success_probability(profile, readiness["score"], len(readiness["missing_skills"]))
    matches = career_matches(profile, careers)
    top_matches = matches[:4]
    resume = st.session_state.get("resume_parse")
    github_analysis = st.session_state.get("github_analysis")
    roadmap_items = fallback_roadmap(
        readiness["missing_skills"],
        profile.career_goal,
        profile.target_country,
        profile.weekly_study_hours,
    )
    resume_match = analyze_resume_match(resume, profile, selected_career, github_analysis) if resume else None
    mentor_context = build_mentor_context(
        profile=profile,
        resume=resume,
        github_analysis=github_analysis,
        country_intelligence=country_intelligence,
        roadmap=roadmap_items,
        missing_skills=readiness["missing_skills"],
        resume_match=resume_match,
    )

    if st.sidebar.button("Save Snapshot", use_container_width=True):
        save_profile(profile, readiness, probability)
        st.sidebar.success("Snapshot saved.")

    st.subheader(f"{profile.career_goal} in {profile.target_country}")
    metric_cols = st.columns(4)
    with metric_cols[0]:
        render_metric("Readiness Score", f"{readiness['score']}%", "Skills plus projects, internships, certifications, and study consistency.")
        st.progress(readiness["score"] / 100)
    with metric_cols[1]:
        render_metric("Success Probability", f"{probability}%", "A practical estimate based on your current momentum.")
        st.progress(probability / 100)
    with metric_cols[2]:
        render_metric("Matched Skills", str(len(readiness["matched_skills"])), f"Out of {len(readiness['required_skills'])} required skills.")
    with metric_cols[3]:
        render_metric("Weekly Effort", f"{profile.weekly_study_hours}h", "Consistency is your route multiplier.")
    render_ai_mentor_chat(mentor_context)

    st.divider()
    render_digital_twin(profile, readiness, probability)
    st.divider()
    render_country_intelligence(country_intelligence)
    st.divider()

    if resume:
        render_resume_insights(resume, readiness["missing_skills"])
        st.divider()

    if resume and resume_match:
        render_resume_match_score(resume_match, resume, careers)
        st.divider()

    if github_analysis:
        render_github_analysis(github_analysis)
        st.divider()

    gap_cols = st.columns([1, 1])
    with gap_cols[0]:
        st.subheader("Skill Gap Analysis")
        st.caption("Current skills that match your target role.")
        render_pills(readiness["matched_skills"])
    with gap_cols[1]:
        st.subheader("Missing Skills")
        st.caption("Prioritize these to increase readiness fastest.")
        render_pills(readiness["missing_skills"])

    st.divider()

    st.subheader("Career Match Engine")
    match_cols = st.columns(4)
    for column, match in zip(match_cols, top_matches):
        with column:
            with st.container(border=True):
                st.metric(match["career"], f"{match['probability']}%")
                st.caption(f"Readiness {match['score']}%")
                st.progress(match["probability"] / 100)

    st.divider()

    explanation = generate_explanation(profile, readiness)
    with st.container():
        st.subheader("Career Probability Reasoning")
        if explanation:
            render_clean_response(explanation)
        else:
            reasons = [
                f"You already match {len(readiness['matched_skills'])} required skills.",
                f"You need to close {len(readiness['missing_skills'])} skill gaps.",
                f"Your weekly study pace is {profile.weekly_study_hours} hours.",
            ]
            if profile.internship_count:
                reasons.append("Internship experience improves your credibility for this path.")
            else:
                reasons.append("Adding one internship or applied project would improve your signal.")
            st.markdown("\n".join(f"- {reason}" for reason in reasons))

    st.divider()

    st.subheader("Future Simulation Notes")
    gemini_future = generate_future_simulation(profile, readiness)
    with st.expander("Classic timeline summary"):
        render_timeline(fallback_future(profile, readiness["score"]))
    if gemini_future:
        with st.expander("AI future notes"):
            render_clean_response(gemini_future)

    st.divider()

    st.subheader("AI Career Roadmap")
    gemini_roadmap = generate_roadmap(profile, readiness)
    render_roadmap(roadmap_items)
    if gemini_roadmap:
        with st.expander("AI roadmap notes"):
            render_clean_response(gemini_roadmap)

    st.divider()

    action_cols = st.columns([2, 1])
    with action_cols[0]:
        st.subheader("Weekly Action Plan")
        for action in fallback_action_plan(
            readiness["missing_skills"],
            profile.career_goal,
            profile.weekly_study_hours,
            profile.target_country,
        ):
            st.markdown(f"**{action['week']}**: {action['task']}")
    with action_cols[1]:
        st.subheader("Recent Snapshots")
        profiles = recent_profiles()
        if profiles:
            for item in profiles:
                st.caption(
                    f"{item['name']} | {item['career_goal']} | Readiness {item['readiness_score']}% | Probability {item['success_probability']}%"
                )
        else:
            st.caption("No saved snapshots yet.")


if __name__ == "__main__":
    main()
