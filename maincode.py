"""Check every line of a requirements.txt against PyPI (JSON API)."""
import json
import sys
import urllib.error
import urllib.request

BASE = "https://pypi.org/pypi"


def get_json(url):
    """Return parsed JSON, or None if PyPI answers 404.

    Any other error (network down, 5xx, ...) is re-raised, so a broken
    connection is never mistaken for 'package does not exist'.
    """
    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            return json.load(response)
    except urllib.error.HTTPError as err:
        if err.code == 404:
            return None
        raise


def parse_line(line):
    """'flask==1.3.0' -> ('flask', '1.3.0')"""
    name, version = line.split("==", 1)
    return name.strip(), version.strip()


def main(path):
    with open(path, encoding="utf-8") as f:
        lines = [ln.strip() for ln in f if ln.strip()]

    missing_packages = 0
    missing_versions = 0
    oldest = None  # (upload_time, "name==version")

    for line in lines:
        name, version = parse_line(line)

        if get_json(f"{BASE}/{name}/json") is None:
            missing_packages += 1
            continue

        release = get_json(f"{BASE}/{name}/{version}/json")
        if release is None:
            missing_versions += 1
            continue

        files = release.get("urls", [])
        if not files:  # release exists but lists no files
            continue
        upload_time = files[0]["upload_time"]  # first file, as the task says
        if oldest is None or upload_time < oldest[0]:
            oldest = (upload_time, f"{name}=={version}")

    print(f"Dependencies checked: {len(lines)}")
    print(f"Packages not on PyPI: {missing_packages}")
    print(f"Versions not on PyPI: {missing_versions}")
    if oldest:
        print(f"Oldest pinned release: {oldest[1]} ({oldest[0][:4]})")
    else:
        print("Oldest pinned release: none")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "requirements.txt")