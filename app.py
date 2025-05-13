# app.py · Cool Assistant — Survey (About link fixed) + Postgres storage
import datetime as dt
import requests
import psycopg2
import streamlit as st
import folium
from streamlit_folium import st_folium
from auth import handle_authentication

# ───────── DATABASE ─────────
PG_URL = (
    "postgresql://cool_owner:npg_jpi5LdZUbvw1@"
    "ep-frosty-tooth-a283lla4-pooler.eu-central-1.aws.neon.tech/cool?sslmode=require"
)
TABLE = "survey_responses"

def save_to_db(row: dict):
    create = f"""CREATE TABLE IF NOT EXISTS {TABLE}(
        ts TIMESTAMPTZ, user_email TEXT, location TEXT,
        lat DOUBLE PRECISION, lon DOUBLE PRECISION,
        feeling TEXT, issues TEXT);"""
    insert = f"""INSERT INTO {TABLE}
        (ts,user_email,location,lat,lon,feeling,issues)
        VALUES (%(ts)s,%(user)s,%(location)s,%(lat)s,%(lon)s,%(feeling)s,%(issues)s);"""
    try:
        with psycopg2.connect(PG_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(create)
                cur.execute(insert, row)
        st.toast("Saved to database ✅")
    except Exception as e:
        st.error(f"Database error: {e}")

# ───────── STREAMLIT CONFIG ─────────
st.set_page_config(page_title="Cool Assistant Survey", layout="centered")
handle_authentication()
user = st.experimental_user

# ───────── SIDEBAR ─────────
with st.sidebar:
    st.image(
        "https://github.com/AIforimpact22/coolassistant/blob/main/input/cool_logo.png?raw=true",
        width=180,
    )

    st.markdown("### Navigation")
    # Survey button does nothing (we are already on survey)
    st.button("📝 Survey", disabled=True, type="primary")

    # About button tries to switch page
    if st.button("ℹ️ About", type="secondary"):
        if hasattr(st, "switch_page"):
            try:
                st.switch_page("about.py")
            except Exception as e:
                st.warning("About page not found in this multipage setup.")
        else:
            st.warning("Use the default Streamlit sidebar to open the About page.")

    st.markdown("---")
    st.subheader("Account")
    st.write(user.email)
    st.button("Log out", on_click=st.logout)

# ───────── SESSION STATE ─────────
state = st.session_state
state.setdefault("feeling", None)
state.setdefault("issues", set())
state.setdefault("latlon", None)
state.setdefault("loc_name", "")

# ───────── HELPERS ─────────
def reverse_geocode(lat, lon):
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
    try:
        data = requests.get(url, timeout=5, headers={"User-Agent": "coolassistant"}).json()
        a = data.get("address", {})
        city = a.get("city") or a.get("town") or a.get("village") or ""
        region = a.get("state", "")
        country = a.get("country", "")
        return ", ".join(p for p in (city, region, country) if p) or f"{lat:.3f},{lon:.3f}"
    except Exception:
        return f"{lat:.3f},{lon:.3f}"

# ───────── SURVEY ─────────
st.title("🌡️ Weather Feeling Survey")

# Q1 – Feeling
st.markdown("### 1. How do you feel about the weather *right now*?")
feelings = ["😃 Good", "😐 Neutral", "☹️ Uncomfortable", "😫 Bad"]
fcols = st.columns(len(feelings))
for i, lab in enumerate(feelings):
    if fcols[i].button(lab, key=f"feel_{i}", type="primary" if state.feeling == lab else "secondary"):
        state.feeling = lab
if state.feeling:
    st.success(f"Feeling selected: {state.feeling}")

# Q2 – Issues
st.markdown("### 2. What's bothering you? (toggle)")
issues_all = ["🔥 Heat", "🌪️ Dust", "💨 Wind", "🏭 Pollution", "💧 Humidity",
              "☀️ UV", "⚡ Storms", "🌧️ Rain", "❄️ Cold", "🌫️ Fog"]
icol = st.columns(2)
for i, issue in enumerate(issues_all):
    picked = issue in state.issues
    label  = ("✅ " if picked else "☐ ") + issue
    if icol[i % 2].button(label, key=f"iss_{i}", type="primary" if picked else "secondary"):
        state.issues.discard(issue) if picked else state.issues.add(issue)
if state.issues:
    st.info("Issues: " + ", ".join(sorted(state.issues)))

# Map section appears only after feeling chosen
if state.feeling:
    st.markdown("### 3. Click on the map to select your exact location")
    m = folium.Map(location=[36.2, 44.0], zoom_start=6)
    if state.latlon:
        folium.Marker(state.latlon, tooltip=state.loc_name).add_to(m)
    result = st_folium(m, height=380, use_container_width=True)
    if result and result.get("last_clicked"):
        lat, lon = result["last_clicked"]["lat"], result["last_clicked"]["lng"]
        if state.latlon != (lat, lon):
            state.latlon = (lat, lon)
            state.loc_name = reverse_geocode(lat, lon)
            st.toast(f"Location set: {state.loc_name}", icon="📍")
    if state.latlon:
        st.success(f"Location: {state.loc_name}")

# Submit
ready = state.feeling and state.latlon
if st.button("🚀 Submit Response", disabled=not ready, type="primary"):
    row = {
        "ts": dt.datetime.utcnow(),
        "user": user.email,
        "location": state.loc_name,
        "lat": state.latlon[0],
        "lon": state.latlon[1],
        "feeling": state.feeling,
        "issues": ", ".join(sorted(state.issues)),
    }
    save_to_db(row)
    st.success("🎉 Thank you! Your feedback was saved.")

st.markdown("---")
st.caption("© 2025 Cool Assistant • Kurdistan Region")
