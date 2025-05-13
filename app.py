# app.py  •  Cool Assistant – Heat-Wave & Dust-Storm Helper
import os
import datetime as dt
import random
import requests
import streamlit as st
from auth import handle_authentication


# ────────────────────────────── CONFIG ──────────────────────────────
st.set_page_config(page_title="Cool Assistant", layout="wide")
API_KEY = os.getenv("OPENWEATHER_API_KEY")            # 5-day / 3-hour forecast
LOCATION = "Erbil,IQ"                                 # OpenWeather “city,country”


# ─────────────────────────── AUTHENTICATION ─────────────────────────
handle_authentication()
user = st.experimental_user


# ────────────────────────── SIDEBAR (ACCOUNT) ───────────────────────
with st.sidebar:
    st.subheader("Account")
    st.write(user.email)
    st.button("Log out", on_click=st.logout, use_container_width=True)


# ─────────────────────────── HEADER & MOTTO ─────────────────────────
st.title("🏠 Cool Assistant")
st.caption(
    "Your companion for mitigating **heat waves** and **dust storms** "
    "across the Kurdistan Region."
)


# ───────────────────────────── DAILY TIP ────────────────────────────
st.subheader("💡 Daily Tip")
st.write(
    random.choice(
        [
            "Close windows during midday heat; ventilate late night / early morning.",
            "Use damp cotton curtains to pre-filter dust and cool incoming air.",
            "Add weather-stripping to doors to keep hot, dusty air outside.",
        ]
    )
)


# ─────────────────────────────── TABS ───────────────────────────────
dust_tab, heat_tab = st.tabs(["🌪️ Dust-Storm Forecast", "🌞 Heat-Wave Forecast"])


# ── 1)  DUST-STORM FORECAST TAB ─────────────────────────────────────
with dust_tab:
    st.header("🌪️ Dust-Storm Risk – Next 5 Days")

    def fetch_dust_data(city: str):
        """
        Placeholder: Replace with a real dust / PM10 / PM2.5 forecast API
        (e.g. IQAir, BreezoMeter, Copernicus CAMS).
        """
        dummy = []
        base = dt.date.today()
        for i in range(5):
            dummy.append(
                {
                    "date": base + dt.timedelta(days=i),
                    "pm10": random.randint(100, 400),      # µg/m³
                    "risk": random.choice(["Low", "Moderate", "High"]),
                }
            )
        return dummy

    dust = fetch_dust_data(LOCATION)

    # Display
    for day in dust:
        color = {"Low": "🟢", "Moderate": "🟠", "High": "🔴"}[day["risk"]]
        st.metric(
            label=day["date"].strftime("%A %d %b"),
            value=f"{color} {day['risk']}",
            delta=f"PM10 ≈ {day['pm10']} µg/m³",
        )

    st.info(
        "Data source: replace `fetch_dust_data()` with a live API such as "
        "**IQAir Forecast** or **Copernicus CAMS Dust ‘DIFS’**."
    )


# ── 2)  HEAT-WAVE FORECAST TAB ──────────────────────────────────────
with heat_tab:
    st.header("🌞 Heat-Wave Outlook – Next 5 Days")

    def fetch_heat_data(city: str, api_key: str):
        """
        Pull OpenWeatherMap 5-day / 3-hour forecast and extract daily highs.
        """
        if not api_key:
            return None

        url = (
            "https://api.openweathermap.org/data/2.5/forecast?"
            f"q={city}&appid={api_key}&units=metric"
        )
        raw = requests.get(url, timeout=8).json()

        # Aggregate max temp per calendar day
        daily_highs = {}
        for item in raw["list"]:
            day = dt.datetime.fromtimestamp(item["dt"]).date()
            temp = item["main"]["temp_max"]
            daily_highs[day] = max(temp, daily_highs.get(day, -999))

        today = dt.date.today()
        outlook = [
            {"date": today + dt.timedelta(days=i), "max": daily_highs.get(today + dt.timedelta(days=i))}
            for i in range(5)
        ]
        return outlook

    if not API_KEY:
        st.warning("Set OPENWEATHER_API_KEY in your environment to view heat data.")
    else:
        forecast = fetch_heat_data(LOCATION, API_KEY)
        thresholds = {"Heat-Wave": 43, "Warning": 38}

        for day in forecast:
            status = (
                "🔥 Heat-Wave" if day["max"] >= thresholds["Heat-Wave"]
                else "⚠️ Hot" if day["max"] >= thresholds["Warning"]
                else "🙂 Warm"
            )
            st.metric(
                label=day["date"].strftime("%A %d %b"),
                value=f"{day['max']:.1f} °C",
                delta=status,
            )

        st.success(
            f"Thresholds: **Heat-Wave ≥ {thresholds['Heat-Wave']} °C**, "
            f"Warning ≥ {thresholds['Warning']} °C."
        )


# ───────────────────────── FOOTER (OPTIONAL) ────────────────────────
st.markdown("---")
st.caption("© 2025 Cool Assistant • Kurdistan Region")
