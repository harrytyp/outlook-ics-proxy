# outlook-ics-proxy

> 📅 A lightweight, self-hosted HTTP proxy for ICS calendar URLs with Outlook Classic support.

Bring your Google Calendar, Nextcloud, and other CalDAV-compatible calendars to Outlook Classic – with automatic refresh and browser User-Agent spoofing to bypass Microsoft's blocking.

[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)](https://www.python.org/)

## ⚡ Quick Start

```bash
# 1. Clone & enter directory
git clone https://github.com/yourusername/outlook-ics-proxy.git
cd outlook-ics-proxy

# 2. Build
docker compose build

# 3. Run
docker compose up -d
```

✅ Service runs on `http://127.0.0.1:8080`  
✅ Auto-restarts with `restart: unless-stopped`  
✅ Health checks enabled  

## 🎯 Why This Project?

Microsoft Outlook Classic **blocks ICS imports from Google Calendar** and other providers without a proper browser User-Agent. This lightweight proxy:

- ✅ **Fetches ICS server-side** with a real browser UA
- ✅ **Forwards to Outlook** as `text/calendar`
- ✅ **5-min in-memory caching** to reduce upstream requests
- ✅ **SSRF-protected** (blocks private IPs, localhost, reserved IPs)
- ✅ **Minimal** (~300 LOC Python/Flask)
- ✅ **Docker-ready** (production WSGI with Gunicorn)
- ✅ **Portable** (easy to move to home server later)

## 📋 Usage

### Add to Outlook Classic

1. **Get your Google Calendar ICS URL:**
   - Open Google Calendar → Calendar Settings
   - Scroll to "Integrate calendar"
   - Copy the **private iCal URL** (contains a secret token)

2. **URL-encode it** (percent-encode):
   ```bash
   python -c "import urllib.parse; print(urllib.parse.quote('YOUR_ICS_URL', safe=':/?#[]@!$&\\'()*+,;='))"
   ```

3. **In Outlook Classic:**
   - File → Options → Calendar → Internet Calendars
   - Paste: `http://127.0.0.1:8080/proxy?url=YOUR_ENCODED_URL`
   - Click Add
   - Calendar imports & auto-refreshes every ~60 min

### Example URL

```
http://127.0.0.1:8080/proxy?url=https%3A%2F%2Fcalendar.google.com%2Fcalendar%2Fical%2Fyour-email%40gmail.com%2Fprivate-token%2Fbasic.ics
```

## 🔧 API Reference

### `GET /proxy?url=<encoded-url>`

Proxy an external ICS URL with browser User-Agent.

**Parameters:**
- `url` (required): Percent-encoded ICS URL (http/https only)

**Response:**
- Success (200–299): ICS calendar as `text/calendar; charset=utf-8`
- Invalid URL (400): JSON error
- Fetch error (502): JSON error with upstream failure reason

**Example:**
```bash
curl 'http://127.0.0.1:8080/proxy?url=https%3A%2F%2Fcalendar.google.com%2Fcalendar%2Fical%2Fuser%40gmail.com%2Fbasic.ics'
```

### `GET /healthz`

Health check endpoint.

**Response:** `{"status": "ok"}` (200)

### `GET /`

Service info and available endpoints.

## 🔐 Security

**SSRF Protection:**
- Blocks requests to private IPs: `10.0.0.0/8`, `192.168.0.0/16`, `172.16.0.0/12`
- Blocks localhost, link-local, reserved IPs, `0.0.0.0`, `255.255.255.255`
- Only allows `http://` and `https://` schemes

**Privacy:**
- Service runs **only on `127.0.0.1:8080`** (local machine only, not LAN/Internet)
- No authentication needed (local-only binding)
- Your Google Calendar private token never leaves your machine
- All requests logged to stdout (for Docker log aggregation)

**Container Security:**
- Runs as non-root user (`appuser:1000:1000`)
- Alpine base image (~120 MB)
- Multi-stage build (minimal final image)
- No unnecessary packages

## 📦 Features

- **Minimal dependencies**: Flask, requests, Gunicorn only
- **In-memory caching** with 5-min TTL (configurable via code)
- **Request timeouts** (10s upstream, 5s health check)
- **Size limits** (5 MB max response)
- **Structured logging** to stdout
- **Health checks** integrated in docker-compose
- **Restart policy**: `unless-stopped` (auto-restart on reboot)

## 🐳 Docker

### Build from source
```bash
docker compose build
```

### Run
```bash
docker compose up -d
```

### View logs
```bash
docker compose logs -f outlook-ics-proxy
```

### Stop
```bash
docker compose down
```

## 📂 Project Structure

```
.
├── app/
│   └── proxy.py              # Main Flask app (300 LOC)
├── Dockerfile                # Multi-stage, Alpine, non-root
├── docker-compose.yml        # Production config
├── requirements.txt          # Python dependencies
├── .env.example              # Environment template
├── .gitignore                # Git ignore rules
├── README.md                 # This file
├── LICENSE                   # MIT license
└── CONTRIBUTING.md           # Contribution guide
```

## 🚀 Architecture Decisions

### Why Docker?

| Aspect | Docker | Bare Script |
|--------|--------|------------|
| **Isolation** | ✅ System-independent | ❌ Depends on system Python |
| **Restarts** | ✅ Auto via `restart: unless-stopped` | ❌ Manual setup required |
| **Logging** | ✅ Centralized via `docker logs` | ❌ Separate log file |
| **Portability** | ✅ Identical everywhere | ❌ Path/environment issues |
| **Security** | ✅ Non-root, minimal image | ❌ Full user permissions |
| **Maintenance** | ✅ Easy to move to home server | ❌ Dependencies drift |

### Why Gunicorn over Flask dev server?

Flask's development server:
- Only binds to `127.0.0.1` by default
- Cannot be reached from Windows host in Docker Desktop
- Single-threaded, slow

Gunicorn:
- Binds to `0.0.0.0:8080` (reachable from Windows)
- Multi-worker (2 workers by default)
- Production-ready
- Properly logs access requests

### Why Browser User-Agent?

Google Calendar and similar services check User-Agent headers. Outlook's default UA is either missing or generic, causing rejection. A real browser UA (`Mozilla/5.0 Chrome/91...`) is accepted as legitimate traffic. **This is not hacking – it's normal web behavior.**

### Why only `127.0.0.1` (by default)?

- **Security**: No LAN/Internet exposure
- **Clarity**: "Local service, not for network"
- **Flexibility**: Change to `0.0.0.0:8080` + reverse proxy for production

## 🔧 Troubleshooting

### Container won't start

```bash
docker compose logs outlook-ics-proxy
```

Common issues:
- Port `8080` already in use → change `docker-compose.yml`
- Old image cached → `docker compose build --no-cache`

### Outlook doesn't import calendar

1. Check if service is running: `docker compose ps` → should show `(healthy)`
2. Verify URL is percent-encoded (no spaces, special chars raw)
3. Test manually:
   ```bash
   curl 'http://127.0.0.1:8080/proxy?url=YOUR_ENCODED_URL'
   ```
4. Check logs: `docker compose logs -f outlook-ics-proxy`

### Cache not working / Always fetching fresh

Cache is **in-memory only** (5 min TTL by default). To configure:

Edit `app/proxy.py`, find `CACHE_TTL = 300` and adjust (seconds).

### SSRF error when adding URL

If you get "Private/reserved IP blocked", the URL points to a local IP. Only public URLs (Google Calendar, Nextcloud on public domain, etc.) are allowed.

## 📝 License

MIT – see [LICENSE](LICENSE) for details.

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Ideas for improvements:**
- [ ] Persistent Redis/SQLite cache
- [ ] Prometheus metrics endpoint
- [ ] Support for basic auth in upstream URL
- [ ] Rate limiting
- [ ] Multi-calendar dashboard (UI)

## ❓ FAQ

**Q: Will my Google Calendar private token leak?**  
A: No. The service runs locally on your machine. The token is never sent to the internet, only between Outlook and `localhost:8080`.

**Q: Can I edit events in Outlook and have them sync back to Google Calendar?**  
A: No, this is read-only. ICS is a static format. For bidirectional sync, you'd need CalDAV + OAuth2, which is complex. Keep Google Calendar as source of truth.

**Q: What if I restart my computer?**  
A: Docker Desktop will restart automatically (if configured to do so), and `outlook-ics-proxy` will come back up due to `restart: unless-stopped`.

**Q: Can I move this to my home server?**  
A: Yes, easily. Copy the files, run `docker compose up -d` on the server. Optionally change port binding from `127.0.0.1:8080` to `0.0.0.0:8080` and add a reverse proxy (nginx) in front.

**Q: How often does Outlook refresh?**  
A: Typically every 60 minutes. The 5-min proxy cache helps avoid hammering Google Calendar between Outlook refreshes.

**Q: Multiple calendars?**  
A: Yes, just add multiple URLs in Outlook, each with a different ICS URL. Each will be cached separately.

---

**Built with ❤️ for Outlook Classic users.**
