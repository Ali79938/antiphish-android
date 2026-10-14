import re

_HOMOGLYPHS = {
    "\u0430": "a", "\u0435": "e", "\u043e": "o", "\u0440": "p",
    "\u0441": "c", "\u0443": "y", "\u0445": "x", "\u0456": "i",
    "\u0458": "j", "\u0455": "s",
    "0": "o", "1": "l", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a",
}

def normalize(text):
    if not text:
        return ""
    return "".join(_HOMOGLYPHS.get(c, c) for c in text)

URGENCY = [
    "urgent", "immediately", "act now", "verify now", "within 24 hours",
    "final warning", "account will be closed", "suspended", "limited time",
    "expires today", "respond immediately", "immediate action required",
    "last warning", "your account has been", "unauthorized login",
    "unusual activity", "we detected", "security alert", "verify immediately",
    "confirm now",
]
FINANCE = [
    "wire transfer", "bitcoin", "crypto wallet", "gift card", "western union",
    "money gram", "payment failed", "refund", "bank account", "ssn",
    "social security", "credit card", "debit card", "routing number",
    "bill payment", "invoice attached", "purchase confirmation",
    "unauthorized transaction", "tax refund", "irs", "hmrc",
    "social security suspended", "stimulus", "relief fund",
]
CREDENTIALS = [
    "verify your account", "confirm your password", "click here to login",
    "update your payment", "re-enter your password", "reset your password",
    "unusual sign-in", "suspicious activity", "confirm your identity",
    "login attempt", "sign-in attempt", "password expired",
    "update your information", "complete verification",
    "reactivate your account", "confirm your details",
]
GREETING_MISMATCH = ["dear customer", "dear user", "dear member", "dear sir/madam"]
BRANDS = ["paypal", "apple", "amazon", "microsoft", "google",
          "netflix", "bank of america", "chase", "wells fargo", "coinbase"]
BRAND_REAL_DOMAINS = {
    "paypal": "paypal.com", "apple": "apple.com", "amazon": "amazon.com",
    "microsoft": "microsoft.com", "google": "google.com",
    "netflix": "netflix.com", "bank of america": "bankofamerica.com",
    "chase": "chase.com", "wells fargo": "wellsfargo.com",
    "coinbase": "coinbase.com",
}
SUSPICIOUS_TLDS = [
    ".tk", ".ml", ".ga", ".cf", ".gq", ".xyz", ".top", ".work",
    ".click", ".link", ".zip", ".mov", ".rest", ".bar", ".review",
    ".country", ".stream", ".download", ".racing", ".party",
    ".science", ".gdn", ".loan",
]
URL_SHORTENERS = [
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd",
    "buff.ly", "rebrand.ly", "cutt.ly", "shorturl.at",
]
LOOKALIKE = [
    r"paypa[l1]", r"app[l1]e", r"arnazon", r"micros0ft", r"g00gle",
    r"netf[l1]ix", r"faceb00k",
]
DANGEROUS_EXTS = [
    ".exe", ".scr", ".js", ".vbs", ".jar", ".bat", ".cmd",
    ".lnk", ".hta", ".iso", ".img", ".docm", ".xlsm",
    ".ps1", ".vbe", ".wsf", ".msi", ".reg", ".chm", ".svg",
    ".html", ".htm", ".zip", ".rar", ".7z",
]

URL_RE = re.compile(r"https?://[^\s<>\"']+")

def has_any(text, words):
    t = normalize(text).lower()
    return [w for w in words if w in t]

def has_patterns(text, patterns):
    t = normalize(text).lower()
    return [p for p in patterns if re.search(p, t)]

def urls(text):
    return URL_RE.findall(text or "")

def r_urgency(msg):
    hits = has_any(msg.get("body", ""), URGENCY)
    return bool(hits), 15, "Urgency: " + ", ".join(hits[:3])

def r_finance(msg):
    hits = has_any(msg.get("body", ""), FINANCE)
    return bool(hits), 20, "Financial lures: " + ", ".join(hits[:3])

def r_credentials(msg):
    hits = has_any(msg.get("body", ""), CREDENTIALS)
    return bool(hits), 20, "Credential request: " + ", ".join(hits[:3])

def r_generic_greeting(msg):
    hits = has_any(msg.get("body", ""), GREETING_MISMATCH)
    return bool(hits), 8, "Generic greeting: " + ", ".join(hits[:2])

def r_brand_impersonation(msg):
    body = msg.get("body", "") or ""
    sender = normalize(msg.get("sender", "") or "").lower()
    combined = normalize(body).lower() + " " + sender
    hits = [b for b in BRANDS if b in combined]
    suspicious = []
    for brand in hits:
        real = BRAND_REAL_DOMAINS.get(brand, "")
        if brand in sender and real and not sender.endswith(real):
            suspicious.append(brand + " (fake sender domain)")
        elif brand not in sender:
            suspicious.append(brand)
    return bool(suspicious), 20, "Brand impersonation: " + ", ".join(suspicious[:3])

