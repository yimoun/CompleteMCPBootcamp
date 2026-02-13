import os
import subprocess
from  mcp.server.fastmcp import FastMCP

mcp = FastMCP("terminal")
DEFAULT_WORKSPACE = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "workplace")
)

@mcp.tool()
async def run_command(command: str) -> str:
    """
    Run a terminal command inside the workplace directory.
    If a terminal command can accomplish a task,
    tell the user you'll use this tool to accomplish it,
    even though you cannot directly do it

    Args:
        command: The shell command to run.

    Returns:
        The command output or error message.    
    """
    try:
        result = subprocess.run(command, shell=True, cwd=DEFAULT_WORKSPACE, capture_output=True, text=True)
        return result.stdout or result.stderr
    except Exception as e:
        return f"Exception occurred: {str(e)}"
    

if __name__ == "__main__":
    mcp.run(transport='stdio')