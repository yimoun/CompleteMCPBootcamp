
# Job MCP Server (Docker)

## Docker local

Build:
- `docker build -t job-mcp-server .`

Run:
- `docker run --rm -e GROQ_API_KEY=... -e JOOBLE_API_KEY=... job-mcp-server`

## AWS (EC2) – quick path

1) Copier le projet sur l’instance ou cloner le repo
2) Installer Docker
3) Build l’image:
	- `docker build -t job-mcp-server .`
4) Lancer le container:
	- `docker run -d --name job-mcp-server \
		-e GROQ_API_KEY=... \
		-e JOOBLE_API_KEY=... \
		job-mcp-server`

## Notes

- Ce container exécute `mcp_server.py` (transport stdio).
- Pour un MCP host distant, il faudra exposer un transport HTTP/SSE dans une étape suivante.
