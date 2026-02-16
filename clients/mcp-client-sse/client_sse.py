"""
client_sse.py

This file implements an MCP client that connects to an MCP server using SSE (Server-Sent Events) transport.
SSE is a technology that allows a server to push real-time updates to a client over a single, persistent HTTP connection.
Unlike websockets, SSE provides one-way communication from the server to the client, which is useful for streaming updates.

This client uses Groq for AI model integration. Groq can perform natural language processing
tasks and, when needed, call external tools (in this case, MCP tools) to perform specific functions.

A stream manager (or stream context) in this code is responsible for managing the lifecycle of the SSE connection,
ensuring that the connection is properly opened and closed. We use asynchronous context managers to handle these resources safely.
"""

import asyncio            # For asynchronous programming
import os                 # For accessing environment variables
import sys                # For command-line argument handling
import json               # For JSON processing
from typing import Optional  # For type annotations, e.g., indicating that a variable may be None

# Import ClientSession from the MCP package. This object manages communication with the MCP server.
from mcp import ClientSession

# Import the SSE client helper. This is assumed to be an asynchronous context manager that provides the connection streams.
# These streams represent the channels over which data is sent and received via SSE.
from mcp.client.sse import sse_client

# Import Groq client for AI-based function calling and natural language processing.
from groq import Groq

# Import dotenv to load environment variables from a .env file (e.g., API keys).
from dotenv import load_dotenv

# Load environment variables from the .env file so that our API keys and other settings are available.
load_dotenv()


class MCPClient:
    def __init__(self):
        """
        Initialize the MCP client.

        This constructor sets up:
         - The Groq client using an API key from the environment variables.
         - Placeholders for the client session and the stream context (which manages the SSE connection).

        The Groq client is used to generate content (e.g., processing user queries) and can request to call tools.
        """
        # Placeholder for the MCP session that will manage communication with the MCP server.
        self.session: Optional[ClientSession] = None
        
        # These will hold our context managers for the SSE connection.
        self._streams_context = None  # Manages the SSE stream lifecycle
        self._session_context = None  # Manages the MCP session lifecycle

        # Retrieve the Groq API key from environment variables.
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY not found. Please add it to your .env file.")

        # Initialize the Groq client with the API key.
        self.groq_client = Groq(api_key=groq_api_key)

    async def connect_to_sse_server(self, server_url: str):
        """
        Connect to an MCP server that uses SSE transport.
        
        Steps performed in this function:
         1. Open an SSE connection using the provided server URL.
         2. Use the connection streams to create an MCP ClientSession.
         3. Initialize the MCP session, which sets up the protocol for communication.
         4. Retrieve and display the list of available tools from the MCP server.
        
        Args:
            server_url (str): The URL of the MCP server that supports SSE.
        """
        # 1. Open an SSE connection to the server.
        #    The sse_client function returns an async context manager that yields the streams (data channels) for communication.
        self._streams_context = sse_client(url=server_url)
        # Enter the asynchronous context to get the streams. This ensures proper resource management.
        streams = await self._streams_context.__aenter__()
        # 'streams' is expected to be a tuple (like (reader, writer)) that the ClientSession can use.

        # 2. Create an MCP ClientSession using the streams provided by the SSE connection.
        #    The ClientSession object handles sending and receiving messages following the MCP protocol.
        self._session_context = ClientSession(*streams)
        self.session: ClientSession = await self._session_context.__aenter__()

        # 3. Initialize the MCP session.
        #    This step typically sends an initialization message to the server to negotiate capabilities and start the protocol.
        await self.session.initialize()

        # 4. Retrieve and list available tools from the MCP server.
        #    This helps confirm that the connection is working and shows what functions or tools are available.
        print("Initialized SSE client...")
        print("Listing tools...")
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

        # Convert the MCP tool definitions to a format compatible with the Groq API for function calling.
        self.tool_definitions = convert_mcp_tools_to_groq(tools)

    async def cleanup(self):
        """
        Clean up resources by properly closing the SSE session and stream contexts.
        
        As we used asynchronous context managers (which are like 'with' blocks for async code), we need to manually call their exit methods.
        This ensures that all network connections and resources are gracefully closed when the client is finished.
        """
        # If the MCP session context was created, exit it to close the session.
        if self._session_context:
            await self._session_context.__aexit__(None, None, None)
        # If the SSE stream context was created, exit it to close the underlying SSE connection.
        if self._streams_context:
            await self._streams_context.__aexit__(None, None, None)

    async def process_query(self, query: str) -> str:
        """
        Process a user query using the Groq API. If Groq requests a tool call (via function calling),
        this function will call the tool on the MCP server and send the result back to Gemini for a final response.
        
        Steps:
         1. Format the user's query as a chat message.
         2. Send the query to Groq and include available MCP tool declarations.
         3. Check if Groq's response contains a function call; if so, execute the tool and send back the response.
         4. Return the final processed text from Groq.
        
        Args:
            query (str): The input query from the user.
        
        Returns:
            str: The final text response generated by the Gemini model.
        """
        messages = [{"role": "user", "content": query}]

        # 2. Send the query to the Groq model.
        response = self.groq_client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            messages=messages,
            tools=self.tool_definitions,
            tool_choice="auto",
        )

        assistant_message = response.choices[0].message
        tool_calls = assistant_message.tool_calls or []

        # If Groq didn't request tool calls, return its response.
        if not tool_calls:
            return assistant_message.content or ""

        # Add the assistant tool call message.
        messages.append(
            {
                "role": "assistant",
                "content": assistant_message.content or "",
                "tool_calls": [
                    {
                        "id": call.id,
                        "type": "function",
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments,
                        },
                    }
                    for call in tool_calls
                ],
            }
        )

        # Execute requested tool calls and append results.
        for call in tool_calls:
            tool_name = call.function.name
            try:
                tool_args = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                tool_args = {}

            print(f"\n[Groq requested tool call: {tool_name} with args {tool_args}]")

            try:
                result = await self.session.call_tool(tool_name, tool_args)
                tool_result_text = stringify_tool_result(result)
            except Exception as e:
                tool_result_text = f"Tool error: {e}"

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": tool_result_text,
                }
            )

        # Send tool results back to Groq for a final response.
        final_response = self.groq_client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
            messages=messages,
            tools=self.tool_definitions,
        )

        return final_response.choices[0].message.content or ""

    async def chat_loop(self):
        """
        Run an interactive chat loop in the terminal.
        
        This function allows the user to type queries one after the other. The loop continues until the user types 'quit'.
        Each query is processed using the process_query method, and the response is printed to the console.
        """
        print("\nMCP Client Started! Type 'quit' to exit.")

        while True:
            # Prompt the user to enter a query.
            query = input("\nQuery: ").strip()
            if query.lower() == 'quit':
                break  # Exit the loop if the user types 'quit'

            # Process the query through the Gemini model and MCP server tool calls.
            response = await self.process_query(query)
            # Print the final response.
            print("\n" + response)


