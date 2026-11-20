"""Tag Stimuler Play + App Store reviews and write the numbers behind REPORT.md.

python analyze.py   ->  out/summary.json, out/quotes.json, out/tagged_play.csv
"""
import json, os, sys
import pandas as pd
from themes import COMPLAINTS, PRAISE, COMPETITORS, tags, language, says_paid

sys.stdout.reconfigure(encoding="utf-8")
WINDOW_START = "2026-05-20"   # last 6 months of the snapshot


def tag_frame(d):
    d = d.copy()
    d["text"] = d.text.fillna("").astype(str)
    d["lang"] = d.text.map(language)
    d["paid_mention"] = d.text.map(says_paid)
    for group in (COMPLAINTS, PRAISE, COMPETITORS):
        hits = d.text.map(lambda t, g=group: tags(t, g))
        for k in group:
            d[k] = hits.map(lambda h, k=k: k in h)
    return d


def theme_table(low, names):
    n = len(low)
    return {k: {"n": int(low[k].sum()), "pct": round(100 * low[k].mean(), 1) if n else 0.0} for k in names}


def quotes(low, names, per=3, maxlen=260):
    out = {}
    for k in names:
        sub = low[low[k] & (low.text.str.split().str.len() >= 8)].sort_values("date", ascending=False).head(per)
        out[k] = [{"date": str(r.date.date()), "stars": int(r.score), "text": r.text[:maxlen]} for r in sub.itertuples()]
    return out


def main():
    os.makedirs("out", exist_ok=True)
    play = tag_frame(pd.read_csv("data/stimuler.csv", parse_dates=["date"]).drop_duplicates("id"))
    ios = tag_frame(pd.read_csv("data/appstore_in.csv", parse_dates=["date"]).drop_duplicates("id"))
    play["low"] = play.score <= 2
    ios["low"] = ios.score <= 2

    win = play[play.date >= WINDOW_START]
    low = win[win.low].drop_duplicates("text")
    long_low = low[low.text.str.split().str.len() >= 5]          # short "worst app" texts carry no theme
    happy = win[(win.score >= 4) & (win.text.str.split().str.len() >= 5)]

    s = {"play": {
            "fetched": len(play), "date_from": str(play.date.min().date()), "date_to": str(play.date.max().date()),
            "window": f"{WINDOW_START} to {play.date.max().date()}", "reviews_in_window": len(win),
            "low_in_window": int(win.low.sum()), "low_share_in_window": round(win.low.mean(), 3),
            "low_unique_texts": len(low), "low_unique_5plus_words": len(long_low)}}
    m = play.assign(month=play.date.dt.to_period("M").astype(str)).groupby("month").agg(n=("id", "size"), low_share=("low", "mean"))
    s["play"]["monthly_low_share"] = {k: {"n": int(r.n), "low_share": round(r.low_share, 3)} for k, r in m.iterrows()}
    half = play.assign(h=play.date.dt.year.astype(str) + "H" + ((play.date.dt.month > 6) + 1).astype(str))
    s["play"]["half_year_low_share"] = half.groupby("h").low.agg(["size", "mean"]).round(3).to_dict("index")

    # complaint themes, last 6 months, 1-2 star with 5+ words
    s["play"]["complaints"] = theme_table(long_low, COMPLAINTS)
    s["play"]["untagged_pct"] = round(100 * (~long_low[list(COMPLAINTS)].any(axis=1)).mean(), 1)
    s["play"]["low_lang_mix"] = long_low.lang.value_counts().to_dict()
    s["play"]["low_says_they_paid"] = {"n": int(long_low.paid_mention.sum()), "pct": round(100 * long_low.paid_mention.mean(), 1)}
    paid_low = long_low[long_low.paid_mention]
    s["play"]["themes_among_payers"] = theme_table(paid_low, COMPLAINTS)
    # refund asks: what else they complain about
    ref = long_low[long_low.refund_ask]
    s["play"]["refund_ask_co_themes"] = theme_table(ref, [k for k in COMPLAINTS if k != "refund_ask"])
    s["play"]["competitor_mentions_low"] = {k: int(long_low[k].sum()) for k in COMPETITORS if long_low[k].sum()}
    s["play"]["competitor_mentions_all_window"] = {k: int(win[k].sum()) for k in COMPETITORS if win[k].sum()}
    # does a theme drag stars down? share of reviews mentioning it that are 1-2 star (all stars, window)
    s["play"]["low_share_when_mentioned"] = {
        k: {"mentions": int(win[k].sum()), "low_share": round(win[win[k]].low.mean(), 3)} for k in COMPLAINTS if win[k].sum() >= 20}
    # praise
    s["play"]["happy_5plus_words"] = len(happy)
    s["play"]["praise"] = theme_table(happy, PRAISE)
    # replies
    rep = low.reply.fillna("")
    s["play"]["low_replied_pct"] = round(100 * (rep != "").mean(), 1)
    s["play"]["top_reply_openings"] = rep[rep != ""].str[:60].value_counts().head(3).to_dict()
    # versions
    v = win.assign(ver=win.version.fillna("unknown").astype(str).str.extract(r"^(\d+\.\d+\.\d+)")[0].fillna("unknown"))
    vt = v.groupby("ver").agg(n=("id", "size"), low_share=("low", "mean"), bug_share=("bugs_stuck", "mean")).query("n>=60").round(3)
    s["play"]["by_version_n60"] = vt.to_dict("index")

    ilow = ios[ios.low]
    s["ios_in"] = {"fetched": len(ios), "date_from": str(ios.date.min().date()), "date_to": str(ios.date.max().date()),
                   "low": len(ilow), "low_share": round(ios.low.mean(), 3),
                   "complaints": theme_table(ilow, COMPLAINTS),
                   "low_says_they_paid": {"n": int(ilow.paid_mention.sum()), "pct": round(100 * ilow.paid_mention.mean(), 1)}}

    json.dump(s, open("out/summary.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
    q = {"play": quotes(long_low, COMPLAINTS), "play_praise": quotes(happy.assign(date=happy.date), PRAISE, per=2),
         "ios_in": quotes(ilow, COMPLAINTS, per=2)}
    json.dump(q, open("out/quotes.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    long_low.to_csv("out/tagged_play_low.csv", index=False)
    print(json.dumps(s, indent=1, ensure_ascii=False, default=str))


if __name__ == "__main__":
    main()
