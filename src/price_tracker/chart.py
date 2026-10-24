"""Página HTML autocontenida con un gráfico escalonado por producto (SVG, sin JavaScript)."""

import base64
from html import escape
from importlib.resources import files

from .store import Store
from . import text
from .text import delta, money, t

COLORS = ["#0f5a45", "#b0401f", "#2f6aa8", "#7b56b8", "#7f938a"]
W, H, PAD_R, PAD_B = 720, 200, 64, 22


def _font(name: str) -> str:
    data = base64.b64encode((files(__package__) / "assets" / name).read_bytes()).decode()
    return f"url(data:font/woff2;base64,{data}) format('woff2')"


def _svg(series: dict[str, list[tuple[str, float]]], currency: str) -> str:
    days = sorted({d for points in series.values() for d, _ in points})
    prices = [p for points in series.values() for _, p in points]
    lo, hi = min(prices), max(prices)
    margin = (hi - lo) * 0.12 or hi * 0.05
    lo, hi = lo - margin, hi + margin
    w, h = W - PAD_R, H - PAD_B
    x = lambda day: days.index(day) / max(len(days) - 1, 1) * w
    y = lambda price: h - (price - lo) / (hi - lo) * h

    out = [f'<svg viewBox="0 0 {W} {H}" role="img" aria-label="{t("title")}">']
    for i in range(4):
        gy, value = h / 3 * i, hi - (hi - lo) / 3 * i
        out.append(f'<line x1="0" x2="{w}" y1="{gy:.1f}" y2="{gy:.1f}" class="grid"/>')
        out.append(f'<text x="{W}" y="{gy + 4:.1f}" text-anchor="end" class="axis">{money(round(value, -1), currency)}</text>')
    out.append(f'<text x="0" y="{H - 4}" class="axis">{days[0]}</text>')
    out.append(f'<text x="{w}" y="{H - 4}" text-anchor="end" class="axis">{days[-1]}</text>')
    for color, points in zip(COLORS, series.values()):
        (d0, p0), *rest = points
        path = f"M{x(d0):.1f},{y(p0):.1f}" + "".join(f"H{x(d):.1f}V{y(p):.1f}" for d, p in rest)
        if rest:
            path += f"H{w}"
        out.append(f'<path d="{path}" fill="none" stroke="{color}" stroke-width="1.8"/>')
    return "".join(out) + "</svg>"


def _card(name: str, size: str | None, series: dict, currency: str) -> str:
    cheapest = min(points[-1][1] for points in series.values())
    rows = []
    for color, (retailer, points) in zip(COLORS, series.items()):
        last = points[-1][1]
        change, cls = delta(points[0][1], last)
        badge = f'<span class="chip">{t("cheapest")}</span>' if last == cheapest else ""
        rows.append(
            f'<tr><td><span class="sw" style="background:{color}"></span>{escape(retailer)} {badge}</td>'
            f'<td class="num">{money(last, currency)}</td>'
            f'<td class="num {cls}">{change}</td><td class="num dim">{points[-1][0]}</td></tr>'
        )
    first_day = min(p[0][0] for p in series.values())
    return (
        f'<section class="card"><header><h2>{escape(name)}</h2>'
        f'<span class="dim">{escape(size or "")}</span></header>{_svg(series, currency)}'
        f'<table><thead><tr><th></th><th class="num">{t("latest")}</th>'
        f'<th class="num">{t("since")} {first_day}</th><th></th></tr></thead>'
        f'<tbody>{"".join(rows)}</tbody></table></section>'
    )


def render(store: Store) -> str:
    currency = store.meta("currency") or "CLP"
    cards = [
        _card(p["name"], p["size"], series, currency)
        for p in store.products() if (series := store.series(p["id"]))
    ]
    return page(store, t("title"), "".join(cards) or f"<p>{t('empty')}</p>")


def page(store: Store, title: str, body: str, width: int = 760) -> str:
    """La página con el sistema visual de la marca, la nota de la sandbox y la línea de fuente."""
    sample = f'<p class="note">{t("sample")}</p>' if store.meta("sample_data") == "True" else ""
    return f"""<!doctype html>
<html lang="{text.LANG}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{escape(title)}</title>
<style>
@font-face {{ font-family: 'Host Grotesk'; font-weight: 300 800; src: {_font("host-grotesk-latin.woff2")}; }}
@font-face {{ font-family: 'Geist Mono'; font-weight: 100 900; src: {_font("geist-mono-latin.woff2")}; }}
:root {{ --ink: #0f2a22; --text: #24392f; --dim: #51665c; --line: #dfe8e3; --line2: #c6d3cc; --bg2: #f2f6f4;
  --canto: #0f5a45; --canto-sombra: #0a4031; --sube: #b42318; --baja: #0b5f8f; --igual: #51665c;
  --accent-soft: #ffeee8; --accent-ink: #b0401f; --warn: #8a4b00; --warn-soft: #fdf1dc; }}
* {{ box-sizing: border-box; margin: 0; font-style: normal; font-synthesis: none; }}
body {{ font: 15px/1.5 'Host Grotesk', system-ui, sans-serif; color: var(--text); background: var(--bg2); padding: 40px 20px; }}
main {{ max-width: {width}px; margin: 0 auto; display: grid; gap: 28px; }}
h1 {{ font-size: 32px; letter-spacing: -0.03em; color: var(--ink); }}
h2 {{ font-size: 18px; letter-spacing: -0.01em; color: var(--ink); }}
.card {{ background: #fff; border: 1px solid var(--line2); border-radius: 3px; padding: 18px 20px;
  box-shadow: 3px 3px 0 var(--canto), 6px 6px 0 var(--canto-sombra); display: grid; gap: 14px; }}
.card header {{ display: flex; justify-content: space-between; align-items: baseline; gap: 12px; }}
svg {{ width: 100%; height: auto; overflow: visible; }}
.grid {{ stroke: #e8efeb; }}
.axis {{ font: 10.5px 'Geist Mono', monospace; fill: var(--dim); }}
table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
th {{ font: 500 10.5px 'Geist Mono', monospace; letter-spacing: .08em; text-transform: uppercase; color: var(--dim);
  text-align: left; padding: 6px 8px; border-bottom: 1px solid var(--line2); }}
td {{ padding: 8px; border-bottom: 1px solid var(--line); white-space: nowrap; }}
td .sw {{ display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 8px; }}
.num {{ text-align: right; font-family: 'Geist Mono', monospace; font-variant-numeric: tabular-nums; }}
.dim {{ color: var(--dim); font: 12px 'Geist Mono', monospace; }}
.sube {{ color: var(--sube); }} .baja {{ color: var(--baja); }} .igual {{ color: var(--igual); }}
.chip {{ font: 11.5px 'Geist Mono', monospace; padding: 2px 8px; border-radius: 999px; background: var(--accent-soft); color: var(--accent-ink); margin-left: 6px; }}
.note {{ font: 12.5px 'Geist Mono', monospace; color: var(--warn); background: var(--warn-soft); padding: 8px 12px; border-radius: 6px; }}
footer {{ font: 12px 'Geist Mono', monospace; color: var(--dim); border-top: 1px dashed var(--line2); padding-top: 8px; }}
</style></head>
<body><main><h1>{escape(title)}</h1>{sample}{body}
<footer>{escape(store.meta("attribution") or "")}</footer></main></body></html>
"""
