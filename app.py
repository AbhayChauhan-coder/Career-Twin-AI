from __future__ import annotations

import hashlib
import html
import json
import re
from datetime import datetime

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
    salary_midpoint,
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
from services.career_knowledge import (
    build_transition_plan,
    career_search_suggestions,
    discover_careers,
    get_career_knowledge,
    interview_preparation,
    learning_recommendations,
    recommend_careers_for_profile,
)


HTML_TAG_RE = re.compile(r"</?[a-z][\s\S]*?>", re.IGNORECASE)
SCRIPT_STYLE_RE = re.compile(r"<(script|style)[\s\S]*?</\1>", re.IGNORECASE)


st.set_page_config(
    page_title="Career Twin AI",
    page_icon="CT",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
    <style>
    section.main > div { padding-top: 1.2rem; }
    div[data-testid="stMetric"] { min-height: 76px; }
    div[data-testid="stHorizontalBlock"] { gap: 0.85rem; }
    .block-container { padding-bottom: 3rem; }
    @media (max-width: 760px) {
        div[data-testid="column"] { width: 100% !important; flex: 1 1 100% !important; }
        div[data-testid="stMetric"] { min-height: auto; }
        .stButton button, .stDownloadButton button, .stLinkButton a { width: 100%; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def render_metric(label: str, value: str, note: str = "") -> None:
    with st.container(border=True):
        st.metric(label, value)
        if note:
            st.caption(note)


def render_about_developer() -> None:
    st.subheader("About the Developer")
    with st.container(border=True):
        cols = st.columns([1.2, 1])
        with cols[0]:
            st.markdown("**Developer:** Abhay Chauhan")
            st.markdown("**Role:** AI Engineer")
            st.markdown("**Project:** Career Twin AI")
            st.caption("A production-focused AI career intelligence platform for resume analysis, career matching, roadmap generation, and digital twin simulation.")
        with cols[1]:
            st.markdown(
                """
                <div style="display:flex; gap:12px; flex-wrap:wrap;">
                    <a href="https://github.com/AbhayChauhan-coder" target="_blank"
                       style="display:flex; align-items:center; gap:8px; border:1px solid rgba(128,128,128,.35); border-radius:8px; padding:10px 12px; text-decoration:none;">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                            <path d="M12 .5A12 12 0 0 0 8.2 23.9c.6.1.8-.3.8-.6v-2.1c-3.3.7-4-1.4-4-1.4-.5-1.3-1.2-1.6-1.2-1.6-1-.7.1-.7.1-.7 1.1.1 1.7 1.2 1.7 1.2 1 .1.8 2.1 3.3 1.5.1-.7.4-1.2.7-1.5-2.6-.3-5.4-1.3-5.4-5.9 0-1.3.5-2.4 1.2-3.2-.1-.3-.5-1.6.1-3.2 0 0 1-.3 3.3 1.2a11.5 11.5 0 0 1 6 0C17.1 5.1 18 5.4 18 5.4c.6 1.6.2 2.9.1 3.2.8.8 1.2 1.9 1.2 3.2 0 4.6-2.8 5.6-5.4 5.9.4.4.8 1.1.8 2.2v3.3c0 .3.2.7.8.6A12 12 0 0 0 12 .5Z"/>
                        </svg>
                        <span>GitHub</span>
                    </a>
                    <a href="https://www.linkedin.com/in/abhay-chauhan-6b06a837a" target="_blank"
                       style="display:flex; align-items:center; gap:8px; border:1px solid rgba(128,128,128,.35); border-radius:8px; padding:10px 12px; text-decoration:none;">
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                            <path d="M20.4 20.4h-3.6v-5.6c0-1.3 0-3-1.8-3s-2.1 1.4-2.1 2.9v5.7H9.3V9h3.4v1.6h.1c.5-.9 1.6-1.8 3.3-1.8 3.6 0 4.3 2.4 4.3 5.4v6.2ZM5.2 7.4a2.1 2.1 0 1 1 0-4.2 2.1 2.1 0 0 1 0 4.2Zm1.8 13H3.4V9H7v11.4ZM22.2 0H1.8C.8 0 0 .8 0 1.8v20.4c0 1 .8 1.8 1.8 1.8h20.4c1 0 1.8-.8 1.8-1.8V1.8c0-1-.8-1.8-1.8-1.8Z"/>
                        </svg>
                        <span>LinkedIn</span>
                    </a>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_footer() -> None:
    st.divider()
    st.markdown(
        """
        <div style="padding: 18px 0 8px; text-align:center; opacity:.9;">
            <div style="font-weight:700;">Developed by Abhay Chauhan</div>
            <div style="font-size:0.95rem;">Aspiring AI Engineer | Career Twin AI Creator</div>
            <div style="margin-top:8px;">
                <a href="https://github.com/AbhayChauhan-coder" target="_blank" style="margin-right:14px; text-decoration:none;">GitHub</a>
                <a href="https://www.linkedin.com/in/abhay-chauhan-6b06a837a" target="_blank" style="text-decoration:none;">LinkedIn</a>
            </div>
            <div style="font-size:0.85rem; margin-top:8px;">© 2026 Career Twin AI. All Rights Reserved.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def github_username_from_url(value: str) -> str:
    cleaned = (value or "").strip().rstrip("/")
    if not cleaned:
        return ""
    cleaned = re.sub(r"^https?://", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^www\.", "", cleaned, flags=re.IGNORECASE)
    if cleaned.casefold().startswith("github.com/"):
        cleaned = cleaned.split("/", 1)[1]
    return re.split(r"[/#?]", cleaned, maxsplit=1)[0].strip()


def analyze_github_to_state(username: str, *, force: bool = False, source: str = "manual") -> bool:
    username = github_username_from_url(username)
    if not username:
        st.session_state.github_error = "Enter a GitHub username."
        st.session_state.pop("github_analysis", None)
        return False
    existing = st.session_state.get("github_analysis")
    existing_username = github_username_from_url(getattr(existing, "username", ""))
    if not force and existing and existing_username.casefold() == username.casefold():
        st.session_state.github_username = existing_username or username
        st.session_state.github_error = ""
        st.session_state.github_analysis_skipped = True
        return False
    analysis = analyze_github_profile(username)
    st.session_state.github_username = username
    st.session_state.github_analysis = analysis
    st.session_state.github_analysis_username = username
    st.session_state.github_analysis_source = source
    st.session_state.github_analysis_skipped = False
    st.session_state.github_error = ""
    return True


def build_dashboard_report(
    profile: UserProfile,
    readiness: dict[str, object],
    probability: int,
    country_intelligence: CountryCareerIntelligence,
    resume: ResumeParseResult | None,
    github_analysis: GitHubAnalysis | None,
    resume_match: ResumeMatchAnalysis | None,
    roadmap_items: list[dict[str, object]],
) -> dict[str, object]:
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "profile": {
            "name": profile.name,
            "degree": profile.degree,
            "branch": profile.branch,
            "current_year": profile.current_year,
            "career_goal": profile.career_goal,
            "target_country": profile.target_country,
            "weekly_study_hours": profile.weekly_study_hours,
            "skills": profile.skills,
            "projects": profile.projects,
            "certifications": profile.certifications,
            "experience": profile.internships,
            "languages": getattr(profile, "languages", []),
            "achievements": getattr(profile, "achievements", []),
        },
        "readiness": readiness,
        "success_probability": probability,
        "country_intelligence": country_intelligence.__dict__,
        "resume": {
            "status": resume.extraction_status,
            "detected_domain": resume.detected_domain,
            "current_designation": resume.current_designation,
            "strength_score": resume.strength_score,
            "skills": resume.skills,
        } if resume else None,
        "github": {
            "username": github_analysis.username,
            "score": github_analysis.github_score,
            "repositories": github_analysis.repository_count,
            "languages": github_analysis.language_counts,
        } if github_analysis else None,
        "resume_match": {
            "overall_match": resume_match.overall_match,
            "weighted_scores": resume_match.weighted_scores,
            "critical_missing_skills": resume_match.critical_missing_skills,
        } if resume_match else None,
        "roadmap": roadmap_items,
    }


def build_pdf_report(report: dict[str, object]) -> bytes:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PDF export requires PyMuPDF.") from exc

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    y = 48

    def write_line(text: str, size: int = 10, bold: bool = False) -> None:
        nonlocal y, page
        if y > 790:
            page = doc.new_page(width=595, height=842)
            y = 48
        font = "helv" if not bold else "helv"
        page.insert_text((48, y), text[:105], fontsize=size, fontname=font)
        y += size + 8

    profile = report["profile"]
    write_line("Career Twin AI - Dashboard Report", 18, True)
    write_line(f"Generated: {report['generated_at']}", 9)
    write_line("")
    write_line(f"Name: {profile['name'] or 'Not specified'}", 11)
    write_line(f"Career Goal: {profile['career_goal']} in {profile['target_country']}", 11)
    write_line(f"Readiness Score: {report['readiness']['score']}%", 11)
    write_line(f"Success Probability: {report['success_probability']}%", 11)
    write_line("")
    write_line("Matched Skills", 13, True)
    for item in report["readiness"].get("matched_skills", [])[:12]:
        write_line(f"- {item}")
    write_line("Missing Skills", 13, True)
    for item in report["readiness"].get("missing_skills", [])[:12]:
        write_line(f"- {item}")
    write_line("Country Intelligence", 13, True)
    country = report["country_intelligence"]
    for key in ["demand_level", "entry_salary", "mid_level_salary", "senior_salary", "visa_difficulty", "market_growth"]:
        write_line(f"{key.replace('_', ' ').title()}: {country.get(key, '')}")
    if report.get("github"):
        github = report["github"]
        write_line("GitHub Analysis", 13, True)
        write_line(f"Username: {github['username']}")
        write_line(f"Score: {github['score']}% | Repositories: {github['repositories']}")
    if report.get("resume_match"):
        match = report["resume_match"]
        write_line("Resume Match", 13, True)
        write_line(f"Overall Match: {match['overall_match']}%")
    write_line("Roadmap", 13, True)
    for item in report["roadmap"][:6]:
        write_line(f"{item['month']}: {item['focus']}")
        for week in item.get("weeks", [])[:4]:
            write_line(f"  {week['week']}: {week['milestone']}", 9)
    write_line("")
    write_line("Developed by Abhay Chauhan | Career Twin AI", 9)
    pdf = doc.tobytes()
    doc.close()
    return pdf


def render_ai_mentor_chat(context: dict[str, object]) -> None:
    st.session_state.setdefault("mentor_messages", [])

    with st.popover("AI Mentor Chat", use_container_width=True):
        st.caption("Personalized mentor using your resume, career goal, GitHub, country, roadmap, missing skills, and match scores.")
        quick_prompts = [
            "Review my resume.",
            "What should I learn next?",
            "Which certification should I do?",
            "Prepare interview questions.",
            "How can I increase my Resume Match Score?",
        ]
        if context.get("detected_domain") == "Technology":
            quick_prompts.insert(4, "Improve my GitHub.")
        selected_prompt = st.selectbox("Quick question", [""] + quick_prompts, key="mentor_quick_prompt")
        custom_prompt = st.text_area("Ask your mentor", value="", height=90, key="mentor_custom_prompt")

        if st.button("Ask Mentor", use_container_width=True):
            question = custom_prompt.strip() or selected_prompt.strip()
            if question:
                st.session_state.mentor_messages.append({"role": "user", "content": question})
                with st.spinner("Mentor is preparing a personalized answer..."):
                    answer = answer_mentor_question(question, context, st.session_state.mentor_messages)
                st.session_state.mentor_messages.append({"role": "assistant", "content": answer})
                st.success("Mentor response ready.")

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
        st.write(f"Detected Domain: {resume.detected_domain} ({round(resume.domain_confidence * 100)}%)")
        st.write(f"Current Designation: {confident_value(resume, 'current_designation', resume.current_designation)} ({confidence_pct(resume, 'current_designation')})")
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
        render_metric("AI/ML Projects", str(len(analysis.ai_ml_projects)), "Detected from repository names, topics, and descriptions.")
    with project_cols[1]:
        render_metric("Web Projects", str(len(analysis.web_projects)), "Detected from repository names, topics, and descriptions.")

    st.markdown("**Project Summary Cards**")
    render_project_summary_cards(analysis.repos)

    with st.expander("Recommendations", expanded=True):
        for recommendation in analysis.recommendations:
            st.write(f"- {recommendation}")


def render_github_cta() -> None:
    st.subheader("GitHub Profile Analysis")
    with st.container(border=True):
        st.markdown("**Connect your GitHub portfolio**")
        st.caption("Enter your GitHub username in the sidebar to analyze your actual public repositories, languages, project quality, and portfolio strength.")
        if st.session_state.get("github_error"):
            st.warning(st.session_state.github_error)


def render_resume_career_recommendations(
    profile: UserProfile,
    resume: ResumeParseResult | None,
    careers: dict[str, dict],
) -> None:
    if not resume:
        return
    recommendations = recommend_careers_for_profile(profile, resume, careers, limit=5)
    if not recommendations:
        return
    st.subheader("Top Career Recommendations From Resume")
    cols = st.columns(min(5, len(recommendations)))
    for column, recommendation in zip(cols, recommendations):
        with column:
            with st.container(border=True):
                st.metric(recommendation.career, f"{recommendation.fit_score}%")
                st.caption(recommendation.domain)
                st.write(recommendation.explanation)


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


def career_match_reason(match: dict[str, object]) -> str:
    matched = match.get("matched_skills", [])
    missing = match.get("missing_skills", [])
    reasons = []
    if matched:
        reasons.append(f"matches {len(matched)} required skill(s): {', '.join(matched[:3])}")
    if missing:
        reasons.append(f"still needs {', '.join(missing[:3])}")
    if not reasons:
        reasons.append("uses project, experience, certification, and study-hour signals")
    return "; ".join(reasons) + "."


def probability_factors(profile: UserProfile, readiness: dict[str, object]) -> tuple[list[str], list[str]]:
    positives = []
    gaps = []
    if readiness["matched_skills"]:
        positives.append(f"{len(readiness['matched_skills'])} matched skill(s)")
    if profile.project_count:
        positives.append(f"{profile.project_count} project signal(s)")
    else:
        gaps.append("add at least one role-specific project")
    if profile.internship_count:
        positives.append("experience or internship signal")
    else:
        gaps.append("add internship, freelance, lab, or volunteer experience")
    if profile.certification_count:
        positives.append("certification proof")
    if profile.weekly_study_hours >= 8:
        positives.append(f"{profile.weekly_study_hours} weekly study hours")
    elif profile.weekly_study_hours < 5:
        gaps.append("increase weekly study consistency")
    if readiness["missing_skills"]:
        gaps.append("close missing skills: " + ", ".join(readiness["missing_skills"][:4]))
    return positives or ["profile created successfully"], gaps or ["no major scoring blockers detected"]


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

    top_cols = st.columns(5)
    with top_cols[0]:
        render_metric("Demand", intelligence.demand_level, "Hiring appetite for this role.")
    with top_cols[1]:
        render_metric("Remote Jobs", intelligence.remote_jobs, "Remote and hybrid opportunity level.")
    with top_cols[2]:
        render_metric("Visa Difficulty", intelligence.visa_difficulty, "Directional mobility complexity.")
    with top_cols[3]:
        render_metric("Market Growth", intelligence.market_growth, "Expected sector momentum.")
    with top_cols[4]:
        render_metric("Future Demand", intelligence.demand_level, intelligence.future_demand)

    context_cols = st.columns(3)
    with context_cols[0]:
        render_metric("Cost of Living", intelligence.cost_of_living, "Planning context for relocation.")
    with context_cols[1]:
        render_metric("Career Growth", intelligence.career_growth, "Expected long-term market direction.")
    with context_cols[2]:
        render_metric("Interview Style", intelligence.interview_style, "Typical first-stage evaluation pattern.")

    salary_cols = st.columns(3)
    with salary_cols[0]:
        render_metric("Entry Salary", intelligence.entry_salary)
    with salary_cols[1]:
        render_metric("Mid-Level Salary", intelligence.mid_level_salary)
    with salary_cols[2]:
        render_metric("Senior Salary", intelligence.senior_salary)

    detail_cols = st.columns([1, 1, 1])
    with detail_cols[0]:
        st.markdown("**Most Required Skills**")
        render_skill_grid(intelligence.most_required_skills)
    with detail_cols[1]:
        st.markdown("**Top Hiring Companies**")
        render_pills(intelligence.top_hiring_companies)
    with detail_cols[2]:
        st.markdown("**Interview Process**")
        for step in intelligence.interview_process:
            st.write(f"- {step}")

    value_cols = st.columns(3)
    with value_cols[0]:
        st.markdown("**Most Valuable Certifications**")
        render_pills(intelligence.most_valuable_certifications)
    with value_cols[1]:
        if intelligence.most_valuable_programming_languages:
            st.markdown("**Most Valuable Programming Languages**")
            render_pills(intelligence.most_valuable_programming_languages)
        else:
            st.markdown("**Role-Specific Market Skills**")
            render_pills(intelligence.most_required_skills[:5])
    with value_cols[2]:
        if intelligence.most_valuable_frameworks:
            st.markdown("**Most Valuable Frameworks**")
            render_pills(intelligence.most_valuable_frameworks)
        else:
            st.markdown("**Professional Focus Areas**")
            render_pills(intelligence.interview_process[:4])

    with st.expander("Language Requirements"):
        render_pills(intelligence.language_requirements)

    with st.expander("Market Insights", expanded=True):
        st.markdown("**Market Insights**")
        for insight in intelligence.insights:
            st.write(f"- {insight}")
        st.caption("Salary and visa indicators are directional planning estimates, not legal or compensation advice.")


def render_universal_career_intelligence(
    profile: UserProfile,
    resume: ResumeParseResult | None,
    career_knowledge: dict[str, object],
    missing_skills: list[str],
) -> None:
    st.subheader("Universal Career Intelligence")
    detected_domain = getattr(resume, "detected_domain", "") if resume else ""
    domain_confidence = getattr(resume, "domain_confidence", 0.0) if resume else 0.0
    domain = detected_domain or str(career_knowledge.get("domain", "General"))

    intro_cols = st.columns(4)
    with intro_cols[0]:
        render_metric("Profession Domain", domain, f"{round(domain_confidence * 100)}% confidence" if resume else "Based on selected career.")
    with intro_cols[1]:
        render_metric("AI Impact", str(career_knowledge.get("future_growth", "Medium")), str(career_knowledge.get("ai_impact", ""))[:110])
    with intro_cols[2]:
        render_metric("Remote", str(career_knowledge.get("remote_opportunities", "Medium")), "Remote opportunity level.")
    with intro_cols[3]:
        render_metric("Freelance / Startup", f"{career_knowledge.get('freelance_opportunities', 'Medium')} / {career_knowledge.get('startup_opportunities', 'Medium')}")

    info_cols = st.columns(3)
    with info_cols[0]:
        st.markdown("**Degree Requirements**")
        render_pills(list(career_knowledge.get("degree_requirements", [])))
    with info_cols[1]:
        st.markdown("**Portfolio Requirements**")
        render_pills(list(career_knowledge.get("portfolio_requirements", [])))
    with info_cols[2]:
        st.markdown("**Most Demanded Cities**")
        render_pills(list(career_knowledge.get("most_demanded_cities", [])))

    profile_cols = st.columns(4)
    with profile_cols[0]:
        st.markdown("**Profession Skills**")
        render_pills(list(career_knowledge.get("required_skills", []))[:6])
    with profile_cols[1]:
        st.markdown("**Tools / Software**")
        tools = list(career_knowledge.get("tools", [])) + list(career_knowledge.get("software", []))
        render_pills(tools[:6])
    with profile_cols[2]:
        st.markdown("**Top Employers**")
        render_pills(list(career_knowledge.get("top_hiring_companies", career_knowledge.get("hiring_companies", [])))[:6])
    with profile_cols[3]:
        st.markdown("**Career Path**")
        render_pills(list(career_knowledge.get("career_path", []))[:5])

    cert_cols = st.columns(2)
    with cert_cols[0]:
        st.markdown("**Certifications**")
        render_pills(list(career_knowledge.get("certifications", career_knowledge.get("preferred_certifications", [])))[:6])
    with cert_cols[1]:
        st.markdown("**Interview Pattern**")
        render_pills(list(career_knowledge.get("interview_pattern", []))[:6])

    discovery_query = st.text_input(
        "Career discovery from interests",
        value=st.session_state.get("career_discovery_query", ""),
        placeholder="Example: I enjoy biology and coding",
    )
    st.session_state.career_discovery_query = discovery_query
    recommendations = discover_careers(discovery_query or profile.career_goal, profile)
    st.markdown("**Career Discovery Recommendations**")
    rec_cols = st.columns(min(4, max(1, len(recommendations))))
    for column, recommendation in zip(rec_cols, recommendations):
        with column:
            with st.container(border=True):
                st.metric(recommendation.career, f"{recommendation.fit_score}%")
                st.caption(recommendation.domain)
                st.write(recommendation.explanation)

    transition_background = st.text_input(
        "Career transition background",
        value=st.session_state.get("transition_background", profile.branch or profile.degree or domain),
        placeholder="Example: BCom, Mechanical Engineer, BA Psychology",
    )
    st.session_state.transition_background = transition_background
    transition = build_transition_plan(transition_background, profile.career_goal, profile)
    with st.expander("Career Transition Engine", expanded=True):
        transition_cols = st.columns(4)
        with transition_cols[0]:
            render_metric("Difficulty", transition["difficulty"], transition["why"])
        with transition_cols[1]:
            render_metric("Timeline", transition["timeline"])
        with transition_cols[2]:
            render_metric("Success Probability", f"{transition['success_probability']}%")
        with transition_cols[3]:
            render_metric("Expected Salary", str(transition["expected_salary"]))
        st.markdown("**Transition Roadmap**")
        for step in transition["roadmap"]:
            st.write(f"- {step}")
        st.markdown("**Required Certifications**")
        render_pills(transition["required_certifications"])

    learning = learning_recommendations(profile.career_goal, profile, missing_skills)
    with st.expander("Learning Recommendations", expanded=True):
        learning_cols = st.columns(3)
        for index, (label, values) in enumerate(learning.items()):
            with learning_cols[index % 3]:
                st.markdown(f"**{label.replace('_', ' ').title()}**")
                render_pills(values)

    interview = interview_preparation(profile.career_goal, profile)
    with st.expander("Interview Preparation", expanded=True):
        st.metric("Difficulty Level", interview["difficulty_level"])
        interview_cols = st.columns(3)
        sections = [
            ("HR Questions", interview["hr_questions"]),
            ("Technical / Role Questions", interview["technical_questions"]),
            ("Case Study Questions", interview["case_study_questions"]),
            ("Behavioral Questions", interview["behavioral_questions"]),
            ("Portfolio Review", interview["portfolio_review"]),
            ("Checklist", interview["checklist"]),
        ]
        for index, (label, values) in enumerate(sections):
            with interview_cols[index % 3]:
                st.markdown(f"**{label}**")
                render_pills(values)


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
        "AI": ["Not applicable", "INR 6-8 LPA", "INR 12-18 LPA", "INR 25-40 LPA", "INR 45-75 LPA"],
        "Data": ["Not applicable", "INR 5-7 LPA", "INR 10-16 LPA", "INR 22-35 LPA", "INR 38-60 LPA"],
        "Cybersecurity": ["Not applicable", "INR 5-8 LPA", "INR 12-20 LPA", "INR 24-38 LPA", "INR 42-65 LPA"],
        "Cloud": ["Not applicable", "INR 6-9 LPA", "INR 14-22 LPA", "INR 28-45 LPA", "INR 50-80 LPA"],
        "DevOps": ["Not applicable", "INR 6-9 LPA", "INR 14-24 LPA", "INR 30-48 LPA", "INR 55-85 LPA"],
        "Developer": ["Not applicable", "INR 4-7 LPA", "INR 10-18 LPA", "INR 22-38 LPA", "INR 40-70 LPA"],
        "Product": ["Not applicable", "INR 7-10 LPA", "INR 16-28 LPA", "INR 35-60 LPA", "INR 65-100 LPA"],
        "UX": ["Not applicable", "INR 4-7 LPA", "INR 10-16 LPA", "INR 20-32 LPA", "INR 35-55 LPA"],
    }
    for keyword, bands in salary_bands.items():
        if keyword.casefold() in career_goal.casefold():
            return bands[stage_index]
    return ["Not applicable", "INR 4-7 LPA", "INR 10-18 LPA", "INR 22-35 LPA", "INR 40-65 LPA"][stage_index]


def digital_twin_stages(
    profile: UserProfile,
    readiness: dict[str, object],
    probability: int,
    country_intelligence: CountryCareerIntelligence | None = None,
) -> list[dict[str, object]]:
    missing_skills = list(readiness.get("missing_skills", []))
    matched_skills = list(readiness.get("matched_skills", []))
    career_goal = profile.career_goal or "Target Career"
    current_role = profile.current_year if profile.current_year not in {"Not specified", "Not Specified"} else "Current You"

    staged_skills = [
        matched_skills[:4] or profile.skills[:4],
        missing_skills[:3] or matched_skills[:3] or ["Portfolio Building"],
        (missing_skills[:5] + ["Real Projects"])[:5] if missing_skills else matched_skills[:5],
        (missing_skills + ["Leadership", "System Design", "Mentoring"])[:6],
        (missing_skills + ["Architecture", "Strategy", "Leadership", "Mentoring", "Market Expertise"])[:7],
    ]
    confidence_scores = [
        max(10, min(readiness["score"], 100)),
        max(20, min(readiness["score"] + 18, 100)),
        max(35, min(probability, 100)),
        max(45, min(probability + 12, 100)),
        max(55, min(probability + 20, 100)),
    ]
    probability_scores = [
        max(5, min(probability - 20, 100)),
        max(10, min(probability - 5, 100)),
        max(20, min(probability, 100)),
        max(25, min(probability + 8, 100)),
        max(30, min(probability + 15, 100)),
    ]
    salary_ranges = projected_salary_ranges(career_goal, country_intelligence)

    return [
        {
            "label": "Current You",
            "role": current_role or "Student",
            "salary": salary_ranges[0],
            "skills": staged_skills[0],
            "career_stage": "Foundation",
            "confidence": confidence_scores[0],
            "probability": probability_scores[0],
            "salary_value": 0,
        },
        {
            "label": "1 Year Future",
            "role": f"{career_goal.split()[0]} Intern" if career_goal else "Career Intern",
            "salary": salary_ranges[1],
            "skills": staged_skills[1],
            "career_stage": "Internship Ready",
            "confidence": confidence_scores[1],
            "probability": probability_scores[1],
            "salary_value": salary_midpoint(salary_ranges[1]),
        },
        {
            "label": "3 Year Future",
            "role": career_goal,
            "salary": salary_ranges[2],
            "skills": staged_skills[2],
            "career_stage": "Early Professional",
            "confidence": confidence_scores[2],
            "probability": probability_scores[2],
            "salary_value": salary_midpoint(salary_ranges[2]),
        },
        {
            "label": "5 Year Future",
            "role": f"Senior {career_goal}",
            "salary": salary_ranges[3],
            "skills": staged_skills[3],
            "career_stage": "Advanced Contributor",
            "confidence": confidence_scores[3],
            "probability": probability_scores[3],
            "salary_value": salary_midpoint(salary_ranges[3]),
        },
        {
            "label": "10 Year Future",
            "role": f"Lead / Principal {career_goal}",
            "salary": salary_ranges[4],
            "skills": staged_skills[4],
            "career_stage": "Leadership Track",
            "confidence": confidence_scores[4],
            "probability": probability_scores[4],
            "salary_value": salary_midpoint(salary_ranges[4]),
        },
    ]


def projected_salary_ranges(career_goal: str, country_intelligence: CountryCareerIntelligence | None) -> list[str]:
    if not country_intelligence:
        return [salary_range_for_stage(career_goal, index) for index in range(5)]
    senior_mid = salary_midpoint(country_intelligence.senior_salary)
    ten_year_salary = f"{country_intelligence.senior_salary}+" if senior_mid else salary_range_for_stage(career_goal, 4)
    return [
        "Not applicable",
        country_intelligence.entry_salary,
        country_intelligence.mid_level_salary,
        country_intelligence.senior_salary,
        ten_year_salary,
    ]


def render_digital_twin(
    profile: UserProfile,
    readiness: dict[str, object],
    probability: int,
    country_intelligence: CountryCareerIntelligence | None = None,
) -> None:
    st.header("🚀 Your Digital Twin")
    st.caption("A projected career timeline based on your current profile, selected goal, skills, and readiness score.")

    stages = digital_twin_stages(profile, readiness, probability, country_intelligence)
    selected_stage_label = st.radio(
        "Explore timeline stage",
        [str(stage["label"]) for stage in stages],
        horizontal=True,
        label_visibility="collapsed",
    )
    for index, stage in enumerate(stages):
        with st.container(border=True):
            top_cols = st.columns([1.2, 2, 1])
            with top_cols[0]:
                st.caption(str(stage["label"]))
                st.subheader(str(stage["role"]))
            with top_cols[1]:
                st.markdown(f"**Salary Estimate:** {stage['salary']}")
                st.markdown(f"**Career Stage:** {stage['career_stage']}")
                skills = stage["skills"] or ["No skills detected yet"]
                st.markdown("**Skills Acquired:** " + ", ".join(str(skill) for skill in skills))
            with top_cols[2]:
                st.metric("Confidence Score", f"{stage['confidence']}%")
                st.progress(int(stage["confidence"]) / 100)
                st.metric("Probability", f"{stage['probability']}%")
                st.progress(int(stage["probability"]) / 100)
            if stage["label"] == selected_stage_label:
                st.info(f"Selected stage: {stage['label']} - focus on {', '.join(str(skill) for skill in (stage['skills'] or [])[:3])}.")

        if index < len(stages) - 1:
            arrow_cols = st.columns([1, 1, 1])
            with arrow_cols[1]:
                next_stage = stages[index + 1]["label"]
                st.markdown(f"**Progresses to {next_stage}**")
                st.progress((index + 1) / (len(stages) - 1))
                st.markdown("### ↓")

    salary_data = pd.DataFrame(
        [
            {"Stage": stage["label"], "Projected Salary Midpoint": stage["salary_value"]}
            for stage in stages
            if int(stage["salary_value"]) > 0
        ]
    )
    if not salary_data.empty:
        st.markdown("**Salary Graph**")
        chart = (
            alt.Chart(salary_data)
            .mark_line(point=True)
            .encode(
                x=alt.X("Stage:N", sort=None),
                y=alt.Y("Projected Salary Midpoint:Q"),
                tooltip=["Stage", "Projected Salary Midpoint"],
            )
        )
        st.altair_chart(chart, use_container_width=True)


def render_roadmap(items: list[dict[str, object]]) -> None:
    for item in items:
        with st.expander(f"{item['month']}: {item['focus']}", expanded=item["month"] in {"Month 1", "Month 2"}):
            for task in item["tasks"]:
                st.write(f"- {task}")
            if item.get("weeks"):
                st.markdown("**Weekly Milestones**")
                for week in item["weeks"]:
                    st.write(f"- **{week['week']}**: {week['milestone']}")
            st.success(str(item["outcome"]))


def render_profile_form(careers: dict[str, dict], autofill: dict[str, object], submit_label: str) -> bool:
    career_options = sorted(careers.keys())
    default_career_index = career_options.index("AI Engineer") if "AI Engineer" in career_options else 0
    gpa_value = str(autofill.get("gpa") or "")
    current_year_options = ["Not Specified", "1st Year", "2nd Year", "3rd Year", "4th Year", "Graduate", "Professional"]
    autofill_current_year = str(autofill.get("current_year") or "Not Specified")
    current_year_index = current_year_options.index(autofill_current_year) if autofill_current_year in current_year_options else 0

    with st.sidebar.expander("Education", expanded=True):
        name = st.text_input("Name", value=str(autofill.get("name") or ""))
        age_text = st.text_input("Age", value=str(autofill.get("age") or ""), placeholder="Not Specified")
        degree = st.text_input("Degree", value=str(autofill.get("degree") or ""))
        branch = st.text_input("Branch", value=str(autofill.get("branch") or ""))
        current_year = st.selectbox("Current Year", current_year_options, index=current_year_index)
        gpa_text = st.text_input("GPA / CGPA", value=gpa_value, placeholder="Not Specified")
    with st.sidebar.expander("Skills", expanded=True):
        skills = st.text_area("Skills", value=str(autofill.get("skills") or ""), help="Use commas or new lines.")
    with st.sidebar.expander("Projects"):
        projects = st.text_area("Projects", value=str(autofill.get("projects") or ""))
    with st.sidebar.expander("Experience"):
        internships = st.text_area("Experience / Internships", value=str(autofill.get("internships") or ""))
    with st.sidebar.expander("Certifications"):
        certifications = st.text_area("Certifications", value=str(autofill.get("certifications") or ""))
    with st.sidebar.expander("Languages"):
        languages = st.text_area("Languages", value=str(autofill.get("languages") or ""))
    with st.sidebar.expander("Achievements"):
        achievements = st.text_area("Achievements", value=str(autofill.get("achievements") or ""))
    with st.sidebar.expander("Career Preferences", expanded=True):
        weekly_study_hours = st.slider("Weekly Study Hours", min_value=0, max_value=40, value=0)
        career_query = st.text_input("Search Career Goal", value="", placeholder="Try fina, soft, audit, teach")
        suggested_careers = career_search_suggestions(career_query, careers, limit=80) if career_query.strip() else career_options
        if "AI Engineer" in suggested_careers:
            suggested_index = suggested_careers.index("AI Engineer")
        elif suggested_careers:
            suggested_index = 0
        else:
            suggested_careers = career_options
            suggested_index = default_career_index
        career_goal = st.selectbox("Career Goal", suggested_careers, index=suggested_index)
        target_country = st.selectbox("Target Country", SUPPORTED_COUNTRIES, index=0)
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
            languages=split_multiline_or_csv(languages),
            achievements=split_multiline_or_csv(achievements),
            weekly_study_hours=int(weekly_study_hours),
            career_goal=career_goal,
            target_country=target_country.strip(),
        )
        if submitted:
            st.session_state.profile_created = True

    return submitted


def clear_resume_state(clear_profile: bool = True, clear_github: bool = True) -> None:
    keys = [
        "profile",
        "profile_created",
        "resume_parse",
        "resume_autofill",
        "resume_error",
        "resume_file_key",
        "github_username",
        "github_analysis",
        "github_error",
        "github_analysis_username",
        "github_analysis_source",
        "github_analysis_skipped",
    ]
    if not clear_profile:
        keys.remove("profile")
    if not clear_github:
        for key in [
            "github_username",
            "github_analysis",
            "github_error",
            "github_analysis_username",
            "github_analysis_source",
            "github_analysis_skipped",
        ]:
            keys.remove(key)
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
                clear_resume_state(clear_github=False)
                st.session_state.resume_file_key = current_file_key

        if uploaded_resume and st.sidebar.button("Analyze Resume", use_container_width=True):
            try:
                current_file_key = uploaded_file_key(uploaded_resume)
                clear_resume_state(clear_github=False)
                st.session_state.resume_file_key = current_file_key
                with st.spinner("Parsing resume and extracting profile..."):
                    resume = parse_uploaded_resume(uploaded_resume, careers)
                st.session_state.resume_parse = resume
                if resume.extraction_status == "Failed":
                    st.session_state.resume_error = "Resume extraction failed. No usable fields were detected."
                    st.sidebar.error(st.session_state.resume_error)
                else:
                    st.session_state.resume_autofill = resume.autofill()
                    st.sidebar.success("Resume Analysis Complete")
                    extracted_username = github_username_from_url(resume.github)
                    if extracted_username:
                        try:
                            with st.spinner(f"Analyzing GitHub profile `{extracted_username}`..."):
                                did_analyze = analyze_github_to_state(extracted_username, force=False, source="resume")
                            if did_analyze:
                                st.sidebar.success("GitHub analysis complete.")
                            else:
                                st.sidebar.info("GitHub analysis already exists for this username.")
                        except RuntimeError as exc:
                            st.session_state.github_username = extracted_username
                            st.session_state.github_error = str(exc)
                            st.sidebar.warning(f"GitHub analysis needs attention: {exc}")
                st.rerun()
            except RuntimeError as exc:
                clear_resume_state(clear_github=False)
                st.session_state.resume_error = str(exc)
                st.sidebar.error(str(exc))
            except Exception:
                clear_resume_state(clear_github=False)
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
                st.write(f"Detected Domain: {display_value(resume.detected_domain)} ({round(resume.domain_confidence * 100)}%)")
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
        clear_resume_state(clear_profile=False, clear_github=False)
        st.sidebar.subheader("Manual Entry")
        render_profile_form(careers, {}, "Generate Career Twin")

    st.sidebar.divider()
    st.sidebar.subheader("GitHub Profile Analysis")
    github_username = st.sidebar.text_input("GitHub Username", value=st.session_state.get("github_username", ""))
    if st.sidebar.button("Analyze GitHub", use_container_width=True):
        try:
            with st.spinner("Analyzing GitHub repositories..."):
                analyze_github_to_state(github_username, force=True, source="manual")
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
        if st.session_state.get("github_analysis"):
            st.divider()
            render_github_analysis(st.session_state.github_analysis)
        else:
            st.divider()
            render_github_cta()
        render_about_developer()
        render_footer()
        return

    selected_career = careers[profile.career_goal]
    career_knowledge = get_career_knowledge(profile.career_goal, selected_career)
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
    mentor_context["career_knowledge"] = career_knowledge
    mentor_context["detected_domain"] = getattr(resume, "detected_domain", career_knowledge.get("domain", "General")) if resume else career_knowledge.get("domain", "General")

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

    report = build_dashboard_report(
        profile,
        readiness,
        probability,
        country_intelligence,
        resume,
        github_analysis,
        resume_match,
        roadmap_items,
    )
    with st.expander("Download Report"):
        export_cols = st.columns(2)
        with export_cols[0]:
            try:
                st.download_button(
                    "Download PDF Report",
                    data=build_pdf_report(report),
                    file_name="career_twin_report.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except RuntimeError as exc:
                st.warning(str(exc))
        with export_cols[1]:
            st.download_button(
                "Download JSON Export",
                data=json.dumps(report, indent=2, default=str),
                file_name="career_twin_export.json",
                mime="application/json",
                use_container_width=True,
            )

    st.divider()
    render_digital_twin(profile, readiness, probability, country_intelligence)
    st.divider()
    render_country_intelligence(country_intelligence)
    st.divider()

    render_universal_career_intelligence(profile, resume, career_knowledge, readiness["missing_skills"])
    st.divider()

    if resume:
        render_resume_insights(resume, readiness["missing_skills"])
        st.divider()
        render_resume_career_recommendations(profile, resume, careers)
        st.divider()

    if resume and resume_match:
        render_resume_match_score(resume_match, resume, careers)
        st.divider()

    if github_analysis:
        render_github_analysis(github_analysis)
        st.divider()
    else:
        render_github_cta()
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
                st.caption("Why: " + career_match_reason(match))

    st.divider()

    with st.spinner("Generating career probability reasoning..."):
        explanation = generate_explanation(profile, readiness)
    with st.container():
        st.subheader("Career Probability Reasoning")
        positive_factors, improvement_factors = probability_factors(profile, readiness)
        factor_cols = st.columns(2)
        with factor_cols[0]:
            st.markdown("**Positive Factors**")
            render_pills(positive_factors)
        with factor_cols[1]:
            st.markdown("**Score Constraints**")
            render_pills(improvement_factors)
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
    with st.spinner("Generating future simulation notes..."):
        gemini_future = generate_future_simulation(profile, readiness)
    with st.expander("Classic timeline summary"):
        render_timeline(fallback_future(profile, readiness["score"]))
    if gemini_future:
        with st.expander("AI future notes"):
            render_clean_response(gemini_future)

    st.divider()

    st.subheader("AI Career Roadmap")
    with st.spinner("Generating AI roadmap notes..."):
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

    render_about_developer()
    render_footer()


if __name__ == "__main__":
    main()
