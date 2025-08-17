#!/usr/bin/env python3
import os, sys, requests, datetime as dt
from typing import List, Tuple

# ===== User-tweakable defaults =====
HOURS_AHEAD = int(os.environ.get("HOURS_AHEAD", "12"))
THRESHOLD = int(os.environ.get("THRESHOLD", "30"))  # percent precip prob
TIMEZONE = os.environ.get("TIMEZONE", "America/New_York")
CITY = os.environ.get("CITY", "Your City")
WEEKDAYS_ONLY = os.environ.get("WEEKDAYS_ONLY", "false").lower() == "true"
INCLUDE_SUMMARY = os.environ.get("INCLUDE_SUMMARY", "true").lower() == "true"

# Notification target: pushover | telegram | stdout
NOTIFY = os.environ.get("NOTIFY", "stdout").lower()

# Lat/Lon (required for live runs)
def get_float(name: str, default: float) -> float:
    v = os.environ.get(name, None)
    if v is None:
        return default
    try:
        return float(v)
    except ValueError:
        return default

# TODO: get these based on device location
LAT = get_float("LAT", 40.7128)
LON = get_float("LON", -74.0060)

# ===== Weathercode sets =====
RAIN_CODES = {51,53,55,56,57,61,63,65,66,67,80,81,82,95,96,99}  # Open-Meteo WMO codes considered "rainy"

def fetch_open_meteo(lat: float, lon: float, timezone: str):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "precipitation_probability,weathercode",
        "timezone": timezone
    }
    r = requests.get(url, params=params, timeout=20)
    r.raise_for_status()
    return r.json()

def analyze_rain(wx: dict, hours_ahead: int) -> Tuple[bool, str]:
    hourly = wx.get("hourly", {})
    times = hourly.get("time", [])[:hours_ahead]
    probs = hourly.get("precipitation_probability", [])[:hours_ahead]
    codes = hourly.get("weathercode", [])[:hours_ahead]

    will_rain = False
    peak_prob = -1
    peak_time = None

    for t, p, c in zip(times, probs, codes):
        # normalize None values
        p = 0 if p is None else p
        if c in RAIN_CODES or (isinstance(p, (int, float)) and p >= THRESHOLD):
            will_rain = True
        if isinstance(p, (int, float)) and p > peak_prob:
            peak_prob = p
            peak_time = t

    summary = ""
    if INCLUDE_SUMMARY and peak_prob >= 0 and peak_time:
        # peak_time is local time string thanks to timezone param
        # Format HH:MM from ISO string
        try:
            hhmm = peak_time.split("T")[1][:5]
        except Exception:
            hhmm = peak_time
        summary = f" Peak precip probability {peak_prob}% around {hhmm}."

    return will_rain, summary

def notify_pushover(msg: str):
    token = os.environ.get("PUSHOVER_TOKEN")
    user = os.environ.get("PUSHOVER_USER")
    if not token or not user:
        print("Pushover missing PUSHOVER_TOKEN or PUSHOVER_USER; falling back to stdout.")
        print(msg)
        return
    requests.post("https://api.pushover.net/1/messages.json", data={
        "token": token,
        "user": user,
        "message": msg,
        "title": "Rain Check",
        "priority": 0,
    }, timeout=20)


def maybe_notify(msg: str):
    if NOTIFY == "pushover":
        notify_pushover(msg)
    else:
        print(msg)

def main():
    # Optional: weekday gating
    if WEEKDAYS_ONLY:
        # America/New_York local weekday check by offset from UTC is messy inside Actions;
        # we'll just compute local weekday using the API's local times (first hour's date).
        pass

    try:
        wx = fetch_open_meteo(LAT, LON, TIMEZONE)
    except Exception as e:
        print("Failed to fetch weather:", e)
        sys.exit(0)  # Don't fail the workflow hard

    will_rain, summary = analyze_rain(wx, HOURS_AHEAD)

    if will_rain:
        msg = f"🌧️ Rain likely in the next {HOURS_AHEAD}h in {CITY}.{summary}"
        maybe_notify(msg)
    else:
        # Optional: say nothing on clear days. For visibility during testing, print a line.
        print(f"No rain expected next {HOURS_AHEAD}h in {CITY}.")

if __name__ == "__main__":
    main()
