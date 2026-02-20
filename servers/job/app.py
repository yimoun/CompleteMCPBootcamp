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
    keywords_prompt,
)
from src.ui_helpers import clean_mermaid_code, normalize_mermaid, mermaid_image_url

load_dotenv()

st.set_page_config(page_title="Job Recommender", layout="wide")
st.title("📄AI Job Recommender")
st.markdown("Upload your resume and get job recommendations based on your skills and experience from free job APIs.")

uploaded_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"])

if uploaded_file:
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

    with st.spinner("Summarizing your resume..."):
        summary = ask_groq(summary_prompt(resume_text), max_tokens=500)

    
    with st.spinner("Finding skill Gaps..."):
        gaps = ask_groq(gaps_prompt(resume_text), max_tokens=400)


    with st.spinner("Creating Future Roadmap..."):
        roadmap = ask_groq(roadmap_prompt(resume_text), max_tokens=400)

    with st.spinner("Creating Visual Roadmap..."):
        roadmap_mermaid = ask_groq(roadmap_mermaid_prompt(resume_text), max_tokens=500)
        roadmap_mermaid = normalize_mermaid(clean_mermaid_code(roadmap_mermaid))
        if roadmap_mermaid:
            print("[Mermaid Roadmap]\n", roadmap_mermaid)
            print("[Mermaid Image URL]\n", mermaid_image_url(roadmap_mermaid))
    
    # Display nicely formatted results
    st.markdown("---")
    st.header("📑 Resume Summary")
    st.markdown(f"<div style='background-color: #000000; padding: 15px; border-radius: 10px; font-size:16px; color:white;'>{summary}</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.header("🛠️ Skill Gaps & Missing Areas")
    st.markdown(f"<div style='background-color: #000000; padding: 15px; border-radius: 10px; font-size:16px; color:white;'>{gaps}</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.header("🚀 Future Roadmap & Preparation Strategy")
    st.markdown(f"<div style='background-color: #000000; padding: 15px; border-radius: 10px; font-size:16px; color:white;'>{roadmap}</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.header("🗺️ Visual Roadmap (Mermaid)")
    if roadmap_mermaid:
        render_mermaid_svg(roadmap_mermaid)
    else:
        st.warning("Mermaid vide. Vérifie le prompt ou la réponse du modèle.")

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



