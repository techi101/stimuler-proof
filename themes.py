"""Keyword rules that tag Stimuler reviews by theme.

Complaint themes are run on 1-2 star reviews. Praise themes are run on 4-5 star reviews.
Rules are English plus some Hinglish, Spanish and Indonesian words, because the
Play listing mixes all four. They are rules, not a model, so expect some misses.
"""
import re

COMPLAINTS = {
    # paid, but Pro did not unlock, vanished, or money kept being taken
    "paid_not_unlocked": r"(after (making )?(the )?payment|payment (has )?(already )?(been )?(success|done|complete|deduct)|"
                         r"(deducted|debit(ed|ing)|charged|cut) (my |the |it )?(money|amount|already)|money got deducted|still got charged|"
                         r"(unable|not able|can'?t) (to )?(use|access) (the )?(premium|pro|subscription)|"
                         r"(subscription|premium|pro|pro version|pro plan|pro features)( is| are)? (not )?(active|activated|reflect|gone)|"
                         r"not reflect|lost (my )?(\w+ )?subscription|showing to apply for pro|"
                         r"(asks?|asking) (me )?(to )?(purchase|buy|pay) (it |the subscription )?again|after (unsubscrib|cancel)|"
                         r"can'?t cancel|want to unsubscribe|plan cancellation|i did not buy|didn'?t get (the )?(premium|subscription))",
    # tried to reach support and heard nothing back
    "support_no_reply": r"(no (response|reply|help|support|in app support|customer (care|service|support))|"
                        r"not (responding|replying|getting (any )?(reply|response))|(didn'?t|don'?t|did not|do not) (reply|respond)|"
                        r"(no ?one|nobody) (is |seems to be )?(replying|responding|reply|respond|listening|contacting)|"
                        r"(mailed|emailed|email(ed)?) (them|you|support)|switched off|"
                        r"customer (care|service|support)|support team|whatsapp|\bwa\b|komplain|tidak (ada )?(respon|balas)|sin respuesta)",
    # explicitly asks for money back
    "refund_ask": r"(refund|money back|return(ing)? my money|send my \d+|reembolso|uang (saya )?kembali)",
    # free tier felt too short, paywall surprising, waits, price too high
    "paywall_price": r"(not (totally )?free|isn'?t free|fully paid|completely free|free nhi|free nahi|say free|"
                     r"ask(s|ing)? (for )?(money|payment|to pay|pro|membership|the paid)|always ask|again and again asking|"
                     r"(force|forces|forcing) (us |you |me )?(to )?(buy|pay|get)|have to (pay|buy)|need to (pay|buy)|unless you pay|"
                     r"(too |very |so )?(expensive|costly|high (price|payment|cost))|over ?priced|charged very high|not worth|"
                     r"waste (of|your|my) money|money ?makers?|grab money|greedy|push for buying|"
                     r"(after|in) (one|1|a|two|2|few|some|4|four) (week|day|minute)s?.{0,40}(pay|lock|premium|subscri|money|free)|"
                     r"free for \d+ days|without (a )?subscription|only asking for paid|"
                     r"take premium|premium (to|for) (unlock|continue|learn)|\bvip\b|they want \$|"
                     r"\b11 ?(hrs|hours|jam)\b|esperar|paise|pese|paisa|bayar|berbayar|de paga|pagar)",
    # content too basic, repetitive, or ran out
    "content_basic_repetitive": r"(too basic|very basic|so basic|incredibly basic|overly basic|only basic|basic (words|english|level|lessons|things)|"
                                r"beginner|from zero|1st grader|first grader|repetit|repeat(s|ed|ing)? (the )?(same|question|frases)|"
                                r"same (question|lesson|reading|conversation|pattern|topic)|boring|coming soon|no (more|new) lesson|no lesson|"
                                r"exercises? finish|not challenging|can'?t continue to day|stop at exercise|"
                                r"\ba2\b|\bb1\b|intermediate|advanced (learner|user|level))",
    # Sarah / speech engine does not hear, understand, score or correct properly
    "ai_speech_quality": r"(recogni[sz]|detect|kedeteksi|terdeteksi|dekteksi|budek|budeg|gadenger|tidak mendengar|"
                         r"(can'?t|cannot|couldn'?t|doesn'?t|does not|not|didn'?t) (properly )?(understand|listen|hear|interpret|catch|capture|convert)|"
                         r"(doesn'?t|does not|never|not) correct|pronounced it (just )?fine|mispronounc|auto ?correct|mismatch|"
                         r"robotic|templated|interrump|interrupt|cuts? (the )?call|(call|audio) (cut|drop|disconnect)|keeps talking|"
                         r"sarah (is|ai|doesn|don|cuts|keeps)|speech|"
                         r"chat ?gpt|gemini|claude|free ai)",
    # crashes, loading loops, stuck screens, slowness
    "bugs_stuck": r"(bug|glitch|crash|\bhang|freez|froze|congela|pegado|colgada|cargando|loading|buffer|\blag(gy|ging|s)?\b|"
                  r"stuck|stucked|not (working|opening|loading|moving)|doesn'?t (work|open|load)|stopped working|"
                  r"can'?t (open|move|progress)|preparing ?exercises|\beror\b|\berror\b|rusak|broken|internal issue|"
                  r"\bslow\b|takes? (too )?(much|long) time|takes ages|ages to|much time to|"
                  r"mic (is )?(not|disappear)|mic nya|closed automatically|automatically (getting )?closed|tidak bisa|se corta)",
    # login, sign-up, device change, progress or Pro lost across devices
    "account_device": r"(log ?in|logged out|sign ?up|sing up|create (an )?account|new (mobile|phone|device)|changed (my )?(mobile|phone)|"
                      r"ipad|tablet|\btab\b|lost (all )?(my )?(\w+ )?(progress|streak)|start from (day 1|the beginning)|delete (my )?account)",
    # stuck in the first-run introduction questions
    "onboarding_stuck": r"(introduction|intro (part|question|section)|tell me about yourself|last (step|question) of|"
                        r"onboarding|first screen|almost done|so many questions|tantas preguntas|information asking)",
    # felt misled by ads, influencers or ratings
    "ad_mismatch": r"(advert|instagram|social media|tiktok|promot|fake claim|marketing|iklan|buzzer|kemakan|"
                   r"overhyped|misleading|false promi|heard a lot|(ratings|reviews) (are |is )?fake|faked|promete|what i thought)",
}

