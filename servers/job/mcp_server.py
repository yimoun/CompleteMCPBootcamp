from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP 
from src.ai_tools import analyze_career_gaps, extract_resume_profile, rank_jobs
from src.job_api import fetch_remote_jobs 

load_dotenv()

mcp = FastMCP("Job Recommender")

@mcp.tool()
async def fetch_remote_jobs(listofkey):
    return fetch_remote_jobs(listofkey)


@mcp.tool()
async def extract_profile(resume_text: str):
    return extract_resume_profile(resume_text)


@mcp.tool()
async def match_jobs(profile: dict, jobs: list):
    return rank_jobs(profile, jobs)


@mcp.tool()
async def analyze_gaps(profile: dict, target_role: str):
    return analyze_career_gaps(profile, target_role)

if __name__ == "__main__":
    mcp.run(transport='stdio')