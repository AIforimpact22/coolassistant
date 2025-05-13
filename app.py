# app.py · Cool Assistant — Real-time AQI & Temperature (Open-Meteo)
import datetime as dt
import random
import requests
import streamlit as st
import pandas as pd
import altair as alt
import folium
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
st.caption("European AQI and 24-h heat-wave & dust outlook for Kurdistan (Open-Meteo)")
st.subheader("💡 Daily Tip")
st.write(random.choice(
    ["Ventilate late-night or early-morning for coolest air.",
     "Damp cotton curtains pre-filter dust and cool incoming air.",
     "Weather-strip doors to block hot, dusty air."]
))

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
        "&hourly=pm10,pm2_5,nitrogen_dioxide,sulphur_dioxide"
        "&current=european_aqi,pm10,pm2_5,nitrogen_dioxide"
        "&past_days=5"
        f"&timezone={TIMEZONE}"
    )
    j = requests.get(url, timeout=10).json()

    cur_raw = j.get("current", {})
    cur = {k: _first(v) for k, v in cur_raw.items() if k != "time"}
    cur["time"] = dt.datetime.fromisoformat(_first(cur_raw.get("time", dt.datetime.utcnow().isoformat())))

    hr = j.get("hourly", {})
    t = [dt.datetime.fromisoformat(x) for x in hr.get("time", [])]
    def series(name): return hr.get(name, [None]*len(t)) or [None]*len(t)
    hourly = {"time": t,
              "pm10": series("pm10"),
              "pm2_5": series("pm2_5"),
              "no2":  series("nitrogen_dioxide"),
              "so2":  series("sulphur_dioxide")}
    return cur, hourly

@st.cache_data(ttl=600)
def fetch_temps(lat, lon):
    url = ( "https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            "&hourly=temperature_2m"
            f"&timezone={TIMEZONE}" )
    j = requests.get(url, timeout=10).json()
    times = [dt.datetime.fromisoformat(t) for t in j["hourly"]["time"]]
    return {"time": times, "temp": j["hourly"]["temperature_2m"]}

# ───────── BUCKET TABLES (exact EU ranges) ─────────
def rules(lst): return [(lo, hi, lab, col) for lo, hi, lab, col in lst]

PM25_R = rules([(0,10,"Good","green"),(10,20,"Fair","limegreen"),(20,25,"Moderate","yellow"),
                (25,50,"Poor","orange"),(50,75,"Very poor","red"),(75,800,"Extremely poor","darkred")])
PM10_R = rules([(0,20,"Good","green"),(20,40,"Fair","limegreen"),(40,50,"Moderate","yellow"),
                (50,100,"Poor","orange"),(100,150,"Very poor","red"),(150,1200,"Extremely poor","darkred")])
NO2_R  = rules([(0,40,"Good","green"),(40,90,"Fair","limegreen"),(90,120,"Moderate","yellow"),
                (120,230,"Poor","orange"),(230,340,"Very poor","red"),(340,1000,"Extremely poor","darkred")])
SO2_R  = rules([(0,100,"Good","green"),(100,200,"Fair","limegreen"),(200,350,"Moderate","yellow"),
                (350,500,"Poor","orange"),(500,750,"Very poor","red"),(750,1250,"Extremely poor","darkred")])
AQI_R  = [(0,25,"Good","green"),(25,50,"Fair","limegreen"),(50,75,"Moderate","yellow"),
          (75,100,"Poor","orange"),(100,1e9,"Very poor","red")]

def bucket(val, tbl):
    for lo, hi, lab, col in tbl:
        if val is not None and lo <= val < hi:
            return lab, col
    return "No data", "grey"

# ───────── Chart helper ─────────
def bar(df, vmax, tbl):
    if df.empty:
        return alt.Chart(pd.DataFrame({"day":[],"value":[]}))
    df["bucket"], df["colour"] = zip(*df["value"].map(lambda v: bucket(v, tbl)))
    return (alt.Chart(df)
            .mark_bar(height=22)
            .encode(y="day:N",
                    x=alt.X("value:Q", scale=alt.Scale(domain=[0, vmax])),
                    color=alt.Color("colour:N", scale=None, legend=None),
                    tooltip=["day:N","value:Q","bucket:N"])
            .properties(width=380))

