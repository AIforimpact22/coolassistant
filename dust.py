"""
dust.py
========
Utility module for Cool Assistant.

• Fetches current European AQI and key pollutants from Open-Meteo  
• Provides risk-bucket tables + helper to classify a value (label + colour)
"""

from __future__ import annotations
import datetime as dt
import requests

TIMEZONE = "auto"

# --- exact EU-AQI ranges ------------------------------------------------------
AQI_RULES = [
    (0, 25, "Good", "green"),
    (25, 50, "Fair", "limegreen"),
    (50, 75, "Moderate", "yellow"),
    (75, 100, "Poor", "orange"),
    (100, 1e9, "Very poor", "red"),
]
PM25_RULES = [
    (0, 10, "Good", "green"),
    (10, 20, "Fair", "limegreen"),
    (20, 25, "Moderate", "yellow"),
    (25, 50, "Poor", "orange"),
    (50, 75, "Very poor", "red"),
    (75, 800, "Extremely poor", "darkred"),
]
PM10_RULES = [
    (0, 20, "Good", "green"),
    (20, 40, "Fair", "limegreen"),
    (40, 50, "Moderate", "yellow"),
    (50, 100, "Poor", "orange"),
    (100, 150, "Very poor", "red"),
    (150, 1200, "Extremely poor", "darkred"),
]
NO2_RULES = [
    (0, 40, "Good", "green"),
    (40, 90, "Fair", "limegreen"),
    (90, 120, "Moderate", "yellow"),
    (120, 230, "Poor", "orange"),
    (230, 340, "Very poor", "red"),
    (340, 1000, "Extremely poor", "darkred"),
]


# -----------------------------------------------------------------------------


def _first(x):
    """Return first element if it's a list; else return x."""
    return x[0] if isinstance(x, list) else x


def fetch_air_quality(lat: float, lon: float) -> dict:
    """
    Return a dict with keys:
        time, european_aqi, pm2_5, pm10, nitrogen_dioxide
    """
    url = (
        "https://air-quality-api.open-meteo.com/v1/air-quality"
        f"?latitude={lat}&longitude={lon}"
        "&current=european_aqi,pm10,pm2_5,nitrogen_dioxide"
        f"&timezone={TIMEZONE}"
    )
    data = requests.get(url, timeout=10).json().get("current", {})

    # flatten lists → scalar
    out = {k: _first(v) for k, v in data.items() if k != "time"}
    out["time"] = dt.datetime.fromisoformat(
        _first(data.get("time", dt.datetime.utcnow().isoformat()))
    )
    return out


def classify(value: float | None, table: list[tuple]) -> tuple[str, str]:
    """
    Map a numeric value into (label, colour) using `table`.
    If value is None, returns ("No data", "grey").
    """
    for low, high, label, colour in table:
        if value is not None and low <= value < high:
            return label, colour
    return "No data", "grey"
