# app.py · Cool Assistant — Sidebar Buttons Navigation
import datetime as dt
import random
import requests
import streamlit as st
import pandas as pd
import altair as alt
import folium
from streamlit_folium import st_folium

import dust                                # local module (see dust.py)
from auth import handle_authentication     # your existing auth helper

# ───────── CONFIG ─────────
LAT, LON      = 36.1912, 44.0094
HOURS_FORWARD = 24
st.set_page_config(page_title="Cool Assistant", layout="wide")

# ───────── AUTHENTICATION ─────────
handle_authentication()
user = st.experimental_user

# ───────── SIDEBAR ─────────
with st.sidebar:
    # Logo
    st.image("https://github.com/AIforimpact22/coolassistant/blob/main/input/cool_logo.png?raw=true", width=180)

    # Navigation buttons
    if "page" not in st.session_state:
        st.session_state.page = "home"

    if st.button("🏠 Home"):
        st.session_state.page = "home"
    if st.button("🌞 Temperature"):
        st.session_state.page = "temp"
    if st.button("🌪️ Dust / AQI"):
        st.session_state.page = "dust"

    st.markdown("---")
    st.subheader("Account")
    st.write(user.email)
    st.button("Log out", on_click=st.logout, use_container_width=True)

# ───────── HELPER FUNCTIONS ─────────
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
    j = requests.get(url, timeout=10).json()
    return pd.DataFrame({"time": pd.to_datetime(j["hourly"]["time"]),
                         "temp": j["hourly"]["temperature_2m"]})

# ───────── PAGE ROUTER ─────────
page = st.session_state.page

# ---- HOME PAGE ----
if page == "home":
    st.title("🏠 Cool Assistant — Home")
    st.subheader("💡 Daily Tip")
    st.write(random.choice([
        "Ventilate late at night or early morning for coolest air.",
        "Damp cotton curtains help filter dust and cool incoming air.",
        "Weather-strip doors to block hot, dusty air."
    ]))
    st_folium(make_map(LAT, LON), use_container_width=True, height=500)

# ---- TEMPERATURE PAGE ----
elif page == "temp":
    st.title("🌞 Next 24-hour Temperature")
    st_folium(make_map(LAT, LON), use_container_width=True, height=380)

    df = fetch_temps(LAT, LON)
    start = dt.datetime.now().replace(minute=0, second=0, microsecond=0)
    df_24 = df[df["time"].between(start, start + dt.timedelta(hours=HOURS_FORWARD))]

    if not df_24.empty:
        line = (
            alt.Chart(df_24)
            .mark_line(point=True)
            .encode(
                x=alt.X("time:T", axis=alt.Axis(format="%H:%M", title="")),
                y=alt.Y("temp:Q", title="°C"),
                tooltip=[alt.Tooltip("time:T", format="%H:%M"), "temp:Q"],
            )
            .properties(height=300, width=700)
        )
        st.altair_chart(line, use_container_width=True)
    else:
        st.info("Temperature data unavailable.")

# ---- DUST / AQI PAGE ----
elif page == "dust":
    st.title("🌪️ Current European AQI & Pollutants")
    st_folium(make_map(LAT, LON), use_container_width=True, height=380)

    cur = dust.fetch_air_quality(LAT, LON)

    st.subheader(f"As of {cur['time'].strftime('%H:%M')}")
    aqi_val = cur.get("european_aqi")
    aqi_lab, aqi_col = dust.classify(aqi_val, dust.AQI_RULES)
    st.metric("European AQI", f"{aqi_val or '–'}", aqi_lab, delta_color="off")
    st.write(f"<div style='height:10px;background:{aqi_col}'></div>", unsafe_allow_html=True)

    cols = st.columns(3)
    for c, (label, key, table) in zip(
        cols,
        [
            ("PM2.5 µg/m³", "pm2_5", dust.PM25_RULES),
            ("PM10 µg/m³",  "pm10",  dust.PM10_RULES),
            ("NO₂ µg/m³",   "nitrogen_dioxide", dust.NO2_RULES),
        ],
    ):
        val          = cur.get(key)
        risk, colour = dust.classify(val, table)
        with c:
            st.metric(label, f"{val:.0f}" if val is not None else "–", risk, delta_color="off")
            st.write(f"<div style='height:6px;background:{colour}'></div>", unsafe_allow_html=True)

# ---- FOOTER ----
st.markdown("---")
st.caption("© 2025 Cool Assistant • Kurdistan Region")
