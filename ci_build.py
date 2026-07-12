#!/usr/bin/env python3
"""GitHub Action build: refresh view counts with a read-only API key and rebuild
index.html from the committed catalog + template. Runs in CI on the PUBLIC repo,
so: no OAuth token, no local files, stdlib only (no pip install needed).

Structural data (tags, collections, dates) is authored locally and committed; this
only refreshes the view counts + re-sorts. Needs env YOUTUBE_API_KEY."""
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path

P = Path(__file__).resolve().parent
KEY = os.environ.get("YOUTUBE_API_KEY")
if not KEY:
    sys.exit("YOUTUBE_API_KEY not set")


def fetch_views(ids):
    ids = [i for i in dict.fromkeys(ids) if i]
    out = {}
    for i in range(0, len(ids), 50):
        url = "https://www.googleapis.com/youtube/v3/videos?" + urllib.parse.urlencode(
            {"part": "statistics", "id": ",".join(ids[i:i + 50]), "key": KEY})
        with urllib.request.urlopen(url) as r:
            data = json.load(r)
        for it in data.get("items", []):
            s = it.get("statistics", {})
            out[it["id"]] = int(s["viewCount"]) if "viewCount" in s else 0
    return out


def main():
    cat = json.load(open(P / "catalog_tagged.json", encoding="utf-8"))
    views = fetch_views([c["regId"] for c in cat] + [c["shortId"] for c in cat])
    for c in cat:
        c["regViews"] = views.get(c["regId"]) if c["regId"] else None
        c["shortViews"] = views.get(c["shortId"]) if c["shortId"] else None
    cat.sort(key=lambda c: (c["regViews"] or 0), reverse=True)
    json.dump(cat, open(P / "catalog_tagged.json", "w", encoding="utf-8"), ensure_ascii=False)
    tpl = (P / "catalog_template.html").read_text(encoding="utf-8")
    (P / "index.html").write_text(
        tpl.replace("__CATALOG__", json.dumps(cat, ensure_ascii=False)), encoding="utf-8")
    print(f"✓ refreshed {len(cat)} songs")


if __name__ == "__main__":
    main()
