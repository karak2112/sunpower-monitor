# Data model (draft)

Full schema lands in Phase 3. Entities planned:

- **Site** — id, name, timezone (`America/Chicago` display), optional geo only if enabled
- **Supervisor** — PVS id, hw/fw, last communication, capabilities, collection method
- **Device** — stable internal id, PVS id, type, model, redacted serial handling, status, parent links
- **Panel / Microinverter** — layout row/col (user-editable), rated W (360), enabled
- **Measurement** — UTC time, device, metric, value, unit, quality, source, parser version
- **RawObservation** — optional compressed payload, hash, retention-limited

Site profile seed facts: 44 × 360 W microinverters, no battery.
