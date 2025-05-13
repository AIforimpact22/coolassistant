# app.py · Cool Assistant — Button-Only Weather-Feeling Survey
import datetime as dt
import streamlit as st
from auth import handle_authentication

# ───────────────── CONFIG ─────────────────
st.set_page_config(page_title="Cool Assistant Survey", layout="centered")

# ───────────────── AUTH ──────────────────
handle_authentication()
user = st.experimental_user

# ───────────────── SIDEBAR ───────────────
with st.sidebar:
    st.image(
        "https://github.com/AIforimpact22/coolassistant/blob/main/input/cool_logo.png?raw=true",
        width=180,
    )
    st.markdown("---")
    st.subheader("Logged in as")
    st.write(user.email)
    st.button("Log out", on_click=st.logout)

# ───────────────── SESSION STATE ─────────
if "feeling" not in st.session_state:
    st.session_state.feeling = None          # str | None
if "issues" not in st.session_state:
    st.session_state.issues = set()          # set[str]

# ───────────────── MAIN PAGE ─────────────
st.title("🌡️ How’s the weather *right now*?")

# --- 1. location (text still easiest) ----
location = st.text_input("📍 Your Location")

st.markdown("### 2. Your overall feeling")
col1, col2, col3, col4 = st.columns(4)
feel_buttons = {
    "😃 Good": col1,
    "😐 Neutral": col2,
    "☹️ Uncomfortable": col3,
    "😫 Bad": col4,
}
for label, col in feel_buttons.items():
    if col.button(label):
        st.session_state.feeling = label

if st.session_state.feeling:
    st.success(f"Selected: **{st.session_state.feeling}**")

st.markdown("### 3. What’s bothering you? *(tap to toggle)*")
choices = [
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
# display buttons in a grid of 2 columns
cols = st.columns(2)
for i, choice in enumerate(choices):
    idx = i % 2
    selected = choice in st.session_state.issues
    style = "background-color:#4CAF50;color:white;" if selected else ""
    if cols[idx].button(choice, key=f"issue_{i}", help="click to toggle", type="secondary" if selected else "default"):
        # toggle
        if selected:
            st.session_state.issues.remove(choice)
        else:
            st.session_state.issues.add(choice)

if st.session_state.issues:
    st.info("Selected issues: " + ", ".join(st.session_state.issues))

# --- 4. submit ---------------------------
ready = location.strip() and st.session_state.feeling
if st.button("✅ Submit Response", disabled=not ready):
    timestamp = dt.datetime.now().isoformat()
    response = {
        "Timestamp": timestamp,
        "User": user.email,
        "Location": location.strip(),
        "Feeling": st.session_state.feeling,
        "Issues": ", ".join(sorted(st.session_state.issues)),
    }
    # TODO: persist `response` to a database / sheet
    st.success("Thank you! Your feedback was recorded.")
    st.json(response)

# footnote
st.markdown("---")
st.caption("© 2025 Cool Assistant • Kurdistan Region")
