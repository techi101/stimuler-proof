"""Export the analysis into web/data.json (and data.js so the page also works opened as a file).

Counts come from out/summary.json, out/quotes.json and out/alert_week_2026-11-19.md.
The few numbers under REPORT are copied from REPORT.html (store listing, founder post,
reply check), which is where they were first measured. Run from the repo root:
    python web/export.py
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
summary = json.load(open(os.path.join(ROOT, "out", "summary.json"), encoding="utf-8"))
quotes = json.load(open(os.path.join(ROOT, "out", "quotes.json"), encoding="utf-8"))

alert_md = open(os.path.join(ROOT, "out", "alert_week_2026-11-19.md"), encoding="utf-8").read()
m = re.search(r"week (\S+) to (\S+)\s+(\d+) reviews, (\d+) at 1-2 stars \(share ([\d.]+); previous 4 weeks ([\d.]+)\)", alert_md)
alert = {"from": m.group(1), "to": m.group(2), "reviews": int(m.group(3)), "low": int(m.group(4)),
         "low_share": float(m.group(5)), "prev4_share": float(m.group(6)),
         "spikes": re.search(r"Spikes: (.*)", alert_md).group(1).strip(),
         "payers_need_human": int(re.search(r"Payers who need a human \((\d+)\)", alert_md).group(1)),
         "rows": [{"theme": a, "week": float(b), "avg": float(c)} for a, b, c in
                  re.findall(r"^\| (\w+) \| ([\d.]+) \| ([\d.]+) \|$", alert_md, flags=re.M)]}

REPORT = {
    "snapshot": "20 Nov 2026",
    "play_listing": {"stars": 4.57, "ratings": "232,987", "installs": "10M+", "price": "₹99 to ₹3,999"},
    "ios_listing": {"stars": 4.71, "ratings": "10,211"},
    "d30": {"india_from": 3.8, "india_to": 8.7, "indonesia": 12.6, "latam": 14.2, "source": "Akshay Akash, Sep 2026"},
    "money_support_reviews": 46, "replies_asking_email": 45,
    "chatbots_named": 7, "duolingo_named": 8,
    "hand_check": "Hand check of 10 random reviews per main theme: about 9 in 10 right for bugs, AI, support and payment; lower for the ad theme.",
    "earlier_alert_flags": ["AI speech complaints in the week to 12 Nov", "paywall complaints in the week to 29 Oct"],
    "most_liked": [
        {"thumbs": 67, "date": "5 Jul", "stars": 5, "text": "my main problem in English language is speaking"},
        {"thumbs": 18, "date": "6 Aug", "stars": 5, "text": "i feel very confident"}],
    "tests": 13,
}


def clip(qs):
    return [{**q, "text": q["text"].strip() + ("…" if len(q["text"]) >= 255 else "")} for q in qs]


out = {
    "summary": summary,
    "quotes": {src: {k: clip(v) for k, v in d.items()} for src, d in quotes.items()},
    "alert": alert,
    "report": REPORT,
}
W = os.path.join(ROOT, "web")
json.dump(out, open(os.path.join(W, "data.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
open(os.path.join(W, "data.js"), "w", encoding="utf-8").write("window.DATA = " + json.dumps(out, ensure_ascii=False) + ";\n")
print("ok", alert)
