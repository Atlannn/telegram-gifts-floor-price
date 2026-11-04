import collect

PAGE = (
    '<a href="/gift/plushpepe-1" class="tm-grid-item"><div class="tm-grid-item-value tm-value icon-before icon-ton">6,099</div></a>'
    '<a href="/gift/plushpepe-2" class="tm-grid-item"><div class="js-timer-wrap"></div>'
    '<div class="tm-grid-item-value tm-value icon-before icon-ton">5,900</div></a>'
    '<a href="/gift/plushpepe-3" class="tm-grid-item"><div>Not for sale</div></a>'
)


def test_parse_and_summarize():
    lots = collect.parse_lots(PAGE)
    assert lots == [(6099.0, False), (5900.0, True)]
    s = collect.summarize(lots)
    assert s == {"floor_gram": 5900.0, "floor_fixed_gram": 6099.0, "lots_seen": 2, "auctions_seen": 1}


def test_summarize_empty_is_none():
    assert collect.summarize([]) is None


def test_all_auctions_has_no_fixed_floor():
    assert collect.summarize([(10.0, True)])["floor_fixed_gram"] == ""


def test_merge_replaces_same_day_only():
    old = [{"date": "2026-11-03", "collection": "a"}, {"date": "2026-11-04", "collection": "a"},
           {"date": "2026-11-04", "collection": "b"}]
    new = [{"date": "2026-11-04", "collection": "a"}]
    out = collect.merge_rows(old, new, "2026-11-04")
    assert len(out) == 3 and {"date": "2026-11-04", "collection": "b"} in out


def test_parse_rate():
    payload = {"rates": {"TON": {"prices": {"USD": 1.17566, "EUR": 1.04747}}}}
    assert collect.parse_rate(payload) == {"gram_usd": 1.1757, "gram_eur": 1.0475}


def test_save_rate_one_row_per_day(tmp_path, monkeypatch):
    monkeypatch.setattr(collect, "DATA_DIR", str(tmp_path))
    monkeypatch.setattr(collect, "RATES_PATH", str(tmp_path / "rates.csv"))
    collect.save_rate("2026-11-04", {"gram_usd": 1.0, "gram_eur": 0.9})
    collect.save_rate("2026-11-04", {"gram_usd": 1.2, "gram_eur": 1.0})
    lines = (tmp_path / "rates.csv").read_text().strip().splitlines()
    assert lines == ["date,gram_usd,gram_eur", "2026-11-04,1.2,1.0"]
