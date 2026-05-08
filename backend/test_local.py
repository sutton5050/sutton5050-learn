import os
import json

os.environ["FOOTBALL_API_KEY"] = "65de886ae48c45cfbe8f8d3a9af7fbc4"

from lambda_function import fetch_json, BASE, LIVERPOOL_ID
from datetime import datetime, timedelta

today = datetime.utcnow()
date_from = (today - timedelta(days=120)).strftime("%Y-%m-%d")
date_to = today.strftime("%Y-%m-%d")

data = fetch_json(
    f"{BASE}/teams/{LIVERPOOL_ID}/matches?status=FINISHED&dateFrom={date_from}&dateTo={date_to}"
)

matches = data.get("matches", [])
if matches:
    latest = sorted(matches, key=lambda m: m["utcDate"], reverse=True)[0]
    detail = fetch_json(f"{BASE}/matches/{latest['id']}")
    print(json.dumps(detail.get("goals", []), indent=2))
else:
    print("No matches returned")
