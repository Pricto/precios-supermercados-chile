"""Monitor de muchos SKU: precio de hoy en cada tienda, cambio contra días atrás y exportación a CSV."""

import csv
import io
from datetime import date, timedelta
from html import escape

from .chart import page
from .store import Store
from .text import delta, money, t

FIELDS = ["product_id", "name", "retailer", "day", "price", "previous_day", "previous_price", "change_pct"]


def changes(store: Store, days: int = 1) -> list[dict]:
    """Una fila por producto y tienda: el último precio y el que tenía `days` días antes."""
    rows = []
    for product in store.products():
        for retailer, points in store.series(product["id"]).items():
            day, price = points[-1]
            previous_day = (date.fromisoformat(day) - timedelta(days=days)).isoformat()
            earlier = [p for d, p in points if d <= previous_day]
            previous = earlier[-1] if earlier else None
            rows.append({
                "product_id": product["id"], "name": product["name"], "retailer": retailer, "day": day,
                "price": price, "previous_day": previous_day, "previous_price": previous,
                "change_pct": round((price - previous) / previous * 100, 1) if previous else None,
            })
    return rows


def to_csv(rows: list[dict]) -> str:
    out = io.StringIO()
    writer = csv.DictWriter(out, FIELDS)
    writer.writeheader()
    writer.writerows(rows)
    return out.getvalue()


def render(store: Store, rows: list[dict], csv_href: str | None = None) -> str:
    currency = store.meta("currency") or "CLP"
    retailers = sorted({r["retailer"] for r in rows}, key=lambda name: (-sum(r["retailer"] == name for r in rows), name))
    products: dict[str, dict[str, dict]] = {}
    for r in rows:
        products.setdefault(r["name"], {})[r["retailer"]] = r
    # Primero los productos que cambiaron, la baja más grande arriba.
    moved = lambda cells: min((c["change_pct"] for c in cells.values() if c["change_pct"]), default=None)
    order = sorted(products, key=lambda name: (moved(products[name]) is None, moved(products[name]) or 0, name))

    body = []
    for name in order:
        cells = products[name]
        cheapest = min(c["price"] for c in cells.values())
        tds = []
        for retailer in retailers:
            c = cells.get(retailer)
            if c is None:
                tds.append('<td class="num dim">—<span class="d"></span></td>')
                continue
            # Solo se marcan los cambios, para que se vean entre muchos SKU.
            change, cls = delta(c["previous_price"], c["price"]) if c["change_pct"] else ("", "igual")
            tds.append(f'<td class="num{" min" if c["price"] == cheapest else ""}">{money(c["price"], currency)}'
                       f'<span class="d {cls}">{change}</span></td>')
        body.append(f'<tr><td class="name">{escape(name)}</td>{"".join(tds)}</tr>')

    changed = [r for r in rows if r["change_pct"]]
    down = sum(r["change_pct"] < 0 for r in changed)
    days = sorted({r["day"] for r in rows})
    summary = (
        f'<div class="stats"><span><b>{len(products)}</b> {t("products")}</span><span><b>{len(retailers)}</b> {t("stores")}</span>'
        f'<span><b>{len(changed)}</b> {t("changes")}</span><span class="baja">▼ {down} {t("drops")}</span>'
        f'<span class="sube">▲ {len(changed) - down} {t("rises")}</span>'
        f'<span class="dim">{rows[0]["previous_day"] if rows else ""} → {days[-1] if days else ""}</span>'
        f'<span class="legend">{t("cheapest")}</span>'
        + (f'<a class="export" href="{escape(csv_href)}" download>{t("export")}</a>' if csv_href else "") + "</div>"
    )
    head = "".join(f'<th class="num">{escape(r)}</th>' for r in retailers)
    table = f'<div class="wide"><table class="monitor"><thead><tr><th>{t("product")}</th>{head}</tr></thead><tbody>{"".join(body)}</tbody></table></div>'
    return page(store, t("monitor"), summary + table, width=1120).replace("</style>", CSS + "</style>")


CSS = """
.stats { display: flex; flex-wrap: wrap; gap: 10px 28px; align-items: baseline; font: 13px 'Geist Mono', monospace; color: var(--dim); }
.export { margin-left: auto; font: 600 13px 'Host Grotesk', sans-serif; color: #fff; background: var(--canto);
  padding: 9px 14px; border-radius: 6px; text-decoration: none; box-shadow: 3px 3px 0 #ff8a6b; }
.stats b { font: 500 26px 'Geist Mono', monospace; color: var(--ink); letter-spacing: -0.03em; margin-right: 6px; }
.wide { background: #fff; border: 1px solid var(--line2); border-radius: 3px; overflow-x: auto;
  box-shadow: 3px 3px 0 var(--canto), 6px 6px 0 var(--canto-sombra); }
.monitor th { background: var(--bg2); padding: 10px 14px; }
.monitor td { padding: 9px 14px; vertical-align: top; }
.monitor td.name { color: var(--ink); white-space: normal; min-width: 260px; }
.monitor td.min { color: var(--ink); font-weight: 600; }
.min::before, .legend::before { content: ""; display: inline-block; width: 8px; height: 8px; border-radius: 50%;
  background: #ff8a6b; margin-right: 8px; vertical-align: 1px; }
.monitor .d { display: inline-block; min-width: 76px; margin-left: 8px; font-size: 11.5px; padding: 1px 6px;
  border-radius: 3px; font-weight: 400; text-align: right; }
.monitor .d.sube { background: #fdecea; } .monitor .d.baja { background: #e5f0f8; }
"""
