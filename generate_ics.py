#!/usr/bin/env python3
"""Fetch team schedules from ESPN's public JSON API and write .ics feeds.

Reads teams.yaml, writes one .ics per team plus a combined all.ics, into
docs/ (served via GitHub Pages so Google Calendar can subscribe to a URL).
"""
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid5, NAMESPACE_URL

import requests
import yaml
from icalendar import Calendar, Event

ROOT = Path(__file__).parent
OUTPUT_DIR = ROOT / "docs"
SCHEDULE_URL = "https://site.api.espn.com/apis/site/v2/sports/{sport}/{league}/teams/{team_id}/schedule"
GAME_DURATION = timedelta(hours=3)
REQUEST_TIMEOUT = 15
# ESPN's schedule endpoint without a seasontype param only returns whichever
# phase it currently considers "the" season (e.g. just the 3 preseason games
# while the real season hasn't started yet, silently omitting the other 17).
# Fetching every phase and merging avoids that.
SEASON_TYPES = (1, 2, 3)  # preseason, regular season, postseason


def fetch_schedule_events(sport: str, league: str, team_id: str) -> list[dict]:
    events_by_id: dict[str, dict] = {}
    any_success = False
    for season_type in SEASON_TYPES:
        url = SCHEDULE_URL.format(sport=sport, league=league, team_id=team_id)
        try:
            resp = requests.get(url, params={"seasontype": season_type}, timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
        except requests.RequestException:
            continue
        any_success = True
        for event in resp.json().get("events", []):
            events_by_id[event["id"]] = event

    if not any_success:
        raise requests.RequestException(
            f"all seasontype requests failed for {sport}/{league}/{team_id}"
        )
    return sorted(events_by_id.values(), key=lambda e: e["date"])


def event_uid(sport: str, league: str, event_id: str) -> str:
    return str(uuid5(NAMESPACE_URL, f"espn:{sport}:{league}:{event_id}"))


def build_event(sport: str, league: str, team_name: str, event: dict) -> Event:
    ev = Event()
    event_id = event["id"]
    ev.add("uid", f"{event_uid(sport, league, event_id)}@sports-ics-sync")

    competition = event["competitions"][0]
    competitors = {c["homeAway"]: c["team"]["displayName"] for c in competition["competitors"]}
    home = competitors.get("home", "?")
    away = competitors.get("away", "?")
    ev.add("summary", f"{away} @ {home}")

    time_valid = event.get("timeValid", True)
    start_raw = event["date"]  # e.g. "2026-10-06T02:00Z"
    start = datetime.strptime(start_raw, "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc)

    if time_valid:
        ev.add("dtstart", start)
        ev.add("dtend", start + GAME_DURATION)
    else:
        # ESPN hasn't confirmed a start time yet -- use an all-day placeholder
        # rather than guessing a time.
        ev.add("dtstart", start.date())
        ev.add("dtend", start.date() + timedelta(days=1))

    venue = competition.get("venue", {})
    address = venue.get("address", {})
    location_parts = [
        venue.get("fullName"),
        address.get("city"),
        address.get("state"),
    ]
    ev.add("location", ", ".join(p for p in location_parts if p))

    broadcasts = competition.get("broadcasts", [])
    broadcast_names = [n for b in broadcasts for n in b.get("names", [])]
    description_lines = [f"Tracked team: {team_name}"]
    if broadcast_names:
        description_lines.append(f"Broadcast: {', '.join(broadcast_names)}")
    status = competition.get("status", {}).get("type", {}).get("description")
    if status:
        description_lines.append(f"Status: {status}")
    ev.add("description", "\n".join(description_lines))

    ev.add("dtstamp", datetime.now(timezone.utc))
    return ev


def build_calendar(name: str, events: list[Event]) -> Calendar:
    cal = Calendar()
    cal.add("prodid", "-//sports-ics-sync//espn//EN")
    cal.add("version", "2.0")
    cal.add("x-wr-calname", name)
    cal.add("calscale", "GREGORIAN")
    for ev in events:
        cal.add_component(ev)
    return cal


def main() -> int:
    config = yaml.safe_load((ROOT / "teams.yaml").read_text())
    teams = config.get("teams", [])
    if not teams:
        print("teams.yaml has no teams configured", file=sys.stderr)
        return 1

    slugs_seen: dict[str, str] = {}
    for team in teams:
        slug = team["slug"]
        if slug in slugs_seen:
            print(
                f"teams.yaml error: '{slugs_seen[slug]}' and '{team['name']}' both use "
                f"slug '{slug}', which would overwrite one team's feed with the other's. "
                "Give each team a distinct slug (e.g. ark-fb vs ark-bb).",
                file=sys.stderr,
            )
            return 1
        slugs_seen[slug] = team["name"]

    OUTPUT_DIR.mkdir(exist_ok=True)
    all_events: list[Event] = []

    for team in teams:
        name = team["name"]
        slug = team["slug"]
        sport = team["sport"]
        league = team["league"]
        team_id = str(team["team_id"])

        print(f"Fetching {name} ({sport}/{league}/{team_id})...")
        try:
            raw_events = fetch_schedule_events(sport, league, team_id)
        except requests.RequestException as exc:
            print(f"  WARNING: failed to fetch {name}: {exc}", file=sys.stderr)
            continue

        events = [build_event(sport, league, name, raw_event) for raw_event in raw_events]
        print(f"  {len(events)} events")

        cal = build_calendar(name, events)
        out_path = OUTPUT_DIR / f"{slug}.ics"
        out_path.write_bytes(cal.to_ical())

        all_events.extend(events)

    combined = build_calendar("All Teams", all_events)
    (OUTPUT_DIR / "all.ics").write_bytes(combined.to_ical())
    print(f"Wrote {len(teams)} team feed(s) + all.ics to {OUTPUT_DIR}")

    expected = {f"{team['slug']}.ics" for team in teams} | {"all.ics"}
    for existing in OUTPUT_DIR.glob("*.ics"):
        if existing.name not in expected:
            print(f"Removing stale feed no longer in teams.yaml: {existing.name}")
            existing.unlink()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
