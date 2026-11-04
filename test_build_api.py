import build_api

ROWS = [
    {"date": "2026-11-03", "collection": "plushpepe", "floor_gram": "7000.0", "floor_fixed_gram": "", "lots_seen": "60", "auctions_seen": "60"},
    {"date": "2026-11-04", "collection": "plushpepe", "floor_gram": "7500.0", "floor_fixed_gram": "", "lots_seen": "60", "auctions_seen": "60"},
    {"date": "2026-11-04", "collection": "lolpop", "floor_gram": "5.0", "floor_fixed_gram": "5.0", "lots_seen": "60", "auctions_seen": "0"},
    {"date": "2026-11-01", "collection": "oldone", "floor_gram": "9.0", "floor_fixed_gram": "9.0", "lots_seen": "3", "auctions_seen": "0"},
]
RATES = {"2026-11-04": {"usd": 1.0, "eur": 0.5}}


def test_build_files():
    files = build_api.build(ROWS, RATES)
    assert files["index.json"]["latest_date"] == "2026-11-04"
    assert files["index.json"]["collections"] == ["lolpop", "oldone", "plushpepe"]
    hist = files["collections/plushpepe.json"]["history"]
    assert [p["date"] for p in hist] == ["2026-11-03", "2026-11-04"]
    assert hist[0]["floor_usd"] is None  # no rate for that day
    assert hist[1]["floor_usd"] == 7500.0 and hist[1]["floor_eur"] == 3750.0
    assert hist[1]["floor_fixed_gram"] is None


def test_latest_skips_stale_collections():
    latest = build_api.build(ROWS, RATES)["latest.json"]
    assert set(latest["floors"]) == {"plushpepe", "lolpop"}
    assert latest["rate"] == {"usd": 1.0, "eur": 0.5}
