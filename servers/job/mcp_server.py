from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP 
from src.ai_tools import analyze_career_gaps, extract_resume_profile, rank_jobs, classify_jobs
from src.job_api import fetch_remote_jobs, fetch_jooble_jobs, fetch_jsearch_jobs

load_dotenv()

mcp = FastMCP("Job Recommender")

@mcp.tool()
async def fetch_remote(search_query: str, location: str = "", rows: int = 60):
    """Fetch job listings from Remotive, Jooble, and JSearch APIs."""
    remote_jobs, remote_err = fetch_remote_jobs(search_query, location=location, rows=rows)
    jooble_jobs, jooble_err = fetch_jooble_jobs(search_query, location=location, rows=rows)
    jsearch_jobs, jsearch_err = fetch_jsearch_jobs(search_query, location=location, rows=rows)
    return {
        "remote_jobs": remote_jobs,
        "jooble_jobs": jooble_jobs,
        "jsearch_jobs": jsearch_jobs,
        "errors": [e for e in (remote_err, jooble_err, jsearch_err) if e],
    }


@mcp.tool()
async def extract_profile(resume_text: str):
    """Extract a structured profile (skills, experience, education) from resume text."""
    return extract_resume_profile(resume_text)


@mcp.tool()
async def match_jobs(profile: dict, jobs: list):
    """Rank a list of jobs against a candidate profile and return top matches."""
    return rank_jobs(profile, jobs)


@mcp.tool()
async def analyze_gaps(profile: dict, target_role: str):
    """Identify skill gaps and recommend certifications for a target role."""
    return analyze_career_gaps(profile, target_role)

if __name__ == "__main__":
    mcp.run(transport='stdio')