import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
from concurrent.futures import ThreadPoolExecutor

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"


# -----------------------------
# GET JOB LIST
# -----------------------------
def get_jobs(start):
    params = {
        "keywords": "data OR software OR analyst",
        "location": "Europe",
        "f_TPR": "r2592000",
        "start": start
    }

    r = requests.get(URL, params=params, headers=HEADERS, timeout=10)

    soup = BeautifulSoup(r.text, "html.parser")
    cards = soup.select(".base-card")

    jobs = []

    for job in cards:
        jobs.append({
            "title": job.select_one(".base-search-card__title").text.strip() if job.select_one(".base-search-card__title") else None,
            "company": job.select_one(".base-search-card__subtitle").text.strip() if job.select_one(".base-search-card__subtitle") else None,
            "location": job.select_one(".job-search-card__location").text.strip() if job.select_one(".job-search-card__location") else None,
            "date": job.select_one("time")["datetime"] if job.select_one("time") else None,
            "link": job.select_one("a")["href"] if job.select_one("a") else None
        })

    return jobs


# -----------------------------
# GET JOB DETAILS
# -----------------------------
def get_details(link):
    try:
        r = requests.get(link, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        def get_nth(n):
            item = soup.select_one(
                f".description__job-criteria-item:nth-of-type({n}) "
                ".description__job-criteria-text--criteria"
            )
            return item.text.strip() if item else None

        desc = soup.select_one(".description__text")

        return {
            "description": desc.text.strip() if desc else None,
            "seniority": get_nth(1),
            "employment": get_nth(2),
            "function": get_nth(3),
            "industry": get_nth(4),
        }

    except Exception as e:
        print("Error:", e)
        return {}


# -----------------------------
# MAIN
# -----------------------------
def run():
    os.makedirs("data", exist_ok=True)

    all_jobs = []

    for start in [0, 25, 50]:
        all_jobs.extend(get_jobs(start))
        time.sleep(2)

    df = pd.DataFrame(all_jobs)

    print("Jobs:", len(df))

    # 🔥 IMPORTANT: limităm pentru speed
    df_details = df.head(20).copy()

    with ThreadPoolExecutor(max_workers=5) as executor:
        details = list(executor.map(get_details, df_details["link"]))

    details_df = pd.DataFrame(details)

    df_details = pd.concat([df_details, details_df], axis=1)

    # 🔥 combinăm înapoi
    final_df = df.merge(df_details, how="left", on=["title", "company", "location", "date", "link"])

    final_df.to_csv("data/jobs.csv", index=False)

    print("Saved with details")


if __name__ == "__main__":
    run()
