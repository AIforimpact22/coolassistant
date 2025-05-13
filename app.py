# app.py · Cool Assistant — Smart-Location Weather-Feeling Survey
import datetime as dt
import requests
import streamlit as st
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

# ───────── SESSION STATE INIT ─────────
state = st.session_state
state.setdefault("location", "")
state.setdefault("feeling", None)
state.setdefault("issues", set())

# ───────── LOCATION DETECTION ─────────
def detect_location():
    """Fill session_state.location with 'City, Region, Country' via IP."""
    try:
        data = requests.get("https://ipinfo.io/json", timeout=5).json()
        city, region, country = data.get("city", ""), data.get("region", ""), data.get("country", "")
        loc = ", ".join(p for p in (city, region, country) if p)
        if loc:
            state.location = loc
            st.toast(f"Detected location: {loc}", icon="📍")
        else:
            st.toast("Could not detect location.", icon="⚠️")
    except Exception:
        st.toast("Location detection failed.", icon="⚠️")

# ───────── SURVEY UI ─────────
st.title("🌡️ Weather Feeling Survey")

# 1) Location
st.markdown("#### 1. Where are you right now?")
loc_cols = st.columns([4, 1])
state.location = loc_cols[0].text_input("Location", value=state.location, key="loc_input")
loc_cols[1].button("Detect 📍", on_click=detect_location, type="secondary")

# 2) Feeling
st.markdown("#### 2. How do you feel about the weather?")
feel_labels = ["😃 Good", "😐 Neutral", "☹️ Uncomfortable", "😫 Bad"]
feel_cols = st.columns(len(feel_labels))
for i, label in enumerate(feel_labels):
    selected = state.feeling == label
    if feel_cols[i].button(label, key=f"feel_{i}", type="primary" if selected else "secondary"):
        state.feeling = label

if state.feeling:
    st.success(f"Selected feeling: **{state.feeling}**")

# 3) Issues
st.markdown("#### 3. What’s bothering you? (toggle)")
issue_pool = [
    "🔥 High Temperature",
    "🌪️ Dust",
    "💨 Strong Wind",
    "🏭 Air Pollution",
    "💧 Humidity",
    "☀️ UV Exposure",
    "⚡️ Thunderstorms",
    "🌧️ Rain",
    "❄️ Cold",
    "🌫️ Fog",
]
issue_cols = st.columns(2)
for i, issue in enumerate(issue_pool):
    selected = issue in state.issues
    label = ("✅ " if selected else "☐ ") + issue
    if issue_cols[i % 2].button(label, key=f"issue_{i}", type="primary" if selected else "secondary"):
        if selected:
            state.issues.remove(issue)
        else:
            state.issues.add(issue)

if state.issues:
    st.info("Selected issues: " + ", ".join(sorted(state.issues)))

# 4) Submit
ready = state.location.strip() and state.feeling
if st.button("🚀 Submit Response", type="primary", disabled=not ready):
    response = {
        "Timestamp": dt.datetime.now().isoformat(),
        "User": user.email,
        "Location": state.location.strip(),
        "Feeling": state.feeling,
        "Issues": ", ".join(sorted(state.issues)),
    }
    # TODO: save `response` to a database / sheet
    st.success("Thank you! Your feedback was recorded.")
    st.json(response)

# ───────── FOOTER ─────────
st.markdown("---")
st.caption("© 2025 Cool Assistant • Kurdistan Region")
