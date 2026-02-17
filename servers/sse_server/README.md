docker build -t terminal_server_sse .

docker run --rm -p 8081:8081 -v C:/Users/AC/mcp/workspace:/root/mcp/workspace terminal_server_sse


docker run --rm -p 8081:8081 -v /Users/nelsonjunioryimounoubissi/Downloads/CompleteMCPBootcamp/workplace:/workplace terminal_server_sse


uv run client_sse.py http://3.148.190.68:8081/sse