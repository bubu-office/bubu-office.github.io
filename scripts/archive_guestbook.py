#!/usr/bin/env python3
"""把 ntfy 上最近 12 小時的訪客留言存進 guestbook.json（ntfy 只保留 12 小時）。"""
import json, re, sys, urllib.request

TOPIC = "bubu-office-guestbook-868719bc"
PATH = "guestbook.json"
NAME_MAX, MSG_MAX, KEEP = 12, 120, 2000
URL_RE = re.compile(r"(https?://|www\.)\S+|[a-z0-9-]+(\.[a-z0-9-]+)*\.(com|net|org|tw|io|me|cc|xyz|top|app|ly|link|info|co|site|shop|vip|club|online)\b\S*", re.I)
CTRL_RE = re.compile("[\u0000-\u0008\u000B-\u001F\u007F\u200B-\u200F\u202A-\u202E\u2066-\u2069]")

def clean(s, n):
    s = CTRL_RE.sub("", str(s or ""))
    s = URL_RE.sub("（網址已移除）", s).replace("<", "").replace(">", "")
    s = re.sub(r"\n{3,}", "\n\n", s).strip()
    return s[:n]

def main():
    with open(PATH, encoding="utf-8") as f:
        db = json.load(f)
    db.setdefault("messages", []); db.setdefault("hidden", [])
    have = {m["id"] for m in db["messages"]}
    req = urllib.request.Request(f"https://ntfy.sh/{TOPIC}/json?poll=1&since=all", headers={"User-Agent": "bubu-office-archiver"})
    with urllib.request.urlopen(req, timeout=30) as r:
        lines = r.read().decode("utf-8").splitlines()
    added, per_minute = 0, {}
    for line in lines:
        try:
            e = json.loads(line)
            if e.get("event") != "message" or e["id"] in have:
                continue
            b = json.loads(e["message"])
            m = clean(b.get("m"), MSG_MAX)
            if not m:
                continue
            k = e["time"] // 60
            per_minute[k] = per_minute.get(k, 0) + 1
            if per_minute[k] > 10:  # 同一分鐘灌爆就不收
                continue
            db["messages"].append({"id": e["id"], "t": e["time"], "n": clean(b.get("n"), NAME_MAX) or "路過的奴才", "m": m})
            have.add(e["id"]); added += 1
        except Exception:
            continue
    db["messages"].sort(key=lambda x: x["t"], reverse=True)
    db["messages"] = db["messages"][:KEEP]
    with open(PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(f"added {added}")

if __name__ == "__main__":
    sys.exit(main())