# ───────── Tabs ─────────
aq_tab, temp_tab = st.tabs(["🌪️ Air-Quality", "🌞 Temperature"])

# ─────── AIR-QUALITY TAB ───────
with aq_tab:
    st.header("🌪️ European AQI & Pollutants")
    st_folium(make_map(LATITUDE, LONGITUDE), use_container_width=True, height=420, key="map_aq")

    cur, hr = fetch_air(LATITUDE, LONGITUDE)

    st.subheader(f"Current — {cur['time'].strftime('%H:%M')}")
    aqi_val = cur.get("european_aqi")
    aqi_lab, aqi_col = bucket(aqi_val, AQI_R)
    st.metric("European AQI", f"{aqi_val or '–'}", aqi_lab, delta_color="off")
    st.write(f"<div style='height:10px;background:{aqi_col}'></div>", unsafe_allow_html=True)

    cols = st.columns(3)
    for c, (lbl, key, tbl) in zip(
        cols,
        [("PM2.5 µg/m³","pm2_5",PM25_R),("PM10 µg/m³","pm10",PM10_R),("NO₂ µg/m³","nitrogen_dioxide",NO2_R)]
    ):
        val = cur.get(key)
        lab, col = bucket(val, tbl)
        with c:
            st.metric(lbl, f"{val:.0f}" if val else "–", lab, delta_color="off")
            st.write(f"<div style='height:6px;background:{col}'></div>", unsafe_allow_html=True)

    st.divider()

    # 4-day max aggregation
    agg = {p:{} for p in ["pm2_5","pm10","no2","so2"]}
    for t,v25,v10,n,s in zip(hr["time"],hr["pm2_5"],hr["pm10"],hr["no2"],hr["so2"]):
        d = t.date()
        if v25 is not None: agg["pm2_5"][d] = max(v25, agg["pm2_5"].get(d,-1))
        if v10 is not None: agg["pm10"][d]  = max(v10,  agg["pm10"].get(d,-1))
        if n   is not None: agg["no2"][d]   = max(n,    agg["no2"].get(d,-1))
        if s   is not None: agg["so2"][d]   = max(s,    agg["so2"].get(d,-1))

    def frame(dct): return pd.DataFrame(
        {"day":[d.strftime("%a %d") for d in list(dct)[:4]],
         "value":list(dct.values())[:4]}
    )

    for ttl, series, vmax, tbl in [
        ("PM2.5", frame(agg["pm2_5"]), 800,  PM25_R),
        ("PM10",  frame(agg["pm10"]),  1200, PM10_R),
        ("NO₂",   frame(agg["no2"]),   1000, NO2_R),
        ("SO₂",   frame(agg["so2"]),   1250, SO2_R),
    ]:
        st.subheader(ttl)
        st.altair_chart(bar(series, vmax, tbl), use_container_width=True)

# ─────── TEMPERATURE TAB ───────
with temp_tab:
    st.header("🌞 Next 24 h Temperature")
    st_folium(make_map(LATITUDE, LONGITUDE), use_container_width=True, height=420, key="map_temp")

    temps = fetch_temps(LATITUDE, LONGITUDE)
    now = dt.datetime.now().replace(minute=0, second=0, microsecond=0)
    nxt = [(t,v) for t,v in zip(temps["time"], temps["temp"]) if now <= t < now+dt.timedelta(hours=HOURS_TO_SHOW)]

    st.subheader("Hourly outlook (°C)")
    cols = st.columns(4)
    for i,(t,v) in enumerate(nxt):
        with cols[i%4]:
            st.write(f"{t.strftime('%H:%M')}: **{v:.1f}°C**")

st.markdown("---")
st.caption("© 2025 Cool Assistant • Kurdistan Region")
