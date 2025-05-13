# app.py · Cool Assistant – Heat-Wave & Dust-Storm Helper
import os, datetime as dt, random, requests, streamlit as st, folium
from streamlit_folium import st_folium
from auth import handle_authentication


# ─────────── CONFIG ────────────
st.set_page_config(page_title="Cool Assistant", layout="wide")
CENTER_LAT, CENTER_LON = 36.206, 44.009      # Kurdistan Region centre

# Key lookup helper ---------------------------------------------------
def get_api_key() -> str | None:
    if "OWM_API_KEY" in st.secrets:              # Streamlit Cloud / secrets.toml
        return st.secrets["OWM_API_KEY"]
    return os.getenv("OWM_API_KEY")              # local env var

OWM_API_KEY = get_api_key()

# ───────── AUTH & SIDEBAR ─────────
handle_authentication()
user = st.experimental_user

with st.sidebar:
    st.subheader("Account")
    st.write(user.email)
    st.button("Log out", on_click=st.logout, use_container_width=True)

    # ▸ Runtime API-key entry (if missing or wrong)
    if not OWM_API_KEY:
        st.info("Paste your OpenWeather API key:")
        OWM_API_KEY = st.text_input(
            "OWM_API_KEY", type="password", placeholder="b0xxxxxxxxxxxxxxxxxxxxxxxxx"
        )

# ───────── HEADER ────────────────
st.title("🏠 Cool Assistant")
st.caption(
    "Your assistant for **mitigating heat waves and dust storms** across the Kurdistan Region."
)

# Daily tip -----------------------------------------------------------
st.subheader("💡 Daily Tip")
st.write(
    random.choice(
        [
            "Close windows during the midday heat; ventilate late-night / early morning.",
            "Hang damp cotton curtains – they pre-filter dust and cool incoming air.",
            "Add weather-stripping to doors to keep hot, dusty air outside.",
        ]
    )
)

# Tabs ---------------------------------------------------------------
dust_tab, heat_tab = st.tabs(["🌪️ Dust-Storm Forecast", "🌞 Heat-Wave Forecast"])


# Folium builder ------------------------------------------------------
def build_folium(layer_code: str, opacity: float = 0.6) -> folium.Map:
    m = folium.Map(location=[CENTER_LAT, CENTER_LON], zoom_start=6)
    if OWM_API_KEY:
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


# Cached fetch helpers -----------------------------------------------
@st.cache_data(ttl=600)
def fetch_pm10_daily_max(lat: float, lon: float, key: str):
    url = (
        "https://api.openweathermap.org/data/2.5/air_pollution/forecast?"
        f"lat={lat}&lon={lon}&appid={key}"
    )
    r = requests.get(url, timeout=8)
    r.raise_for_status()
    daily = {}
    for item in r.json()["list"]:
        day = dt.datetime.utcfromtimestamp(item["dt"]).date()
        pm10 = item["components"]["pm10"]
        daily[day] = max(pm10, daily.get(day, -1))
    return daily


@st.cache_data(ttl=600)
def fetch_daily_highs(lat: float, lon: float, key: str):
    url = (
        "https://api.openweathermap.org/data/2.5/forecast?"
        f"lat={lat}&lon={lon}&appid={key}&units=metric"
    )
    r = requests.get(url, timeout=8)
    r.raise_for_status()
    highs = {}
    for i in r.json()["list"]:
        day = dt.datetime.fromtimestamp(i["dt"]).date()
        highs[day] = max(highs.get(day, -273), i["main"]["temp_max"])
    return highs


# ─────── DUST-STORM TAB ─────────
with dust_tab:
    st.header("🌪️ Dust-Storm Risk – Next 4 Days")
    st.markdown("##### Wind layer (higher winds ⇒ higher blowing-dust risk)")
    st_folium(build_folium("wind_new"), use_container_width=True, height=480)

    if not OWM_API_KEY:
        st.warning("Enter an API key in the sidebar to load PM10 forecasts.")
    else:
        with st.spinner("Loading PM10 forecast…"):
            try:
                pm10 = fetch_pm10_daily_max(CENTER_LAT, CENTER_LON, OWM_API_KEY)
                for day, value in list(pm10.items())[:4]:
                    risk = (
                        "🔴 Very High" if value >= 300
                        else "🟠 High" if value >= 200
                        else "🟡 Moderate" if value >= 100
                        else "🟢 Low"
                    )
                    st.metric(day.strftime("%a %d %b"), f"{value:.0f} µg/m³", risk)
            except Exception as e:
                st.error(f"PM10 fetch failed → {e}")


# ─────── HEAT-WAVE TAB ──────────
with heat_tab:
    st.header("🌞 Heat-Wave Outlook – Next 5 Days")
    st.markdown("##### Temperature layer (°C)")
    st_folium(build_folium("temp_new"), use_container_width=True, height=480)

    if not OWM_API_KEY:
        st.warning("Enter an API key in the sidebar to load the heat forecast.")
    else:
        with st.spinner("Loading 5-day forecast…"):
            try:
                highs = fetch_daily_highs(CENTER_LAT, CENTER_LON, OWM_API_KEY)
                thresholds = {"Heat-Wave": 43, "Warning": 38}
                for day, tmax in list(highs.items())[:5]:
                    status = (
                        "🔥 Heat-Wave" if tmax >= thresholds["Heat-Wave"]
                        else "⚠️ Hot" if tmax >= thresholds["Warning"]
                        else "🙂 Warm"
                    )
                    st.metric(day.strftime("%a %d %b"), f"{tmax:.1f} °C", status)
            except Exception as e:
                st.error(f"Forecast fetch failed → {e}")


# Footer --------------------------------------------------------------
st.markdown("---")
st.caption("© 2025 Cool Assistant • Kurdistan Region")
