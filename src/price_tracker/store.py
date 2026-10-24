"""Historial local en SQLite: un precio por oferta y día."""

import sqlite3

SCHEMA = """
create table if not exists products (id text primary key, name text not null, size text);
create table if not exists prices (
  product_id text not null, offer_id text not null, retailer text not null,
  day text not null, price real not null, url text,
  primary key (offer_id, day)
);
create table if not exists meta (key text primary key, value text);
"""


class Store:
    def __init__(self, path: str):
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)

    def add_product(self, product: dict) -> None:
        self.db.execute(
            "insert or replace into products values (?, ?, ?)",
            (product["id"], product["name"], (product.get("size") or {}).get("text")),
        )
        self.db.commit()

    def remove_product(self, product_id: str) -> bool:
        removed = self.db.execute("delete from products where id = ?", (product_id,)).rowcount
        self.db.execute("delete from prices where product_id = ?", (product_id,))
        self.db.commit()
        return removed > 0

    def products(self) -> list[sqlite3.Row]:
        return self.db.execute("select * from products order by name").fetchall()

    def save_prices(self, product_id: str, rows: list[tuple]) -> None:
        """rows: (offer_id, retailer, day, price, url)."""
        self.db.executemany(
            "insert or replace into prices values (?, ?, ?, ?, ?, ?)",
            [(product_id, *row) for row in rows],
        )
        self.db.commit()

    def series(self, product_id: str) -> dict[str, list[tuple[str, float]]]:
        """{retailer: [(day, price), ...]} por día; la tienda más barata hoy, primero."""
        out: dict[str, list[tuple[str, float]]] = {}
        for r in self.db.execute(
            "select retailer, day, price from prices where product_id = ? order by retailer, day",
            (product_id,),
        ):
            out.setdefault(r["retailer"], []).append((r["day"], r["price"]))
        return dict(sorted(out.items(), key=lambda item: item[1][-1][1]))

    def set_meta(self, key: str, value: str) -> None:
        self.db.execute("insert or replace into meta values (?, ?)", (key, value))
        self.db.commit()

    def meta(self, key: str) -> str | None:
        row = self.db.execute("select value from meta where key = ?", (key,)).fetchone()
        return row["value"] if row else None
