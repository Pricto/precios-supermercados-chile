"""Lo que hace el tracker: buscar un producto y guardar sus precios por tienda."""

from datetime import date, timedelta

from .api import Client
from .store import Store


def resolve(client: Client, query: str) -> tuple[str, list[dict]]:
    """Un product_id (prd_...) o un GTIN se usan tal cual; un texto se busca y gana el primero."""
    if query.startswith("prd_") or query.isdigit():
        return query, []
    results = client.search(query)
    if not results:
        raise LookupError(query)
    return results[0]["id"], results[1:]


def track(client: Client, store: Store, product: str, history_days: int = 0) -> dict:
    """Guarda el precio de hoy en cada tienda y, si se pide, los días anteriores."""
    response = client.prices(product)
    data = response["data"]
    product_id = data["product"]["id"]
    offers = {p["offer_id"]: p for p in data["prices"]}

    rows = []
    if history_days:
        since = (date.today() - timedelta(days=history_days)).isoformat()
        for s in client.history(product_id, since)["data"]["series"]:
            offer = offers.get(s["offer_id"])
            if offer is None:  # el historial también trae packs y otros formatos: solo el mismo artículo
                continue
            rows += [(s["offer_id"], offer["retailer"]["name"], p["t"], p["price"], offer["url"])
                     for p in s["points"] if p["price"] is not None]
    rows += [(p["offer_id"], p["retailer"]["name"], p["observed_local_date"], p["price"], p["url"])
             for p in data["prices"]]

    store.add_product(data["product"])
    store.save_prices(product_id, rows)
    meta = response["meta"]
    store.set_meta("attribution", meta["attribution"]["text"])
    store.set_meta("currency", data["prices"][0]["currency"] if data["prices"] else "CLP")
    store.set_meta("sample_data", str(any(w.startswith("synthetic_data") for w in meta.get("warnings", []))))
    return data
