"""Corre contra la sandbox pública (sk_test_sandbox). PRICES_API_URL apunta a otra instancia."""

import pytest

from price_tracker import text
from price_tracker.api import ApiError, Client
from price_tracker.chart import render
from price_tracker.cli import main
from price_tracker.store import Store
from price_tracker.tracker import resolve, track


@pytest.fixture
def client():
    return Client(key="sk_test_sandbox")


def test_search_finds_the_product(client):
    product_id, others = resolve(client, "leche entera colun 1 litro")
    assert product_id.startswith("prd_")
    assert all(o["id"] != product_id for o in others)


def test_track_saves_today_and_history(client, tmp_path):
    store = Store(str(tmp_path / "prices.db"))
    data = track(client, store, "prd_01colu", history_days=30)
    series = store.series("prd_01colu")
    assert set(series) == {p["retailer"]["name"] for p in data["prices"]}
    assert all(len(points) > 1 for points in series.values())
    cheapest = min(p["price"] for p in data["prices"])
    assert next(iter(series.values()))[-1][1] == cheapest
    assert store.meta("sample_data") == "True"


def test_chart_is_a_self_contained_page(client, tmp_path):
    store = Store(str(tmp_path / "prices.db"))
    track(client, store, "prd_01colu", history_days=7)
    html = render(store)
    assert html.count("<svg") == 1 and "<script" not in html
    assert "italic" not in html


def test_cli_add_and_list(tmp_path, capsys):
    db = str(tmp_path / "prices.db")
    assert main(["--db", db, "--lang", "en", "add", "paracetamol", "--days", "7"]) == 0
    assert main(["--db", db, "--lang", "en", "list"]) == 0
    assert "CLP" in capsys.readouterr().out


def test_bad_key_explains_what_to_do():
    with pytest.raises(ApiError) as e:
        Client(key="sk_test_wrong").search("leche")
    assert e.value.code == "unauthorized"


def test_money_and_delta():
    text.LANG = "es"
    assert text.money(1090) == "$1.090"
    assert text.delta(1000, 1035) == ("▲ 3,5 %", "sube")
    text.LANG = "en"
    assert text.money(1090) == "CLP 1,090"
    assert text.delta(1000, 965) == ("▼ 3.5%", "baja")