PRAISE = {
    "confidence": r"(confiden|hesitat|\bshy\b|\bfear|nervous|jhijhak)",
    "speaking_fluency": r"(fluen|speak(ing)? (skill|better|fluent|english)|spoken english|conversation)",
    "pronunciation": r"(pronunc|accent)",
    "grammar_vocab": r"(grammar|vocab)",
    "feedback_report": r"(feedback|report|correct(s|ion)? my|my mistake)",
    "sarah_ai_partner": r"(sarah|ai (call|partner|tutor|teacher)|talk(ing)? (to|with) (an )?ai|practice partner)",
    "interview_job_ielts": r"(interview|\bjob|ielts|placement|office|work ?place)",
    "price_value": r"(worth|value for money|affordable|cheap|price)",
}

COMPETITORS = {
    "chatgpt": r"chat ?gpt", "gemini": r"gemini", "claude": r"\bclaude\b", "duolingo": r"duo ?lingo|deolingo|duolinggo",
    "elsa": r"\belsa\b", "praktika": r"praktika", "loora": r"loora",
    "youtube": r"youtube", "magnetic": r"\bmagnetic\b", "character_ai": r"character\.?ai",
}

_COMPILED = {name: re.compile(p) for name, p in {**COMPLAINTS, **PRAISE, **COMPETITORS}.items()}


def tags(text, group):
    """Return the sorted list of theme names in `group` (a dict above) whose rule matches `text`."""
    low = (text or "").lower()
    return sorted(k for k in group if _COMPILED[k].search(low))


def language(text):
    """Rough language guess so non-English reviews can be counted separately."""
    t = " " + re.sub(r"[^\w\s]", " ", (text or "").lower()) + " "
    if re.search(r"[ऀ-ॿ]", t):
        return "hindi"
    if re.search(r" (yang|tidak|aplikasi|saya|sangat|bisa|untuk|ini|nggak|gak|ga|banget|aku|apk) ", t):
        return "indonesian"
    if re.search(r" (que|la|el|muy|para|aplicación|pero|una|inglés|esta|es|lo) ", t):
        return "spanish"
    if re.search(r" (hai|nahi|nhi|mein|kya|bahut|accha|acha|sikh|liye|yaar|bhai|karo|isme) ", t):
        return "hinglish"
    return "english"

# reviewer says they paid (Pro, subscription, price amounts) in English, Indonesian or Spanish
PAID = re.compile(r"(premium|subscri|\bpro\b|paid|purchas|payment|bought|\b(399|400|499|999|1999)\b|annual|yearly|one year|1 year|"
                  r"langganan|anualidad|suscrip)")


def says_paid(text):
    return bool(PAID.search((text or "").lower()))
