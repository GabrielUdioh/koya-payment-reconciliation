#!/usr/bin/env python3
"""Payment reconciliation.

Reads payments.jsonl and works out how much money we actually collected.

Rules (from the README):
  - Skip lines that can't be parsed and events without a txn_id.
  - A txn_id can have several attempts; only the latest attempt (by ts) counts.
  - A payment is collected only if its latest attempt is 'success'.
  - Amounts can be numbers or strings with thousands separators ("4,804.15").

Run: python3 reconcile.py
"""

import json
from datetime import datetime
from decimal import Decimal

latest = {}  # txn_id -> (timestamp, event)

with open("payments.jsonl", encoding="utf-8", errors="replace") as f:
    for line in f:
        try:
            event = json.loads(line)
        except ValueError:
            continue  # unreadable line
        if not isinstance(event, dict) or not event.get("txn_id"):
            continue  # no txn_id

        # ts is UTC like "2026-09-21T15:30:26Z"; parse so ordering is by time,
        # not by position in the file (the export is not in time order).
        ts = datetime.fromisoformat(event["ts"].replace("Z", "+00:00"))
        txn = event["txn_id"]
        if txn not in latest or ts > latest[txn][0]:
            latest[txn] = (ts, event)

total = Decimal("0")
count = 0
for ts, event in latest.values():
    if event["status"] == "success":
        # Decimal avoids float rounding drift; str() handles int/float,
        # and removing commas handles values like "4,804.15".
        total += Decimal(str(event["amount"]).replace(",", ""))
        count += 1

with open("expected.txt") as f:
    expected = int(f.read().strip())

if count != expected:
    print(f"Check failed: counted {count} successful payments, expected {expected}.")
    print("Something in the data isn't being handled the way the README describes.")
else:
    print(f"Check passed: {count} successful payments.")
    print(f"Your code: KOYA-{round(total)}")
