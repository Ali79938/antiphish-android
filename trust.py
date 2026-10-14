"""Track senders, call counts, and recent activity.
Backed by a plain text file so it works on Android and desktop."""

import os
import time

TRUST_FILE = os.path.join(os.path.expanduser("~"), "antiphish_trust.txt")
WINDOW = 3600  # 1 hour


def _load():
    if not os.path.isfile(TRUST_FILE):
        return {}
    data = {}
    try:
        with open(TRUST_FILE, "r", errors="replace") as f:
            for line in f:
                parts = line.strip().split("|")
                if len(parts) != 4:
                    continue
                key, known, count, last = parts
                data[key] = {
                    "known": known == "1",
                    "count": int(count),
                    "last": float(last),
                }
    except Exception:
        pass
    return data


def _save(data):
    try:
        with open(TRUST_FILE, "w") as f:
            for key, v in data.items():
                f.write("%s|%d|%d|%s\n" % (
                    key, 1 if v["known"] else 0, v["count"], v["last"]
                ))
    except Exception:
        pass


def record(key, known=False):
    """Record an incoming event for a sender key (number or ID)."""
    data = _load()
    now = time.time()
    entry = data.get(key, {"known": known, "count": 0, "last": 0})
    if now - entry["last"] > WINDOW:
        entry["count"] = 0
    entry["count"] += 1
    entry["last"] = now
    entry["known"] = entry["known"] or known
    data[key] = entry
    _save(data)
    return entry


def is_trusted(key):
    """True if the sender is marked known, or has interacted 3+ times."""
    data = _load()
    entry = data.get(key)
    if not entry:
        return False
    if entry["known"]:
        return True
    return entry["count"] >= 3


def recent_count(key):
    data = _load()
    entry = data.get(key)
    if not entry:
        return 0
    now = time.time()
    if now - entry["last"] > WINDOW:
        return 0
    return entry["count"]


def add_known(key):
    data = _load()
    entry = data.get(key, {"known": False, "count": 0, "last": 0})
    entry["known"] = True
    data[key] = entry
    _save(data)
