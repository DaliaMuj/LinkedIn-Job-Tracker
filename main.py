import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"


def get_jobs(start):
    params = {
        "keywords": "data",
        "location": "Romania",
        "f_TPR": "r2592000",  # 30 days
        "start": start
    }

    try:
        r = requests.get(URL, params=params, headers=HEADERS, timeout=10)

        if r.status_code != 200:
            print("❌ Failed:", r.status_code)
            return []

        soup = BeautifulSoup(r.text, "html.parser")
        cards = soup.select(".base-card")

        print(f"📦 Page {start} → {len(cards)} jobs")

        jobs = []

        for job in cards:
            title = job.select_one(".base-search-card__title")
            company = job.select_one(".base-search-card__subtitle")
            location = job.select_one(".job-search-card__location")
            time_tag = job.select_one("time")
            link = job.select_one("a")

            jobs.append({
                "title": title.text.strip() if title else None,
                "company": company.text.strip() if company else None,
                "location": location.text.strip() if location else None,
                "date": time_tag["datetime"] if time_tag else None,
                "link": link["href"] if link else None
            })

        return jobs

    except Exception as e:
        print("❌ Error:", e)
        return []


def run():
    os.makedirs("data", exist_ok=True)

    all_jobs = []

    # ✔️ corect pagination
    for start in [0, 25, 50]:
        all_jobs.extend(get_jobs(start))
        time.sleep(2)  # important

    print("🔢 Total jobs:", len(all_jobs))

    df = pd.DataFrame(all_jobs)

    if df.empty:
        print("⚠️ No data extracted!")
        return

    df.to_csv("data/jobs.csv", index=False)

    print("✅ Saved CSV")


if __name__ == "__main__":
    run()
