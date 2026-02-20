
# Job Recommender (Remote)

Application Streamlit qui analyse un CV (PDF), génère un résumé et un plan d’amélioration via Groq, puis propose des offres **remote** depuis des APIs gratuites (Remotive).

## ✅ Fonctionnalités actuelles

- Upload de CV (PDF) et extraction du texte
- Résumé automatique du CV
- Analyse des gaps de compétences
- Roadmap d’amélioration
- Recommandations d’emplois **remote uniquement**
- Mise à jour des jobs quand la location change (sans relancer Groq)
- MCP server minimal pour exposer l’outil de recherche d’emplois

## 🧩 Structure

- [app.py](app.py) : UI Streamlit
- [src/job_api.py](src/job_api.py) : appels à l’API Remotive
- [src/helper.py](src/helper.py) : extraction PDF + appel Groq
- [mcp_server.py](mcp_server.py) : serveur MCP (tool de jobs)

## ▶️ Lancer en local

1. Installer les dépendances
	- `pip install -r requirements.txt`
2. Créer un `.env` avec la clé Groq (ex: `GROQ_API_KEY=...`)
3. Lancer l’app
	- `streamlit run app.py`

## 🧪 MCP Server (local)

- `python mcp_server.py`

## 📌 Notes

- Les jobs sont **remote uniquement** (Remotive). Les villes entrées servent à affiner la recherche, mais ne garantissent pas un périmètre géographique strict.

