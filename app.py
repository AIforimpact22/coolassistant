# app.py · Cool Assistant — Auto-Location Weather-Feeling Survey
import datetime as dt
import importlib
import requests
import streamlit as st
from auth import handle_authentication

# ───────── CONFIG ─────────
st.set_page_config(page_title="Cool Assistant Survey", layout="centered")

# ───────── TRY TO IMPORT streamlit-geolocation ─────────
def _dummy_geo(): return {}
geolocation = _dummy_geo
try:
    geo_mod = importlib.import_module("streamlit_geolocation")
    # function name differs across early releases: geolocation() or get_geolocation()
    geolocation = getattr(geo_mod, "geolocation", None) or getattr(geo_mod, "get_geolocation", _dummy_geo)
except ModuleNotFoundError:
    pass  # fall back to IP lookup later

# ───────── AUTH ─────────
handle_authentication()
user = st.experimental_user

# ───────── SIDEBAR ─────────
with st.sidebar:
    st.image("https://github.com/AIforimpact22/coolassistant/blob/main/input/cool_logo.png?raw=true", width=180)
    st.markdown("---")
    st.subheader("Logged in as")
    st.write(user.email)
    st.button("Log out", on_click=st.logout)

# ───────── SESSION INIT ─────────
state = st.session_state
state.setdefault("location", "")
state.setdefault("feeling", None)
state.setdefault("issues", set())

# ───────── LOCATION HELPERS ─────────
def reverse_geocode(lat, lon):
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&zoom=10&format=json"
    try:
        data = requests.get(url, timeout=5, headers={"User-Agent": "coolassistant"}).json()
        addr = data.get("address", {})
        city = addr.get("city") or addr.get("town") or addr.get("village") or ""
        region = addr.get("state", "")
        country = addr.get("country", "")
        return ", ".join(p for p in (city, region, country) if p) or None
    except Exception:
        return None

def ip_lookup():
    try:
        data = requests.get("https://ipinfo.io/json", timeout=5).json()
        return ", ".join(p for p in (data.get("city"), data.get("region"), data.get("country")) if p) or None
    except Exception:
        return None

# ───────── AUTO-DETECT ON FIRST LOAD ─────────
if not state.location:
    geo = geolocation()
    if geo and geo.get("lat"):
        loc = reverse_geocode(geo["lat"], geo["lng"]) or f"{geo['lat']:.3f}, {geo['lng']:.3f}"
        state.location = loc
        st.toast(f"Detected by GPS: {loc}", icon="📍")
    else:
        fallback = ip_lookup()
        if fallback:
            state.location = fallback
            st.toast(f"Detected by IP: {fallback}", icon="🌐")

# ───────── UI ─────────
st.title("🌡️ Weather Feeling Survey")

# 1) Location (editable)
st.markdown("#### 1. Where are you?")
state.location = st.text_input("Location", value=state.location, key="loc_input")

# 2) Feeling buttons
st.markdown("#### 2. Your overall feeling")
feels = ["😃 Good", "😐 Neutral", "☹️ Uncomfortable", "😫 Bad"]
cols = st.columns(len(feels))
for i, lab in enumerate(feels):
    sel = state.feeling == lab
    if cols[i].button(lab, key=f"feel_{i}", type="primary" if sel else "secondary"):
        state.feeling = lab
if state.feeling:
    st.success(f"Feeling selected: {state.feeling}")

# 3) Issues toggles
st.markdown("#### 3. What's bothering you? (tap to toggle)")
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
    st.info("Selected: " + ", ".join(sorted(state.issues)))

# 4) Submit
ready = state.location.strip() and state.feeling
if st.button("🚀 Submit", type="primary", disabled=not ready):
    payload = {
        "Timestamp": dt.datetime.now().isoformat(),
        "User": user.email,
        "Location": state.location.strip(),
        "Feeling": state.feeling,
        "Issues": ", ".join(sorted(state.issues)),
    }
    # TODO: save payload
    st.success("Thank you! Your feedback is recorded.")
    st.json(payload)

st.markdown("---")
st.caption("© 2025 Cool Assistant • Kurdistan Region")
