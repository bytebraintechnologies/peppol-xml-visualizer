"""Unit tests for rendering styles (HTML output only; no Edge required).

Run with: pytest tests/test_styles.py
The `peppol` style tests are skipped unless the official stylesheet is installed
(scripts/fetch_peppol_stylesheet.sh).
"""
import os
import re

import pytest
from fastapi.testclient import TestClient

from app.core.config import XSLT_PEPPOL
from app.main import app

TEST_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "test_data")
HTML = {"accept": "text/html"}
needs_peppol = pytest.mark.skipif(not os.path.exists(XSLT_PEPPOL), reason="official Peppol stylesheet not installed")


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:  # runs lifespan -> compiles stylesheets
        yield c


def render(client, name, content=None, **params):
    if content is None:
        with open(os.path.join(TEST_DATA, name), "rb") as f:
            content = f.read()
    return client.post("/render", params=params, headers=HTML, files={"file": (name, content, "text/xml")})


def text_of(html):
    html = re.sub(r"<style.*?</style>", "", html, flags=re.S)
    return " ".join(re.sub(r"<[^>]+>", " ", html).split())


def test_styles_endpoint(client):
    styles = client.get("/styles").json()
    assert set(styles) == {"default", "peppol"}
    assert styles["default"]["available"] is True


def test_default_style_unchanged(client):
    r = render(client, "peppol-sample-invoice.xml", lang="fr")
    assert r.status_code == 200
    assert r.headers["X-Style"] == "default"
    assert "Facture" in r.text


def test_unknown_style_rejected(client):
    r = render(client, "peppol-sample-invoice.xml", style="nope")
    assert r.status_code == 400


def test_supplier_name_falls_back_to_registration_name(client):
    with open(os.path.join(TEST_DATA, "peppol-sample-invoice.xml"), encoding="utf-8") as f:
        xml = f.read()
    supplier_start = xml.index("<cac:AccountingSupplierParty>")
    supplier_end = xml.index("</cac:AccountingSupplierParty>")
    supplier = re.sub(r"\s*<cac:PartyName>.*?</cac:PartyName>", "", xml[supplier_start:supplier_end], flags=re.S)
    reg_name = re.search(r"<cbc:RegistrationName>(.*?)</cbc:RegistrationName>", supplier).group(1)
    xml = xml[:supplier_start] + supplier + xml[supplier_end:]

    r = render(client, "no-trading-name.xml", content=xml.encode("utf-8"))
    assert r.status_code == 200
    assert re.search(r'class="bold-name">\s*' + re.escape(reg_name.replace("&", "&amp;")), r.text)


@needs_peppol
@pytest.mark.parametrize("name,title", [
    ("peppol-sample-invoice.xml", "Invoice"),
    ("peppol-sample-creditnote.xml", "Credit Note"),
])
def test_peppol_style_renders(client, name, title):
    r = render(client, name, style="peppol")
    assert r.status_code == 200
    assert r.headers["X-Style"] == "peppol"
    assert text_of(r.text).startswith(title)
    assert "Unknown document type" not in r.text


@needs_peppol
def test_peppol_style_rejects_self_billing(client):
    r = render(client, "peppol-sample-selfbilling-invoice.xml", style="peppol")
    assert r.status_code == 422
    assert "style=default" in r.json()["detail"]
