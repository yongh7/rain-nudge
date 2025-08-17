# Rain Nudger (GitHub Actions + Python)

Daily 7:00 AM America/New_York push if rain is likely in the next N hours, so I knwo I should flex my 800 dollar arcteryx alpha jacket on that day.

**Stack:** GitHub Actions (cron) → Python (Open‑Meteo, no API key) → Pushover 

---

## Quick start

1. **Create a private GitHub repo** and upload these files.
2. In your repo, go to **Settings → Secrets and variables → Actions → Secrets** and add:
   - `LAT` (e.g., `40.7128` for NYC)
   - `LON` (e.g., `-74.0060` for NYC)
   - `CITY` (for display, e.g., `NYC`)
   - `NOTIFY` = `pushover` 
   - If `NOTIFY=pushover`: add `PUSHOVER_TOKEN` and `PUSHOVER_USER` (from your Pushover app setup)
3. (Optional) Adjust thresholds in `rain.py` (HOURS_AHEAD, THRESHOLD).
4. Commit to `main`. The workflow runs every morning at **7:00 AM ET** (DST-safe) and can be run on-demand via **Actions → Rain nudger → Run workflow**.


---

## How it works

- Pulls the next `HOURS_AHEAD` hours from Open‑Meteo (no API key) for your `LAT/LON` and timezone `America/New_York`.
- Triggers a push if (a) any hour has precipitation probability ≥ `THRESHOLD` **or** (b) any hour’s `weathercode` indicates rain.
- The message includes the peak probability and the time it occurs.

---

## Files

- `rain.py` — main script
- `.github/workflows/rain.yml` — GitHub Actions schedule (DST-aware)
- `requirements.txt` — Python deps (just `requests`)
- `config.env.example` — Example of environment configuration

---

## Customization

Edit constants near the top of `rain.py`:
- `HOURS_AHEAD`: look-ahead window (default 12)
- `THRESHOLD`: minimum precip probability to alert (default 30%)
- `WEEKDAYS_ONLY`: only alert Mon–Fri (default False)
- `INCLUDE_SUMMARY`: include peak-probability summary in the message (default True)

You can also change the emoji/title or message format.

---

## Troubleshooting

- Use **Actions → Rain nudger → Run workflow** (manual) and check logs.
- Set `NOTIFY=stdout` to print instead of pushing while testing.
- Scheduled workflows in GitHub Actions run in **UTC**; this repo uses **two crons** for DST and Standard Time to align with 7:00 AM ET.

