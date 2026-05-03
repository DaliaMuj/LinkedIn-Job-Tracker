import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime, timedelta
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Accept-Language": "en-US,en;q=0.9"
}

URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

DAYS_LIMIT = 7
cutoff_date = datetime.utcnow() - timedelta(days=DAYS_LIMIT)


def safe_text(el):
    return el.text.strip() if el else None


def get_jobs_until_limit():
    all_jobs = []
    start = 0

    while True:
        print(f"Fetching page: {start}")

        params = {
            "keywords": "a",       # 🔥 IMPORTANT
            "location": "Europe",
            "start": start
        }

        r = requests.get(URL, params=params, headers=HEADERS, timeout=10)

        if r.status_code != 200:
            print("Request failed:", r.status_code)
            break

        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.select(".base-card")

        if not cards:
            print("No more jobs")
            break

        page_has_recent = False

        for job in cards:
            time_tag = job.select_one("time")

            if not time_tag:
                continue

            try:
                job_date = datetime.fromisoformat(
                    time_tag["datetime"].replace("Z", "")
                )
            except:
                continue

            # 🔥 DOAR filtrăm, NU oprim
            if job_date >= cutoff_date:
                page_has_recent = True

                all_jobs.append({
                    "title": safe_text(job.select_one(".base-search-card__title")),
                    "company": safe_text(job.select_one(".base-search-card__subtitle")),
                    "location": safe_text(job.select_one(".job-search-card__location")),
                    "date": job_date,
                    "link": job.select_one("a")["href"] if job.select_one("a") else None
                })

        # 🔥 STOP DOAR dacă toată pagina e veche
        if not page_has_recent:
            print("All jobs on this page are older than 7 days → STOP")
            break

        start += 25
        time.sleep(1)

        # 🔥 safety limit (evită loop infinit)
        if start > 300:
            print("Safety stop reached")
            break

    return pd.DataFrame(all_jobs)


def run():
    os.makedirs("data", exist_ok=True)

    df = get_jobs_until_limit()

    print("Total jobs:", len(df))

    if df.empty:
        print("⚠️ No jobs found")
        return

    df.to_csv("data/jobs.csv", index=False)
    print("Saved to data/jobs.csv")


if __name__ == "__main__":
    run()
