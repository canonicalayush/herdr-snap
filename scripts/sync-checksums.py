#!/usr/bin/env python3
"""Recompute the sha256 digests pinned in snap/local/upstream.json.

Renovate's custom regex manager (see renovate.json) only rewrites the
"version" field of snap/local/upstream.json -- it has no way to also fetch
and rewrite the two sha256 digests, because postUpgradeTasks requires the
allowedCommands option the Mend-hosted app does not expose to free/community
users. This script fills them in: it downloads both release assets for the
pinned version, hashes them, and cross-checks against the digests upstream
itself publishes at https://herdr.dev/latest.json when that manifest agrees
on the version. A digest that disagrees with upstream's own manifest is a
supply-chain signal and is treated as fatal, not something to silently
overwrite.

Exits 0 whether or not anything changed; the calling workflow decides based
on `git diff --quiet`.
"""
import hashlib
import json
import sys
import urllib.request
from pathlib import Path

PIN_PATH = Path(__file__).resolve().parent.parent / "snap" / "local" / "upstream.json"
LATEST_JSON_URL = "https://herdr.dev/latest.json"
RELEASE_ASSET_URL = "https://github.com/herdrdev/herdr/releases/download/v{version}/{asset}"

# amd64/arm64 (snapcraft CRAFT_ARCH_BUILD_FOR values) -> upstream release asset name
ASSET_NAMES = {
    "amd64": "herdr-linux-x86_64",
    "arm64": "herdr-linux-aarch64",
}

# amd64/arm64 -> herdr.dev/latest.json's own per-platform key, for the cross-check
LATEST_JSON_KEYS = {
    "amd64": "linux-x86_64",
    "arm64": "linux-aarch64",
}


USER_AGENT = "herdr-snap-sync-checksums (+https://github.com/canonicalayush/herdr-snap)"


def _request(url: str) -> urllib.request.Request:
    return urllib.request.Request(url, headers={"User-Agent": USER_AGENT})


def sha256_of_url(url: str) -> str:
    digest = hashlib.sha256()
    with urllib.request.urlopen(_request(url)) as response:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(_request(url)) as response:
        return json.load(response)


def main() -> int:
    pin = json.loads(PIN_PATH.read_text())
    version = pin["version"]

    try:
        latest = fetch_json(LATEST_JSON_URL)
    except Exception as exc:  # network/manifest issues never block a digest recompute
        print(f"warning: could not fetch {LATEST_JSON_URL}: {exc}", file=sys.stderr)
        latest = None

    computed = {}
    for arch, asset in ASSET_NAMES.items():
        url = RELEASE_ASSET_URL.format(version=version, asset=asset)
        print(f"hashing {url}", file=sys.stderr)
        computed[arch] = sha256_of_url(url)

        if latest is not None and latest.get("version") == version:
            manifest_key = LATEST_JSON_KEYS[arch]
            manifest_digest = latest.get("sha256", {}).get(manifest_key)
            if manifest_digest and manifest_digest != computed[arch]:
                print(
                    f"FATAL: computed sha256 for {arch} ({computed[arch]}) "
                    f"disagrees with {LATEST_JSON_URL} ({manifest_digest}) "
                    f"for version {version}",
                    file=sys.stderr,
                )
                return 1

    pin["sha256"] = computed
    PIN_PATH.write_text(json.dumps(pin, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
