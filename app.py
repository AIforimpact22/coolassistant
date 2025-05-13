# app.py · Cool Assistant — Map-Click Survey + Postgres storage
import datetime as dt
import requests
import psycopg2
import streamlit as st
import folium
from streamlit_folium import st_folium
from auth import handle_authentication

# ───────── DATABASE CONFIG ─────────
PG_URL = "postgresql://cool_owner:npg_jpi5LdZUbvw1@ep-frosty-tooth-a283lla4-pooler.eu-central-1.aws.neon.tech/cool?sslmode=require"
TABLE = "survey_responses"

def save_to_db(record: dict):
    """Create table if needed and insert a row."""
    create_sql = f"""
    CREATE TABLE IF NOT EXISTS {TABLE} (
      ts          TIMESTAMPTZ,
      user_email  TEXT,
      location    TEXT,
      lat         DOUBLE PRECISION,
      lon         DOUBLE PRECISION,
      feeling     TEXT,
      issues      TEXT
    );
    """
    insert_sql = f"""
    INSERT INTO {TABLE} (ts,user_email,location,lat,lon,feeling,issues)
    VALUES (%(Timestamp)s, %(User)s, %(Location)s, %(Lat)s, %(Lon)s,
            %(Feeling)s, %(Issues)s);
    """
    try:
        with psycopg2.connect(PG_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(create_sql)
                cur.execute(insert_sql, record)
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
    st.markdown("---")
    st.subheader("Logged in as")
    st.write(user.email)
    st.button("Log out", on_click=st.logout)

# ───────── SESSION STATE ─────────
state = st.session_state
state.setdefault("latlon", None)
state.setdefault("loc_name", "")
state.setdefault("feeling", None)
state.setdefault("issues", set())

# ───────── HELPERS ─────────
def reverse_geocode(lat, lon):
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
    try:
        j = requests.get(url, timeout=5, headers={"User-Agent": "coolassistant"}).json()
        a = j.get("address", {})
        city = a.get("city") or a.get("town") or a.get("village") or ""
        region = a.get("state", "")
        country = a.get("country", "")
        return ", ".join(p for p in (city, region, country) if p) or f"{lat:.3f},{lon:.3f}"
    except Exception:
        return f"{lat:.3f},{lon:.3f}"

# ───────── 1️⃣ MAP ─────────
st.title("📍 Select Your Exact Location")
m = folium.Map(location=[36.2, 44.0], zoom_start=6)
if state.latlon:
    folium.Marker(state.latlon, tooltip=state.loc_name).add_to(m)
out = st_folium(m, height=400, use_container_width=True)

if out and out.get("last_clicked"):
    lat = out["last_clicked"]["lat"]
    lon = out["last_clicked"]["lng"]
    if state.latlon != (lat, lon):
        state.latlon  = (lat, lon)
        state.loc_name = reverse_geocode(lat, lon)
        st.toast(f"Location chosen: {state.loc_name}", icon="📍")

if state.latlon:
    st.success(f"Location: {state.loc_name}")
else:
    st.info("Click the map to set your location.")

# ───────── 2️⃣ FEELING ─────────
st.markdown("#### 😊 Your feeling")
feelings = ["😃 Good", "😐 Neutral", "☹️ Uncomfortable", "😫 Bad"]
fcols = st.columns(len(feelings))
for i, lab in enumerate(feelings):
    sel = state.feeling == lab
    if fcols[i].button(lab, key=f"feel_{i}", type="primary" if sel else "secondary"):
        state.feeling = lab
if state.feeling:
    st.success(f"Feeling: {state.feeling}")

# ───────── 3️⃣ ISSUES ─────────
st.markdown("#### 🌪️ What's bothering you? (toggle)")
all_issues = ["🔥 Heat","🌪️ Dust","💨 Wind","🏭 Pollution","💧 Humidity",
              "☀️ UV","⚡ Storms","🌧️ Rain","❄️ Cold","🌫️ Fog"]
icol = st.columns(2)
for i, issue in enumerate(all_issues):
    sel = issue in state.issues
    label = ("✅ " if sel else "☐ ") + issue
    if icol[i%2].button(label, key=f"iss_{i}", type="primary" if sel else "secondary"):
        state.issues.discard(issue) if sel else state.issues.add(issue)
if state.issues:
    st.info("Issues: " + ", ".join(sorted(state.issues)))

# ───────── 4️⃣ SUBMIT ─────────
ready = state.latlon and state.feeling
if st.button("🚀 Submit", type="primary", disabled=not ready):
    rec = {
        "Timestamp": dt.datetime.now(),
        "User": user.email,
        "Location": state.loc_name,
        "Lat": state.latlon[0],
        "Lon": state.latlon[1],
        "Feeling": state.feeling,
        "Issues": ", ".join(sorted(state.issues)),
    }
    save_to_db(rec)
    st.success("Thanks! Your response was saved.")
    st.json(rec)

# ───────── FOOTER ─────────
st.markdown("---")
st.caption("© 2025 Cool Assistant • Kurdistan Region")
