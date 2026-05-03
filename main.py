import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
from datetime import datetime, timedelta

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept-Language": "en-US,en;q=0.9"
}

URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"

DAYS_LIMIT = 7
cutoff_date = datetime.utcnow() - timedelta(days=DAYS_LIMIT)


def get_jobs_until_limit():
    all_jobs = []
    start = 0

    while True:
        print(f"Fetching page: {start}")

        params = {
            "keywords": "data",
            "location": "Romania",
            "start": start
        }

        r = requests.get(URL, params=params, headers=HEADERS, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")

        cards = soup.select(".base-card")

        if not cards:
            print("No more jobs")
            break

        stop = False

        for job in cards:
            time_tag = job.select_one("time")

            if not time_tag:
                continue

            job_date = datetime.fromisoformat(time_tag["datetime"].replace("Z", ""))

            # 🔥 STOP CONDITION
            if job_date < cutoff_date:
                stop = True
                break

            all_jobs.append({
                "title": job.select_one(".base-search-card__title").text.strip(),
                "company": job.select_one(".base-search-card__subtitle").text.strip(),
                "location": job.select_one(".job-search-card__location").text.strip(),
                "date": job_date,
                "link": job.select_one("a")["href"]
            })

        if stop:
            print("Reached 7-day limit")
            break

        start += 25
        time.sleep(1)

    return pd.DataFrame(all_jobs)


def run():
    df = get_jobs_until_limit()
    print("Total jobs:", len(df))
    df.to_csv("jobs_7_days.csv", index=False)


if __name__ == "__main__":
    run()
