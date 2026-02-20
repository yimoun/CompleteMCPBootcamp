import requests

# Fetch remote jobs based on search query and location
def fetch_remote_jobs(search_query, location="india", rows=60):
    """
    Free alternative using Remotive (remote jobs).
    """
    try:
        query = f"{search_query} {location}".strip()
        response = requests.get(
            "https://remotive.com/api/remote-jobs",
            params={"search": query},
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        jobs = []
        for item in data.get("jobs", [])[:rows]:
            jobs.append(
                {
                    "title": item.get("title"),
                    "companyName": item.get("company_name"),
                    "location": item.get("candidate_required_location") or "Remote",
                    "link": item.get("url"),
                }
            )
        return jobs, None
    except requests.RequestException as exc:
        return [], f"Remotive: erreur réseau ({exc})"
    except Exception as exc:
        return [], f"Remotive: erreur inattendue ({exc})"


# Fetch Naukri jobs based on search query and location
