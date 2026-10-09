"""
import csv
import logging
import os

import requests
from bs4 import BeautifulSoup

os.makedirs("logs", exist_ok=True)
os.makedirs("data", exist_ok=True)

logging.basicConfig(
    filename="logs/naive.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

BASE = "https://news.ycombinator.com"
MAX_PAGES = 30
FIELDS = ["id", "title", "url", "author", "score", "comments_count", "date"]


def parse_page(html):
    soup = BeautifulSoup(html, "lxml")
    rows = []
    for item in soup.select("tr.athing"):
        sub = item.find_next_sibling("tr")
        link = item.select_one(".titleline > a")
        if link is None or sub is None:
            continue

        href = link.get("href", "")
        if href.startswith("item?id="):
            href = f"{BASE}/{href}"

        score = sub.select_one(".score")
        author = sub.select_one(".hnuser")
        age = sub.select_one(".age")

        comments = 0
        for a in sub.select("a"):
            text = a.get_text(strip=True).replace("\xa0", " ")
            if text.endswith("comments") or text.endswith("comment"):
                comments = int(text.split()[0])

        rows.append({
            "id": item.get("id"),
            "title": link.get_text(strip=True),
            "url": href,
            "author": author.get_text(strip=True) if author else None,
            "score": int(score.get_text().split()[0]) if score else None,
            "comments_count": comments,
            "date": age["title"].split()[0] if age and age.has_attr("title") else None,
        })
    return rows


def main():
    all_rows = []
    for page in range(1, MAX_PAGES + 1):
        url = f"{BASE}/news?p={page}"
        try:
            r = requests.get(url)  # naive: no headers, no delay, no retries
        except requests.RequestException as e:
            logging.error("page %s | request failed: %s", page, e)
            print(f"page {page}: request failed ({e})")
            break

        logging.info("page %s | status %s | %s bytes", page, r.status_code, len(r.content))
        print(f"page {page}: status {r.status_code}")

        if r.status_code != 200:
            logging.error("page %s | blocked or error, stopping (status %s)", page, r.status_code)
            break

        rows = parse_page(r.text)
        if not rows:
            logging.warning("page %s | no items parsed", page)
            print(f"page {page}: no items found, stopping")
            break
        all_rows.extend(rows)

    with open("data/naive_data.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\n{len(all_rows)} records saved to data/naive_data.csv")


if __name__ == "__main__":
    main()
"""