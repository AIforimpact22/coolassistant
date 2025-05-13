# app.py · Cool Assistant – Heat-Wave & Dust-Storm Helper  (OPEN-METEO version)
import datetime as dt
import random
import requests
import streamlit as st
import folium
from streamlit_folium import st_folium
from auth import handle_authentication


# ───────── CONFIG ─────────
st.set_page_config(page_title="Cool Assistant", layout="wide")
CENTER_LAT, CENTER_LON = 36.206, 44.009        # Kurdistan Region centre


# ─────── AUTH & SIDEBAR ───────
handle_authentication()
user = st.experimental_user

with st.sidebar:
    st.subheader("Account")
    st.write(user.email)
    st.button("Log out", on_click=st.logout, use_container_width=True)


# ───────── HEADER ─────────
st.title("🏠 Cool Assistant")
st.caption(
    "Your assistant for **mitigating heat-waves and dust-storms** across the Kurdistan Region."
)

st.subheader("💡 Daily Tip")
st.write(
    random.choice(
        [
            "Close windows during the midday heat; ventilate late-night / early-morning.",
            "Hang damp cotton curtains – they pre-filter dust and cool incoming air.",
            "Add weather-stripping to doors to keep hot, dusty air outside.",
        ]
    )
)

# ───────── TABS ─────────
dust_tab, heat_tab = st.tabs(["🌪️ Dust-Storm Forecast", "🌞 Heat-Wave Forecast"])


# ─────── Folium helper ───────
def build_folium(lat: float, lon: float) -> folium.Map:
    """Return a simple OpenStreetMap-only map centred on (lat, lon)."""
    m = folium.Map(location=[lat, lon], zoom_start=6)
    folium.Marker([lat, lon], tooltip="Kurdistan Region").add_to(m)
    return m


# ─────── Cached fetch helpers (Open-Meteo) ───────
@st.cache_data(ttl=600)
def fetch_pm10_daily_max(lat: float, lon: float) -> dict:
    """Return {date → daily max PM10 µg/m³} for the next 4 days."""
    url = (
        "https://air-quality-api.open-meteo.com/v1/air-quality"
        f"?latitude={lat}&longitude={lon}"
        "&hourly=pm10&timezone=auto"
    )
    data = requests.get(url, timeout=10).json()
    times  = data["hourly"]["time"]
    values = data["hourly"]["pm10"]

    daily = {}
    for ts, val in zip(times, values):
        day = dt.datetime.fromisoformat(ts).date()
        daily[day] = max(val, daily.get(day, -1))
    return daily


@st.cache_data(ttl=600)
def fetch_daily_highs(lat: float, lon: float) -> dict:
    """Return {date → daily max °C} for the next 5 days."""
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&daily=temperature_2m_max"
        "&timezone=auto"
    )
    data = requests.get(url, timeout=10).json()
    dates = [dt.date.fromisoformat(d) for d in data["daily"]["time"]]
    temps = data["daily"]["temperature_2m_max"]
    return dict(zip(dates, temps))


# ─────── DUST-STORM TAB ───────
with dust_tab:
    st.header("🌪️ Dust-Storm Risk – Next 4 Days")
    st.markdown("##### Map view")
    st_folium(build_folium(CENTER_LAT, CENTER_LON), use_container_width=True, height=480)

    with st.spinner("Loading dust forecast…"):
        try:
            pm10 = fetch_pm10_daily_max(CENTER_LAT, CENTER_LON)
            for day, value in list(pm10.items())[:4]:
                risk = (
                    "🔴 Very High" if value >= 300
                    else "🟠 High" if value >= 200
                    else "🟡 Moderate" if value >= 100
                    else "🟢 Low"
                )
                st.metric(day.strftime("%a %d %b"), f"{value:.0f} µg/m³", risk)
        except Exception as e:
            st.error(f"Dust forecast failed → {e}")


# ─────── HEAT-WAVE TAB ───────
with heat_tab:
    st.header("🌞 Heat-Wave Outlook – Next 5 Days")
    st.markdown("##### Map view")
    st_folium(build_folium(CENTER_LAT, CENTER_LON), use_container_width=True, height=480)

    with st.spinner("Loading temperature forecast…"):
        try:
            highs = fetch_daily_highs(CENTER_LAT, CENTER_LON)
            thresholds = {"Heat-Wave": 43, "Warning": 38}
            for day, tmax in list(highs.items())[:5]:
                status = (
                    "🔥 Heat-Wave" if tmax >= thresholds["Heat-Wave"]
                    else "⚠️ Hot"  if tmax >= thresholds["Warning"]
                    else "🙂 Warm"
                )
                st.metric(day.strftime("%a %d %b"), f"{tmax:.1f} °C", status)
        except Exception as e:
            st.error(f"Temperature forecast failed → {e}")


# ─────── FOOTER ───────
st.markdown("---")
st.caption("© 2025 Cool Assistant • Kurdistan Region")
