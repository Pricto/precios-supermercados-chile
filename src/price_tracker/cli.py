"""price-tracker add | update | list | chart | remove"""

import argparse
import os
import sys
from pathlib import Path

from . import text
from .api import ApiError, Client
from .chart import render
from .report import changes, render as render_report, to_csv
from .store import Store
from .text import delta, money, t
from .tracker import resolve, track, update_all


def show(data: dict) -> None:
    for p in data["prices"]:
        print(f"  {p['retailer']['name']:<24} {money(p['price'], p['currency']):>10}   {p['observed_local_date']}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="price-tracker", description="Track retail prices by store.")
    parser.add_argument("--db", default=os.environ.get("PRICE_TRACKER_DB", "prices.db"), help="SQLite file (prices.db)")
    parser.add_argument("--lang", choices=["es", "en"], default=text.LANG)
    commands = parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser("add", help="track a product (text, product_id or GTIN), or a whole brand or category")
    add.add_argument("product", nargs="?")
    add.add_argument("--brand", help="every product of a brand, e.g. colun")
    add.add_argument("--category", help="every product of a category, e.g. food.dairy")
    add.add_argument("--days", type=int, default=30, help="days of history to load (30)")
    commands.add_parser("update", help="save today's prices for every tracked product (one call per 500)")
    commands.add_parser("list", help="tracked products and their latest prices")
    chart = commands.add_parser("chart", help="write an HTML page with the charts")
    chart.add_argument("-o", "--output", default="prices.html")
    report = commands.add_parser("report", help="table of every product and store with its price change")
    report.add_argument("-o", "--output", default="monitor.html")
    report.add_argument("--csv", help="also write the table as CSV")
    report.add_argument("--vs", type=int, default=1, help="compare against this many days before (1)")
    remove = commands.add_parser("remove", help="stop tracking a product")
    remove.add_argument("product_id")
    args = parser.parse_args(argv)

    text.LANG = args.lang
    client, store = Client(lang=args.lang), Store(args.db)
    currency = store.meta("currency") or "CLP"
    try:
        if args.command == "add" and (args.brand or args.category):
            products = client.products(brand=args.brand, category=args.category)
            for p in products:
                track(client, store, p["id"], args.days)
            print(f"{t('added_many')}: {len(products)} {t('products')} · {args.days} {t('days')}")
        elif args.command == "add":
            if not args.product:
                parser.error("add needs a product, --brand or --category")
            product_id, others = resolve(client, args.product)
            data = track(client, store, product_id, args.days)
            print(f"{t('added')}: {data['product']['name']} ({data['product']['id']}) · "
                  f"{len(data['prices'])} {t('stores')} · {args.days} {t('days')}")
            show(data)
            if others:
                print(t("also"))
                for o in others:
                    print(f"  {o['id']}  {o['name']}")
        elif args.command == "update":
            update_all(client, store)
            for p in store.products():
                print(p["name"])
                for retailer, points in store.series(p["id"]).items():
                    change = delta(points[-2][1], points[-1][1])[0] if len(points) > 1 else ""
                    print(f"  {retailer:<24} {money(points[-1][1], currency):>10}   {change}")
        elif args.command == "list":
            products = store.products()
            if not products:
                print(t("empty"))
            for p in products:
                print(f"{p['name']} ({p['id']})")
                for retailer, points in store.series(p["id"]).items():
                    day, price = points[-1]
                    print(f"  {retailer:<24} {money(price, currency):>10}   {day}")
        elif args.command == "chart":
            Path(args.output).write_text(render(store), encoding="utf-8")
            print(f"{t('chart_saved')} {Path(args.output).resolve()}")
        elif args.command == "report":
            rows = changes(store, args.vs)
            if args.csv:
                Path(args.csv).write_text(to_csv(rows), encoding="utf-8")
            href = os.path.relpath(args.csv, Path(args.output).resolve().parent) if args.csv else None
            Path(args.output).write_text(render_report(store, rows, href), encoding="utf-8")
            print(f"{t('report_saved')} {Path(args.output).resolve()}")
        elif args.command == "remove":
            print(f"{t('removed') if store.remove_product(args.product_id) else t('not_tracked')}: {args.product_id}")
    except ApiError as e:
        print(f"[{e.code}] {e}", file=sys.stderr)
        return 1
    except LookupError as e:
        print(f"{t('not_found')} \"{e}\"", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
