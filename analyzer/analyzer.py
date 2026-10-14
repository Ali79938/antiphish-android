from .rules import MESSAGE_RULES, CALL_RULES, VIDEO_RULES

def _verdict(score):
    if score < 25:
        return "safe"
    if score < 45:
        return "suspicious"
    return "phishing"

def _recommendations(verdict, signals):
    fired = {s["rule"] for s in signals}
    recs = []
    if verdict == "safe":
        return ["No action needed. Message looks normal."]

    if verdict == "phishing":
        recs.append("DO NOT click any links in this message.")
        recs.append("DO NOT reply, call back, or provide any personal information.")
        recs.append("Delete or report the message as spam/phishing.")
    else:
        recs.append("Treat links in this message with caution.")
        recs.append("Do not enter credentials or payment info from any link here.")

    if "r_credentials" in fired:
        recs.append("Log in by typing the official URL directly - never through a link here.")
    if "r_finance" in fired:
        recs.append("Never send money, gift cards, or crypto to someone who contacted you first.")
    if "r_brand_impersonation" in fired:
        recs.append("Verify the sender by contacting the real company through their official app.")
    if "r_shortener" in fired or "r_suspicious_tld" in fired or "r_ip_link" in fired:
        recs.append("Inspect any short links before clicking - or skip them entirely.")
    if "r_dangerous_attachment" in fired:
        recs.append("Do not open the attachment. Delete the message.")
    if "r_lookalike" in fired:
        recs.append("The domain looks like a typosquat. Check the spelling carefully.")
    if "r_urgency" in fired:
        recs.append("Urgency is a pressure tactic. Slow down and verify independently.")
    if "r_at_in_url" in fired:
        recs.append("URL contains an @ symbol - a known obfuscation trick.")
    if "r_excessive_caps" in fired or "r_excessive_punct" in fired:
        recs.append("Excessive caps and punctuation are common in mass-market spam.")
    if "r_vishing_keywords" in fired:
        recs.append("Hang up. Real companies do not demand payment or credentials over the phone.")
    if "r_short_call_burst" in fired:
        recs.append("Block the number. Bursts of short calls are typical of robocallers.")
    if "r_video_deepfake_hints" in fired:
        recs.append("Video may be AI-generated. Verify the sender through another channel.")
    if "r_video_suspicious_host" in fired:
        recs.append("Video is not on a major platform. Treat it as untrusted.")

    seen = set()
    out = []
    for r in recs:
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out

def score(data, rules):
    total = 0
    fired = []
    for rule in rules:
        try:
            hit, weight, explanation = rule(data)
        except Exception:
            continue
        if hit:
            total += weight
            fired.append({"rule": rule.__name__, "weight": weight, "why": explanation})
    final = min(total, 100)
    verdict = _verdict(final)
    recs = _recommendations(verdict, fired)
    return {"score": final, "verdict": verdict, "signals": fired, "recommendations": recs}

def analyze_message(msg):
    return score(msg, MESSAGE_RULES)

def analyze_call(call):
    return score(call, CALL_RULES)

def analyze_video(vid):
    return score(vid, VIDEO_RULES)
