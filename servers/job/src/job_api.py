import os
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


def fetch_jooble_jobs(search_query, location="", rows=60):
    """
    Location-based jobs using Jooble API. Requires JOOBLE_API_KEY.
    """
    api_key = os.getenv("JOOBLE_API_KEY")
    debug = os.getenv("JOOBLE_DEBUG", "").lower() in {"1", "true", "yes"}
    if not api_key:
        return [], "Jooble: JOOBLE_API_KEY manquant."

    try:
        keywords = search_query or ""
        if "," in keywords:
            keywords = " OR ".join([k.strip() for k in keywords.split(",") if k.strip()])
        url = f"https://jooble.org/api/{api_key}"

        jobs = []
        page = 1
        session = requests.Session()
        while len(jobs) < rows and page <= 3:
            payload = {
                "keywords": keywords,
                "location": location or "",
                "page": page,
            }
            if debug:
                print("[Jooble] Request payload:", payload)
            response = session.post(url, json=payload, timeout=20)
            if debug:
                print("[Jooble] Status:", response.status_code)
            response.raise_for_status()
            data = response.json()
            if debug:
                print("[Jooble] Total:", data.get("totalCount"))
            results = data.get("jobs", [])
            if not results:
                if debug:
                    print("[Jooble] No results for", payload)
                break
            for item in results:
                jobs.append(
                    {
                        "title": item.get("title"),
                        "companyName": item.get("company"),
                        "location": item.get("location"),
                        "link": item.get("link"),
                    }
                )
                if len(jobs) >= rows:
                    break
            page += 1
        return jobs, None
    except requests.RequestException as exc:
        status = exc.response.status_code if exc.response else "n/a"
        body = exc.response.text if exc.response else ""
        if debug and body:
            print("[Jooble] Error body:", body[:500])
        return [], f"Jooble: erreur réseau ({status}) {body[:200]}"
    except Exception as exc:
        return [], f"Jooble: erreur inattendue ({exc})"
