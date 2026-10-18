from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
from datetime import datetime, timezone
from importlib.resources import files
from pathlib import Path

from .research_api import ResearchService


PUBLIC_ENDPOINTS = (
    "overview",
    "universe",
    "coverage",
    "macro",
    "portfolios",
    "backtests",
    "validation",
    "pipelines",
    "operations",
    "paper-trading",
)
SITE_MARKER = ".uzquant-static-site"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )


def _database_hash(database: Path) -> str:
    digest = hashlib.sha256()
    with database.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def export_static_site(database: Path, output: Path, source_revision: str = "UNKNOWN") -> dict[str, object]:
    if not database.is_file():
        raise FileNotFoundError(f"canonical database not found: {database}")
    if output.exists() and not output.joinpath(SITE_MARKER).is_file():
        raise ValueError(f"refusing to replace an unmarked output directory: {output}")

    database_sha256 = _database_hash(database)
    temporary = tempfile.TemporaryDirectory(prefix="uzquant-static-")
    database_copy = Path(temporary.name) / database.name
    shutil.copy2(database, database_copy)
    service = ResearchService(database_copy)
    try:
        universe = service.universe({})
        securities = universe["securities"]
        if not securities:
            raise ValueError("canonical database contains no current research securities")
        issuer_ids = sorted({row["issuer_id"] for row in securities})

        if output.exists():
            shutil.rmtree(output)
        assets = output / "assets"
        assets.mkdir(parents=True)

        static = files("uzquant.static")
        index = static.joinpath("index.html").read_text(encoding="utf-8")
        index = index.replace(
        '<meta name="viewport" content="width=device-width,initial-scale=1">',
        '<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        '  <meta name="uzquant-static-snapshot" content="true">',
        )
        (output / "index.html").write_text(index, encoding="utf-8")
        for name in ("app.js", "styles.css"):
            assets.joinpath(name).write_bytes(static.joinpath(name).read_bytes())
        (output / ".nojekyll").write_text("", encoding="utf-8")
        (output / SITE_MARKER).write_text("uzquant-static-snapshot/1.0.0\n", encoding="utf-8")

        endpoint_payloads = {
        "overview": service.overview(),
        "universe": universe,
        "coverage": service.coverage(),
        "macro": service.macro(),
        "portfolios": service.portfolios(),
        "backtests": service.backtests(),
        "validation": service.validation(),
        "pipelines": service.pipelines(),
        "operations": service.operations(),
        "paper-trading": service.paper_trading(),
        }
        for endpoint, payload in endpoint_payloads.items():
            _write_json(output / "data" / f"{endpoint}.json", payload)

        tickers: list[str] = []
        for row in securities:
            ticker = row["ticker"]
            tickers.append(ticker)
            _write_json(output / "data" / "securities" / f"{ticker}.json", service.security(ticker))
            _write_json(output / "data" / "lineage" / f"{ticker}.json", service.lineage(ticker))
        for issuer_id in issuer_ids:
            _write_json(output / "data" / "issuers" / f"{issuer_id}.json", service.issuer(issuer_id))

        manifest = {
        "format": "uzquant-static-snapshot/1.0.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_revision": source_revision,
        "database_sha256": database_sha256,
        "security_count": len(tickers),
        "issuer_count": len(issuer_ids),
        "tickers": sorted(tickers),
        "public_endpoints": list(PUBLIC_ENDPOINTS),
        "policy": "READ_ONLY_BACKEND_DERIVED_SNAPSHOT",
        }
        _write_json(output / "data" / "manifest.json", manifest)
        return manifest
    finally:
        temporary.cleanup()


def verify_static_site(output: Path) -> dict[str, object]:
    manifest_path = output / "data" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("format") != "uzquant-static-snapshot/1.0.0":
        raise ValueError("unsupported static snapshot format")
    tickers = manifest.get("tickers") or []
    if manifest.get("security_count") != len(tickers) or len(tickers) != len(set(tickers)):
        raise ValueError("static snapshot security manifest is inconsistent")
    for required in (
        "index.html",
        "assets/app.js",
        "assets/styles.css",
        ".nojekyll",
        SITE_MARKER,
    ):
        if not output.joinpath(required).is_file():
            raise FileNotFoundError(f"missing static asset: {required}")
    for endpoint in manifest.get("public_endpoints") or []:
        json.loads(output.joinpath("data", f"{endpoint}.json").read_text(encoding="utf-8"))
    for ticker in tickers:
        json.loads(output.joinpath("data", "securities", f"{ticker}.json").read_text(encoding="utf-8"))
        json.loads(output.joinpath("data", "lineage", f"{ticker}.json").read_text(encoding="utf-8"))
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m uzquant.static_site")
    sub = parser.add_subparsers(dest="command", required=True)
    export = sub.add_parser("export")
    export.add_argument("--database", type=Path, required=True)
    export.add_argument("--output", type=Path, default=Path("site"))
    export.add_argument("--source-revision", default="UNKNOWN")
    verify = sub.add_parser("verify")
    verify.add_argument("--output", type=Path, default=Path("site"))
    args = parser.parse_args(argv)
    payload = (
        export_static_site(args.database, args.output, args.source_revision)
        if args.command == "export"
        else verify_static_site(args.output)
    )
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
