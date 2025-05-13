# app.py · Cool Assistant — Button-Only Weather Feeling Survey
import datetime as dt
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

# ───────── SESSION STATE ─────────
if "feeling" not in st.session_state:
    st.session_state.feeling = None         # str
if "issues" not in st.session_state:
    st.session_state.issues = set()         # set[str]

# ───────── SURVEY UI ─────────
st.title("🌡️ How do you feel about the weather right now?")

# 1) Location
location = st.text_input("📍 Location (city / area)")

# 2) Feeling buttons
st.markdown("### 1. Select your overall feeling")
feelings = ["😃 Good", "😐 Neutral", "☹️ Uncomfortable", "😫 Bad"]
cols = st.columns(len(feelings))
for i, label in enumerate(feelings):
    selected = st.session_state.feeling == label
    if cols[i].button(
        label,
        key=f"feel_{i}",
        type="primary" if selected else "secondary",
    ):
        st.session_state.feeling = label

if st.session_state.feeling:
    st.success(f"Selected feeling: **{st.session_state.feeling}**")

# 3) Issue toggle buttons
st.markdown("### 2. What’s bothering you? *(tap to toggle)*")
issues_list = [
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
for i, issue in enumerate(issues_list):
    selected = issue in st.session_state.issues
    pressed = issue_cols[i % 2].button(
        ("✅ " if selected else "☐ ") + issue,
        key=f"issue_{i}",
        type="primary" if selected else "secondary",
    )
    if pressed:  # toggle state
        if selected:
            st.session_state.issues.remove(issue)
        else:
            st.session_state.issues.add(issue)

if st.session_state.issues:
    st.info("Selected issues: " + ", ".join(sorted(st.session_state.issues)))

# 4) Submit
ready = location.strip() and st.session_state.feeling
if st.button("🚀 Submit Response", type="primary", disabled=not ready):
    response = {
        "Timestamp": dt.datetime.now().isoformat(),
        "User": user.email,
        "Location": location.strip(),
        "Feeling": st.session_state.feeling,
        "Issues": ", ".join(sorted(st.session_state.issues)),
    }
    # TODO: send `response` to your database / sheet
    st.success("Thank you! Your feedback was recorded.")
    st.json(response)

# ───────── FOOTER ─────────
st.markdown("---")
st.caption("© 2025 Cool Assistant • Kurdistan Region")
