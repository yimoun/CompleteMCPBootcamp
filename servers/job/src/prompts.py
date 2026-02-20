def summary_prompt(resume_text: str) -> str:
    return (
        "Summarize this resume highlighting the skills, education, and experience:\n\n"
        f"{resume_text}"
    )


def gaps_prompt(resume_text: str) -> str:
    return (
        "Analyze this resume and highlight missing skills, certifications, and experiences needed "
        "for better job opportunities:\n\n"
        f"{resume_text}"
    )


def roadmap_prompt(resume_text: str) -> str:
    return (
        "Based on this resume, suggest a future roadmap to improve this person's career prospects "
        "(skills to learn, certifications needed, industry exposure):\n\n"
        f"{resume_text}"
    )


def roadmap_mermaid_prompt(resume_text: str) -> str:
    return (
        "Generate a Mermaid flowchart roadmap with phases (0-3 months, 3-6 months, 6-12 months). "
        "Use nodes for skills, certifications, projects, and milestones. Keep it concise. "
        "Output only Mermaid code.\n\n"
        f"Resume:\n{resume_text}"
    )


def keywords_prompt(summary_text: str) -> str:
    return (
        "Based on this resume summary, suggest the best job titles and keywords for searching jobs. "
        "Give a comma-separated list only, no explanation.\n\nSummary: "
        f"{summary_text}"
    )


def profile_extract_prompt(resume_text: str) -> str:
    return (
        "Extract a structured resume profile as JSON with this schema: "
        "{\"name\":string|null,\"seniority\":string,\"years_experience\":number|null,"
        "\"roles\":[string],\"skills\":[string],\"domains\":[string],"
        "\"tools\":[string],\"languages\":[string],\"education\":[string],"
        "\"certifications\":[string],\"remote_preference\":string}. "
        "Return JSON only.\n\nResume:\n"
        f"{resume_text}"
    )


def career_gap_prompt(profile_json: str, target_role: str) -> str:
    return (
        "Given the candidate profile JSON and target role, return JSON with: "
        "{\"target_role\":string,\"gaps\":[string],\"recommended_skills\":[string],"
        "\"recommended_certifications\":[string],\"projects\":[string]}. "
        "Return JSON only.\n\nProfile:\n"
        f"{profile_json}\n\nTarget role: {target_role}"
    )


def job_match_prompt(profile_json: str, jobs_json: str) -> str:
    return (
        "Given a candidate profile JSON and a list of job objects, return JSON with the top 5 matches. "
        "Schema: {\"matches\":[{\"title\":string,\"company\":string,\"score\":number,"
        "\"reasons\":[string]}]}. Return JSON only.\n\nProfile:\n"
        f"{profile_json}\n\nJobs:\n{jobs_json}"
    )
