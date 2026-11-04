#!/usr/bin/env python3
"""Collect the floor price of every Telegram gift collection from fragment.com.

For each collection it reads the cheapest listings (filter=sale, sorted by price)
and appends one row per collection per day to data/floor_prices.csv.
Prices are in GRAM (the coin formerly called TON). Standard library only.

    python collect.py                 # all collections
    python collect.py plushpepe lolpop
"""
import csv
import datetime as dt
import html
import json
import os
import re
import sys
import time
import urllib.request

BASE = "https://fragment.com"
UA = "Mozilla/5.0 (compatible; telegram-gifts-floor-price/0.1; +https://github.com/Atlannn/telegram-gifts-floor-price)"
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
CSV_PATH = os.path.join(DATA_DIR, "floor_prices.csv")
LATEST_PATH = os.path.join(DATA_DIR, "latest.json")
COLUMNS = ["date", "collection", "floor_gram", "floor_fixed_gram", "lots_seen", "auctions_seen"]
DELAY = 1.0  # seconds between requests, be polite to the source

COLLECTION_RE = re.compile(r'href="/gifts/([a-z0-9]+)')
ITEM_RE = re.compile(r'<a href="/gift/([a-z0-9]+)-(\d+)[^"]*" class="tm-grid-item">(.*?)</a>', re.S)
PRICE_RE = re.compile(r'icon-ton">([\d,\.]+)</div>')


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return re.sub(r"\s+", " ", r.read().decode("utf-8", "replace"))


def list_collections():
    return sorted(set(COLLECTION_RE.findall(get(f"{BASE}/gifts"))))


def parse_lots(page):
    """Return [(price, is_auction)] for the lots on a Fragment listing page."""
    lots = []
    for m in ITEM_RE.finditer(page):
        block = m.group(3)
        pm = PRICE_RE.search(block)
        if not pm:
            continue
        try:
            price = float(html.unescape(pm.group(1)).replace(",", ""))
        except ValueError:
            continue
        lots.append((price, "js-timer-wrap" in block))
    return lots


def summarize(lots):
    """Floor numbers from one page of listings (Fragment returns up to 60 lots per page)."""
    if not lots:
        return None
    fixed = [p for p, auction in lots if not auction]
    return {
        "floor_gram": min(p for p, _ in lots),
        "floor_fixed_gram": min(fixed) if fixed else "",
        "lots_seen": len(lots),
        "auctions_seen": sum(1 for _, a in lots if a),
    }


def collect_one(slug):
    page = get(f"{BASE}/gifts/{slug}?sort=price_asc&filter=sale")
    return summarize(parse_lots(page))


def merge_rows(existing, new_rows, day):
    """Replace today's rows for the same collections, keep the rest (re-runs are safe)."""
    replaced = {r["collection"] for r in new_rows}
    kept = [r for r in existing if not (r["date"] == day and r["collection"] in replaced)]
    return kept + new_rows


def read_csv():
    if not os.path.exists(CSV_PATH):
        return []
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(rows):
    os.makedirs(DATA_DIR, exist_ok=True)
    rows = sorted(rows, key=lambda r: (r["date"], r["collection"]))
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS)
        w.writeheader()
        w.writerows(rows)


def main(argv):
    day = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d")
    slugs = argv or list_collections()
    new_rows, failed = [], []
    for i, slug in enumerate(slugs):
        if i:
            time.sleep(DELAY)
        try:
            s = collect_one(slug)
        except Exception as e:  # one bad collection must not lose the whole run
            failed.append(f"{slug}: {e}")
            continue
        if s:  # a collection with nothing for sale has no floor, so no row
            new_rows.append({"date": day, "collection": slug, **s})
    if not new_rows:
        sys.exit("No prices collected; keeping the existing data.")
    write_csv(merge_rows(read_csv(), new_rows, day))
    with open(LATEST_PATH, "w", encoding="utf-8") as f:
        json.dump({"date": day, "unit": "GRAM", "source": "fragment.com",
                   "floors": {r["collection"]: r["floor_gram"] for r in new_rows}}, f, indent=1)
    print(f"{day}: {len(new_rows)} collections saved, {len(failed)} failed")
    for line in failed:
        print("  failed", line)


if __name__ == "__main__":
    main(sys.argv[1:])
