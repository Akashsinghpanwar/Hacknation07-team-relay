"""Synthetic DEMO price store. Every record is fictional and must never be presented as a live price."""

import datetime as dt
import sqlite3

from coop_assistant.config import DB_PATH

FIELDS = (
    "id", "country", "district", "market", "crop", "product_form", "grade", "currency", "unit",
    "observed_at", "valid_until", "price_value", "sample_count", "source_name", "source_contact",
    "usage_permission", "imported_at",
)

DISTRICTS = {
    "nyeri": "Nyeri",
    "kiambu": "Kiambu",
    "muranga": "Murang'a",
    "kirinyaga": "Kirinyaga",
}


def _records(today):
    day = dt.timedelta(days=1)
    demo = dict(country="Kenya (DEMO)", crop="coffee", currency="KES", unit="kg",
                source_name="SYNTHETIC DEMO FIXTURE", source_contact="none - not a real source",
                usage_permission="demo only", imported_at=today.isoformat())
    return [
        dict(demo, id="DEMO-NYR-PARCH-A", district="Nyeri", market="Demo Co-op Nyeri",
             product_form="parchment", grade="A", observed_at=(today - 2 * day).isoformat(),
             valid_until=(today + 5 * day).isoformat(), price_value=120.0, sample_count=12),
        dict(demo, id="DEMO-NYR-CHERRY", district="Nyeri", market="Demo Co-op Nyeri",
             product_form="cherry", grade="ungraded", observed_at=(today - 2 * day).isoformat(),
             valid_until=(today + 5 * day).isoformat(), price_value=65.0, sample_count=9),
        dict(demo, id="DEMO-KMB-PARCH-A-STALE", district="Kiambu", market="Demo Co-op Kiambu",
             product_form="parchment", grade="A", observed_at=(today - 45 * day).isoformat(),
             valid_until=(today - 30 * day).isoformat(), price_value=110.0, sample_count=8),
        dict(demo, id="DEMO-KRN-PARCH-A-SPARSE", district="Kirinyaga", market="Demo Co-op Kirinyaga",
             product_form="parchment", grade="A", observed_at=(today - 1 * day).isoformat(),
             valid_until=(today + 6 * day).isoformat(), price_value=125.0, sample_count=1),
    ]


def connect(path=DB_PATH, today=None):
    """Open the store, re-seeding so demo dates stay relative to today."""
    today = today or dt.date.today()
    if str(path) != ":memory:":
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute(f"CREATE TABLE IF NOT EXISTS prices ({', '.join(FIELDS)}, PRIMARY KEY (id))")
    conn.execute("DELETE FROM prices")
    conn.executemany(
        f"INSERT INTO prices VALUES ({', '.join('?' * len(FIELDS))})",
        [tuple(r[f] for f in FIELDS) for r in _records(today)],
    )
    conn.commit()
    return conn
