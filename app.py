# app.py · Cool Assistant – Multi-Pollutant & Temperature (Open-Meteo)
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
CENTER_LAT, CENTER_LON = 36.1912, 44.0094      # updated lat/lon (Erbil)
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
    "24-hour **heat** & multi-pollutant air-quality outlook for the Kurdistan Region "
    "(data from Open-Meteo)."
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
def build_map(lat, lon):
    m = folium.Map(location=[lat, lon], zoom_start=6)
    folium.Marker([lat, lon], tooltip="Kurdistan Region").add_to(m)
    return m

# ───────── Data fetchers ─────────
@st.cache_data(ttl=900)
def get_air_quality(lat, lon):
    url = (
        "https://air-quality-api.open-meteo.com/v1/air-quality"
        f"?latitude={lat}&longitude={lon}"
        "&hourly=pm10,pm2_5,nitrogen_dioxide,sulphur_dioxide"
        ",aerosol_optical_depth,dust,ammonia,methane"
        "&past_days=5"
        f"&timezone={TIMEZONE}"
    )
    j = requests.get(url, timeout=10).json()
    t = [dt.datetime.fromisoformat(x) for x in j["hourly"]["time"]]
    return {
        "time": t,
        "pm10": j["hourly"]["pm10"],
        "pm2_5": j["hourly"]["pm2_5"],
        "no2": j["hourly"]["nitrogen_dioxide"],
        "so2": j["hourly"]["sulphur_dioxide"],
    }

@st.cache_data(ttl=600)
def get_hourly_temps(lat, lon):
    url = (
        "https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        "&hourly=temperature_2m"
        f"&timezone={TIMEZONE}"
    )
    j = requests.get(url, timeout=10).json()
    times = [dt.datetime.fromisoformat(t) for t in j["hourly"]["time"]]
    return {"time": times, "temp": j["hourly"]["temperature_2m"]}

# ───────── EU-AQI bucket rules ─────────
def buckets(ranges):
    return [(lo, hi, lab, col) for (lo, hi, lab, col) in ranges]

PM25_RULES = buckets([
    (0, 10,   "Good",            "green"),
    (10, 20,  "Fair",            "limegreen"),
    (20, 25,  "Moderate",        "yellow"),
    (25, 50,  "Poor",            "orange"),
    (50, 75,  "Very poor",       "red"),
    (75, 800, "Extremely poor",  "darkred"),
])
PM10_RULES = buckets([
    (0, 20,   "Good",            "green"),
    (20, 40,  "Fair",            "limegreen"),
    (40, 50,  "Moderate",        "yellow"),
    (50, 100, "Poor",            "orange"),
    (100, 150,"Very poor",       "red"),
    (150, 1200,"Extremely poor", "darkred"),
])
NO2_RULES = buckets([
    (0, 40,   "Good",            "green"),
    (40, 90,  "Fair",            "limegreen"),
    (90, 120, "Moderate",        "yellow"),
    (120, 230,"Poor",            "orange"),
    (230, 340,"Very poor",       "red"),
    (340, 1000,"Extremely poor", "darkred"),
])
SO2_RULES = buckets([
    (0, 100,  "Good",            "green"),
    (100, 200,"Fair",            "limegreen"),
    (200, 350,"Moderate",        "yellow"),
    (350, 500,"Poor",            "orange"),
    (500, 750,"Very poor",       "red"),
    (750, 1250,"Extremely poor", "darkred"),
])

def classify(v, rules):
    for lo, hi, label, colour in rules:
        if lo <= v < hi:
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
        .properties(width=380)
    )

# ───────── UI TABS ─────────
dust_tab, heat_tab = st.tabs(["🌪️ Dust / Air-Quality", "🌞 Temperature"])

# ─────── DUST / AIR-QUALITY TAB ───────
with dust_tab:
    st.header("🌪️ Multi-Pollutant Air Quality – next 4 days")
    st_folium(build_map(CENTER_LAT, CENTER_LON), use_container_width=True, height=420, key="dust_map")

    aq = get_air_quality(CENTER_LAT, CENTER_LON)

    # Aggregate daily maxima / peaks
    aggs = {p: {} for p in ["pm10", "pm2_5", "no2", "so2"]}
    for t, v10, v25, n, s in zip(
        aq["time"], aq["pm10"], aq["pm2_5"], aq["no2"], aq["so2"]
    ):
        d = t.date()
        aggs["pm10"][d] = max(v10, aggs["pm10"].get(d, -1))
        aggs["pm2_5"][d] = max(v25, aggs["pm2_5"].get(d, -1))
        aggs["no2"][d] = max(n, aggs["no2"].get(d, -1))
        aggs["so2"][d] = max(s, aggs["so2"].get(d, -1))

    def make_df(series):
        return pd.DataFrame(
            {
                "day": [d.strftime("%a %d %b") for d in list(series)[:4]],
                "value": list(series.values())[:4],
            }
        )

    charts = [
        ("PM2.5 (µg/m³)", make_df(aggs["pm2_5"]), 800, PM25_RULES),
        ("PM10 (µg/m³)",  make_df(aggs["pm10"]),  1200, PM10_RULES),
        ("NO₂ (µg/m³)",   make_df(aggs["no2"]),   1000, NO2_RULES),
        ("SO₂ (µg/m³)",   make_df(aggs["so2"]),   1250, SO2_RULES),
    ]

    for title, df, vmax, rules in charts:
        st.subheader(title)
        st.altair_chart(bar_chart(df, title.split()[0], vmax, rules), use_container_width=True)

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
