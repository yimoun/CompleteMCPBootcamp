import requests

# Fetch LinkedIn jobs based on search query and location
def fetch_linkedin_jobs(search_query, location="india", rows=60):
    """
    Free alternative using Remotive (remote jobs). We keep the function name for UI consistency.
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
def fetch_naukri_jobs(search_query, location="india", rows=60):
    """
    Free alternative using The Muse public API. Keeps name for UI consistency.
    """
    try:
        jobs = []
        page = 1
        while len(jobs) < rows and page <= 5:
            params = {"page": page, "q": search_query}
            if location:
                params["location"] = location
            response = requests.get(
                "https://www.themuse.com/api/public/jobs",
                params=params,
                timeout=20,
            )
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            if not results:
                break
            for item in results:
                locations = item.get("locations") or []
                job_location = locations[0].get("name") if locations else ""
                jobs.append(
                    {
                        "title": item.get("name"),
                        "companyName": (item.get("company") or {}).get("name"),
                        "location": job_location,
                        "url": (item.get("refs") or {}).get("landing_page"),
                    }
                )
                if len(jobs) >= rows:
                    break
            page += 1
        return jobs, None
    except requests.RequestException as exc:
        return [], f"The Muse: erreur réseau ({exc})"
    except Exception as exc:
        return [], f"The Muse: erreur inattendue ({exc})"
