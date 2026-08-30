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

This repo is already live at https://github.com/russellwortham/sports-ics-sync
with GitHub Pages serving `docs/` from `main`, so setup below is done — this
is the reference for maintaining it.

## Adding or changing a team

Run these from the repo root (`/Users/russellwortham/repositories/personal/sports-ics-sync`).

1. **Find the team's `sport`/`league`/`team_id`**:
   ```
   .venv/bin/python list_teams.py <sport> <league> <name-filter>
   ```
   Examples:
   ```
   .venv/bin/python list_teams.py football nfl chiefs
   .venv/bin/python list_teams.py baseball mlb dodgers
   .venv/bin/python list_teams.py basketball mens-college-basketball duke
   .venv/bin/python list_teams.py football college-football alabama
   ```
   Common `sport`/`league` pairs:
   - `basketball`/`nba`, `basketball`/`mens-college-basketball`, `basketball`/`wnba`
   - `football`/`nfl`, `football`/`college-football`
   - `baseball`/`mlb`
   - `hockey`/`nhl`

2. **Add an entry to `teams.yaml`**:
   ```yaml
     - name: "Kansas City Chiefs"
       slug: kc-chiefs
       sport: football
       league: nfl
       team_id: kc
   ```

3. **Test locally** before pushing:
   ```
   .venv/bin/python generate_ics.py
   ```
   Check that `docs/<slug>.ics` was created and looks right.

4. **Commit and push**:
   ```
   git add teams.yaml docs
   git commit -m "Add <team name>"
   git push
   ```

5. **(Optional) Force an immediate refresh** instead of waiting up to 6 hours
   for the next scheduled run:
   ```
   gh workflow run update-ics.yml
   ```

6. **Subscribe the new feed in Google Calendar**: Settings → Add calendar →
   From URL → paste `https://russellwortham.github.io/sports-ics-sync/<slug>.ics`
   (one per team, so you can toggle/color each team independently), or
   `.../all.ics` for a single combined calendar.

## Scheduling

GitHub Actions is the scheduler — no local cron or launchd job needed, and it
runs even if your Mac is off. `.github/workflows/update-ics.yml` has:
```yaml
on:
  schedule:
    - cron: "0 */6 * * *"  # every 6 hours
```
It regenerates the `.ics` files and commits any changes automatically. To
change the frequency, edit that cron expression and push. Google Calendar
then polls the published URL on its own schedule (roughly every 12-24 hours,
Google's choice, not push-based) — so the feed being fresh on GitHub doesn't
mean Google grabs it instantly.

## Notes

- Game start times come from ESPN in UTC; each event is given a 3-hour
  duration since ESPN doesn't publish an explicit end time.
- If ESPN hasn't confirmed a start time yet (`timeValid: false`), the event
  is written as an all-day placeholder for that date instead of guessing a
  time.
- UIDs are derived from ESPN's event ID, so re-running the generator updates
  existing calendar entries in place rather than duplicating them.
