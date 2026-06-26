# Career Twin AI

Career Twin AI is a Streamlit career dashboard that creates a digital profile of a student or early professional, compares it against target career requirements, and shows a personalized route forward.

## Features

- Career readiness score calculated locally from skills, projects, internships, certifications, and weekly study hours
- Skill gap analysis for the selected career goal
- Success probability estimate with reasoning
- Alternative career match engine
- 1-year, 3-year, and 5-year future simulation
- Six-month roadmap and weekly action plan
- Optional Google Gemini generation for explanations, roadmap text, and future simulation
- SQLite snapshot storage
- PDF resume upload with PyMuPDF text extraction
- Resume strength score, extracted skills, and resume insights

## Setup

```bash
pip install -r requirements.txt
```

Add your Gemini key to `.env` if you want AI-generated narrative output:

```bash
GEMINI_API_KEY=your_key_here
```

The app still works without a key by using local fallback guidance.

## Run

```bash
streamlit run app.py
```

## Project Structure

```text
app.py
services/
  career_engine.py
  gemini_service.py
database/
  db.py
models/
  user.py
prompts/
  career_prompt.py
  future_prompt.py
  roadmap_prompt.py
data/
  careers.json
assets/
requirements.txt
README.md
.env
```
