# Troubleshooting

## Phase 0

- Empty runtime: expected. No collector yet.
- Do not probe the PVS until [discovery/phase-1-plan.md](discovery/phase-1-plan.md) is approved.

## Later phases (stubs)

- Collector cannot reach PVS → check Wi-Fi, `PVS_HOST`, AP client isolation, TLS.
- Stale data → check circuit breaker state and poll interval logs.
- Missing panels at night → expected communication drop; distinguish from daylight faults in alerts (Phase 5+).
