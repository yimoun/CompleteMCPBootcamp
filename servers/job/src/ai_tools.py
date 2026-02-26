import json
import re
from typing import Any, Dict, List

from src.helper import ask_groq
from src.prompts import (
    profile_extract_prompt,
    career_gap_prompt,
    job_match_prompt,
    job_classify_prompt,
    roadmap_mermaid_prompt,
)


def _extract_json(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    for match in re.finditer(r"(\{[\s\S]*?\}|\[[\s\S]*?\])", text):
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            continue
    return None


def extract_resume_profile(resume_text: str) -> Dict[str, Any]:
    response = ask_groq(profile_extract_prompt(resume_text), max_tokens=700)
    data = _extract_json(response)
    if data is None:
        return {"error": "invalid_json", "raw": response}
    return data


def analyze_career_gaps(profile: Dict[str, Any], target_role: str) -> Dict[str, Any]:
    profile_json = json.dumps(profile, ensure_ascii=False)
    response = ask_groq(career_gap_prompt(profile_json, target_role), max_tokens=700)
    data = _extract_json(response)
    if data is None:
        return {"error": "invalid_json", "raw": response}
    return data


def rank_jobs(profile: Dict[str, Any], jobs: List[Dict[str, Any]]) -> Dict[str, Any]:
    profile_json = json.dumps(profile, ensure_ascii=False)
    jobs_json = json.dumps(jobs, ensure_ascii=False)
    response = ask_groq(job_match_prompt(profile_json, jobs_json), max_tokens=700)
    data = _extract_json(response)
    if data is None:
        return {"error": "invalid_json", "raw": response}
    return data


def _strip_code_fences(text: str) -> str:
    """Remove markdown ```json ... ``` wrappers."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return text.strip()


def classify_jobs(
    profile_summary: str,
    jobs: List[Dict[str, Any]],
    user_location: str = "",
) -> Dict[str, Any]:
    """Classify jobs as Remote or Presentiel and add a relevance note."""
    # Send only essential fields to reduce token usage
    slim_jobs = [
        {
            "title": j.get("title"),
            "companyName": j.get("companyName"),
            "location": j.get("location"),
            "link": j.get("link"),
            "_source": j.get("_source"),
            "_is_remote": j.get("_is_remote", False),
        }
        for j in jobs
    ]
    jobs_json = json.dumps(slim_jobs, ensure_ascii=False)
    response = ask_groq(
        job_classify_prompt(profile_summary, jobs_json, user_location),
        max_tokens=4000,
    )

    # Strip markdown code fences
    cleaned = _strip_code_fences(response or "")

    # Try full parse first
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict) and "classified_jobs" in data:
            return data
    except (json.JSONDecodeError, TypeError):
        pass

    # Greedy regex to capture the outermost JSON object
    match = re.search(r"\{[\s\S]*\}", cleaned)
    if match:
        try:
            data = json.loads(match.group(0))
            if isinstance(data, dict) and "classified_jobs" in data:
                return data
        except (json.JSONDecodeError, TypeError):
            pass

    return {"error": "invalid_json", "raw": response}


def build_roadmap_mermaid(resume_text: str) -> str:
    return ask_groq(roadmap_mermaid_prompt(resume_text), max_tokens=500).strip()
