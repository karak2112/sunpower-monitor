# Solar Monitor

Local, cloud-free monitoring for a home SunPower PVS6 photovoltaic supervisor.

This project collects telemetry from **your own** PVS6 on **your own** LAN, stores history in a local time-series database, and serves a mobile-friendly web UI. The PVS6 is never exposed directly to browsers or phones—the collector and API mediate all access.

## Status

**Phase 2 checkpoint — collector scaffolding + authenticated discovery complete.**

- Redacted fixtures in `fixtures/pvs6/`
- Read-only Python collector in `services/collector/` (fixture tests pass)
- No continuous polling loop yet; no database/API/UI yet

Do not enable PVS writes or WebSocket without a new written plan.

## Site profile (sanitized)

| Item | Value |
|------|--------|
| Supervisor | SunPower PVS6 |
| Firmware | Build 61846 (varserver local API available) |
| Array | 44 × SunPower X-Series 360 W with microinverters |
| Battery | None |
| PVS LAN path | Wi-Fi interface on home LAN |
| Display timezone | America/Chicago (timestamps stored in UTC) |
| Dev / always-on host | This Windows PC (Docker Compose; portable to other hosts later) |

## What “Home Assistant” means here

[Home Assistant](https://www.home-assistant.io/) is optional open-source home-automation software some people already run for lights, sensors, and energy dashboards. This project is a **standalone** stack and does **not** require Home Assistant. Community PVS integrations for HA exist; we may optionally publish MQTT or an HA integration later.

## Architecture (target)

```
PVS6 (LAN) → Python collector (read-only) → TimescaleDB
                                              ↑
                         PWA / phone  ←  FastAPI
```

See [docs/architecture.md](docs/architecture.md) and [docs/adr/0001-architecture-choice.md](docs/adr/0001-architecture-choice.md).

## Repository layout

```
apps/           # web (PWA), api, mobile (later)
services/       # collector
packages/       # shared clients / domain (later)
database/       # migrations, seeds
fixtures/pvs6/  # redacted response fixtures for tests
infrastructure/ # docker, monitoring
scripts/
docs/           # architecture, discovery, ADRs, safety
tests/
```

## Quick start

Not available yet. After Phase 2+, expect:

```bash
cp .env.example .env
# edit .env with local PVS host only — never commit secrets
docker compose up -d
```

## Safety

- Read-only interaction with the PVS6 unless you explicitly authorize otherwise.
- Conservative polling (default target: **300 seconds**).
- No subnet scans, firmware changes, or cloud uploads of captures/serials.
- See [SECURITY.md](SECURITY.md) and [docs/polling-safety.md](docs/polling-safety.md).

## Documentation

| Doc | Purpose |
|-----|---------|
| [docs/architecture.md](docs/architecture.md) | System design |
| [docs/prior-art.md](docs/prior-art.md) | Community / official projects and licenses |
| [docs/pvs6-discovery.md](docs/pvs6-discovery.md) | Observed interfaces (sanitized) |
| [docs/polling-safety.md](docs/polling-safety.md) | Hardware protection policy |
| [docs/adr/](docs/adr/) | Architecture Decision Records |

## License

To be decided (project-local). Third-party projects retain their own licenses; see `docs/prior-art.md`.
