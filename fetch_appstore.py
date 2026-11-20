"""Pull recent App Store reviews for an app from Apple's public RSS feed (max 10 pages x 50)."""
import sys, csv, json, urllib.request

def fetch(app_id, country, out):
    rows = []
    for page in range(1, 11):
        url = f"https://itunes.apple.com/{country}/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/json"
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=30) as r:
                feed = json.load(r)["feed"]
        except Exception as e:
            print("stop at page", page, e); break
        entries = feed.get("entry", [])
        if isinstance(entries, dict): entries = [entries]
        entries = [e for e in entries if "im:rating" in e]
        if not entries: break
        for e in entries:
            rows.append([e["id"]["label"], e["updated"]["label"][:10], int(e["im:rating"]["label"]),
                         e.get("im:version", {}).get("label", ""), e["title"]["label"],
                         e["content"]["label"].replace("\n", " ")])
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["id", "date", "score", "version", "title", "text"]); w.writerows(rows)
    print(country, "fetched", len(rows), "| newest", rows[0][1] if rows else None, "| oldest", rows[-1][1] if rows else None)

if __name__ == "__main__":
    fetch(sys.argv[1], sys.argv[2], sys.argv[3])
