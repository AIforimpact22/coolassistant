# app.py · Cool Assistant — Sidebar Navigation (Home • Temperature • Dust)
import datetime as dt
import random
import requests
import streamlit as st
import pandas as pd
import altair as alt
import folium
from streamlit_folium import st_folium

import dust                      # local helper module for air-quality
from auth import handle_authentication

# ───────── GLOBALS ─────────
LAT, LON      = 36.1912, 44.0094
HOURS_FORWARD = 24
st.set_page_config(page_title="Cool Assistant", layout="wide")

# ───────── AUTH ─────────
handle_authentication()
user = st.experimental_user

# ───────── SIDEBAR: NAV & PROFILE ─────────
st.sidebar.image("https://raw.githubusercontent.com/Hakari-Bibani/photo/refs/heads/main/logo/hasar1.png", width=180)
page = st.sidebar.radio("Navigate", ["🏠 Home", "🌞 Temperature", "🌪️ Dust / AQI"])
st.sidebar.markdown("---")
st.sidebar.subheader("Account")
st.sidebar.write(user.email)
st.sidebar.button("Log out", on_click=st.logout, use_container_width=True)

# ───────── SHARED HELPERS ─────────
def make_map(lat, lon):
    m = folium.Map(location=[lat, lon], zoom_start=6)
    folium.Marker([lat, lon], tooltip="Kurdistan Region").add_to(m)
    return m

@st.cache_data(ttl=600)
def fetch_temps(lat, lon):
    url = ( "https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            "&hourly=temperature_2m"
            f"&timezone={dust.TIMEZONE}" )
    j = requests.get(url, timeout=10).json()
    return pd.DataFrame({"time": pd.to_datetime(j["hourly"]["time"]),
                         "temp": j["hourly"]["temperature_2m"]})

# ───────── PAGE: HOME ─────────
if page == "🏠 Home":
    st.title("🏠 Cool Assistant")
    st.caption("Helping Kurdistan households stay cool and safe from dust & heat.")
    st.subheader("💡 Daily Tip")
    st.write(random.choice([
        "Ventilate late-night or early-morning when outdoor air is coolest.",
        "Hang damp cotton curtains — they cool and pre-filter dust.",
        "Seal door gaps with weather-stripping to block hot, dusty air."
    ]))
    st_folium(make_map(LAT, LON), use_container_width=True, height=500, key="home_map")

# ───────── PAGE: TEMPERATURE ─────────
elif page == "🌞 Temperature":
    st.title("🌞 Next 24-Hour Temperature")
    st_folium(make_map(LAT, LON), use_container_width=True, height=420, key="temp_map")

    df = fetch_temps(LAT, LON)
    now = dt.datetime.now().replace(minute=0, second=0, microsecond=0)
    df_24 = df[df["time"].between(now, now + dt.timedelta(hours=HOURS_FORWARD))]

    if df_24.empty:
        st.info("Temperature data unavailable.")
    else:
        line = (alt.Chart(df_24)
                  .mark_line(point=True)
                  .encode(x=alt.X("time:T", axis=alt.Axis(format="%H:%M", title="")),
                          y=alt.Y("temp:Q", title="°C"),
                          tooltip=[alt.Tooltip("time:T", format="%H:%M"), "temp"])
                  .properties(height=300, width=700))
        st.altair_chart(line, use_container_width=True)

# ───────── PAGE: DUST / AQI ─────────
else:
    st.title("🌪️ Current European AQI & Pollutants")
    st_folium(make_map(LAT, LON), use_container_width=True, height=420, key="aq_map")

    cur = dust.fetch_air_quality(LAT, LON)
    st.subheader(f"As of {cur['time'].strftime('%H:%M')}")
    aqi_val   = cur.get("european_aqi")
    aqi_label, aqi_col = dust.classify(aqi_val, dust.AQI_RULES)
    st.metric("European AQI", f"{aqi_val or '–'}", aqi_label, delta_color="off")
    st.write(f"<div style='height:10px;background:{aqi_col}'></div>", unsafe_allow_html=True)

    cols = st.columns(3)
    for col, (label, key, table) in zip(
        cols,
        [("PM2.5 µg/m³", "pm2_5", dust.PM25_RULES),
         ("PM10 µg/m³",  "pm10",  dust.PM10_RULES),
         ("NO₂ µg/m³",   "nitrogen_dioxide", dust.NO2_RULES)]
    ):
        val = cur.get(key)
        lab, clr = dust.classify(val, table)
        with col:
            st.metric(label, f"{val:.0f}" if val is not None else "–", lab, delta_color="off")
            st.write(f"<div style='height:6px;background:{clr}'></div>", unsafe_allow_html=True)

# ───────── FOOTER ─────────
st.markdown("---")
st.caption("© 2025  Cool Assistant  |  Kurdistan Region")
