import json
import re
from typing import Any, Dict, List

from src.helper import ask_groq
from src.prompts import (
    profile_extract_prompt,
    career_gap_prompt,
    job_match_prompt,
    roadmap_mermaid_prompt,
)


def _extract_json(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"(\{[\s\S]*\}|\[[\s\S]*\])", text)
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
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


def build_roadmap_mermaid(resume_text: str) -> str:
    return ask_groq(roadmap_mermaid_prompt(resume_text), max_tokens=500).strip()
