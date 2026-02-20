from mcp.server.fastmcp import FastMCP 
from src.job_api import fetch_remote_jobs 

mcp = FastMCP("Job Recommender")

@mcp.tool()
async def fetchlinkedin(listofkey):
    return fetch_remote_jobs(listofkey)

if __name__ == "__main__":
    mcp.run(transport='stdio')