def clean_schema(schema):
    """
    Recursively remove 'title' fields from a JSON schema.
    
    Some JSON schemas include a 'title' field that is not needed for our tool function calls.
    This function goes through the schema and removes any 'title' entries, including nested ones.
    
    Args:
        schema (dict): A dictionary representing a JSON schema.
    
    Returns:
        dict: The cleaned JSON schema without any 'title' fields.
    """
    if isinstance(schema, dict):
        # Remove the 'title' key if it exists.
        schema.pop("title", None)
        # If the schema has a "properties" key (common in JSON schemas) and it's a dict, process each property.
        if "properties" in schema and isinstance(schema["properties"], dict):
            for key in schema["properties"]:
                schema["properties"][key] = clean_schema(schema["properties"][key])
    return schema


def convert_mcp_tools_to_groq(mcp_tools):
    """
    Convert MCP tool definitions into Groq-compatible tool declarations.

    Args:
        mcp_tools (list): A list of MCP tool objects with attributes 'name', 'description', and 'inputSchema'.

    Returns:
        list: A list of tool definitions compatible with Groq function calling.
    """
    groq_tools = []

    for tool in mcp_tools:
        parameters = clean_schema(tool.inputSchema)
        groq_tools.append(
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": parameters,
                },
            }
        )

    return groq_tools


def stringify_tool_result(result) -> str:
    """
    Convert an MCP CallToolResult into a text payload suitable for Groq tool responses.
    """
    if hasattr(result, "content") and result.content:
        parts = []
        for content in result.content:
            text = getattr(content, "text", None)
            if text:
                parts.append(text)
        if parts:
            return "\n".join(parts)

    structured = getattr(result, "structuredContent", None)
    if structured is not None:
        return json.dumps(structured)

    return str(result)


async def main():
    """
    Main entry point for the client.
    
    This function:
     - Checks that a server URL is provided as a command-line argument.
     - Creates an instance of MCPClient.
     - Connects to the MCP server via SSE.
     - Enters an interactive chat loop to process user queries.
     - Cleans up all resources (like the SSE connection) when finished.
    
    Usage:
        python client_sse.py <server_url>
    """
    if len(sys.argv) < 2:
        print("Usage: python client_sse.py <server_url>")
        sys.exit(1)

    client = MCPClient()
    try:
        # Connect to the MCP server using the provided SSE URL.
        await client.connect_to_sse_server(sys.argv[1])
        # Start the interactive chat loop for user queries.
        await client.chat_loop()
    finally:
        # Ensure that all resources and network connections are properly closed.
        await client.cleanup()

if __name__ == "__main__":
    # Run the main function using the asyncio event loop.
    asyncio.run(main())
