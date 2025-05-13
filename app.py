# app.py  ·  Cool Assistant – Heat-Wave & Dust-Storm Helper
import os
import datetime as dt
import random
import requests
import streamlit as st
import folium
from streamlit_folium import st_folium
from auth import handle_authentication


# ───────────────────────── CONFIG ─────────────────────────
st.set_page_config(page_title="Cool Assistant", layout="wide")

# ◼️ OpenWeather key – keep it secret in prod!
OWM_API_KEY = os.getenv("OWM_API_KEY") or "b06517965860a77b4a73885dad3915d1"
LOCATION_NAME = "Erbil,IQ"
CENTER_LAT, CENTER_LON = 36.206, 44.009       # Kurdistan centre

# ─────────────────────── AUTH & SIDEBAR ───────────────────
handle_authentication()
user = st.experimental_user

with st.sidebar:
    st.subheader("Account")
    st.write(user.email)
    st.button("Log out", on_click=st.logout, use_container_width=True)

# ───────────────────────── HEADER ─────────────────────────
st.title("🏠 Cool Assistant")
st.caption(
    "Your assistant for **mitigating heat waves and dust storms** across the Kurdistan Region."
)

# ─────────────────────── DAILY TIP ────────────────────────
st.subheader("💡 Daily Tip")
st.write(
    random.choice(
        [
            "Close windows during the midday heat; ventilate late-night / early-morning.",
            "Hang damp cotton curtains—they pre-filter dust and cool incoming air.",
            "Add weather-stripping to doors to keep hot, dusty air outside.",
        ]
    )
)

# ────────────────────────── TABS ──────────────────────────
dust_tab, heat_tab = st.tabs(["🌪️ Dust-Storm Forecast", "🌞 Heat-Wave Forecast"])


# ── HELPER: build a Folium map with an OpenWeather tile ──
def build_folium(layer_code: str, opacity: float = 0.6) -> folium.Map:
    """
    layer_code examples (Weather Maps 1.0):
        - 'wind_new'  (wind speed & direction)
        - 'temp_new'  (air temperature)
    """
    m = folium.Map(location=[CENTER_LAT, CENTER_LON], zoom_start=6)
    folium.TileLayer(
        tiles=f"https://tile.openweathermap.org/map/{layer_code}/{{z}}/{{x}}/{{y}}.png?appid={OWM_API_KEY}",
        attr="OpenWeatherMap",
        name=layer_code,
        overlay=True,
        control=True,
        opacity=opacity,
    ).add_to(m)

    folium.LayerControl().add_to(m)
    return m


# ─────────────────── DUST-STORM TAB ───────────────────────
with dust_tab:
    st.header("🌪️ Dust-Storm Risk – Next 4 Days")

    # A. Dust-proxy map (wind layer)
    st.markdown("##### Wind layer (higher winds ⇒ higher blowing-dust risk)")
    st_folium(build_folium("wind_new"), use_container_width=True, height=500)

    # B. PM10 / AQI forecast for Erbil (OpenWeather Air-Pollution API)
    def fetch_pm10_daily_max(lat: float, lon: float):
        url = (
            f"https://api.openweathermap.org/data/2.5/air_pollution/forecast?"
            f"lat={lat}&lon={lon}&appid={OWM_API_KEY}"
        )
        data = requests.get(url, timeout=8).json()
        daily_max = {}
        for item in data["list"]:
            day = dt.datetime.utcfromtimestamp(item["dt"]).date()
            pm10 = item["components"]["pm10"]
            daily_max[day] = max(pm10, daily_max.get(day, -1))
        return daily_max

    try:
        pm10 = fetch_pm10_daily_max(CENTER_LAT, CENTER_LON)
        for day, value in list(pm10.items())[:4]:  # only next 4 days
            risk = (
                "🔴 Very High" if value >= 300
                else "🟠 High" if value >= 200
                else "🟡 Moderate" if value >= 100
                else "🟢 Low"
            )
            st.metric(day.strftime("%A %d %b"), f"{value:.0f} µg/m³", risk)
    except Exception:
        st.warning("Could not load PM10 forecast – check API quota.")


# ─────────────────── HEAT-WAVE TAB ────────────────────────
with heat_tab:
    st.header("🌞 Heat-Wave Outlook – Next 5 Days")

    # A. Temperature map layer
    st.markdown("##### Temperature layer (°C)")
    st_folium(build_folium("temp_new"), use_container_width=True, height=500)

    # B. Daily-high extraction
    def fetch_daily_highs(city: str):
        url = (
            "https://api.openweathermap.org/data/2.5/forecast?"
            f"q={city}&appid={OWM_API_KEY}&units=metric"
        )
        raw = requests.get(url, timeout=8).json()
        highs = {}
        for i in raw["list"]:
            day = dt.datetime.fromtimestamp(i["dt"]).date()
            highs[day] = max(highs.get(day, -273), i["main"]["temp_max"])
        return highs

    try:
        highs = fetch_daily_highs(LOCATION_NAME)
        thresholds = {"Heat-Wave": 43, "Warning": 38}
        for day, tmax in list(highs.items())[:5]:
            status = (
                "🔥 Heat-Wave" if tmax >= thresholds["Heat-Wave"]
                else "⚠️ Hot" if tmax >= thresholds["Warning"]
                else "🙂 Warm"
            )
            st.metric(day.strftime("%A %d %b"), f"{tmax:.1f} °C", status)
    except Exception:
        st.warning("Could not load 5-day forecast – check API key or quota.")


# ───────────────────────── FOOTER ─────────────────────────
st.markdown("---")
st.caption("© 2025 Cool Assistant • Kurdistan Region")
