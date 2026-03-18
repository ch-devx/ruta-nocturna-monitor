import instaloader
import os
import json
import requests
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
IG_PROFILE       = "cclasamericas"
KEYWORD          = "ruta nocturna"
NTFY_TOPIC       = os.environ.get("NTFY_TOPIC", "")        # Set as GitHub secret
SEEN_FILE        = "seen_posts.json"
POSTS_TO_CHECK   = 12   # últimos N posts a revisar
# ─────────────────────────────────────────────────────────────────────────────


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
        print("[WARN] NTFY_TOPIC no configurado, no se enviará notificación.")
        return

    payload = {
        "topic":    NTFY_TOPIC,
        "title":    "🏃 ¡Ruta Nocturna detectada!",
        "message":  f"CC Las Américas publicó algo sobre la ruta nocturna.\n\n{caption_preview[:200]}",
        "actions": [
            {
                "action": "view",
                "label":  "Ver publicación",
                "url":    post_url
            }
        ],
        "priority": 4
    }

    try:
        r = requests.post("https://ntfy.sh", json=payload, timeout=10)
        r.raise_for_status()
        print(f"[OK] Notificación enviada → {NTFY_TOPIC}")
    except Exception as e:
        print(f"[ERROR] No se pudo enviar notificación: {e}")


def check_profile():
    print(f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}] Revisando @{IG_PROFILE}...")

    L = instaloader.Instaloader(
        download_pictures=False,
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        quiet=True
    )

    try:
        profile = instaloader.Profile.from_username(L.context, IG_PROFILE)
    except Exception as e:
        print(f"[ERROR] No se pudo cargar el perfil: {e}")
        return

    seen = load_seen()
    new_seen = set(seen)
    found_any = False

    posts_checked = 0
    for post in profile.get_posts():
        if posts_checked >= POSTS_TO_CHECK:
            break
        posts_checked += 1

        post_id  = str(post.shortcode)
        caption  = (post.caption or "").lower()
        post_url = f"https://www.instagram.com/p/{post.shortcode}/"

        if KEYWORD in caption:
            if post_id not in seen:
                print(f"[MATCH] Post nuevo con '{KEYWORD}': {post_url}")
                send_notification(post_url, post.caption or "")
                found_any = True
            else:
                print(f"[SKIP]  Post ya notificado: {post_id}")

        new_seen.add(post_id)

    if not found_any:
        print(f"[OK] {posts_checked} posts revisados. Sin novedades.")

    save_seen(new_seen)


if __name__ == "__main__":
    check_profile()
