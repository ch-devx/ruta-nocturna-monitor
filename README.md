# Ruta Nocturna Monitor 🏃

Monitorea automáticamente el Instagram de CC Las Américas (@cclasamericas) cada 2 horas.
Si detecta una publicación que mencione "ruta nocturna", te manda una notificación push
a tu teléfono vía **ntfy** con el link directo al post.

---

## Setup (una sola vez)

### 1. Crear el repositorio en GitHub

- Crea un repo **privado** llamado `ruta-nocturna-monitor`
- Sube todos estos archivos tal cual

### 2. Configurar el NTFY_TOPIC como Secret

1. En tu teléfono, descarga la app **ntfy** (Google Play, busca "ntfy" de binwiederhier)
2. Elige un topic name único, ej: `carlos-ruta-veinticinco-2026` (mientras más raro, más seguro)
3. En la app: toca **+** → escribe tu topic → Subscribe
4. En GitHub: ve a tu repo → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**
   - Name: `NTFY_TOPIC`
   - Value: el topic que elegiste (ej: `carlos-ruta-veinticinco-2026`)
   - Guardar

### 3. Activar GitHub Actions

- Ve a la pestaña **Actions** de tu repo
- Si te pide confirmación para activar workflows, acéptala
- Listo. El workflow corre solo cada 2 horas.

### 4. Prueba manual

- En la pestaña **Actions** → selecciona **Ruta Nocturna Monitor** → **Run workflow**
- Verifica que corra sin errores y que el log muestre posts revisados

---

## Cómo funciona

```
Cada 2 horas GitHub levanta una VM gratuita →
  Carga el perfil público de @cclasamericas →
  Revisa los últimos 12 posts →
  Si alguno contiene "ruta nocturna" (sin importar mayúsculas) →
    Y no lo habías notificado antes →
      Manda push notification a tu teléfono con el link
  Guarda los IDs de posts vistos en seen_posts.json para no repetir notificaciones
```

## Archivos

| Archivo | Qué hace |
|---|---|
| `monitor.py` | Script principal |
| `requirements.txt` | Dependencias Python |
| `.github/workflows/monitor.yml` | Automatización con GitHub Actions |
| `seen_posts.json` | Se crea solo, guarda posts ya notificados |

---

## Notas

- El repo debe ser **privado** para que el NTFY_TOPIC no sea visible públicamente
- Si Instagram bloquea temporalmente la request, el script simplemente falla ese ciclo y reintenta 2 horas después
- Puedes correrlo manualmente desde la pestaña Actions cuando quieras