def r_suspicious_tld(msg):
    bad = []
    for u in urls(msg.get("body", "")):
        for tld in SUSPICIOUS_TLDS:
            if u.lower().endswith(tld) or (tld + "/") in u.lower():
                bad.append(u)
    return bool(bad), 18, "Suspicious TLD: " + ", ".join(bad[:2])

def r_shortener(msg):
    hits = []
    for u in urls(msg.get("body", "")):
        for s in URL_SHORTENERS:
            if s in u.lower():
                hits.append(u)
    return bool(hits), 15, "URL shortener: " + ", ".join(hits[:2])

def r_lookalike(msg):
    hits = has_patterns(msg.get("body", ""), LOOKALIKE)
    return bool(hits), 22, "Lookalike domain: " + ", ".join(hits[:3])

def r_ip_link(msg):
    bad = []
    for u in urls(msg.get("body", "")):
        if re.search(r"https?://\d{1,3}(\.\d{1,3}){3}", u):
            bad.append(u)
    return bool(bad), 22, "Raw IP in link: " + ", ".join(bad[:2])

def r_at_in_url(msg):
    bad = [u for u in urls(msg.get("body", "")) if "@" in u]
    return bool(bad), 18, "Credentials-style URL: " + ", ".join(bad[:2])

def r_dangerous_attachment(msg):
    bad = []
    for u in urls(msg.get("body", "")):
        for e in DANGEROUS_EXTS:
            if u.lower().endswith(e):
                bad.append(u)
    return bool(bad), 25, "Dangerous attachment: " + ", ".join(bad[:2])

def r_excessive_caps(msg):
    body = msg.get("body", "")
    if len(body) < 20:
        return False, 0, ""
    letters = [c for c in body if c.isalpha()]
    if not letters:
        return False, 0, ""
    ratio = sum(1 for c in letters if c.isupper()) / len(letters)
    if ratio > 0.5:
        return True, 10, "Excessive capitalization"
    return False, 0, ""

def r_excessive_punct(msg):
    body = msg.get("body", "")
    if len(body) < 20:
        return False, 0, ""
    n = body.count("!")
    if n >= 4:
        return True, 8, "Excessive exclamation marks"
    return False, 0, ""

def r_caller_unknown(call):
    num = (call.get("number", "") or "").strip()
    if not num:
        return False, 0, ""
    return True, 10, "Caller not in contacts"

def r_vishing_keywords(call):
    transcript = call.get("transcript", "") or ""
    hits = has_any(transcript, URGENCY + FINANCE + CREDENTIALS)
    return bool(hits), 25, "Vishing keywords: " + ", ".join(hits[:3])

def r_short_call_burst(call):
    try:
        count = int(call.get("recent_calls_last_hour", 0) or 0)
        avg = float(call.get("avg_duration_seconds", 0) or 0)
    except Exception:
        return False, 0, ""
    if count >= 5 and avg < 15:
        return True, 20, "Burst of short calls"
    return False, 0, ""

def r_video_shortened_link(vid):
    for u in urls(vid.get("link", "")):
        for s in URL_SHORTENERS:
            if s in u.lower():
                return True, 18, "Shortened video link"
    return False, 0, ""

def r_video_suspicious_host(vid):
    link = (vid.get("link", "") or "").lower()
    ok = ["youtube.com", "youtu.be", "vimeo.com", "dailymotion.com"]
    if not link:
        return False, 0, ""
    if not any(h in link for h in ok):
        return True, 15, "Video outside major platforms"
    return False, 0, ""

def r_video_deepfake_hints(vid):
    notes = (vid.get("notes", "") or "").lower()
    hints = ["deepfake", "faceswap", "ai generated", "synthetic voice",
             "voice clone", "urgent video"]
    hits = [h for h in hints if h in notes]
    return bool(hits), 22, "Deepfake hints: " + ", ".join(hits[:3])

def r_video_lures(vid):
    text = (vid.get("link", "") + " " + (vid.get("notes", "") or "")).lower()
    hits = has_any(text, URGENCY + FINANCE + CREDENTIALS)
    return bool(hits), 18, "Video-lure language: " + ", ".join(hits[:3])

MESSAGE_RULES = [
    r_urgency, r_finance, r_credentials, r_generic_greeting,
    r_brand_impersonation, r_suspicious_tld, r_shortener, r_lookalike,
    r_ip_link, r_at_in_url, r_dangerous_attachment,
    r_excessive_caps, r_excessive_punct,
]
CALL_RULES = [r_caller_unknown, r_vishing_keywords, r_short_call_burst]
VIDEO_RULES = [r_video_shortened_link, r_video_suspicious_host,
               r_video_deepfake_hints, r_video_lures]
