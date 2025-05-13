# app.py · Cool Assistant — GPS-based Weather-Feeling Survey
import datetime as dt
import importlib
import requests
import streamlit as st
from auth import handle_authentication

# ───────── BASIC CONFIG ─────────
st.set_page_config(page_title="Cool Assistant Survey", layout="centered")

# ───────── AUTH ─────────
handle_authentication()
user = st.experimental_user

# ───────── TRY to import streamlit-geolocation ─────────
def _dummy_geo():
    return {}          # empty dict if component missing

try:
    geo_mod = importlib.import_module("streamlit_geolocation")
    geolocation = getattr(geo_mod, "geolocation", _dummy_geo)
except ModuleNotFoundError:
    geolocation = _dummy_geo   # graceful fallback

# ───────── SESSION STATE ─────────
state = st.session_state
state.setdefault("location", "")
state.setdefault("feeling", None)
state.setdefault("issues", set())

# ───────── HELPERS ─────────
def reverse_geocode(lat: float, lon: float) -> str | None:
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&zoom=10&format=json"
    try:
        r = requests.get(url, timeout=4, headers={"User-Agent": "coolassistant"})
        addr = r.json().get("address", {})
        city = addr.get("city") or addr.get("town") or addr.get("village") or ""
        region = addr.get("state", "")
        country = addr.get("country", "")
        name = ", ".join(p for p in (city, region, country) if p)
        return name or f"{lat:.3f}, {lon:.3f}"
    except Exception:
        return f"{lat:.3f}, {lon:.3f}"

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

# ───────── MAIN PAGE ─────────
st.title("🌡️ Weather Feeling Survey")

# 1️⃣  Location section
st.markdown("#### 1. Where are you?")
geo = geolocation()               # This triggers browser prompt once
if geo and geo.get("lat") and not state.location:
    state.location = reverse_geocode(geo["lat"], geo["lng"])
    st.toast(f"Detected: {state.location}", icon="📍")

state.location = st.text_input("Location", value=state.location)

if not state.location:
    st.info("Tip: allow location permission or type your city / area.")

# 2️⃣  Feeling buttons
st.markdown("#### 2. Your overall feeling")
feel_labels = ["😃 Good", "😐 Neutral", "☹️ Uncomfortable", "😫 Bad"]
fcols = st.columns(len(feel_labels))
for i, lab in enumerate(feel_labels):
    sel = state.feeling == lab
    if fcols[i].button(lab, key=f"feel_{i}", type="primary" if sel else "secondary"):
        state.feeling = lab
if state.feeling:
    st.success(f"Feeling: {state.feeling}")

# 3️⃣  Issue toggles
st.markdown("#### 3. What’s bothering you? (toggle as needed)")
issues_all = [
    "🔥 High Temperature", "🌪️ Dust", "💨 Wind", "🏭 Air Pollution",
    "💧 Humidity", "☀️ UV", "⚡️ Storms", "🌧️ Rain", "❄️ Cold", "🌫️ Fog"
]
icol = st.columns(2)
for i, issue in enumerate(issues_all):
    chosen = issue in state.issues
    btn_label = ("✅ " if chosen else "☐ ") + issue
    if icol[i % 2].button(btn_label, key=f"issue_{i}", type="primary" if chosen else "secondary"):
        state.issues.discard(issue) if chosen else state.issues.add(issue)
if state.issues:
    st.info("Selected issues: " + ", ".join(sorted(state.issues)))

# 4️⃣  Submit button
ready = bool(state.location.strip()) and state.feeling
if st.button("🚀 Submit", type="primary", disabled=not ready):
    payload = {
        "Timestamp": dt.datetime.now().isoformat(),
        "User": user.email,
        "Location": state.location.strip(),
        "Feeling": state.feeling,
        "Issues": ", ".join(sorted(state.issues)),
    }
    # TODO: save payload somewhere (DB, sheet…)
    st.success("Thanks! Your feedback was recorded.")
    st.json(payload)

st.markdown("---")
st.caption("© 2025 Cool Assistant • Kurdistan Region")
