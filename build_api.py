#!/usr/bin/env python3
"""Build a static JSON API from the CSV files, for GitHub Pages (docs/ folder).

    docs/api/v1/index.json              all collections + the latest date
    docs/api/v1/latest.json             today's floor of every collection (GRAM, USD, EUR)
    docs/api/v1/collections/<slug>.json full daily history of one collection

Standard library only. Run after collect.py.
"""
import csv
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(ROOT, "data", "floor_prices.csv")
RATES_PATH = os.path.join(ROOT, "data", "rates.csv")
OUT = os.path.join(ROOT, "docs", "api", "v1")


def num(value):
    return float(value) if value not in ("", None) else None


def convert(gram, rate):
    if gram is None or rate is None:
        return None
    return round(gram * rate, 2)


def read_rates():
    rates = {}
    if os.path.exists(RATES_PATH):
        with open(RATES_PATH, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                rates[r["date"]] = {"usd": num(r["gram_usd"]), "eur": num(r["gram_eur"])}
    return rates


def build(rows, rates):
    """Return {path_relative_to_OUT: json_object} for the given CSV rows."""
    history = {}
    for r in rows:
        rate = rates.get(r["date"], {})
        floor = num(r["floor_gram"])
        fixed = num(r["floor_fixed_gram"])
        history.setdefault(r["collection"], []).append({
            "date": r["date"],
            "floor_gram": floor,
            "floor_fixed_gram": fixed,
            "floor_usd": convert(floor, rate.get("usd")),
            "floor_eur": convert(floor, rate.get("eur")),
            "lots_seen": int(r["lots_seen"]),
            "auctions_seen": int(r["auctions_seen"]),
        })
    for points in history.values():
        points.sort(key=lambda p: p["date"])

    latest_date = max((p["date"] for pts in history.values() for p in pts), default=None)
    files = {}
    latest = {}
    for slug, points in sorted(history.items()):
        files[f"collections/{slug}.json"] = {"collection": slug, "unit": "GRAM", "history": points}
        if points[-1]["date"] == latest_date:
            latest[slug] = {k: v for k, v in points[-1].items() if k != "date"}

    files["latest.json"] = {
        "date": latest_date, "unit": "GRAM", "source": "fragment.com",
        "rate": rates.get(latest_date, {}), "floors": latest,
    }
    files["index.json"] = {
        "version": "v1", "latest_date": latest_date, "unit": "GRAM", "source": "fragment.com",
        "collections": sorted(history),
    }
    return files


def main():
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    files = build(rows, read_rates())
    for rel, obj in files.items():
        path = os.path.join(OUT, *rel.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(obj, f, indent=1, sort_keys=False)
            f.write("\n")
    print(f"wrote {len(files)} files to {OUT}")


if __name__ == "__main__":
    main()
