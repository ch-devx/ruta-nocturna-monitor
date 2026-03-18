import os
import json
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
KEYWORD     = "world baseball classic"
NTFY_TOPIC  = os.environ.get("NTFY_TOPIC", "")
RSS_FEED    = os.environ.get("RSS_FEED_URL", "")
SEEN_FILE   = "seen_posts.json"
# ─────────────────────────────────────────────────────────────────────────────


def load_seen() -> set:
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_seen(seen: set):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)


def send_notification(post_url: str, description: str):
    if not NTFY_TOPIC:
        print("[WARN] NTFY_TOPIC no configurado.")
        return

    payload = {
        "topic":   NTFY_TOPIC,
        "title":   "🏃 ¡Ruta Nocturna detectada!",
        "message": f"CC Las Américas publicó sobre la ruta nocturna.\n\n{description[:200]}",
        "actions": [{"action": "view", "label": "Ver publicación", "url": post_url}],
        "priority": 4,
    }

    try:
        r = requests.post("https://ntfy.sh", json=payload, timeout=10)
        r.raise_for_status()
        print(f"[OK] Notificación enviada → {NTFY_TOPIC}")
    except Exception as e:
        print(f"[ERROR] Notificación fallida: {e}")


def fetch_feed() -> list[dict]:
    if not RSS_FEED:
        raise ValueError("RSS_FEED_URL no configurado como secret.")

    r = requests.get(RSS_FEED, timeout=15)
    r.raise_for_status()

    root = ET.fromstring(r.content)
    ns   = {}

    # Soporta tanto RSS 2.0 como Atom
    if root.tag == "rss":
        items = root.findall("./channel/item")
        posts = []
        for item in items:
            link  = (item.findtext("link")        or "").strip()
            title = (item.findtext("title")       or "").strip()
            desc  = (item.findtext("description") or "").strip()
            posts.append({"id": link, "url": link, "text": f"{title} {desc}"})
    else:
        # Atom feed
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = root.findall("atom:entry", ns)
        posts = []
        for entry in entries:
            link_el = entry.find("atom:link", ns)
            link    = link_el.attrib.get("href", "") if link_el is not None else ""
            title   = (entry.findtext("atom:title",   "", ns) or "").strip()
            summary = (entry.findtext("atom:summary", "", ns) or "").strip()
            posts.append({"id": link, "url": link, "text": f"{title} {summary}"})

    print(f"[INFO] {len(posts)} posts en el feed.")
    return posts


def check_feed():
    print(f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}] Revisando feed RSS...")

    try:
        posts = fetch_feed()
    except Exception as e:
        print(f"[ERROR] No se pudo obtener el feed: {e}")
        raise SystemExit(1)

    seen     = load_seen()
    new_seen = set(seen)
    found    = False

    for post in posts:
        post_id = post["id"]
        text    = post["text"].lower()
        new_seen.add(post_id)

        if KEYWORD in text:
            if post_id not in seen:
                print(f"[MATCH] '{KEYWORD}' encontrado: {post['url']}")
                send_notification(post["url"], post["text"])
                found = True
            else:
                print(f"[SKIP]  Ya notificado: {post_id}")

    if not found:
        print(f"[OK] Sin novedades sobre '{KEYWORD}'.")

    save_seen(new_seen)


if __name__ == "__main__":
    check_feed()
