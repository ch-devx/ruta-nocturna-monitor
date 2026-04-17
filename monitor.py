import os
import json
import sys
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

NTFY_TOPIC = os.environ.get("NTFY_TOPIC", "")
RSS_FEED_URL = os.environ.get("RSS_FEED_URL", "")
KEYWORD = "ruta nocturna"
SEEN_FILE = "seen_posts.json"


def notify(title, message, priority=3, tags=""):
    if not NTFY_TOPIC:
        print("[WARN] NTFY_TOPIC no configurado.")
        return
    try:
        requests.post(
            f"https://ntfy.sh/{NTFY_TOPIC}",
            data=message.encode("utf-8"),
            headers={
                "Title": title.encode("utf-8"),
                "Priority": str(priority),
                "Tags": tags,
            },
            timeout=10,
        )
    except Exception as e:
        print(f"[ERROR] ntfy falló: {e}")


def load_seen() -> set:
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE) as f:
            return set(json.load(f))
    return set()


def save_seen(seen: set):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)


def fetch_feed():
    """Retorna lista de (guid, title, link) o None si el feed no está disponible."""
    if not RSS_FEED_URL:
        return None
    try:
        resp = requests.get(RSS_FEED_URL, timeout=15)
    except requests.RequestException:
        return None
    if resp.status_code != 200:
        return None
    try:
        root = ET.fromstring(resp.text)
    except ET.ParseError:
        return None
    items = root.findall(".//item")
    if not items:
        return None
    return [
        (
            item.findtext("guid") or "",
            item.findtext("title") or "",
            item.findtext("link") or "",
        )
        for item in items
    ]


def main():
    print(
        f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}] Revisando @cclasamericas..."
    )

    posts = fetch_feed()

    if posts is None:
        notify(
            title="⚠️ Monitor: feed caído",
            message="El feed RSS.app no responde o está vacío. Crea cuenta nueva en rss.app y actualiza el secret RSS_FEED_URL.",
            priority=4,
            tags="warning",
        )
        print("[WARN] Feed no disponible. Notificación enviada. Saliendo con exit 0.")
        sys.exit(0)

    seen = load_seen()
    new_seen = set(seen)
    found = False

    for guid, title, link in posts:
        new_seen.add(guid)
        if KEYWORD.lower() in title.lower():
            if guid not in seen:
                print(f"[MATCH] '{KEYWORD}' encontrado: {link}")
                notify(
                    title="🏃 ¡Ruta Nocturna detectada!",
                    message=f"{title}\n{link}",
                    priority=4,
                    tags="running,tada",
                )
                found = True
            else:
                print(f"[SKIP]  Ya notificado: {guid}")

    if not found:
        print(f"[OK] Sin novedades sobre '{KEYWORD}'.")

    save_seen(new_seen)
    sys.exit(0)


if __name__ == "__main__":
    main()
