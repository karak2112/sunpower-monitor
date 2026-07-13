from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

from solar_collector.config import Settings
from solar_collector.datasource.fixture import FixtureDataSource
from solar_collector.datasource.varserver import VarserverDataSource


def _configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


async def _run_fetch(source: str, fixtures_dir: Path) -> int:
    if source == "fixture":
        ds = FixtureDataSource(fixtures_dir)
    elif source == "varserver":
        settings = Settings()
        if not settings.pvs_password.get_secret_value():
            print("PVS_PASSWORD is required for --source varserver", file=sys.stderr)
            return 2
        ds = VarserverDataSource(settings)
    else:
        print(f"unknown source: {source}", file=sys.stderr)
        return 2

    try:
        health = await ds.health_check()
        measurements = await ds.get_current_measurements()
        payload = {
            "health": health.model_dump(mode="json"),
            "measurements": {
                "collected_at": measurements.collected_at.isoformat(),
                "parser_version": measurements.parser_version,
                "livedata": measurements.livedata.model_dump(mode="json")
                if measurements.livedata
                else None,
                "meter_count": len(measurements.meters),
                "inverter_count": len(measurements.inverters),
                "pv_power_kw": measurements.livedata.pv_power_kw if measurements.livedata else None,
                "site_load_power_kw": measurements.livedata.site_load_power_kw
                if measurements.livedata
                else None,
                "inverter_power_kw_sum": round(
                    sum((i.power_kw or 0.0) for i in measurements.inverters), 6
                ),
            },
        }
        print(json.dumps(payload, indent=2))
        return 0
    finally:
        if source == "varserver":
            assert isinstance(ds, VarserverDataSource)
            try:
                await ds.logout()
            except Exception:  # noqa: BLE001
                logging.exception("logout_failed")
            await ds.aclose()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Solar Monitor PVS collector")
    sub = parser.add_subparsers(dest="command", required=True)

    fetch = sub.add_parser("fetch", help="Fetch current measurements once")
    fetch.add_argument(
        "--source",
        choices=("fixture", "varserver"),
        default="fixture",
        help="Data source (default: fixture — no PVS contact)",
    )
    fetch.add_argument(
        "--fixtures-dir",
        type=Path,
        default=Path(__file__).resolve().parents[4] / "fixtures" / "pvs6",
        help="Directory with redacted fixtures",
    )
    fetch.add_argument("--log-level", default="INFO")

    args = parser.parse_args(argv)
    _configure_logging(args.log_level)

    if args.command == "fetch":
        raise SystemExit(asyncio.run(_run_fetch(args.source, args.fixtures_dir)))


if __name__ == "__main__":
    main()
