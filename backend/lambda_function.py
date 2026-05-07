import json
import os
import urllib.request

BASE = "https://api.football-data.org/v4"
LIVERPOOL_ID = 64  # Liverpool's ID in football-data.org


def fetch_json(url):
    api_key = os.environ.get("FOOTBALL_API_KEY", "")
    req = urllib.request.Request(url, headers={"X-Auth-Token": api_key})
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.loads(response.read().decode())


def lambda_handler(event, context):
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Content-Type": "application/json",
    }

    try:
        # ── Premier League table ──────────────────────────────────
        standings_data = fetch_json(f"{BASE}/competitions/PL/standings")
        table_entries = standings_data["standings"][0]["table"]

        pl_table = [
            {
                "position": e["position"],
                "name": e["team"]["shortName"],
                "played": e["playedGames"],
                "gd": e["goalDifference"],
                "points": e["points"],
            }
            for e in table_entries
        ]

        # ── Liverpool upcoming fixtures ───────────────────────────
        matches_data = fetch_json(
            f"{BASE}/teams/{LIVERPOOL_ID}/matches?status=SCHEDULED&limit=5"
        )
        matches = matches_data.get("matches", [])

        fixtures = [
            {
                "opponent": (
                    m["awayTeam"]["shortName"]
                    if m["homeTeam"]["id"] == LIVERPOOL_ID
                    else m["homeTeam"]["shortName"]
                ),
                "home_away": (
                    "Home" if m["homeTeam"]["id"] == LIVERPOOL_ID else "Away"
                ),
                "kickoff": m.get("utcDate"),
            }
            for m in matches[:5]
        ]

        # ── Return ────────────────────────────────────────────────
        return {
            "statusCode": 200,
            "headers": cors_headers,
            "body": json.dumps(
                {
                    "liverpool_fixtures": fixtures,
                    "pl_table": pl_table,
                }
            ),
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": cors_headers,
            "body": json.dumps({"error": str(e)}),
        }
