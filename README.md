# sports-ics-sync

Pulls game schedules from ESPN's public JSON API for whatever teams you
configure and publishes them as `.ics` feeds that Google Calendar can
subscribe to.

## How it works

- `teams.yaml` lists the teams you want tracked.
- `generate_ics.py` fetches each team's schedule from ESPN and writes one
  `.ics` file per team (plus a combined `all.ics`) into `docs/`.
- A GitHub Actions workflow (`.github/workflows/update-ics.yml`) runs the
  script every 6 hours and commits any changes.
- GitHub Pages serves `docs/` as a website, giving each `.ics` file a stable
  public URL that Google Calendar polls periodically (Google controls the
  refresh interval, typically every 12-24 hours — it does not push updates
  instantly).

## Setup

1. **Configure teams** in `teams.yaml`. Each entry needs `name`, `slug`
   (used as the filename), `sport`, `league`, and `team_id`.

2. **Find team IDs** with the lookup helper:
   ```
   python list_teams.py basketball nba lakers
   python list_teams.py football college-football duke
   ```
   Common `sport`/`league` pairs:
   - `basketball`/`nba`, `basketball`/`mens-college-basketball`, `basketball`/`wnba`
   - `football`/`nfl`, `football`/`college-football`
   - `baseball`/`mlb`
   - `hockey`/`nhl`

3. **Test locally**:
   ```
   python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
   .venv/bin/python generate_ics.py
   ```
   Check the output in `docs/`.

4. **Push to GitHub**, then enable Pages: repo Settings → Pages → Source =
   `Deploy from a branch`, branch `main`, folder `/docs`. GitHub will give you
   a URL like `https://<username>.github.io/<repo>/`.

5. **Subscribe in Google Calendar**: Settings → Add calendar → From URL →
   paste `https://<username>.github.io/<repo>/<slug>.ics` (one per team, so
   you can toggle/color each team independently), or `.../all.ics` for a
   single combined calendar.

6. The GitHub Actions workflow keeps the feeds refreshed automatically going
   forward — no further action needed after setup. You can also trigger it
   manually from the Actions tab (`workflow_dispatch`).

## Notes

- Game start times come from ESPN in UTC; each event is given a 3-hour
  duration since ESPN doesn't publish an explicit end time.
- If ESPN hasn't confirmed a start time yet (`timeValid: false`), the event
  is written as an all-day placeholder for that date instead of guessing a
  time.
- UIDs are derived from ESPN's event ID, so re-running the generator updates
  existing calendar entries in place rather than duplicating them.
