#!/usr/bin/env python3
"""Look up ESPN sport/league/team_id values to put in teams.yaml.

Usage:
    python list_teams.py basketball nba
    python list_teams.py football college-football
    python list_teams.py basketball mens-college-basketball
    python list_teams.py basketball nba lakers   # filter by name

Common league values:
    basketball/nba, basketball/mens-college-basketball, basketball/wnba
    football/nfl, football/college-football
    baseball/mlb
    hockey/nhl
"""
import sys

import requests

TEAMS_URL = "https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/teams?limit=999"


def main() -> int:
    if len(sys.argv) < 3:
        print(__doc__)
        return 1

    sport, league = sys.argv[1], sys.argv[2]
    name_filter = sys.argv[3].lower() if len(sys.argv) > 3 else None

    resp = requests.get(TEAMS_URL.format(sport=sport, league=league), timeout=15)
    resp.raise_for_status()
    data = resp.json()

    teams = data["sports"][0]["leagues"][0]["teams"]
    for entry in teams:
        team = entry["team"]
        display = team["displayName"]
        if name_filter and name_filter not in display.lower():
            continue
        print(f"{team['id']:>6}  {team.get('abbreviation', ''):<6}  {display}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
