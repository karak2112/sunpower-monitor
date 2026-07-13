# Solar Monitor

Local, cloud-free monitoring for a home SunPower PVS6 photovoltaic supervisor.

This project collects telemetry from **your own** PVS6 on **your own** LAN, stores history in a local time-series database, and serves a mobile-friendly web UI. The PVS6 is never exposed directly to browsers or phones—the collector and API mediate all access.

## Status

**MVP online (Phases 0–4).**

| Piece | Where |
|-------|--------|
| Web UI (PWA) | http://127.0.0.1:3080 |
| API | http://127.0.0.1:8000 (`/health`, `/v1/*`) |
| Database | TimescaleDB on port 5432 |
| Collector | Docker service; poll interval **300s** |

Compose defaults to **fixture** replay (safe, no PVS contact). Live collection uses `COLLECTOR_SOURCE=varserver` plus `PVS_PASSWORD` in a gitignored `.env` (see below).

## Site profile (sanitized)

| Item | Value |
|------|--------|
| Supervisor | SunPower PVS6 |
| Firmware | Build 61846 (authenticated varserver local API) |
| Array | 44 × SunPower X-Series 360 W with microinverters |
| Meters | Production (`PVS6M0400p`) + consumption (`PVS6M0400c`) |
| Battery | None |
| PVS LAN path | Wi-Fi on home LAN (`192.168.1.96` in local `.env`) |
| Display timezone | America/Chicago (timestamps stored in UTC) |
| Host | Windows PC via Docker Compose (portable later) |

## Architecture

```
PVS6 (LAN) → Python collector (read-only) → TimescaleDB
                                              ↑
                         PWA / phone  ←  FastAPI
```

See [docs/architecture.md](docs/architecture.md) and [docs/adr/](docs/adr/).

## Quick start

**Prerequisites:** Docker Desktop running.

```powershell
cd c:\Users\tony\Projects\solar-monitor
Copy-Item .env.example .env
# Edit .env: set POSTGRES_PASSWORD at minimum; for live PVS see "Live varserver" below
docker compose up --build -d
```

Then open:

- **App:** http://127.0.0.1:3080
- **API health:** http://127.0.0.1:8000/health

```powershell
curl.exe -s http://127.0.0.1:8000/health
curl.exe -s http://127.0.0.1:8000/v1/current
```

Stop:

```powershell
docker compose down
```

### Live varserver (optional)

`.env` is gitignored. To poll the real PVS (read-only, 300s):

```env
COLLECTOR_SOURCE=varserver
PVS_HOST=192.168.1.96
PVS_USERNAME=ssm_owner
PVS_PASSWORD=xxxxx
PVS_POLL_INTERVAL_SECONDS=300
```

`PVS_PASSWORD` is the **last 5 characters of the PVS serial** (SunStrong owner auth).

```powershell
docker compose up -d collector
docker compose logs -f collector
```

Expect `source=varserver` and `collector_loop_ok`. To return to safe fixtures: set `COLLECTOR_SOURCE=fixture` and recreate the collector.

### Web UI development

```powershell
cd apps\web
npm install
npm run dev
```

http://127.0.0.1:5173 proxies `/api` to the API on :8000.

## What “Home Assistant” means here

[Home Assistant](https://www.home-assistant.io/) is optional home-automation software. This stack is **standalone** and does not require HA. An HA/MQTT integration may come later.

## Repository layout

```
apps/web/          PWA (Vite + React)
apps/api/          FastAPI
services/collector Read-only PVS collector
packages/store     Shared DB ingest/query helpers
database/          SQL migrations + seed
fixtures/pvs6/     Redacted response fixtures
infrastructure/    Dockerfiles, nginx
docs/              Architecture, discovery, ADRs, safety
docker-compose.yml
.env.example       Template (no secrets)
```

## Safety

- Read-only PVS interaction unless you explicitly authorize otherwise.
- Default / recommended poll interval: **300 seconds**.
- No subnet scans, firmware changes, or uploading captures/serials.
- Do not expose the PVS or unauthenticated APIs to the public internet.
- See [SECURITY.md](SECURITY.md) and [docs/polling-safety.md](docs/polling-safety.md).

## Documentation

| Doc | Purpose |
|-----|---------|
| [docs/architecture.md](docs/architecture.md) | System design |
| [docs/data-model.md](docs/data-model.md) | Schema and metrics |
| [docs/mobile-ui.md](docs/mobile-ui.md) | PWA screens |
| [docs/pvs6-discovery.md](docs/pvs6-discovery.md) | Observed PVS interfaces |
| [docs/prior-art.md](docs/prior-art.md) | Related projects and licenses |
| [docs/polling-safety.md](docs/polling-safety.md) | Hardware protection policy |
| [docs/backup-restore.md](docs/backup-restore.md) | Database backup/restore |
| [docs/troubleshooting.md](docs/troubleshooting.md) | Common issues |
| [docs/adr/](docs/adr/) | Architecture Decision Records |

## License

[MIT](LICENSE). Third-party projects retain their own licenses; see [docs/prior-art.md](docs/prior-art.md).
