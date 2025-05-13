# app.py · Cool Assistant – Real-time AQI & Multi-Pollutant Charts (Open-Meteo)
import datetime as dt
import random
import requests
import streamlit as st
import folium
import pandas as pd
import altair as alt
from streamlit_folium import st_folium
from auth import handle_authentication

# ───────── LOCATION & CONFIG ─────────
LATITUDE, LONGITUDE = 36.1912, 44.0094
TIMEZONE = "auto"
HOURS_TO_SHOW = 24
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
st.caption(
    "Real-time **European AQI** plus 24-hour heat & dust outlook for the Kurdistan Region (Open-Meteo)."
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
def _first(x):
    return x[0] if isinstance(x, list) else x

@st.cache_data(ttl=300)
def get_air_quality(lat, lon):
    url = (
        "https://air-quality-api.open-meteo.com/v1/air-quality"
        f"?latitude={lat}&longitude={lon}"
        "&hourly=pm10,pm2_5,nitrogen_dioxide,sulphur_dioxide"
        ",aerosol_optical_depth,dust,ammonia,methane,ozone"
        "&current=aerosol_optical_depth,dust,european_aqi,pm10,pm2_5,nitrogen_dioxide"
        "&past_days=5"
        f"&timezone={TIMEZONE}"
    )
    j = requests.get(url, timeout=10).json()

    cur_raw = j.get("current", {})
    cur = {k: _first(v) for k, v in cur_raw.items() if k != "time"}
    cur_time = dt.datetime.fromisoformat(_first(cur_raw.get("time", dt.datetime.utcnow().isoformat())))
    cur["time"] = cur_time

    hr_raw = j.get("hourly", {})
    times = [dt.datetime.fromisoformat(t) for t in hr_raw.get("time", [])]
    def s(name):  # safe series
        vals = hr_raw.get(name, [])
        return vals if vals else [None] * len(times)
    hourly = {
        "time": times,
        "pm10": s("pm10"),
        "pm2_5": s("pm2_5"),
        "no2":  s("nitrogen_dioxide"),
        "so2":  s("sulphur_dioxide"),
    }
    return cur, hourly

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

# ───────── AQI buckets (exact ranges) ─────────
def rules(r): return [(lo, hi, lab, col) for lo, hi, lab, col in r]

PM25_R = rules([(0,10,"Good","green"),(10,20,"Fair","limegreen"),(20,25,"Moderate","yellow"),
                (25,50,"Poor","orange"),(50,75,"Very poor","red"),(75,800,"Extremely poor","darkred")])
PM10_R = rules([(0,20,"Good","green"),(20,40,"Fair","limegreen"),(40,50,"Moderate","yellow"),
                (50,100,"Poor","orange"),(100,150,"Very poor","red"),(150,1200,"Extremely poor","darkred")])
NO2_R  = rules([(0,40,"Good","green"),(40,90,"Fair","limegreen"),(90,120,"Moderate","yellow"),
                (120,230,"Poor","orange"),(230,340,"Very poor","red"),(340,1000,"Extremely poor","darkred")])
SO2_R  = rules([(0,100,"Good","green"),(100,200,"Fair","limegreen"),(200,350,"Moderate","yellow"),
                (350,500,"Poor","orange"),(500,750,"Very poor","red"),(750,1250,"Extremely poor","darkred")])
EU_AQI_R = [(0,25,"Good","green"),(25,50,"Fair","limegreen"),(50,75,"Moderate","yellow"),
            (75,100,"Poor","orange"),(100,1e9,"Very poor","red")]

def classify(v, rule):
    for lo, hi, lab, col in rule:
        if v is not None and lo <= v < hi:
            return lab, col
    return "No data", "grey"

# ───────── Chart helper ─────────
def bar(df, title, vmax, rule):
    if df.empty:
        return alt.Chart(pd.DataFrame({"day":[],"value":[]}))
    df = df.copy()
    df["bucket"], df["colour"] = zip(*df["value"].map(lambda v: classify(v, rule)))
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

# ───────── Tabs ─────────
aq_tab, heat_tab = st.tabs(["🌪️ Air-Quality", "🌞 Temperature"])

# ─────── AIR-QUALITY TAB ───────
with aq_tab:
    st.header("🌪️ European AQI & Key Pollutants")
    st_folium(build_map(LATITUDE, LONGITUDE), use_container_width=True, height=420, key="aq_map")

    current, hr = get_air_quality(LATITUDE, LONGITUDE)

    # Current panel
    st.subheader(f"Current – {current['time'].strftime('%H:%M')}")
    aqi_val = current.get("european_aqi")
    aqi_lab, aqi_col = classify(aqi_val, EU_AQI_R)
    st.metric("European AQI", f"{aqi_val or '–'}", aqi_lab, delta_color="off")
    st.write(f"<div style='height:10px;background:{aqi_col}'></div>", unsafe_allow_html=True)

    cols = st.columns(3)
    for c, (label, key, rule) in zip(
        cols,
        [("PM2.5 µg/m³","pm2_5",PM25_R),("PM10 µg/m³","pm10",PM10_R),("NO₂ µg/m³","nitrogen_dioxide",NO2_R)]
    ):
        val = current.get(key)
        lab, col = classify(val, rule)
        with c:
            st.metric(label, f"{val:.0f}" if val else "–", lab, delta_color="off")
            st.write(f"<div style='height:6px;background:{col}'></div>", unsafe_allow_html=True)

    st.divider()

    # Aggregate 4-day maxima
    ag = {p:{} for p in ["pm10","pm2_5","no2","so2"]}
    for t,v10,v25,n,s in zip(hr["time"],hr["pm10"],hr["pm2_5"],hr["no2"],hr["so2"]):
        d=t.date()
        if v10 is not None: ag["pm10"][d]=max(v10,ag["pm10"].get(d,-1))
        if v25 is not None: ag["pm2_5"][d]=max(v25,ag["pm2_5"].get(d,-1))
        if n   is not None: ag["no2"][d] =max(n,  ag["no2"].get(d,-1))
        if s   is not None: ag["so2"][d] =max(s,  ag["so2"].get(d,-1))

    def df(series): return pd.DataFrame({"day":[d.strftime("%a %d") for d in list(series)[:4]],
                                         "value":list(series.values())[:4]})

    charts = [
        ("PM2.5", df(ag["pm2_5"]), 800,  PM25_R),
        ("PM10",  df(ag["pm10"]),  1200, PM10_R),
        ("NO₂",   df(ag["no2"]),   1000, NO2_R),
        ("SO₂",   df(ag["so2"]),   1250, SO2_R),
    ]
    for title, dframe, vmax, rule in charts:
        st.subheader(title)
        st.altair_chart(bar(dframe, title, vmax, rule), use_container_width=True)

# ─────── TEMPERATURE TAB ───────
with heat_tab:
    st.header("🌞 Upcoming 24-hour Temperature")
    st_folium(build_map(LATITUDE, LONGITUDE), use_container_width=True, height=420, key="temp_map")

    temps = get_hourly_temps(LATITUDE, LONGITUDE)
    now = dt.datetime.now().replace(minute=0, second=0, microsecond=0)
    next_24 = [(t,v) for t,v in zip(temps["time"],temps["temp"]) if now <= t < now+dt.timedelta(hours=HOURS_TO_SHOW)]

    st.subheader("Hourly outlook (°C)")
    cols = st.columns(4)
    for i,(t,v) in enumerate(next_24):
        with cols[i%4]:
            st.write(f"{t.strftime('%H:%M')}: **{v:.1f} °C**")

# ─────── FOOTER ───────
st.markdown("---")
st.caption("© 2025 Cool Assistant • Kurdistan Region")

