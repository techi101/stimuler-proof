"""Pull Google Play reviews for an app into a CSV."""
import sys, csv
from google_play_scraper import reviews, Sort, app

def fetch(app_id, n, out):
    info = app(app_id, lang="en", country="in")
    rows, token = [], None
    while len(rows) < n:
        batch, token = reviews(app_id, lang="en", country="in", sort=Sort.NEWEST,
                               count=min(200, n - len(rows)), continuation_token=token)
        if not batch: break
        rows += batch
        if token is None: break
    seen = set(); rows = [r for r in rows if not (r["reviewId"] in seen or seen.add(r["reviewId"]))]
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "date", "score", "version", "thumbs", "replied", "text", "reply"])
        for r in rows:
            w.writerow([r["reviewId"], r["at"].date(), r["score"], r.get("reviewCreatedVersion") or "",
                        r["thumbsUpCount"], bool(r.get("replyContent")), (r["content"] or "").replace("\n", " "),
                        (r.get("replyContent") or "").replace("\n", " ")])
    print(app_id, "| rating", round(info["score"], 2), "| ratings", info["ratings"],
          "| histogram", info["histogram"], "| installs", info["installs"], "| version", info.get("version"),
          "| fetched", len(rows), "| oldest", rows[-1]["at"].date() if rows else None)

if __name__ == "__main__":
    fetch(sys.argv[1], int(sys.argv[2]), sys.argv[3])
