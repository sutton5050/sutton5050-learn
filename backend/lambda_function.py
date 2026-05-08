import json
import os
import urllib.request
from datetime import datetime, timedelta

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

        # ── Liverpool last 5 results ──────────────────────────────
        today = datetime.utcnow()
        date_from = (today - timedelta(days=120)).strftime("%Y-%m-%d")
        date_to = today.strftime("%Y-%m-%d")
        results_data = fetch_json(
            f"{BASE}/teams/{LIVERPOOL_ID}/matches?status=FINISHED"
            f"&dateFrom={date_from}&dateTo={date_to}"
        )
        finished = results_data.get("matches", [])
        finished.sort(key=lambda m: m["utcDate"], reverse=True)

        last_5 = []
        for m in finished[:5]:
            is_home = m["homeTeam"]["id"] == LIVERPOOL_ID
            ft = m["score"]["fullTime"]
            lfc_score = ft["home"] if is_home else ft["away"]
            opp_score = ft["away"] if is_home else ft["home"]

            if lfc_score is None or opp_score is None:
                result = "?"
            elif lfc_score > opp_score:
                result = "W"
            elif lfc_score == opp_score:
                result = "D"
            else:
                result = "L"

            goals = [
                {
                    "scorer": g.get("scorer", {}).get("name", "Unknown"),
                    "minute": g.get("minute"),
                    "lfc": g.get("team", {}).get("id") == LIVERPOOL_ID,
                }
                for g in m.get("goals", [])
            ]

            last_5.append({
                "opponent": m["awayTeam"]["shortName"] if is_home else m["homeTeam"]["shortName"],
                "home_away": "Home" if is_home else "Away",
                "date": m.get("utcDate"),
                "score_lfc": lfc_score,
                "score_opp": opp_score,
                "result": result,
                "goals": goals,
            })

        # ── Return ────────────────────────────────────────────────
        return {
            "statusCode": 200,
            "headers": cors_headers,
            "body": json.dumps(
                {
                    "liverpool_fixtures": fixtures,
                    "pl_table": pl_table,
                    "liverpool_results": last_5,
                }
            ),
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": cors_headers,
            "body": json.dumps({"error": str(e)}),
        }
