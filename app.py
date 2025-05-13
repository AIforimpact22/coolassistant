# app.py · Cool Assistant — Map-Click Accurate Location Survey
import datetime as dt
import requests
import streamlit as st
import folium
from streamlit_folium import st_folium
from auth import handle_authentication

# ───────── CONFIG ─────────
st.set_page_config(page_title="Cool Assistant Survey", layout="centered")

# ───────── AUTH ─────────
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
state.setdefault("latlon", None)       # (lat, lon)
state.setdefault("loc_name", "")       # str
state.setdefault("feeling", None)      # str
state.setdefault("issues", set())      # set[str]

# ───────── HELPERS ─────────
def reverse_geocode(lat: float, lon: float) -> str:
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
    try:
        data = requests.get(url, timeout=5, headers={"User-Agent": "coolassistant"}).json()
        addr = data.get("address", {})
        city = addr.get("city") or addr.get("town") or addr.get("village") or ""
        region = addr.get("state", "")
        country = addr.get("country", "")
        place = ", ".join(p for p in (city, region, country) if p)
        return place or f"{lat:.3f}, {lon:.3f}"
    except Exception:
        return f"{lat:.3f}, {lon:.3f}"

# ───────── 1️⃣ MAP SELECTION ─────────
st.title("📍 Select Your Exact Location")

# Build map centred roughly on Kurdistan; zoom so user can scroll/pan
m = folium.Map(location=[36.2, 44.0], zoom_start=6, height=400)
if state.latlon:
    folium.Marker(state.latlon, tooltip=state.loc_name or "Chosen location").add_to(m)

out = st_folium(m, height=400, use_container_width=True)

# Handle click
if out and out.get("last_clicked"):
    lat = out["last_clicked"]["lat"]
    lon = out["last_clicked"]["lng"]
    # Only update if user clicked a new spot
    if state.latlon != (lat, lon):
        state.latlon = (lat, lon)
        state.loc_name = reverse_geocode(lat, lon)
        st.toast(f"Location set: {state.loc_name}", icon="📍")

if state.latlon:
    st.success(f"Location: {state.loc_name}  (lat {state.latlon[0]:.4f}, lon {state.latlon[1]:.4f})")
else:
    st.info("Click on the map to set your exact location.")

# ───────── 2️⃣ FEELING BUTTONS ─────────
st.markdown("#### 😊 How do you feel about the weather right now?")
feels = ["😃 Good", "😐 Neutral", "☹️ Uncomfortable", "😫 Bad"]
cols = st.columns(len(feels))
for i, label in enumerate(feels):
    sel = state.feeling == label
    if cols[i].button(label, key=f"feel_{i}", type="primary" if sel else "secondary"):
        state.feeling = label
if state.feeling:
    st.success(f"Selected feeling: {state.feeling}")

# ───────── 3️⃣ ISSUES TOGGLE BUTTONS ─────────
st.markdown("#### 🌪️ What's bothering you now? (toggle)")
issues_all = [
    "🔥 High Temperature", "🌪️ Dust", "💨 Wind", "🏭 Air Pollution",
    "💧 Humidity", "☀️ UV", "⚡️ Thunderstorms", "🌧️ Rain", "❄️ Cold", "🌫️ Fog"
]
icol = st.columns(2)
for i, issue in enumerate(issues_all):
    picked = issue in state.issues
    label  = ("✅ " if picked else "☐ ") + issue
    if icol[i % 2].button(label, key=f"issue_{i}", type="primary" if picked else "secondary"):
        state.issues.discard(issue) if picked else state.issues.add(issue)
if state.issues:
    st.info("Issues: " + ", ".join(sorted(state.issues)))

# ───────── 4️⃣ SUBMIT ─────────
ready = state.latlon and state.feeling
if st.button("🚀 Submit Response", type="primary", disabled=not ready):
    payload = {
        "Timestamp": dt.datetime.now().isoformat(),
        "User": user.email,
        "Location": state.loc_name,
        "Lat": state.latlon[0],
        "Lon": state.latlon[1],
        "Feeling": state.feeling,
        "Issues": ", ".join(sorted(state.issues)),
    }
    # TODO: store payload (DB / spreadsheet / etc.)
    st.success("Thank you! Your response was recorded.")
    st.json(payload)

st.markdown("---")
st.caption("© 2025 Cool Assistant • Kurdistan Region")
