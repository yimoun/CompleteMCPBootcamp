import html
import json
import re
from concurrent.futures import ThreadPoolExecutor
import requests
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from src.helper import extract_text_from_pdf, ask_groq
from src.job_api import fetch_remote_jobs, fetch_jooble_jobs
from src.prompts import (
    summary_prompt,
    gaps_prompt,
    roadmap_prompt,
    roadmap_mermaid_prompt,
    roadmap_mermaid_labels_prompt,
    roadmap_mermaid_labels_from_roadmap_prompt,
    keywords_prompt,
)
from src.ui_helpers import (
    build_mermaid_from_labels,
    clean_mermaid_code,
    normalize_mermaid,
    mermaid_image_url,
)

load_dotenv()

st.set_page_config(page_title="Job Recommender", layout="wide")
st.title("📄AI Job Recommender")
st.markdown("Upload your resume and get job recommendations based on your skills and experience from free job APIs.")

MAX_PDF_SIZE_MB = 10
uploaded_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"])

if uploaded_file and uploaded_file.size > MAX_PDF_SIZE_MB * 1024 * 1024:
    st.error(f"File too large ({uploaded_file.size // 1024 // 1024} MB). Maximum is {MAX_PDF_SIZE_MB} MB.")
    uploaded_file = None

if uploaded_file:
    def extract_json_object(text: str) -> str:
        if not text:
            return ""
        match = re.search(r"\{[\s\S]*\}", text)
        return match.group(0) if match else ""

    def labels_have_placeholders(labels: dict) -> bool:
        placeholders = {
            "skill 1", "skill 2", "skill 3",
            "certification 1", "certification 2", "certification 3",
            "project 1", "project 2", "project 3",
            "milestone 1", "milestone 2", "milestone 3",
            "experience 1", "outcome 1", "outcome 2", "networking 1",
        }
        for value in labels.values():
            if isinstance(value, str):
                normalized = " ".join(value.lower().split())
                if normalized in placeholders:
                    return True
        return False

    def render_mermaid_svg(mermaid_code: str) -> None:
        try:
            response = requests.post(
                "https://kroki.io/mermaid/svg",
                data=mermaid_code.encode("utf-8"),
                headers={"Content-Type": "text/plain"},
                timeout=15,
            )
            response.raise_for_status()
            components.html(response.text, height=520, scrolling=True)
        except requests.RequestException as exc:
            st.warning(f"Mermaid render fallback: {exc}")
            st.image(mermaid_image_url(mermaid_code), use_container_width=True)


    with st.spinner("Extracting text from your resume..."):
        resume_text = extract_text_from_pdf(uploaded_file)

    with st.spinner("Analyzing your resume (summary, gaps, roadmap)..."):
        with ThreadPoolExecutor(max_workers=3) as pool:
            future_summary = pool.submit(ask_groq, summary_prompt(resume_text), 500)
            future_gaps = pool.submit(ask_groq, gaps_prompt(resume_text), 400)
            future_roadmap = pool.submit(ask_groq, roadmap_prompt(resume_text), 400)
        summary = future_summary.result()
        gaps = future_gaps.result()
        roadmap = future_roadmap.result()

    with st.spinner("Creating Visual Roadmap..."):
        labels_prompt = roadmap_mermaid_labels_from_roadmap_prompt(roadmap)
        labels_raw = ask_groq(labels_prompt, max_tokens=500)
        labels_json = extract_json_object(labels_raw)
        labels = {}
        if labels_json:
            try:
                labels = json.loads(labels_json)
            except json.JSONDecodeError:
                labels = {}

        labels_used = bool(labels and not labels_have_placeholders(labels))
        if labels_used:
            roadmap_mermaid_raw = ""
            roadmap_mermaid_clean = ""
            roadmap_mermaid = build_mermaid_from_labels(labels)
            mermaid_prompt = labels_prompt
        else:
            mermaid_prompt = roadmap_mermaid_prompt(resume_text)
            roadmap_mermaid_raw = ask_groq(mermaid_prompt, max_tokens=500)
            roadmap_mermaid_clean = clean_mermaid_code(roadmap_mermaid_raw)
            roadmap_mermaid = normalize_mermaid(roadmap_mermaid_clean)
        if roadmap_mermaid:
            print("[Mermaid Roadmap]\n", roadmap_mermaid)
            print("[Mermaid Image URL]\n", mermaid_image_url(roadmap_mermaid))
    
    # Display nicely formatted results
    st.markdown("---")
    st.header("📑 Resume Summary")
    st.markdown(f"<div style='background-color: #000000; padding: 15px; border-radius: 10px; font-size:16px; color:white;'>{html.escape(summary or '')}</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.header("🛠️ Skill Gaps & Missing Areas")
    st.markdown(f"<div style='background-color: #000000; padding: 15px; border-radius: 10px; font-size:16px; color:white;'>{html.escape(gaps or '')}</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.header("🚀 Future Roadmap & Preparation Strategy")
    st.markdown(f"<div style='background-color: #000000; padding: 15px; border-radius: 10px; font-size:16px; color:white;'>{html.escape(roadmap or '')}</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.header("🗺️ Visual Roadmap (Mermaid)")
    if roadmap_mermaid:
        render_mermaid_svg(roadmap_mermaid)
    else:
        st.warning("Mermaid vide. Vérifie le prompt ou la réponse du modèle.")

    with st.expander("🔎 Debug Mermaid", expanded=False):
        st.caption("Ces infos aident à voir pourquoi les labels ne sont pas remplacés.")
        st.text(f"resume_text length: {len(resume_text or '')}")
        st.text(f"labels_used: {labels_used}")
        st.text_area("resume_text (début)", (resume_text or "")[:800], height=160)
        st.text_area("labels_prompt", labels_prompt, height=240)
        st.text_area("labels_raw", labels_raw or "", height=240)
        st.text_area("labels_json", labels_json or "", height=200)
        st.text_area("roadmap_mermaid_prompt", mermaid_prompt, height=260)
        st.text_area("ask_groq raw output", roadmap_mermaid_raw or "", height=260)
        st.text_area("clean_mermaid_code output", roadmap_mermaid_clean or "", height=220)
        st.text_area("normalize_mermaid output", roadmap_mermaid or "", height=220)
        st.code(roadmap_mermaid or "", language="mermaid")

    st.success("✅ Analysis Completed Successfully!")


    if "job_keywords" not in st.session_state:
        st.session_state.job_keywords = ""
    if "linkedin_jobs" not in st.session_state:
        st.session_state.linkedin_jobs = []
    if "linkedin_error" not in st.session_state:
        st.session_state.linkedin_error = None
    if "jooble_jobs" not in st.session_state:
        st.session_state.jooble_jobs = []
    if "jooble_error" not in st.session_state:
        st.session_state.jooble_error = None

    def fetch_jobs_only():
        if not st.session_state.job_keywords:
            return
        with st.spinner("Fetching jobs from free job APIs..."):
            linkedin_jobs, linkedin_error = fetch_remote_jobs(
                st.session_state.job_keywords,
                location=st.session_state.location,
                rows=60,
            )
            jooble_jobs, jooble_error = fetch_jooble_jobs(
                st.session_state.get("jooble_keywords", st.session_state.job_keywords),
                location=st.session_state.location,
                rows=60,
            )
        st.session_state.linkedin_jobs = linkedin_jobs or []
        st.session_state.linkedin_error = linkedin_error
        st.session_state.jooble_jobs = jooble_jobs or []
        st.session_state.jooble_error = jooble_error

    col_location, col_button = st.columns([1, 2])
    with col_location:
        st.text_input(
            "Preferred location (city/country)",
            value="Saguenay",
            key="location",
            on_change=fetch_jobs_only,
        )
    with col_button:
        st.markdown("<div style='margin-top: 26px;'></div>", unsafe_allow_html=True)
        get_jobs_clicked = st.button("🔎Get Job Recommendations")

    if get_jobs_clicked:
        with st.spinner("Fetching job recommendations..."):
            keywords = ask_groq(keywords_prompt(summary), max_tokens=100)
            search_keywords_clean = keywords.replace("\n", "").strip()
            st.session_state.job_keywords = search_keywords_clean
            st.session_state.jooble_keywords = " OR ".join(
                [k.strip() for k in search_keywords_clean.split(",") if k.strip()]
            )

        st.success(f"Extracted Job Keywords: {st.session_state.job_keywords}")
        fetch_jobs_only()

    if st.session_state.job_keywords:
        st.success(f"Extracted Job Keywords: {st.session_state.job_keywords}")
        if "jooble_keywords" in st.session_state and st.session_state.jooble_keywords:
            st.caption(f"Jooble query: {st.session_state.jooble_keywords}")

        st.markdown("---")
        col_remote, col_local = st.columns(2)

        with col_remote:
            st.subheader("💼 Top Remotive Jobs (Remote)")
            remote_box = st.container(height=520)
            with remote_box:
                if st.session_state.linkedin_error:
                    st.error(st.session_state.linkedin_error)

                if st.session_state.linkedin_jobs:
                    for job in st.session_state.linkedin_jobs:
                        st.markdown(f"**{job.get('title')}** at *{job.get('companyName')}*")
                        st.markdown(f"- 📍 {job.get('location')}")
                        st.markdown(f"- 🔗 [View Job]({job.get('link')})")
                        st.markdown("---")
                else:
                    st.warning("No Remotive jobs found.")

        with col_local:
            st.subheader("💼 Jooble Jobs (Local/Location-based)")
            local_box = st.container(height=520)
            with local_box:
                if st.session_state.jooble_error:
                    st.error(st.session_state.jooble_error)

                if st.session_state.jooble_jobs:
                    for job in st.session_state.jooble_jobs:
                        st.markdown(f"**{job.get('title')}** at *{job.get('companyName')}*")
                        st.markdown(f"- 📍 {job.get('location')}")
                        st.markdown(f"- 🔗 [View Job]({job.get('link')})")
                        st.markdown("---")
                else:
                    st.warning("No Jooble jobs found.")



