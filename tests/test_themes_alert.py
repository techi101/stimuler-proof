import sys, os
from datetime import date
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from themes import COMPLAINTS, PRAISE, tags, language, says_paid  # noqa: E402
from alert import weekly_report, to_markdown  # noqa: E402


# ---- theme rules ----
def test_paid_but_not_unlocked():
    t = "2 time my money got deducted from my bank account but pro version is not reflecting in my profile."
    assert "paid_not_unlocked" in tags(t, COMPLAINTS)


def test_indonesian_speech_complaint():
    assert "ai_speech_quality" in tags("GW NGOMONG TAPI NGGAK KEDETEKSI", COMPLAINTS)


def test_eleven_hour_wait_is_paywall():
    assert "paywall_price" in tags("sehari Kudu Nunggu 11 jam Mending Gak Rekomend", COMPLAINTS)


def test_no_false_bug_hits_from_substrings():
    # 'change' contains 'hang', 'flag' contains 'lag', Spanish 'errores' means mistakes
    assert "bugs_stuck" not in tags("please change the flag for bangla", COMPLAINTS)
    assert "bugs_stuck" not in tags("no me corrige los errores", COMPLAINTS)


def test_onboarding_stuck():
    assert "onboarding_stuck" in tags("stucked at can you tell me about yourself ? no option", COMPLAINTS)


def test_praise_tags():
    assert set(tags("I feel confident now and my pronunciation improved", PRAISE)) >= {"confidence", "pronunciation"}


def test_empty_text():
    assert tags(None, COMPLAINTS) == [] and language("") == "english" and not says_paid(None)


def test_language_guess():
    assert language("aplikasi ini sangat bagus") == "indonesian"
    assert language("la aplicación es muy lenta") == "spanish"
    assert language("bahut accha app hai") == "hinglish"
    assert language("great app for speaking") == "english"


def test_says_paid():
    assert says_paid("I bought the yearly plan for 999")
    assert not says_paid("nice app for practice")


# ---- weekly alert ----
def _df(rows):
    return pd.DataFrame(rows, columns=["date", "score", "text"])


def test_spike_flagged_when_week_jumps():
    rows = [("2026-11-15", 1, "app is stuck and crash again")] * 4          # this week: 4 bug reviews
    rows += [("2026-10-25", 1, "app crash")]                                  # baseline: 1 in 4 weeks
    rows += [("2026-11-14", 5, "great app")] * 6
    rep = weekly_report(_df(rows), date(2026, 11, 19))
    bugs = next(r for r in rep["themes"] if r["theme"] == "bugs_stuck")
    assert bugs["this_week"] == 4 and bugs["baseline_avg"] == 0.25 and bugs["spike"]
    assert "bugs_stuck" in rep["spikes"]
    assert rep["reviews"] == 10 and rep["low"] == 4


def test_no_spike_when_baseline_is_high():
    rows = [("2026-11-15", 1, "app crash")] * 3
    rows += [("2026-10-28", 1, "app crash")] * 8                              # 2 per week before
    rep = weekly_report(_df(rows), date(2026, 11, 19))
    assert "bugs_stuck" not in rep["spikes"]


def test_priority_queue_only_payers_with_money_or_support_issue():
    rows = [
        ("2026-11-18", 1, "I paid 999 for premium but it is not reflecting, no response from support"),
        ("2026-11-17", 1, "app crash every day"),                             # not a payer
        ("2026-11-16", 5, "I bought premium and love it"),                    # happy
        ("2026-11-01", 1, "I paid but no refund"),                            # outside the week
    ]
    rep = weekly_report(_df(rows), date(2026, 11, 19))
    assert len(rep["priority_queue"]) == 1
    assert rep["priority_queue"][0]["date"] == "2026-11-18"
    md = to_markdown(rep)
    assert "Payers who need a human (1)" in md and "2026-11-18" in md


def test_empty_week():
    rep = weekly_report(_df([("2026-10-01", 5, "good")]), date(2026, 11, 19))
    assert rep["reviews"] == 0 and rep["low_share"] is None and rep["spikes"] == []
    assert "none" in to_markdown(rep)
