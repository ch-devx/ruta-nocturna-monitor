import os
import json
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

# ── Config ────────────────────────────────────────────────────────────────────
IG_PROFILE  = "cclasamericas"
KEYWORD     = "ruta nocturna"
NTFY_TOPIC  = os.environ.get("NTFY_TOPIC", "")
IG_USER     = os.environ.get("IG_USER", "")
IG_PASS     = os.environ.get("IG_PASS", "")
SEEN_FILE   = "seen_posts.json"
SESSION_FILE = "ig_session.json"
# ─────────────────────────────────────────────────────────────────────────────


def load_seen() -> set:
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()


def save_seen(seen: set):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen), f)


def send_notification(post_url: str, caption: str):
    if not NTFY_TOPIC:
        print("[WARN] NTFY_TOPIC no configurado.")
        return

    payload = {
        "topic":   NTFY_TOPIC,
        "title":   "🏃 ¡Ruta Nocturna detectada!",
        "message": f"CC Las Américas publicó sobre la ruta nocturna.\n\n{caption[:200]}",
        "actions": [{"action": "view", "label": "Ver publicación", "url": post_url}],
        "priority": 4,
    }

    try:
        r = requests.post("https://ntfy.sh", json=payload, timeout=10)
        r.raise_for_status()
        print(f"[OK] Notificación enviada → {NTFY_TOPIC}")
    except Exception as e:
        print(f"[ERROR] Notificación fallida: {e}")


def do_login(page):
    print("[INFO] Haciendo login...")
    page.goto("https://www.instagram.com/accounts/login/", wait_until="networkidle")
    page.wait_for_timeout(2000)

    page.fill('input[name="username"]', IG_USER)
    page.wait_for_timeout(500)
    page.fill('input[name="password"]', IG_PASS)
    page.wait_for_timeout(500)
    page.click('button[type="submit"]')

    # Esperar que cargue el feed principal
    try:
        page.wait_for_url("https://www.instagram.com/", timeout=15000)
        print("[INFO] Login exitoso.")
    except PlaywrightTimeout:
        # A veces redirige a /accounts/onetap o similar, igual está logueado
        print("[INFO] Login completado (redirección alternativa).")

    page.wait_for_timeout(2000)

    # Cerrar popups típicos de Instagram (notificaciones, etc.)
    for selector in ['button:has-text("Ahora no")', 'button:has-text("Not Now")', 'button:has-text("Cancel")']:
        try:
            btn = page.locator(selector).first
            if btn.is_visible(timeout=3000):
                btn.click()
                page.wait_for_timeout(1000)
        except Exception:
            pass


def fetch_posts(page) -> list[dict]:
    print(f"[INFO] Navegando a @{IG_PROFILE}...")
    page.goto(f"https://www.instagram.com/{IG_PROFILE}/", wait_until="networkidle")
    page.wait_for_timeout(3000)

    # Extraer links de posts del grid
    post_links = page.locator('a[href*="/p/"]').all()
    shortcodes = []
    seen_sc = set()
    for link in post_links:
        href = link.get_attribute("href") or ""
        # href es del tipo /p/SHORTCODE/
        parts = [p for p in href.split("/") if p]
        if len(parts) == 2 and parts[0] == "p":
            sc = parts[1]
            if sc not in seen_sc:
                seen_sc.add(sc)
                shortcodes.append(sc)
        if len(shortcodes) >= 12:
            break

    print(f"[INFO] {len(shortcodes)} posts encontrados en el grid.")

    posts = []
    for sc in shortcodes:
        post_url = f"https://www.instagram.com/p/{sc}/"
        try:
            page.goto(post_url, wait_until="networkidle")
            page.wait_for_timeout(2000)

            # Intentar obtener el caption del meta tag og:description
            caption = ""
            meta = page.locator('meta[property="og:description"]')
            if meta.count() > 0:
                caption = meta.get_attribute("content") or ""

            posts.append({"shortcode": sc, "url": post_url, "caption": caption})
            print(f"[INFO] Post {sc}: {caption[:60]}...")
        except Exception as e:
            print(f"[WARN] No se pudo leer post {sc}: {e}")
            posts.append({"shortcode": sc, "url": post_url, "caption": ""})

    return posts


def check_profile():
    print(f"[{datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}] Revisando @{IG_PROFILE}...")

    if not IG_USER or not IG_PASS:
        print("[ERROR] IG_USER o IG_PASS no configurados.")
        raise SystemExit(1)

    seen     = load_seen()
    new_seen = set(seen)
    found    = False

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800},
            locale="es-VE",
        )
        page = context.new_page()

        try:
            do_login(page)
            posts = fetch_posts(page)
        except Exception as e:
            print(f"[ERROR] Falló la ejecución: {e}")
            browser.close()
            raise SystemExit(1)

        browser.close()

    for post in posts:
        sc      = post["shortcode"]
        caption = post["caption"].lower()
        new_seen.add(sc)

        if KEYWORD in caption:
            if sc not in seen:
                print(f"[MATCH] '{KEYWORD}' encontrado: {post['url']}")
                send_notification(post["url"], post["caption"])
                found = True
            else:
                print(f"[SKIP]  Ya notificado: {sc}")

    if not found:
        print(f"[OK] Sin novedades sobre '{KEYWORD}'.")

    save_seen(new_seen)


if __name__ == "__main__":
    check_profile()
