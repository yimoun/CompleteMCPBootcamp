from apify_client import ApifyClient
from apify_client._errors import ApifyApiError
import os
from dotenv import load_dotenv

load_dotenv()

APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
LINKEDIN_ACTOR_ID = os.getenv("APIFY_LINKEDIN_ACTOR_ID", "apify/linkedin-jobs-scraper")
NAUKRI_ACTOR_ID = os.getenv("APIFY_NAUKRI_ACTOR_ID", "apify/naukri-jobs-scraper")

apify_client = ApifyClient(APIFY_API_TOKEN) if APIFY_API_TOKEN else None

# Fetch LinkedIn jobs based on search query and location
def fetch_linkedin_jobs(search_query, location="india", rows=60):
    if not apify_client:
        return [], "APIFY_API_TOKEN manquant..."
    run_input = {
            "title": search_query,
            "location": location,
            "rows": rows,
            "proxy": {
                "useApifyProxy": True,
                "apifyProxyGroups": ["RESIDENTIAL"],
            }
        }
    try:
        run = apify_client.actor(LINKEDIN_ACTOR_ID).call(run_input=run_input)
        jobs = list(apify_client.dataset(run["defaultDatasetId"]).iterate_items())
        return jobs, None
    except ApifyApiError as exc:
        return [], f"LinkedIn: {exc}"
    except Exception as exc:
        return [], f"LinkedIn: erreur inattendue ({exc})"


# Fetch Naukri jobs based on search query and location
def fetch_naukri_jobs(search_query, location="india", rows=60):
    if not apify_client:
        return [], "APIFY_API_TOKEN manquant..."
    run_input = {
        "keyword": search_query,
        "maxJobs": 60,
        "freshness": "all",
        "sortBy": "relevance",
        "experience": "all",
    }
    try:
        run = apify_client.actor(NAUKRI_ACTOR_ID).call(run_input=run_input)
        jobs = list(apify_client.dataset(run["defaultDatasetId"]).iterate_items())
        return jobs, None
    except ApifyApiError as exc:
        return [], f"Naukri: {exc}"
    except Exception as exc:
        return [], f"Naukri: erreur inattendue ({exc})"
