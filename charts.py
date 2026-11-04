#!/usr/bin/env python3
"""Draw price charts from data/*.csv into charts/*.png (needs matplotlib).

    charts/floor_gram.png   floor price in GRAM, top collections
    charts/floor_usd.png    the same floors in USD at each day's GRAM rate
"""
import csv
import os
from collections import defaultdict
from datetime import datetime, timedelta

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "charts")
TOP_N = 6
COLORS = ["#d4ff3f", "#5aa9ff", "#ff9a3d", "#b18cff", "#3ddc84", "#ff5c5c"]
BG, FG, GRID = "#0a0b0d", "#eceef2", "#23272f"


def read(name):
    path = os.path.join(DATA, name)
    if not os.path.exists(path):
        return []
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def pretty(slug):
    return slug.replace("-", " ").title()


def series_by_collection(rows, rates=None):
    """{collection: [(date, value)]}; value is GRAM, or USD when `rates` {date: gram_usd} is given."""
    out = defaultdict(list)
    for r in rows:
        value = float(r["floor_gram"])
        if rates is not None:
            if r["date"] not in rates:
                continue
            value *= rates[r["date"]]
        out[r["collection"]].append((datetime.strptime(r["date"], "%Y-%m-%d"), value))
    return out


def top_collections(rows, n=TOP_N):
    """The n collections with the highest latest floor."""
    last = {}
    for r in sorted(rows, key=lambda r: r["date"]):
        last[r["collection"]] = float(r["floor_gram"])
    return [c for c, _ in sorted(last.items(), key=lambda kv: -kv[1])[:n]]


def draw(series, names, title, ylabel, path, money=False):
    fig, ax = plt.subplots(figsize=(10, 5.2), dpi=130)
    fig.patch.set_facecolor(BG)
    ax.set_facecolor(BG)
    for i, name in enumerate(names):
        pts = sorted(series.get(name, []))
        if not pts:
            continue
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        ax.plot(xs, ys, color=COLORS[i % len(COLORS)], lw=2, marker="o", ms=4, label=pretty(name))
    days = sorted({x for pts in series.values() for x, _ in pts})
    if days and days[0] == days[-1]:  # one measurement so far: a narrow window, not years of empty axis
        ax.set_xlim(days[0] - timedelta(days=3), days[0] + timedelta(days=3))
    ax.set_title(title, color=FG, fontsize=14, loc="left", pad=14)
    ax.set_ylabel(ylabel, color=FG)
    ax.grid(color=GRID, lw=0.8)
    ax.tick_params(colors=FG)
    for side in ax.spines.values():
        side.set_color(GRID)
    ax.xaxis.set_major_locator(mdates.AutoDateLocator(minticks=3, maxticks=8))
    ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(ax.xaxis.get_major_locator()))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: (f"${v:,.0f}" if money else f"{v:,.0f}")))
    leg = ax.legend(facecolor=BG, edgecolor=GRID, labelcolor=FG, loc="upper left", fontsize=9)
    leg.get_frame().set_alpha(0.9)
    fig.text(0.99, 0.01, "Source: fragment.com | balticassets.eu", color="#8a919e", fontsize=8, ha="right")
    fig.tight_layout()
    os.makedirs(OUT, exist_ok=True)
    fig.savefig(path, facecolor=BG)
    plt.close(fig)


def main():
    rows = read("floor_prices.csv")
    if not rows:
        raise SystemExit("data/floor_prices.csv is empty")
    names = top_collections(rows)
    draw(series_by_collection(rows), names, "Telegram gifts: floor price (GRAM)",
         "GRAM", os.path.join(OUT, "floor_gram.png"))
    rates = {r["date"]: float(r["gram_usd"]) for r in read("rates.csv")}
    if rates:
        draw(series_by_collection(rows, rates), names, "Telegram gifts: floor price in USD at that day's GRAM rate",
             "USD", os.path.join(OUT, "floor_usd.png"), money=True)
    print("charts written to", OUT)


if __name__ == "__main__":
    main()
