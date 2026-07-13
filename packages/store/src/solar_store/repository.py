from __future__ import annotations

from datetime import datetime
from typing import Any

import asyncpg

from solar_store.ids import HOME_SITE_ID


class Repository:
    def __init__(self, pool: asyncpg.Pool) -> None:
        self._pool = pool

    async def health(self) -> dict[str, Any]:
        async with self._pool.acquire() as conn:
            db_ok = await conn.fetchval("SELECT 1")
            last_run = await conn.fetchrow(
                """
                SELECT id, started_at, finished_at, status, source, message,
                       meter_count, inverter_count, measurement_rows
                FROM collector_runs
                ORDER BY started_at DESC
                LIMIT 1
                """
            )
            latest = await conn.fetchval(
                "SELECT max(collected_at) FROM measurements"
            )
            inverter_seen = await conn.fetchval(
                """
                SELECT count(*) FROM devices
                WHERE site_id = $1::uuid AND device_type = 'inverter'
                """,
                HOME_SITE_ID,
            )
        return {
            "database_ok": db_ok == 1,
            "latest_measurement_at": latest.isoformat() if latest else None,
            "inverter_devices": int(inverter_seen or 0),
            "last_collector_run": dict(last_run) if last_run else None,
        }

    async def current_overview(self) -> dict[str, Any]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT DISTINCT ON (m.metric)
                    m.metric, m.value, m.unit, m.time, m.collected_at, m.quality, m.source
                FROM measurements m
                JOIN devices d ON d.id = m.device_id
                WHERE d.site_id = $1::uuid AND d.device_type = 'site' AND d.pvs_path_id = 'livedata'
                ORDER BY m.metric, m.time DESC
                """,
                HOME_SITE_ID,
            )
            inverters = await conn.fetch(
                """
                SELECT d.pvs_path_id, d.name, d.model, d.last_seen_at,
                       m.value AS power_kw, m.time AS power_time, m.collected_at
                FROM devices d
                LEFT JOIN LATERAL (
                    SELECT value, time, collected_at
                    FROM measurements mm
                    WHERE mm.device_id = d.id AND mm.metric = 'power_kw'
                    ORDER BY mm.time DESC
                    LIMIT 1
                ) m ON TRUE
                WHERE d.site_id = $1::uuid AND d.device_type = 'inverter'
                ORDER BY (d.pvs_path_id)::int
                """,
                HOME_SITE_ID,
            )
            meters = await conn.fetch(
                """
                SELECT d.pvs_path_id, d.name, d.model, d.last_seen_at,
                       m.value AS power_kw, m.time AS power_time
                FROM devices d
                LEFT JOIN LATERAL (
                    SELECT value, time
                    FROM measurements mm
                    WHERE mm.device_id = d.id AND mm.metric = 'power_kw'
                    ORDER BY mm.time DESC
                    LIMIT 1
                ) m ON TRUE
                WHERE d.site_id = $1::uuid AND d.device_type = 'meter'
                ORDER BY (d.pvs_path_id)::int
                """,
                HOME_SITE_ID,
            )

        livedata = {r["metric"]: {
            "value": r["value"],
            "unit": r["unit"],
            "time": r["time"].isoformat(),
            "collected_at": r["collected_at"].isoformat(),
            "quality": r["quality"],
            "source": r["source"],
        } for r in rows}

        return {
            "site_id": HOME_SITE_ID,
            "livedata": livedata,
            "meters": [dict(r) for r in meters],
            "inverters": [dict(r) for r in inverters],
            "inverter_power_kw_sum": round(
                sum(float(r["power_kw"]) for r in inverters if r["power_kw"] is not None),
                6,
            ),
        }

    async def history(
        self,
        *,
        metric: str,
        device_type: str | None,
        pvs_path_id: str | None,
        start: datetime,
        end: datetime,
        limit: int = 5000,
    ) -> list[dict[str, Any]]:
        if limit > 20000:
            limit = 20000
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT m.time, m.value, m.unit, m.quality, m.source, m.collected_at,
                       d.device_type, d.pvs_path_id, d.name
                FROM measurements m
                JOIN devices d ON d.id = m.device_id
                WHERE d.site_id = $1::uuid
                  AND m.metric = $2
                  AND m.time >= $3
                  AND m.time < $4
                  AND ($5::text IS NULL OR d.device_type = $5)
                  AND ($6::text IS NULL OR d.pvs_path_id = $6)
                ORDER BY m.time ASC
                LIMIT $7
                """,
                HOME_SITE_ID,
                metric,
                start,
                end,
                device_type,
                pvs_path_id,
                limit,
            )
        return [dict(r) for r in rows]

    async def devices(self) -> list[dict[str, Any]]:
        async with self._pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, device_type, pvs_path_id, model, name, rated_watts,
                       grid_row, grid_col, enabled, first_seen_at, last_seen_at
                FROM devices
                WHERE site_id = $1::uuid
                ORDER BY device_type, (CASE WHEN pvs_path_id ~ '^[0-9]+$' THEN pvs_path_id::int ELSE 0 END)
                """,
                HOME_SITE_ID,
            )
        return [dict(r) for r in rows]

    async def update_device_layout(
        self,
        device_id: str,
        *,
        grid_row: int | None,
        grid_col: int | None,
        name: str | None = None,
    ) -> dict[str, Any] | None:
        async with self._pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE devices
                SET grid_row = COALESCE($2, grid_row),
                    grid_col = COALESCE($3, grid_col),
                    name = COALESCE($4, name)
                WHERE id = $1::uuid AND site_id = $5::uuid AND device_type = 'inverter'
                RETURNING id, device_type, pvs_path_id, model, name, rated_watts,
                          grid_row, grid_col, enabled, first_seen_at, last_seen_at
                """,
                device_id,
                grid_row,
                grid_col,
                name,
                HOME_SITE_ID,
            )
        return dict(row) if row else None

    async def record_collector_run(
        self,
        *,
        status: str,
        source: str,
        message: str | None,
        meter_count: int | None,
        inverter_count: int | None,
        measurement_rows: int | None,
        started_at: datetime,
        finished_at: datetime,
    ) -> None:
        async with self._pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO collector_runs (
                    site_id, started_at, finished_at, status, source, message,
                    meter_count, inverter_count, measurement_rows
                )
                VALUES ($1::uuid, $2, $3, $4, $5, $6, $7, $8, $9)
                """,
                HOME_SITE_ID,
                started_at,
                finished_at,
                status,
                source,
                message,
                meter_count,
                inverter_count,
                measurement_rows,
            )
