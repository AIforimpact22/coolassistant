# app.py · Cool Assistant — Auto-Location Weather Feeling Survey
import datetime as dt
import requests
import streamlit as st
from streamlit_geolocation import geolocation         # <-- new helper
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

# ───────── SESSION INIT ─────────
state = st.session_state
state.setdefault("location", "")
state.setdefault("feeling", None)
state.setdefault("issues", set())

# ───────── LOCATION AUTO-DETECT ─────────
def reverse_geocode(lat: float, lon: float) -> str | None:
    """Return 'City, Region, Country' string or None."""
    url = (
        "https://nominatim.openstreetmap.org/reverse"
        f"?lat={lat}&lon={lon}&zoom=10&format=json"
    )
    try:
        data = requests.get(url, timeout=5, headers={"User-Agent": "coolassistant"}).json()
        components = data.get("address", {})
        city = components.get("city") or components.get("town") or components.get("village") or ""
        region = components.get("state", "")
        country = components.get("country", "")
        name = ", ".join(p for p in (city, region, country) if p)
        return name or None
    except Exception:
        return None

def ip_lookup() -> str | None:
    try:
        data = requests.get("https://ipinfo.io/json", timeout=5).json()
        return ", ".join(p for p in (data.get("city"), data.get("region"), data.get("country")) if p) or None
    except Exception:
        return None

# ↓ Ask browser for coordinates (prompts user once)
geo = geolocation()
if geo and geo.get("lat") and not state.location:
    loc_name = reverse_geocode(geo["lat"], geo["lng"]) or f"{geo['lat']:.3f}, {geo['lng']:.3f}"
    state.location = loc_name
elif not state.location:                              # fallback
    fallback = ip_lookup()
    if fallback:
        state.location = fallback

# ───────── UI ─────────
st.title("🌡️ Weather Feeling Survey")

# 1) Location (auto-filled but editable)
st.markdown("#### 1. Where are you?")
state.location = st.text_input("Location", value=state.location, key="loc_input")

# 2) Feeling buttons
st.markdown("#### 2. Overall feeling")
feelings = ["😃 Good", "😐 Neutral", "☹️ Uncomfortable", "😫 Bad"]
fcols = st.columns(len(feelings))
for i, lab in enumerate(feelings):
    sel = state.feeling == lab
    if fcols[i].button(lab, key=f"feel_{i}", type="primary" if sel else "secondary"):
        state.feeling = lab
if state.feeling:
    st.success(f"Feeling selected: **{state.feeling}**")

# 3) Issue toggles
st.markdown("#### 3. What’s bothering you? (tap to toggle)")
issues_all = [
    "🔥 High Temperature", "🌪️ Dust", "💨 Wind", "🏭 Air Pollution",
    "💧 Humidity", "☀️ UV", "⚡️ Thunderstorms", "🌧️ Rain", "❄️ Cold", "🌫️ Fog",
]
icols = st.columns(2)
for i, issue in enumerate(issues_all):
    picked = issue in state.issues
    label  = ("✅ " if picked else "☐ ") + issue
    if icols[i % 2].button(label, key=f"issue_{i}", type="primary" if picked else "secondary"):
        state.issues.discard(issue) if picked else state.issues.add(issue)
if state.issues:
    st.info("Selected issues: " + ", ".join(sorted(state.issues)))

# 4) Submit
ready = state.location.strip() and state.feeling
if st.button("🚀 Submit Response", type="primary", disabled=not ready):
    record = {
        "Timestamp": dt.datetime.now().isoformat(),
        "User": user.email,
        "Location": state.location.strip(),
        "Feeling": state.feeling,
        "Issues": ", ".join(sorted(state.issues)),
    }
    # TODO: persist `record`
    st.success("Thank you! Your response has been recorded.")
    st.json(record)

# ───────── FOOTER ─────────
st.markdown("---")
st.caption("© 2025 Cool Assistant • Kurdistan Region")
