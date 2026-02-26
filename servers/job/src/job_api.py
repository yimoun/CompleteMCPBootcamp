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
                    "_source": "remotive",
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
                        "_source": "jooble",
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


def fetch_jsearch_jobs(search_query, location="", rows=20):
    """
    Location-based jobs using JSearch (RapidAPI). Requires JSEARCH_API_KEY.
    """
    api_key = os.getenv("JSEARCH_API_KEY")
    if not api_key:
        return [], "JSearch: JSEARCH_API_KEY manquant."

    try:
        query = search_query.strip()
        if location:
            query = f"{query} in {location}"

        jobs = []
        page = 1
        while len(jobs) < rows and page <= 3:
            response = requests.get(
                "https://jsearch.p.rapidapi.com/search",
                params={
                    "query": query,
                    "page": str(page),
                    "num_pages": "1",
                },
                headers={
                    "X-RapidAPI-Key": api_key,
                    "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
                },
                timeout=20,
            )
            if response.status_code == 429:
                return jobs, "JSearch: rate limit exceeded. Try again later."
            response.raise_for_status()
            data = response.json()
            results = data.get("data", [])
            if not results:
                break
            for item in results:
                loc_parts = [
                    item.get("job_city"),
                    item.get("job_state"),
                    item.get("job_country"),
                ]
                location_str = ", ".join(p for p in loc_parts if p)
                if item.get("job_is_remote"):
                    location_str = f"Remote - {location_str}" if location_str else "Remote"

                jobs.append(
                    {
                        "title": item.get("job_title"),
                        "companyName": item.get("employer_name"),
                        "location": location_str or "Non specifie",
                        "link": item.get("job_apply_link"),
                        "_source": "jsearch",
                        "_is_remote": item.get("job_is_remote", False),
                    }
                )
                if len(jobs) >= rows:
                    break
            page += 1
        return jobs, None
    except requests.RequestException as exc:
        status = getattr(getattr(exc, "response", None), "status_code", "n/a")
        return [], f"JSearch: erreur reseau ({status})"
    except Exception as exc:
        return [], f"JSearch: erreur inattendue ({exc})"
