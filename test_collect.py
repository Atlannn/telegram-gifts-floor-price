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
