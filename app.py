# app.py · Cool Assistant — Live AQI & 24-hour Temperature
import datetime as dt
import random
import pandas as pd
import altair as alt
import streamlit as st
import folium
from streamlit_folium import st_folium

import dust  # local module we just created

# ───────── LOCATION & CONFIG ─────────
LAT, LON = 36.1912, 44.0094
HOURS_TO_SHOW = 24
st.set_page_config(page_title="Cool Assistant", layout="wide")

# ───── AUTH ─────
from auth import handle_authentication  # your original auth helper
handle_authentication()
user = st.experimental_user
with st.sidebar:
    st.subheader("Account")
    st.write(user.email)
    st.button("Log out", on_click=st.logout, use_container_width=True)

# ───── HEADER ─────
st.title("🏠 Cool Assistant")
st.caption("Live European AQI and 24-hour temperature for the Kurdistan Region.")
st.subheader("💡 Daily Tip")
st.write(random.choice([
    "Ventilate late at night or early morning for coolest air.",
    "Damp cotton curtains help filter dust and cool incoming air.",
    "Weather-strip doors to block hot, dusty air."
]))

# ───────── helpers ─────────
def make_map(lat, lon):
    m = folium.Map(location=[lat, lon], zoom_start=6)
    folium.Marker([lat, lon], tooltip="Kurdistan Region").add_to(m)
    return m


@st.cache_data(ttl=600)
def fetch_temps(lat, lon):
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&hourly=temperature_2m"
        f"&timezone={dust.TIMEZONE}"
    )
    j = st.experimental_requests.get(url).json()
    times = pd.to_datetime(j["hourly"]["time"])
    return pd.DataFrame({"time": times, "temp": j["hourly"]["temperature_2m"]})


# ───────── Tabs ─────────
aq_tab, temp_tab = st.tabs(["🌪️ Air-Quality", "🌞 Temperature"])

# ---------- AIR-QUALITY TAB ----------
with aq_tab:
    st.header("Current AQI & Pollutants")
    st_folium(make_map(LAT, LON), use_container_width=True, height=420, key="map_aq")

    current = dust.fetch_air_quality(LAT, LON)

    st.subheader(f"As of {current['time'].strftime('%H:%M')}")
    aqi_val = current.get("european_aqi")
    aqi_label, aqi_colour = dust.classify(aqi_val, dust.AQI_RULES)
    st.metric("European AQI", f"{aqi_val or '–'}", aqi_label, delta_color="off")
    st.write(f"<div style='height:10px;background:{aqi_colour}'></div>", unsafe_allow_html=True)

    cols = st.columns(3)
    for c, (lbl, key, tbl) in zip(
        cols,
        [("PM2.5 µg/m³", "pm2_5", dust.PM25_RULES),
         ("PM10 µg/m³",  "pm10",  dust.PM10_RULES),
         ("NO₂ µg/m³",   "nitrogen_dioxide", dust.NO2_RULES)],
    ):
        val = current.get(key)
        lab, col = dust.classify(val, tbl)
        with c:
            st.metric(lbl, f"{val:.0f}" if val is not None else "–", lab, delta_color="off")
            st.write(f"<div style='height:6px;background:{col}'></div>", unsafe_allow_html=True)

# ---------- TEMPERATURE TAB ----------
with temp_tab:
    st.header("Next 24-hour Temperature")
    st_folium(make_map(LAT, LON), use_container_width=True, height=420, key="map_temp")

    df = fetch_temps(LAT, LON)
    start = dt.datetime.now().replace(minute=0, second=0, microsecond=0)
    df_24 = df[df["time"].between(start, start + dt.timedelta(hours=HOURS_TO_SHOW))]

    if not df_24.empty:
        line = (
            alt.Chart(df_24)
            .mark_line(point=True)
            .encode(
                x=alt.X("time:T", axis=alt.Axis(title="", format="%H:%M")),
                y=alt.Y("temp:Q", title="°C"),
                tooltip=[alt.Tooltip("time:T", format="%H:%M"), "temp:Q"],
            )
            .properties(height=280, width=680)
        )
        st.altair_chart(line, use_container_width=True)
    else:
        st.info("Temperature data unavailable.")

# ---------- FOOTER ----------
st.markdown("---")
st.caption("© 2025 Cool Assistant · Kurdistan Region")
