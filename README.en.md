# Chile supermarket price API: tracking and history

[![Tests](https://github.com/Pricto/precios-supermercados-chile/actions/workflows/tests.yml/badge.svg)](https://github.com/Pricto/precios-supermercados-chile/actions/workflows/tests.yml)
[![MIT license](https://img.shields.io/badge/license-MIT-0f5a45.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-0f5a45.svg)](pyproject.toml)
[![Data: Pricto API](https://img.shields.io/badge/data-Pricto%20API-b0401f.svg)](https://pricto.dev)

Track the price of products at Chilean supermarkets and pharmacies (Jumbo, Unimarc, Santa Isabel, Cruz Verde, Farmacias Ahumada and more) with the [Pricto](https://pricto.dev) price API: it keeps the price history per store in SQLite, charts it and builds a competitor monitor with price changes and CSV export. Python 3.10+, no dependencies.

[Español](README.md) · [API docs](https://pricto.dev/docs) · [Coverage](https://pricto.dev/cobertura) · [Create a free account](https://pricto.dev/registro)

![Price history of a product at several Chilean stores, with the cheapest store marked](docs/chart-en.png)

## Try it in a minute

No account needed: without `PRICTO_API_KEY` the tracker uses Pricto's public sandbox (`sk_test_sandbox`), which answers with sample data. With [uv](https://docs.astral.sh/uv/):

```bash
uvx --from git+https://github.com/Pricto/precios-supermercados-chile price-tracker --lang en add "whole milk"
```

```text
Tracking: Colun whole milk 1 L (prd_01colu) · 3 stores · 30 days of history
  Unimarc                   CLP 1,090   2026-10-23
  Santa Isabel              CLP 1,190   2026-10-23
  Jumbo                     CLP 1,290   2026-10-23
Other matches (add by id):
  prd_04colu  Colun whole milk 6 x 1 L pack
  prd_02sopr  Soprole skimmed milk 1 L
  prd_03lonc  Loncoleche lactose-free semi-skimmed milk 1 L
```

With `pip`: `pip install git+https://github.com/Pricto/precios-supermercados-chile`, then `price-tracker ...`.

## Which stores it covers

The data comes from the Pricto API, which captures the public online prices of more than 120 Chilean stores every day ([full list and status of each](https://pricto.dev/cobertura), source registry as of 2026-10-24):

- Supermarkets: Jumbo, Santa Isabel, Unimarc, Alvi, Mayorista Nacional, Supermercado La Herradura, Supermercados José González, Alimentika, Compras Aqui and Distribuidora Fermarket.
- Pharmacies: Cruz Verde, Farmacias Ahumada, Farmacias del Dr. Simi, Farmacias Knop, Farmacias Novasalud, EcoFarmacias, Farmacia Meki, Farmaloop, Farmazon and Cofar.
- Also electronics, home improvement, department stores, pets, sports, liquor, books and toys.

It does not cover Lider, Tottus, Superbodega aCuenta, Central Mayorista, Salcobrand or Preunic: they block bots that identify themselves or their terms don't allow it. The sandbox has made-up data for 7 of those chains (Jumbo, Santa Isabel, Unimarc, Cruz Verde, Farmacias Ahumada, Dr. Simi and Knop); real prices need a [free account](https://pricto.dev/registro).

## Commands

| Command | What it does |
|---|---|
| `price-tracker add "paracetamol"` | Searches and tracks the first match. Takes text, a `product_id` (`prd_...`) or a barcode. `--days 60` loads more history (default 30). |
| `price-tracker add --brand colun` | Tracks every product of a brand. `--category food.dairy` does the same for a category. |
| `price-tracker update` | Saves today's price of every product, 500 per call, and shows the change against the previous day. |
| `price-tracker list` | Tracked products with their latest price per store, cheapest first. |
| `price-tracker chart` | Writes `prices.html`: one step chart per product, no JavaScript. `-o` sets the file. |
| `price-tracker report --csv monitor.csv` | Writes `monitor.html`: a table of every product and store with each price change and the cheapest store, plus the CSV. `--vs 7` compares against 7 days earlier (default 1). |
| `price-tracker remove prd_01colu` | Stops tracking a product. |

Global options: `--db` (SQLite file, `prices.db` by default, or `PRICE_TRACKER_DB`) and `--lang es|en` (language of messages and product names; defaults to `LANG`).

## Monitor competitors (many SKUs)

For a brand watching its own products and its competitors' at every supermarket:

```bash
price-tracker add --category food.dairy --days 14
price-tracker add --category food.pantry --days 14
price-tracker update                         # one call for all of them
price-tracker report --vs 7 --csv monitor.csv
```

![Monitor of 17 products at three supermarkets with their 7-day changes and CSV export](docs/monitor-en.png)

Products that changed come first, biggest drop on top. The CSV has one row per product and store: `product_id, name, retailer, day, price, previous_day, previous_price, change_pct`. To get a notification instead of opening the table, see [alertas-de-precios-chile](https://github.com/Pricto/alertas-de-precios-chile) (ntfy or webhook).

## Every day

To build your own history, schedule `update` once a day (prices are captured daily):

```bash
# crontab -e
30 9 * * * cd ~/prices && price-tracker update >> update.log 2>&1
```

## Ask your agent

The same data is on Pricto's MCP server, so an agent (Claude, Cursor, VS Code, ChatGPT) can answer these questions without code. Connect it to the sandbox, no login:

```bash
claude mcp add --transport http pricto https://pricto.dev/mcp/sandbox
```

Other clients and connecting with your key: [pricto.dev/docs/mcp](https://pricto.dev/docs/mcp). Questions it answers with the sandbox data:

- How much is Colun whole milk 1 L today at Jumbo, Unimarc and Santa Isabel?
- How did the price of Tucapel grade 2 rice change at each supermarket over the last month?
- Which milk products are on promotion at Jumbo?
- Which pharmacy has Kitadol 24 tablets cheapest?

If you open this repo with the agent, it can also run the tracker for you: "track every Colun product and show me which ones changed price this week" is `price-tracker add --brand colun`, `update` and `report --vs 7`.

## With your key

```bash
export PRICTO_API_KEY=sk_live_...
price-tracker add 7802920000017
```

| Variable | What for | Default |
|---|---|---|
| `PRICTO_API_KEY` | Your API key ([create a free account](https://pricto.dev/registro) and copy it from the console) | `sk_test_sandbox` (sample data) |
| `PRICTO_API_URL` | Another API instance | `https://pricto.dev` |

What it costs (measured against the demo API, 2026-10-24): adding a product sold at 4 stores with 30 days of history is 9 credits (1 for the search, 4 for prices and 4 for history); each `update` charges 1 credit per store, and repeating the same query within 24 hours is free. Every response reports the charge in `meta.credits_charged`. Plans at [pricto.dev/precios](https://pricto.dev/precios).

## How it works

About 500 lines, a third of them HTML and CSS, in [`src/price_tracker/`](src/price_tracker):

- `api.py`: REST client on `urllib`. Retries `429` honoring `Retry-After` and turns errors (RFC 9457) into an `ApiError` with its `code` and a hint on what to do.
- `tracker.py`: `GET /v1/products/search` to find the product (or `GET /v1/products?brand=` / `?category=` for many), `GET /v1/products/{id}/prices` for today's price at every store and `GET /v1/products/{id}/history?interval=day` for the previous days. From the history it keeps only the offers that `/prices` identifies as the same item (history also returns multipacks). `update` uses `POST /v1/prices/batch`, up to 500 products per call.
- `store.py`: SQLite with one price per offer and day; running `update` twice on the same day duplicates nothing.
- `chart.py` and `report.py`: the HTML pages (SVG chart and monitor), with the fonts embedded so they open offline, and the CSV.

`price` is what anyone pays. Store-card prices (`card_price`) and multi-buy promotions come separately in the API and this example doesn't mix them in.

## Tests

They run against the public sandbox:

```bash
git clone https://github.com/Pricto/precios-supermercados-chile && cd precios-supermercados-chile
uv run pytest
```

`PRICTO_API_URL=http://localhost:8787 uv run pytest` runs them against a local instance.

## FAQ

**Is there a supermarket price API for Chile?**
Yes. [Pricto](https://pricto.dev) serves today's price, store-card price, promotions and daily history of products at Chilean supermarkets and pharmacies over a REST API and MCP, with the same product matched across chains. This repo is a Python example.

**How do I compare a product's price at Jumbo, Unimarc and Santa Isabel?**
`price-tracker add "product name"` shows the price at every store and keeps the history. For a whole basket, use the [supermarket comparator](https://github.com/Pricto/comparador-precios-supermercados-chile).

**Does it cover Lider and Tottus?**
No: they block bots that identify themselves. If a chain provides a feed or permission, it comes into coverage. What is and isn't covered is listed at [pricto.dev/cobertura](https://pricto.dev/cobertura).

**Are sandbox prices real?**
No: it is sample data with real store and brand names and made-up prices, barcodes and URLs. With a free account (100 credits a month, no card) the API returns real prices.

**Are these in-store prices?**
No. They are the public prices on each chain's website, with the time and URL of every capture.

**Since when is there history?**
Since 2026-10-24, when daily capture started.

## License

Code under [MIT](LICENSE). The Host Grotesk and Geist Mono fonts are included under the [SIL Open Font License 1.1](src/price_tracker/assets/OFL.txt).
