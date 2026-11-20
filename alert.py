"""Weekly review alert: what changed in 1-2 star reviews this week, and which payers need a human.

python alert.py data/stimuler.csv --today 2026-11-19            # from a saved CSV
python alert.py --fetch com.stimuler 800 --today 2026-11-19      # pull fresh reviews first

A theme is flagged when this week's count is at least MIN_COUNT and at least SPIKE_X times
its average week over the previous BASELINE_WEEKS weeks. The priority queue lists this week's
1-2 star reviews from people who say they paid and mention a payment, refund or support problem.
"""
import argparse, sys
from datetime import date, timedelta
import pandas as pd
from themes import COMPLAINTS, tags, says_paid

MIN_COUNT, SPIKE_X, BASELINE_WEEKS = 3, 2.0, 4
PAYER_THEMES = ("paid_not_unlocked", "refund_ask", "support_no_reply")


def prepare(df):
    d = df.copy()
    d["date"] = pd.to_datetime(d["date"]).dt.date
    d["text"] = d["text"].fillna("").astype(str)
    d["themes"] = d["text"].map(lambda t: tags(t, COMPLAINTS))
    d["paid"] = d["text"].map(says_paid)
    return d


def weekly_report(df, today, baseline_weeks=BASELINE_WEEKS):
    """Return a dict with this week's theme counts, baseline averages, spikes and the payer queue."""
    d = prepare(df)
    week_start = today - timedelta(days=6)
    base_start = week_start - timedelta(days=7 * baseline_weeks)
    this = d[(d.date >= week_start) & (d.date <= today)]
    base = d[(d.date >= base_start) & (d.date < week_start)]
    low_this, low_base = this[this.score <= 2], base[base.score <= 2]
    rows = []
    for k in COMPLAINTS:
        n = int(low_this.themes.map(lambda t: k in t).sum())
        avg = low_base.themes.map(lambda t: k in t).sum() / baseline_weeks
        spike = n >= MIN_COUNT and n >= SPIKE_X * max(avg, 0.5)
        rows.append({"theme": k, "this_week": n, "baseline_avg": round(avg, 2), "spike": bool(spike)})
    queue = low_this[low_this.paid & low_this.themes.map(lambda t: any(x in t for x in PAYER_THEMES))]
    queue = queue.sort_values("date", ascending=False)
    return {
        "week": f"{week_start} to {today}", "reviews": len(this), "low": len(low_this),
        "low_share": round(len(low_this) / len(this), 3) if len(this) else None,
        "baseline_low_share": round(len(low_base) / len(base), 3) if len(base) else None,
        "themes": rows, "spikes": [r["theme"] for r in rows if r["spike"]],
        "priority_queue": [{"date": str(r.date), "stars": int(r.score), "themes": r.themes, "text": r.text[:200]}
                           for r in queue.itertuples()],
    }


def to_markdown(rep):
    out = [f"# Review alert, week {rep['week']}", "",
           f"{rep['reviews']} reviews, {rep['low']} at 1-2 stars "
           f"(share {rep['low_share']}; previous {BASELINE_WEEKS} weeks {rep['baseline_low_share']}).", ""]
    out.append("Spikes: " + (", ".join(rep["spikes"]) if rep["spikes"] else "none") + "")
    out += ["", "| theme | this week | avg week before |", "|---|---|---|"]
    out += [f"| {r['theme']}{' (spike)' if r['spike'] else ''} | {r['this_week']} | {r['baseline_avg']} |" for r in rep["themes"]]
    out += ["", f"## Payers who need a human ({len(rep['priority_queue'])})", ""]
    out += [f"- {q['date']} {q['stars']} star [{', '.join(q['themes'])}]: {q['text']}" for q in rep["priority_queue"]] or ["- none"]
    return "\n".join(out) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", nargs="?")
    ap.add_argument("--fetch", nargs=2, metavar=("APP_ID", "N"))
    ap.add_argument("--today", default=str(date.today()))
    a = ap.parse_args(argv)
    if a.fetch:
        from fetch import fetch
        a.csv = a.csv or "data/latest.csv"
        fetch(a.fetch[0], int(a.fetch[1]), a.csv)
    rep = weekly_report(pd.read_csv(a.csv), date.fromisoformat(a.today))
    sys.stdout.reconfigure(encoding="utf-8")
    print(to_markdown(rep))
    return rep


if __name__ == "__main__":
    main()
