```markdown
# Ruta Nocturna Monitor 🏃

Monitorea automáticamente el Instagram de CC Las Américas (@cclasamericas) cada 2 horas.
Si detecta una publicación que mencione "ruta nocturna", manda una notificación push
al teléfono vía **ntfy** con el link directo al post.

No requiere la laptop encendida. Corre completamente en GitHub Actions de forma gratuita.

---

## Cómo funciona

```
Cada 2 horas GitHub levanta una VM gratuita
  → Hace GET a la URL del feed RSS (rss.app) del perfil de @cclasamericas
  → Parsea los posts del feed
  → Si alguno contiene "ruta nocturna" (sin importar mayúsculas)
      → Y no lo había notificado antes
          → Manda push notification al teléfono con el link
  → Guarda los IDs de posts vistos en seen_posts.json para no repetir notificaciones
```

El feed RSS lo provee **rss.app**, que actúa como intermediario entre GitHub y Instagram.
Esto evita el bloqueo 429 que Instagram aplica a las IPs de GitHub Actions cuando se
intenta hacer scraping directo.

---

## Archivos

| Archivo | Qué hace |
|---|---|
| `monitor.py` | Script principal |
| `.github/workflows/monitor.yml` | Automatización con GitHub Actions (cada 2h) |
| `seen_posts.json` | Se gestiona solo — guarda posts ya notificados para no repetir |

> `requirements.txt` no es necesario — el workflow instala `requests` directamente
> con `pip install requests` en el step de dependencias.

---

## Secrets configurados en el repo

Están en **Settings → Secrets and variables → Actions**.

| Secret | Qué es |
|---|---|
| `NTFY_TOPIC` | El topic de ntfy al que llegan las notificaciones en el teléfono |
| `RSS_FEED_URL` | La URL del feed RSS generado en rss.app para @cclasamericas |

---

## Setup desde cero (si hay que replicarlo)

**1. RSS feed**
- Ir a rss.app, pegar `https://www.instagram.com/cclasamericas/`, generar el feed
- Guardar la URL resultante como secret `RSS_FEED_URL`

**2. ntfy**
- Descargar la app **ntfy** en Android (Google Play, desarrollador: binwiederhier)
- Crear un topic único, ej: `carlos-ruta-2026`, suscribirse
- Guardar el topic como secret `NTFY_TOPIC`

**3. Activar GitHub Actions**
- Pestaña Actions del repo → confirmar que el workflow está activo
- Probar con Run workflow manual

---

## Troubleshooting

**El workflow dice `[SKIP]` y no llega notificación al testear**
El post ya estaba en `seen_posts.json`. Editar el archivo en el repo y reemplazar
el contenido con `[]`, luego correr el workflow de nuevo.

**El workflow falla con error de feed**
Verificar que el secret `RSS_FEED_URL` esté bien escrito (mayúsculas, sin espacios).
También puede ser que rss.app haya caído temporalmente — reintentará en 2 horas.

**Llega notificación "feed caído, renueva RSS.app"**
El feed del plan free de rss.app expira cada ~10–15 días. Cuando ocurre:
1. Ir a rss.app con una cuenta nueva (cuenta de email desechable)
2. Pegar `https://www.instagram.com/cclasamericas/` y generar el feed
3. Copiar la nueva URL
4. En el repo: Settings → Secrets → `RSS_FEED_URL` → Update
5. El siguiente run automático (o uno manual) ya usará el nuevo feed

**Warning de Node.js 20 en el log**
Es un aviso de GitHub sobre versiones futuras, no afecta el funcionamiento.
Habrá que actualizar `actions/checkout@v4` y `actions/setup-python@v5` cuando
GitHub deprece Node.js 20 en los runners (previsto para mediados de 2026).
```