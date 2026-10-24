"""Textos en español e inglés y formato de cifras."""

import os

LANG = "es" if os.environ.get("LANG", "").startswith("es") else "en"

MESSAGES = {
    "added": ("Siguiendo", "Tracking"),
    "removed": ("Eliminado", "Removed"),
    "not_tracked": ("No está en la lista", "Not in the list"),
    "not_found": ("No encontré productos para", "No products found for"),
    "also": ("Otros resultados (agrega por id):", "Other matches (add by id):"),
    "stores": ("tiendas", "stores"),
    "days": ("días de historial", "days of history"),
    "empty": ("La lista está vacía. Agrega un producto: price-tracker add \"leche entera\"",
              "The list is empty. Add a product: price-tracker add \"whole milk\""),
    "chart_saved": ("Gráfico guardado en", "Chart saved to"),
    "cheapest": ("más barato", "cheapest"),
    "sample": ("Datos de ejemplo de la sandbox: precios, códigos y URLs inventados.",
               "Sandbox sample data: prices, barcodes and URLs are made up."),
    "title": ("Historial de precios", "Price history"),
    "since": ("desde", "since"),
    "latest": ("Último precio", "Latest price"),
    "monitor": ("Monitor de precios", "Price monitor"),
    "products": ("productos", "products"),
    "changes": ("cambios", "changes"),
    "drops": ("bajas", "drops"),
    "rises": ("subas", "rises"),
    "product": ("Producto", "Product"),
    "report_saved": ("Monitor guardado en", "Monitor saved to"),
    "added_many": ("Siguiendo", "Tracking"),
    "export": ("Exportar CSV", "Export CSV"),
}


def t(key: str) -> str:
    es, en = MESSAGES[key]
    return es if LANG == "es" else en


def money(amount: float, currency: str = "CLP") -> str:
    """$1.090 en español, CLP 1,090 en inglés. El CLP no tiene decimales."""
    decimals = 0 if currency == "CLP" else 2
    text = f"{amount:,.{decimals}f}"
    if LANG == "es":
        text = text.replace(",", "_").replace(".", ",").replace("_", ".")
        return f"${text}" if currency == "CLP" else f"{currency} {text}"
    return f"{currency} {text}"


def delta(before: float, after: float) -> tuple[str, str]:
    """Variación con flecha y signo, y su clase: sube, baja o igual."""
    pct = (after - before) / before * 100 if before else 0.0
    text = f"{abs(pct):.1f}".replace(".", "," if LANG == "es" else ".")
    text += " %" if LANG == "es" else "%"
    if round(pct, 1) > 0:
        return f"▲ {text}", "sube"
    if round(pct, 1) < 0:
        return f"▼ {text}", "baja"
    return f"= {text}", "igual"
