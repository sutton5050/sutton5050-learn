import json
import urllib.request

FPL_BASE = "https://fantasy.premierleague.com/api"

# FPL needs a browser-like User-Agent or it may block the request
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; dashboard/1.0)",
    "Accept": "application/json",
}


def fetch_json(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.loads(response.read().decode())


def lambda_handler(event, context):
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Content-Type": "application/json",
    }

    try:
        # ── 1. Bootstrap data (teams + league table) ──────────────
        bootstrap = fetch_json(f"{FPL_BASE}/bootstrap-static/")
        teams = bootstrap["teams"]

        # Find Liverpool's ID
        liverpool = next((t for t in teams if t["name"] == "Liverpool"), None)
        if not liverpool:
            raise Exception("Liverpool not found in FPL data")
        liverpool_id = liverpool["id"]

        # Build Premier League table sorted by position
        pl_table = sorted(teams, key=lambda t: t.get("position", 99))
        table_data = [
            {
                "position": t.get("position", 0),
                "name": t["name"],
                "played": t.get("played", 0),
                "won": t.get("win", 0),
                "drawn": t.get("draw", 0),
                "lost": t.get("loss", 0),
                "gf": t.get("goals_scored", 0),
                "ga": t.get("goals_conceded", 0),
                "gd": t.get("goals_scored", 0) - t.get("goals_conceded", 0),
                "points": t.get("points", 0),
            }
            for t in pl_table
        ]

        # ── 2. Fixtures ───────────────────────────────────────────
        fixtures_raw = fetch_json(f"{FPL_BASE}/fixtures/")

        # Liverpool's next 5 unplayed fixtures
        upcoming = [
            f
            for f in fixtures_raw
            if (f["team_h"] == liverpool_id or f["team_a"] == liverpool_id)
            and not f.get("finished", False)
        ][:5]

        team_map = {t["id"]: t["name"] for t in teams}

        fixtures_data = [
            {
                "opponent": team_map.get(
                    f["team_a"] if f["team_h"] == liverpool_id else f["team_h"],
                    "Unknown",
                ),
                "home_away": "Home" if f["team_h"] == liverpool_id else "Away",
                "kickoff": f.get("kickoff_time"),
                "gameweek": f.get("event"),
            }
            for f in upcoming
        ]

        # ── 3. Return everything ──────────────────────────────────
        return {
            "statusCode": 200,
            "headers": cors_headers,
            "body": json.dumps(
                {
                    "liverpool_fixtures": fixtures_data,
                    "pl_table": table_data,
                }
            ),
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": cors_headers,
            "body": json.dumps({"error": str(e)}),
        }
