# app.py · Cool Assistant – Heat-Wave & Dust-Storm Helper
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

# ◼️ OpenWeather key – look in secrets first, then env
OWM_API_KEY = (
    st.secrets.get("OWM_API_KEY")
    if "OWM_API_KEY" in st.secrets
    else os.getenv("OWM_API_KEY")
)
if not OWM_API_KEY:
    st.stop()  # hard-fail early so you don’t burn calls with an empty key

# Kurdistan centre coords
CENTER_LAT, CENTER_LON = 36.206, 44.009

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
    m = folium.Map(location=[CENTER_LAT, CENTER_LON], zoom_start=6)
    folium.TileLayer(
        tiles=(
            f"https://tile.openweathermap.org/map/{layer_code}/{{z}}/{{x}}/{{y}}.png"
            f"?appid={OWM_API_KEY}"
        ),
        attr="OpenWeatherMap",
        name=layer_code,
        overlay=True,
        control=True,
        opacity=opacity,
    ).add_to(m)

    folium.LayerControl().add_to(m)
    return m


# ── API FETCH HELPERS (cached) ────────────────────────────
@st.cache_data(ttl=600)  # cache for 10 min
def fetch_pm10_daily_max(lat: float, lon: float):
    url = (
        "https://api.openweathermap.org/data/2.5/air_pollution/forecast?"
        f"lat={lat}&lon={lon}&appid={OWM_API_KEY}"
    )
    r = requests.get(url, timeout=8)
    if r.status_code != 200:
        raise RuntimeError(f"{r.status_code}: {r.json().get('message','')}")
    data = r.json()
    daily_max = {}
    for item in data["list"]:
        day = dt.datetime.utcfromtimestamp(item["dt"]).date()
        pm10 = item["components"]["pm10"]
        daily_max[day] = max(pm10, daily_max.get(day, -1))
    return daily_max


@st.cache_data(ttl=600)
def fetch_daily_highs(lat: float, lon: float):
    url = (
        "https://api.openweathermap.org/data/2.5/forecast?"
        f"lat={lat}&lon={lon}&appid={OWM_API_KEY}&units=metric"
    )
    r = requests.get(url, timeout=8)
    if r.status_code != 200:
        raise RuntimeError(f"{r.status_code}: {r.json().get('message','')}")
    raw = r.json()
    highs = {}
    for i in raw["list"]:
        day = dt.datetime.fromtimestamp(i["dt"]).date()
        highs[day] = max(highs.get(day, -273), i["main"]["temp_max"])
    return highs


# ─────────────────── DUST-STORM TAB ───────────────────────
with dust_tab:
    st.header("🌪️ Dust-Storm Risk – Next 4 Days")

    st.markdown("##### Wind layer (higher winds ⇒ higher blowing-dust risk)")
    st_folium(build_folium("wind_new"), use_container_width=True, height=480)

    with st.spinner("Loading PM10 forecast…"):
        try:
            pm10 = fetch_pm10_daily_max(CENTER_LAT, CENTER_LON)
            for day, value in list(pm10.items())[:4]:
                risk = (
                    "🔴 Very High" if value >= 300
                    else "🟠 High" if value >= 200
                    else "🟡 Moderate" if value >= 100
                    else "🟢 Low"
                )
                st.metric(day.strftime("%A %d %b"), f"{value:.0f} µg/m³", risk)
        except Exception as e:
            st.error(f"PM10 fetch failed → {e}")


# ─────────────────── HEAT-WAVE TAB ────────────────────────
with heat_tab:
    st.header("🌞 Heat-Wave Outlook – Next 5 Days")

    st.markdown("##### Temperature layer (°C)")
    st_folium(build_folium("temp_new"), use_container_width=True, height=480)

    with st.spinner("Loading 5-day forecast…"):
        try:
            highs = fetch_daily_highs(CENTER_LAT, CENTER_LON)
            thresholds = {"Heat-Wave": 43, "Warning": 38}
            for day, tmax in list(highs.items())[:5]:
                status = (
                    "🔥 Heat-Wave" if tmax >= thresholds["Heat-Wave"]
                    else "⚠️ Hot" if tmax >= thresholds["Warning"]
                    else "🙂 Warm"
                )
                st.metric(day.strftime("%A %d %b"), f"{tmax:.1f} °C", status)
        except Exception as e:
            st.error(f"Forecast fetch failed → {e}")


# ───────────────────────── FOOTER ─────────────────────────
st.markdown("---")
st.caption("© 2025 Cool Assistant • Kurdistan Region")
