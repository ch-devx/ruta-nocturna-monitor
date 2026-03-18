import os
import json
import requests
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
IG_PROFILE  = "cclasamericas"
KEYWORD     = "ruta nocturna"
NTFY_TOPIC  = os.environ.get("NTFY_TOPIC", "")
SEEN_FILE   = "seen_posts.json"
# ─────────────────────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "es-VE,es;q=0.9,en;q=0.8",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "X-IG-App-ID": "936619743392459",
}


def load_seen() -> set:
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_seen(seen: set):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)


def send_notification(post_url: str, caption_preview: str):
    if not NTFY_TOPIC:
        print("[WARN] NTFY_TOPIC no configurado.")
        return

    payload = {
        "topic":   NTFY_TOPIC,
        "title":   "🏃 ¡Ruta Nocturna detectada!",
        "message": f"CC Las Américas publicó sobre la ruta nocturna.\n\n{caption_preview[:200]}",
        "actions": [{"action": "view", "label": "Ver publicación", "url": post_url}],
        "priority": 4,
    }

    try:
        r = requests.post("https://ntfy.sh", json=payload, timeout=10)
        r.raise_for_status()
        print(f"[OK] Notificación enviada → {NTFY_TOPIC}")
    except Exception as e:
        print(f"[ERROR] Notificación fallida: {e}")


def fetch_posts() -> list[dict]:
    url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={IG_PROFILE}"
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    data = r.json()

    user = data["data"]["user"]
    print(f"[INFO] Perfil cargado: @{IG_PROFILE} (id: {user['id']})")

    posts_raw = user.get("edge_owner_to_timeline_media", {}).get("edges", [])
    posts = []
    for edge in posts_raw:
        node = edge["node"]
        shortcode = node.get("shortcode", "")
        caption_edges = node.get("edge_media_to_caption", {}).get("edges", [])
        caption = caption_edges[0]["node"]["text"] if caption_edges else ""
        posts.append({"shortcode": shortcode, "caption": caption})

    print(f"[INFO] {len(posts)} posts obtenidos.")
    return posts


def check_profile():
    print(f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}] Revisando @{IG_PROFILE}...")

    try:
        posts = fetch_posts()
    except Exception as e:
        print(f"[ERROR] No se pudo obtener posts: {e}")
        raise SystemExit(1)

    seen     = load_seen()
    new_seen = set(seen)
    found    = False

    for post in posts:
        shortcode = post["shortcode"]
        caption   = post["caption"].lower()
        post_url  = f"https://www.instagram.com/p/{shortcode}/"
        new_seen.add(shortcode)

        if KEYWORD in caption:
            if shortcode not in seen:
                print(f"[MATCH] Post nuevo con '{KEYWORD}': {post_url}")
                send_notification(post_url, post["caption"])
                found = True
            else:
                print(f"[SKIP]  Ya notificado: {shortcode}")

    if not found:
        print(f"[OK] Sin novedades sobre '{KEYWORD}'.")

    save_seen(new_seen)


if __name__ == "__main__":
    check_profile()
