import html
import json
import re
from concurrent.futures import ThreadPoolExecutor
import requests
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv
from src.helper import extract_text_from_pdf, ask_groq
from src.job_api import fetch_remote_jobs, fetch_jooble_jobs, fetch_jsearch_jobs
from src.ai_tools import classify_jobs
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
    if "jsearch_jobs" not in st.session_state:
        st.session_state.jsearch_jobs = []
    if "jsearch_error" not in st.session_state:
        st.session_state.jsearch_error = None
    if "classified_remote" not in st.session_state:
        st.session_state.classified_remote = []
    if "classified_presentiel" not in st.session_state:
        st.session_state.classified_presentiel = []
    if "classification_error" not in st.session_state:
        st.session_state.classification_error = None

    def fetch_jobs_only():
        if not st.session_state.job_keywords:
            return
        location = st.session_state.location

        keywords_list = [k.strip() for k in st.session_state.job_keywords.split(",") if k.strip()]

        with st.spinner("Fetching jobs from Remotive, Jooble, and JSearch..."):
            with ThreadPoolExecutor(max_workers=8) as pool:
                # Remotive = remote jobs, NO location (adding a city kills results)
                future_remotive = pool.submit(
                    fetch_remote_jobs,
                    st.session_state.job_keywords,
                    location="",
                    rows=20,
                )
                # Jooble = location-based
                future_jooble = pool.submit(
                    fetch_jooble_jobs,
                    st.session_state.get("jooble_keywords", st.session_state.job_keywords),
                    location=location,
                    rows=20,
                )
                # JSearch = one call PER keyword for broad coverage
                jsearch_futures = [
                    pool.submit(fetch_jsearch_jobs, kw, location=location, rows=10)
                    for kw in keywords_list[:3]
                ]

            remotive_jobs, remotive_err = future_remotive.result()
            jooble_jobs, jooble_err = future_jooble.result()

            # Merge all JSearch results
            jsearch_jobs = []
            jsearch_errors = []
            for fut in jsearch_futures:
                jobs_batch, err = fut.result()
                jsearch_jobs.extend(jobs_batch or [])
                if err:
                    jsearch_errors.append(err)
            jsearch_err = jsearch_errors[0] if jsearch_errors else None

        st.session_state.linkedin_jobs = remotive_jobs or []
        st.session_state.linkedin_error = remotive_err
        st.session_state.jooble_jobs = jooble_jobs or []
        st.session_state.jooble_error = jooble_err
        st.session_state.jsearch_jobs = jsearch_jobs or []
        st.session_state.jsearch_error = jsearch_err

        # Store raw data for debug
        st.session_state._debug_remotive = {"jobs": remotive_jobs or [], "error": remotive_err}
        st.session_state._debug_jooble = {"jobs": jooble_jobs or [], "error": jooble_err}
        st.session_state._debug_jsearch = {"jobs": jsearch_jobs or [], "error": jsearch_err}

        # Merge all jobs
        all_jobs = (remotive_jobs or []) + (jooble_jobs or []) + (jsearch_jobs or [])

        if not all_jobs:
            st.session_state.classified_remote = []
            st.session_state.classified_presentiel = []
            st.session_state.classification_error = "Aucun emploi trouve."
            return

        # Deduplicate by (title, company)
        seen = set()
        unique_jobs = []
        for job in all_jobs:
            key = (
                (job.get("title") or "").lower().strip(),
                (job.get("companyName") or "").lower().strip(),
            )
            if key not in seen:
                seen.add(key)
                unique_jobs.append(job)

        # LLM classification
        with st.spinner("Classification des offres (Remote vs Presentiel)..."):
            result = classify_jobs(summary, unique_jobs, user_location=location)

        def _is_remote_category(cat):
            return (cat or "").strip().lower() == "remote"

        def _heuristic_classify(jobs):
            remote_list, presentiel_list = [], []
            for job in jobs:
                loc = (job.get("location") or "").lower()
                is_remote = job.get("_is_remote", False)
                if is_remote or "remote" in loc or "anywhere" in loc or "worldwide" in loc:
                    remote_list.append({**job, "category": "Remote", "relevance": ""})
                else:
                    presentiel_list.append({**job, "category": "Presentiel", "relevance": ""})
            return remote_list, presentiel_list

        st.session_state._classify_debug = result  # for debug expander

        if "error" in result:
            st.session_state.classification_error = (
                "Classification LLM echouee, fallback heuristique utilise."
            )
            r, p = _heuristic_classify(unique_jobs)
            st.session_state.classified_remote = r
            st.session_state.classified_presentiel = p
        else:
            classified = result.get("classified_jobs", [])
            if not classified:
                # LLM returned valid JSON but empty list — use heuristic
                st.session_state.classification_error = (
                    "LLM a retourne une liste vide, fallback heuristique utilise."
                )
                r, p = _heuristic_classify(unique_jobs)
                st.session_state.classified_remote = r
                st.session_state.classified_presentiel = p
            else:
                st.session_state.classified_remote = [
                    j for j in classified if _is_remote_category(j.get("category"))
                ]
                st.session_state.classified_presentiel = [
                    j for j in classified if not _is_remote_category(j.get("category"))
                ]
                st.session_state.classification_error = None

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

        # Show per-source fetch errors as non-blocking warnings
        for err_key in ("linkedin_error", "jooble_error", "jsearch_error"):
            err = st.session_state.get(err_key)
            if err:
                st.warning(err)

        if st.session_state.classification_error:
            st.warning(st.session_state.classification_error)

        # Source counts
        remotive_count = len(st.session_state.linkedin_jobs)
        jooble_count = len(st.session_state.jooble_jobs)
        jsearch_count = len(st.session_state.jsearch_jobs)
        st.caption(
            f"Sources: Remotive ({remotive_count}), "
            f"Jooble ({jooble_count}), JSearch ({jsearch_count})"
        )

        with st.expander("🔎 Debug Classification", expanded=False):
            st.text(f"classified_remote count: {len(st.session_state.classified_remote)}")
            st.text(f"classified_presentiel count: {len(st.session_state.classified_presentiel)}")

            st.subheader("Remotive (raw)")
            debug_remotive = st.session_state.get("_debug_remotive", {})
            if debug_remotive.get("error"):
                st.error(debug_remotive["error"])
            st.text_area(
                f"remotive_jobs ({len(debug_remotive.get('jobs', []))} jobs)",
                json.dumps(debug_remotive.get("jobs", [])[:5], indent=2, ensure_ascii=False),
                height=200,
            )

            st.subheader("Jooble (raw)")
            debug_jooble = st.session_state.get("_debug_jooble", {})
            if debug_jooble.get("error"):
                st.error(debug_jooble["error"])
            st.text_area(
                f"jooble_jobs ({len(debug_jooble.get('jobs', []))} jobs)",
                json.dumps(debug_jooble.get("jobs", [])[:5], indent=2, ensure_ascii=False),
                height=200,
            )

            st.subheader("JSearch (raw)")
            debug_jsearch = st.session_state.get("_debug_jsearch", {})
            if debug_jsearch.get("error"):
                st.error(debug_jsearch["error"])
            st.text_area(
                f"jsearch_jobs ({len(debug_jsearch.get('jobs', []))} jobs)",
                json.dumps(debug_jsearch.get("jobs", [])[:5], indent=2, ensure_ascii=False),
                height=200,
            )

            st.subheader("LLM Classification result")
            debug_classify = st.session_state.get("_classify_debug", {})
            st.text_area(
                "classify_jobs() return value",
                json.dumps(debug_classify, indent=2, ensure_ascii=False)[:4000]
                if isinstance(debug_classify, (dict, list))
                else str(debug_classify)[:4000],
                height=300,
            )

        st.markdown("---")
        col_remote, col_local = st.columns(2)

        with col_remote:
            st.subheader("🌐 Remote")
            remote_box = st.container(height=520)
            with remote_box:
                if st.session_state.classified_remote:
                    for job in st.session_state.classified_remote:
                        source = job.get("_source") or job.get("source", "")
                        st.markdown(
                            f"**{job.get('title')}** at *{job.get('companyName')}*"
                            f"  `[{source}]`"
                        )
                        st.markdown(f"- 📍 {job.get('location')}")
                        if job.get("relevance"):
                            st.markdown(f"- 💡 {job.get('relevance')}")
                        st.markdown(f"- 🔗 [View Job]({job.get('link')})")
                        st.markdown("---")
                else:
                    st.warning("Aucun emploi remote trouve.")

        with col_local:
            st.subheader("🏢 Presentiel")
            local_box = st.container(height=520)
            with local_box:
                if st.session_state.classified_presentiel:
                    for job in st.session_state.classified_presentiel:
                        source = job.get("_source") or job.get("source", "")
                        st.markdown(
                            f"**{job.get('title')}** at *{job.get('companyName')}*"
                            f"  `[{source}]`"
                        )
                        st.markdown(f"- 📍 {job.get('location')}")
                        if job.get("relevance"):
                            st.markdown(f"- 💡 {job.get('relevance')}")
                        st.markdown(f"- 🔗 [View Job]({job.get('link')})")
                        st.markdown("---")
                else:
                    st.warning("Aucun emploi presentiel trouve.")



