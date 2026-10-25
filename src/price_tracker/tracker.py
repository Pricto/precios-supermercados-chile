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
        # La ventana se cuenta desde el último día con datos, no desde hoy: así no depende de la
        # hora ni de cuánto se atrase la captura (la sandbox, por ejemplo, termina en una fecha fija).
        latest = max((date.fromisoformat(p["observed_local_date"]) for p in data["prices"]), default=date.today())
        since = (latest - timedelta(days=history_days)).isoformat()
        for s in client.history(product_id, since)["data"]["series"]:
            offer = offers.get(s["offer_id"])
            if offer is None:  # el historial también trae packs y otros formatos: solo el mismo artículo
                continue
            rows += [(s["offer_id"], offer["retailer"]["name"], p["t"], p["price"], offer["url"])
                     for p in s["points"] if p["price"] is not None]
    store.add_product(data["product"])
    store.save_prices(product_id, rows + _today(data["prices"]))
    _save_meta(store, response["meta"], data["prices"])
    return data


def update_all(client: Client, store: Store) -> int:
    """El precio de hoy de todos los productos seguidos, de a 500 por llamada (/prices/batch)."""
    ids = [p["id"] for p in store.products()]
    for start in range(0, len(ids), 500):
        response = client.batch(ids[start:start + 500])
        for item in response["data"]:
            if item["found"]:
                store.save_prices(item["product_id"], _today(item["prices"]))
        _save_meta(store, response["meta"], [p for item in response["data"] for p in item.get("prices", [])])
    return len(ids)


def _today(prices: list[dict]) -> list[tuple]:
    return [(p["offer_id"], p["retailer"]["name"], p["observed_local_date"], p["price"], p["url"]) for p in prices]


def _save_meta(store: Store, meta: dict, prices: list[dict]) -> None:
    # La atribución de la API, sin el id del recurso: la página muestra varios productos.
    attribution = meta["attribution"]
    store.set_meta("attribution", attribution["text"].removesuffix(f" · {attribution.get('resource_id')}"))
    store.set_meta("currency", prices[0]["currency"] if prices else "CLP")
    store.set_meta("sample_data", str(any(w.startswith("synthetic_data") for w in meta.get("warnings", []))))
