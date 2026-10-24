"""Cliente mínimo de la API REST de precios, solo con la biblioteca estándar."""

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

SANDBOX_KEY = "sk_test_sandbox"
DEFAULT_URL = "https://mercali-platform.vercel.app"


class ApiError(Exception):
    """Error de la API (RFC 9457): `code` es estable y `hint` dice qué hacer."""

    def __init__(self, problem: dict):
        self.code = problem.get("code", "error")
        self.hint = problem.get("hint", "")
        super().__init__(f"{problem.get('detail') or problem.get('title')} {self.hint}".strip())


class Client:
    def __init__(self, key: str | None = None, url: str | None = None, lang: str = "es"):
        self.key = key or os.environ.get("PRICES_API_KEY") or SANDBOX_KEY
        self.base = (url or os.environ.get("PRICES_API_URL") or DEFAULT_URL).rstrip("/") + "/v1"
        self.lang = lang

    def get(self, path: str, **params) -> dict:
        params = {k: v for k, v in params.items() if v is not None} | {"lang": self.lang}
        request = urllib.request.Request(
            f"{self.base}{path}?{urllib.parse.urlencode(params)}",
            headers={"Authorization": f"Bearer {self.key}", "User-Agent": "price-tracker-example/0.1"},
        )
        for attempt in range(4):
            try:
                with urllib.request.urlopen(request, timeout=30) as response:
                    return json.load(response)
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt < 3:
                    time.sleep(float(e.headers.get("Retry-After") or 1))
                    continue
                try:
                    problem = json.load(e)
                except ValueError:
                    problem = {"code": f"http_{e.code}", "title": e.reason}
                raise ApiError(problem) from None
        raise AssertionError("unreachable")

    def search(self, query: str, limit: int = 5) -> list[dict]:
        return self.get("/products/search", q=query, limit=limit)["data"]

    def prices(self, product_id: str) -> dict:
        return self.get(f"/products/{product_id}/prices")

    def history(self, product_id: str, since: str) -> dict:
        return self.get(f"/products/{product_id}/history", interval="day", **{"from": since})
