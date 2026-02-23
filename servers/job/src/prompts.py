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
        "Generate a Mermaid flowchart roadmap with EXACT structure and consistent node IDs. "
        "Use this skeleton and ONLY replace the text inside brackets [] (keep IDs):\n"
        "graph LR\n"
        "  subgraph 0-3 months\n"
        "    A1[Skill 1] --> A2[Certification 1]\n"
        "    A3[Project 1] --> A4[Milestone 1]\n"
        "  end\n"
        "  subgraph 3-6 months\n"
        "    B1[Skill 2] --> B2[Certification 2]\n"
        "    B3[Project 2] --> B4[Milestone 2]\n"
        "    B5[Experience 1] --> B6[Outcome 1]\n"
        "  end\n"
        "  subgraph 6-12 months\n"
        "    C1[Skill 3] --> C2[Certification 3]\n"
        "    C3[Project 3] --> C4[Milestone 3]\n"
        "    C5[Networking 1] --> C6[Outcome 2]\n"
        "  end\n"
        "  A2 --> B1\n"
        "  A4 --> B3\n"
        "  B2 --> C1\n"
        "  B4 --> C3\n"
        "  B6 --> C5\n"
        "Rules: keep IDs, no quotes, no edge labels, output ONLY Mermaid code.\n\n"
        f"Resume:\n{resume_text}"
    )


def roadmap_mermaid_labels_prompt(resume_text: str) -> str:
    return (
        "Extract concrete roadmap labels from this resume. Return JSON ONLY with keys "
        "A1,A2,A3,A4,B1,B2,B3,B4,B5,B6,C1,C2,C3,C4,C5,C6. "
        "Each value must be a short, specific label (no placeholders like 'Skill 1'). "
        "If missing, invent a reasonable, resume-relevant item. "
        "No extra keys, no markdown.\n\nResume:\n"
        f"{resume_text}"
    )


def roadmap_mermaid_labels_from_roadmap_prompt(roadmap_text: str) -> str:
    return (
        "Extract concrete roadmap labels from this roadmap text. Return JSON ONLY with keys "
        "A1,A2,A3,A4,B1,B2,B3,B4,B5,B6,C1,C2,C3,C4,C5,C6. "
        "Each value must be a short, specific label (no placeholders like 'Skill 1'). "
        "If missing, invent a reasonable, roadmap-consistent item. "
        "No extra keys, no markdown.\n\nRoadmap:\n"
        f"{roadmap_text}"
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
