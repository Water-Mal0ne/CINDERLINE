"""Compare every generated static asset with its public Cloudflare response."""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="https://firetrace-bhaktapur-2026.pages.dev/")
    parser.add_argument("--dist", type=Path, default=Path("dist"))
    parser.add_argument("--report", type=Path, default=Path("reports/deployment_verification.json"))
    args = parser.parse_args()
    if not args.url.startswith("https://"):
        parser.error("Use the HTTPS deployment URL.")
    files = sorted(path for path in args.dist.rglob("*") if path.is_file())
    if not files or not (args.dist / "index.html").is_file():
        parser.error("Build the application first; dist/index.html is required.")

    def verify(path: Path) -> dict:
        relative = path.relative_to(args.dist).as_posix()
        url = args.url.rstrip("/") + "/" + ("" if relative == "index.html" else quote(relative))
        expected = hashlib.sha256(path.read_bytes()).hexdigest()
        try:
            with urlopen(Request(url, headers={"User-Agent": "FIRETRACE-release-check/1.0"}), timeout=60) as response:
                body = response.read()
                actual = hashlib.sha256(body).hexdigest()
                return {"file": relative, "status": response.status, "bytes": len(body),
                        "sha256": actual, "matches": actual == expected and response.status == 200}
        except Exception as exc:
            return {"file": relative, "matches": False, "error": str(exc)}

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(verify, files))
    passed = all(item["matches"] for item in results)
    report = {"url": args.url, "verified_at": datetime.now(timezone.utc).isoformat(),
              "status": "passed" if passed else "failed", "files": len(results),
              "bytes": sum(item.get("bytes", 0) for item in results), "assets": results}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in report.items() if key != "assets"}, indent=2))
    if not passed:
        print(json.dumps([item for item in results if not item["matches"]], indent=2))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
