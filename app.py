# app.py · Cool Assistant – Hourly Temperature & Multi-Pollutant Forecast (Open-Meteo)
import datetime as dt
import random
import requests
import streamlit as st
import folium
import pandas as pd
import altair as alt
from streamlit_folium import st_folium
from auth import handle_authentication

# ───────── CONFIG ─────────
st.set_page_config(page_title="Cool Assistant", layout="wide")
CENTER_LAT, CENTER_LON = 36.206, 44.009        # Kurdistan Region centre
TIMEZONE = "auto"
HOURS_TO_SHOW = 24

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
    "Hourly **heat** & **dust** outlook for the Kurdistan Region, powered by free Open-Meteo APIs."
)
st.subheader("💡 Daily Tip")
st.write(
    random.choice(
        [
            "Ventilate late at night or early morning when outside air is coolest.",
            "Hang damp cotton curtains – they filter dust and cool incoming air.",
            "Add weather-stripping to doors to keep hot, dusty air outside.",
        ]
    )
)

# ───────── Folium helper ─────────
def build_map(lat: float, lon: float) -> folium.Map:
    m = folium.Map(location=[lat, lon], zoom_start=6)
    folium.Marker([lat, lon], tooltip="Kurdistan Region").add_to(m)
    return m

# ───────── Data fetchers ─────────
@st.cache_data(ttl=600)
def get_air_quality(lat: float, lon: float) -> dict:
    url = (
        "https://air-quality-api.open-meteo.com/v1/air-quality"
        f"?latitude={lat}&longitude={lon}"
        "&hourly=pm10,pm2_5,uv_index"
        f"&timezone={TIMEZONE}"
    )
    j = requests.get(url, timeout=10).json()
    times = [dt.datetime.fromisoformat(t) for t in j["hourly"]["time"]]
    return {
        "pm10": j["hourly"]["pm10"],
        "pm2_5": j["hourly"]["pm2_5"],
        "uv": j["hourly"]["uv_index"],
        "time": times,
    }

@st.cache_data(ttl=600)
def get_hourly_temps(lat: float, lon: float) -> dict:
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&hourly=temperature_2m"
        f"&timezone={TIMEZONE}"
    )
    j = requests.get(url, timeout=10).json()
    times = [dt.datetime.fromisoformat(t) for t in j["hourly"]["time"]]
    return {"time": times, "temp": j["hourly"]["temperature_2m"]}

# ───────── Bucket rules & helper for charts ─────────
PM10_RULES = [
    (0, 100, "Low", "green"),
    (100, 200, "Moderate", "gold"),
    (200, 300, "High", "orange"),
    (300, 1e9, "Very High", "red"),
]
PM25_RULES = [
    (0, 55, "L", "green"),
    (55, 90, "M", "gold"),
    (90, 150, "H", "orange"),
    (150, 1e9, "VH", "red"),
]

def classify(v, rules):
    for low, high, label, colour in rules:
        if low <= v < high:
            return label, colour
    return "?", "grey"

def bar_chart(df, title, vmax, rules):
    df = df.copy()
    df["bucket"], df["colour"] = zip(*df["value"].map(lambda v: classify(v, rules)))
    return (
        alt.Chart(df)
        .mark_bar(height=22)
        .encode(
            y=alt.Y("day:N", title=""),
            x=alt.X("value:Q", title=title, scale=alt.Scale(domain=[0, vmax])),
            color=alt.Color("colour:N", scale=None, legend=None),
            tooltip=["day:N", "value:Q", "bucket:N"],
        )
        .properties(width=360)
    )

# ───────── UI TABS ─────────
dust_tab, heat_tab = st.tabs(["🌪️ Dust / Air-Quality", "🌞 Temperature"])

# ─────── DUST / AIR-QUALITY TAB ───────
with dust_tab:
    st.header("🌪️ Dust & Air-Quality – next 4 days")
    st_folium(build_map(CENTER_LAT, CENTER_LON), use_container_width=True, height=420, key="dust_map")

    aq = get_air_quality(CENTER_LAT, CENTER_LON)

    # Aggregate daily maxima
    pm10_daily, pm25_daily, uv_daily = {}, {}, {}
    for t, v10, v25, uv in zip(aq["time"], aq["pm10"], aq["pm2_5"], aq["uv"]):
        d = t.date()
        pm10_daily[d] = max(v10, pm10_daily.get(d, -1))
        pm25_daily[d] = max(v25, pm25_daily.get(d, -1))
        uv_daily[d] = max(uv, uv_daily.get(d, -1))

    # Build DataFrames for charts
    pm10_df = pd.DataFrame(
        {"day": [d.strftime("%a %d %b") for d in list(pm10_daily)[:4]],
         "value": list(pm10_daily.values())[:4]}
    )
    pm25_df = pd.DataFrame(
        {"day": [d.strftime("%a %d %b") for d in list(pm25_daily)[:4]],
         "value": list(pm25_daily.values())[:4]}
    )

    st.subheader("PM10 (µg/m³)")
    st.altair_chart(bar_chart(pm10_df, "PM10", 350, PM10_RULES), use_container_width=True)

    st.subheader("PM2.5 (µg/m³)")
    st.altair_chart(bar_chart(pm25_df, "PM2.5", 200, PM25_RULES), use_container_width=True)

    today = dt.date.today()
    if (uv_val := uv_daily.get(today)) is not None:
        st.info(f"**Today’s peak UV index:** {uv_val:.1f}")

# ─────── TEMPERATURE TAB ───────
with heat_tab:
    st.header("🌞 Upcoming 24-hour Temperature")
    st_folium(build_map(CENTER_LAT, CENTER_LON), use_container_width=True, height=420, key="temp_map")

    data = get_hourly_temps(CENTER_LAT, CENTER_LON)
    now = dt.datetime.now().replace(minute=0, second=0, microsecond=0)
    next_24 = [
        (t, temp)
        for t, temp in zip(data["time"], data["temp"])
        if now <= t < now + dt.timedelta(hours=HOURS_TO_SHOW)
    ]

    st.subheader("Hourly outlook (°C)")
    cols = st.columns(4)
    for i, (t, temp) in enumerate(next_24):
        with cols[i % 4]:
            st.write(f"{t.strftime('%H:%M')}: **{temp:.1f} °C**")

# ─────── FOOTER ───────
st.markdown("---")
st.caption("© 2025 Cool Assistant • Kurdistan Region")
