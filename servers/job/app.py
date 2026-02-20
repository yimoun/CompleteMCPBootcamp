import streamlit as st
from src.helper import extract_text_from_pdf, ask_groq
from src.job_api import fetch_remote_jobs

st.set_page_config(page_title="Job Recommender", layout="wide")
st.title("📄AI Job Recommender")
st.markdown("Upload your resume and get job recommendations based on your skills and experience from free job APIs.")

uploaded_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"])

if uploaded_file:
    with st.spinner("Extracting text from your resume..."):
        resume_text = extract_text_from_pdf(uploaded_file)

    with st.spinner("Summarizing your resume..."):
        summary = ask_groq(f"Summarize this resume highlighting the skills, edcucation, and experience: \n\n{resume_text}", max_tokens=500)

    
    with st.spinner("Finding skill Gaps..."):
        gaps = ask_groq(f"Analyze this resume and highlight missing skills, certifications, and experiences needed for better job opportunities: \n\n{resume_text}", max_tokens=400)


    with st.spinner("Creating Future Roadmap..."):
        roadmap = ask_groq(f"Based on this resume, suggest a future roadmap to improve this person's career prospects (Skill to learn, certification needed, industry exposure): \n\n{resume_text}", max_tokens=400)
    
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

    st.success("✅ Analysis Completed Successfully!")


    if "job_keywords" not in st.session_state:
        st.session_state.job_keywords = ""
    if "linkedin_jobs" not in st.session_state:
        st.session_state.linkedin_jobs = []
    if "linkedin_error" not in st.session_state:
        st.session_state.linkedin_error = None

    def fetch_jobs_only():
        if not st.session_state.job_keywords:
            return
        with st.spinner("Fetching jobs from free job APIs..."):
            linkedin_jobs, linkedin_error = fetch_remote_jobs(
                st.session_state.job_keywords,
                location=st.session_state.location,
                rows=60,
            )
        st.session_state.linkedin_jobs = linkedin_jobs or []
        st.session_state.linkedin_error = linkedin_error

    col_location, col_button = st.columns([1, 2])
    with col_location:
        st.text_input(
            "Preferred location (city/country)",
            value="Worldwide",
            key="location",
            on_change=fetch_jobs_only,
        )
    with col_button:
        st.markdown("<div style='margin-top: 26px;'></div>", unsafe_allow_html=True)
        get_jobs_clicked = st.button("🔎Get Job Recommendations")

    if get_jobs_clicked:
        with st.spinner("Fetching job recommendations..."):
            keywords = ask_groq(
                "Based on this resume summary, suggest the best job titles and keywords for searching jobs. "
                "Give a comma-separated list only, no explanation.\n\nSummary: "
                f"{summary}",
                max_tokens=100,
            )
            st.session_state.job_keywords = keywords.replace("\n", "").strip()

        st.success(f"Extracted Job Keywords: {st.session_state.job_keywords}")
        fetch_jobs_only()

    if st.session_state.job_keywords:
        st.success(f"Extracted Job Keywords: {st.session_state.job_keywords}")

        st.markdown("---")
        st.header("💼 Top Remotive Jobs (Remote)")

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



