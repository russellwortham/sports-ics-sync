#!/usr/bin/env python3
"""Look up ESPN teams and print ready-to-paste teams.yaml entries.

Usage:
    python list_teams.py basketball nba
    python list_teams.py football college-football
    python list_teams.py basketball mens-college-basketball
    python list_teams.py basketball nba lakers   # filter by name

Prints one YAML block per matching team -- copy the ones you want straight
into teams.yaml, then adjust `slug` if you'd rather it not match `team_id`.

Common league values:
    basketball/nba, basketball/wnba
    basketball/mens-college-basketball, basketball/womens-college-basketball
    football/nfl, football/college-football
    baseball/mlb
    hockey/nhl
    soccer/eng.1 (Premier League), soccer/usa.1 (MLS)

Not seeing your league here? Go to that sport's page on espn.com -- the
segment right after espn.com/ is usually the league value (e.g.
espn.com/mens-college-basketball), and `sport` is the broader family word
(basketball, football, baseball, hockey, soccer, ...).
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
    if resp.status_code == 404:
        print(
            f"ESPN doesn't recognize sport={sport!r} league={league!r}.\n"
            "Check the sport/league values against the site.espn.com URL for that\n"
            "sport (the part right after espn.com/ is usually the league value),\n"
            "or see the Common league values list above (run with no args).",
            file=sys.stderr,
        )
        return 1
    resp.raise_for_status()
    data = resp.json()

    teams = data["sports"][0]["leagues"][0]["teams"]
    matches = []
    for entry in teams:
        team = entry["team"]
        display = team["displayName"]
        if name_filter and name_filter not in display.lower():
            continue
        matches.append(team)

    if not matches:
        print("No teams matched.", file=sys.stderr)
        return 1

    for team in matches:
        abbr = team.get("abbreviation", "")
        slug = abbr.lower() if abbr else str(team["id"])
        team_id = abbr.lower() if abbr else team["id"]
        print(f"  - name: \"{team['displayName']}\"")
        print(f"    slug: {slug}")
        print(f"    sport: {sport}")
        print(f"    league: {league}")
        print(f"    team_id: {team_id}")
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
