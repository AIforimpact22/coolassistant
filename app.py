# app.py · Cool Assistant — Current AQI & 24-h Temperature (Open-Meteo)
import datetime as dt
import random
import requests
import streamlit as st
import folium
from streamlit_folium import st_folium
from auth import handle_authentication

# ───────── LOCATION & CONFIG ─────────
LATITUDE, LONGITUDE = 36.1912, 44.0094
TIMEZONE            = "auto"
HOURS_TO_SHOW       = 24
st.set_page_config(page_title="Cool Assistant", layout="wide")

# ─────── AUTH & SIDEBAR ───────
handle_authentication()
user = st.experimental_user
with st.sidebar:
    st.subheader("Account")
    st.write(user.email)
    st.button("Log out", on_click=st.logout, use_container_width=True)

# ───────── HEADER ─────────
st.title("🏠 Cool Assistant")
st.caption("Real-time **European AQI** and 24-hour temperature outlook for Kurdistan (Open-Meteo).")
st.subheader("💡 Daily Tip")
st.write(random.choice([
    "Ventilate late-night or early-morning for coolest air.",
    "Damp cotton curtains help filter dust and cool incoming air.",
    "Weather-strip doors to block hot, dusty air."
]))

# ───────── Map helper ─────────
def make_map(lat, lon):
    m = folium.Map(location=[lat, lon], zoom_start=6)
    folium.Marker([lat, lon], tooltip="Kurdistan Region").add_to(m)
    return m

# ───────── API helpers ─────────
def _first(x): return x[0] if isinstance(x, list) else x

@st.cache_data(ttl=300)
def fetch_air(lat, lon):
    url = (
        "https://air-quality-api.open-meteo.com/v1/air-quality"
        f"?latitude={lat}&longitude={lon}"
        "&current=european_aqi,pm10,pm2_5,nitrogen_dioxide"
        f"&timezone={TIMEZONE}"
    )
    j = requests.get(url, timeout=10).json()
    c = j.get("current", {})
    cur = {k: _first(v) for k, v in c.items() if k != "time"}
    cur["time"] = dt.datetime.fromisoformat(_first(c.get("time", dt.datetime.utcnow().isoformat())))
    return cur

@st.cache_data(ttl=600)
def fetch_temps(lat, lon):
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&hourly=temperature_2m"
        f"&timezone={TIMEZONE}"
    )
    j = requests.get(url, timeout=10).json()
    times = [dt.datetime.fromisoformat(t) for t in j["hourly"]["time"]]
    return {"time": times, "temp": j["hourly"]["temperature_2m"]}

# ───────── EU-AQI bucket tables ─────────
AQI_R = [(0,25,"Good","green"),(25,50,"Fair","limegreen"),(50,75,"Moderate","yellow"),
         (75,100,"Poor","orange"),(100,1e9,"Very poor","red")]
PM25_R = [(0,10,"Good","green"),(10,20,"Fair","limegreen"),(20,25,"Moderate","yellow"),
          (25,50,"Poor","orange"),(50,75,"Very poor","red"),(75,800,"Extremely poor","darkred")]
PM10_R = [(0,20,"Good","green"),(20,40,"Fair","limegreen"),(40,50,"Moderate","yellow"),
          (50,100,"Poor","orange"),(100,150,"Very poor","red"),(150,1200,"Extremely poor","darkred")]
NO2_R  = [(0,40,"Good","green"),(40,90,"Fair","limegreen"),(90,120,"Moderate","yellow"),
          (120,230,"Poor","orange"),(230,340,"Very poor","red"),(340,1000,"Extremely poor","darkred")]

def bucket(val, table):
    for lo, hi, lab, col in table:
        if val is not None and lo <= val < hi:
            return lab, col
    return "No data", "grey"

# ───────── Tabs ─────────
aq_tab, temp_tab = st.tabs(["🌪️ Air-Quality", "🌞 Temperature"])

# ─────── AIR-QUALITY TAB ───────
with aq_tab:
    st.header("🌪️ Current European AQI & Pollutants")
    st_folium(make_map(LATITUDE, LONGITUDE), use_container_width=True, height=420, key="map_aq")

    cur = fetch_air(LATITUDE, LONGITUDE)

    # Current AQI panel
    st.subheader(f"Current — {cur['time'].strftime('%H:%M')}")
    aqi_val = cur.get("european_aqi")
    aqi_lab, aqi_col = bucket(aqi_val, AQI_R)
    st.metric("European AQI", f"{aqi_val or '–'}", aqi_lab, delta_color="off")
    st.write(f"<div style='height:10px;background:{aqi_col}'></div>", unsafe_allow_html=True)

    # Current pollutants
    cols = st.columns(3)
    for c, (lbl, key, tbl) in zip(
        cols,
        [("PM2.5 µg/m³","pm2_5",PM25_R),
         ("PM10 µg/m³","pm10",PM10_R),
         ("NO₂ µg/m³","nitrogen_dioxide",NO2_R)]
    ):
        val = cur.get(key)
        lab, col = bucket(val, tbl)
        with c:
            st.metric(lbl, f"{val:.0f}" if val is not None else "–", lab, delta_color="off")
            st.write(f"<div style='height:6px;background:{col}'></div>", unsafe_allow_html=True)

# ─────── TEMPERATURE TAB ───────
with temp_tab:
    st.header("🌞 Temperature — Next 24 h")
    st_folium(make_map(LATITUDE, LONGITUDE), use_container_width=True, height=420, key="map_temp")

    tdata = fetch_temps(LATITUDE, LONGITUDE)
    now = dt.datetime.now().replace(minute=0, second=0, microsecond=0)
    next_24 = [(t, v) for t, v in zip(tdata["time"], tdata["temp"])
               if now <= t < now + dt.timedelta(hours=HOURS_TO_SHOW)]

    st.subheader("Hourly outlook (°C)")
    cols = st.columns(4)
    for i, (t, v) in enumerate(next_24):
        with cols[i % 4]:
            st.write(f"{t.strftime('%H:%M')}: **{v:.1f}°C**")

# ─────── FOOTER ───────
st.markdown("---")
st.caption("© 2025 Cool Assistant • Kurdistan Region")
