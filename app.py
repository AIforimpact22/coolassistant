# app.py · Cool Assistant — Accurate Nominatim Location + Button Survey
import datetime as dt
import requests
import streamlit as st
from auth import handle_authentication

# ───────── CONFIG ─────────
st.set_page_config(page_title="Cool Assistant Survey", layout="centered")
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

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

# ───────── SESSION STATE ─────────
state = st.session_state
state.setdefault("loc_query", "")
state.setdefault("loc_choices", [])   # list of dicts from Nominatim
state.setdefault("loc_choice_idx", -1)
state.setdefault("feeling", None)
state.setdefault("issues", set())

# ───────── HELPERS ─────────
def nominatim_search(query: str):
    """Return list of place dicts [{'display_name', 'lat','lon'}..]."""
    params = {"q": query, "format": "json", "limit": 5, "addressdetails": 0}
    try:
        resp = requests.get(NOMINATIM_URL, params=params, timeout=5,
                            headers={"User-Agent": "coolassistant"})
        return resp.json()
    except Exception:
        return []

# ───────── UI ─────────
st.title("🌡️ Real-Time Weather Feeling Survey")

# 1️⃣  Location search
st.markdown("#### 1. Pick your exact location")
state.loc_query = st.text_input("Start typing…", value=state.loc_query)
if len(state.loc_query) >= 3:
    state.loc_choices = nominatim_search(state.loc_query)
else:
    state.loc_choices = []

# list choices as buttons
for i, place in enumerate(state.loc_choices):
    label = place["display_name"]
    if st.button(label, key=f"loc_{i}", type="primary" if i == state.loc_choice_idx else "secondary"):
        state.loc_choice_idx = i

if state.loc_choice_idx >= 0:
    sel = state.loc_choices[state.loc_choice_idx]
    st.success(f"Chosen: **{sel['display_name']}**  "
               f"(lat {float(sel['lat']):.4f}, lon {float(sel['lon']):.4f})")

# 2️⃣  Feeling
st.markdown("#### 2. Your overall feeling")
feels = ["😃 Good", "😐 Neutral", "☹️ Uncomfortable", "😫 Bad"]
fcols = st.columns(len(feels))
for i, lab in enumerate(feels):
    if fcols[i].button(lab, key=f"feel_{i}", type="primary" if state.feeling == lab else "secondary"):
        state.feeling = lab
if state.feeling:
    st.success(f"Feeling: {state.feeling}")

# 3️⃣  Issues
st.markdown("#### 3. What’s bothering you? (toggle)")
issues_all = [
    "🔥 Heat", "🌪️ Dust", "💨 Wind", "🏭 Pollution", "💧 Humidity",
    "☀️ UV", "⚡ Storms", "🌧️ Rain", "❄️ Cold", "🌫️ Fog"
]
icol = st.columns(2)
for i, issue in enumerate(issues_all):
    picked = issue in state.issues
    label = ("✅ " if picked else "☐ ") + issue
    if icol[i % 2].button(label, key=f"issue_{i}", type="primary" if picked else "secondary"):
        state.issues.discard(issue) if picked else state.issues.add(issue)
if state.issues:
    st.info("Issues: " + ", ".join(sorted(state.issues)))

# 4️⃣  Submit
ready = state.loc_choice_idx >= 0 and state.feeling
if st.button("🚀 Submit", type="primary", disabled=not ready):
    place = state.loc_choices[state.loc_choice_idx]
    payload = {
        "Timestamp": dt.datetime.now().isoformat(),
        "User": user.email,
        "Location": place["display_name"],
        "Lat": place["lat"],
        "Lon": place["lon"],
        "Feeling": state.feeling,
        "Issues": ", ".join(sorted(state.issues)),
    }
    # TODO: store payload (database / sheet / etc.)
    st.success("Thank you! Your feedback has been recorded.")
    st.json(payload)

st.markdown("---")
st.caption("© 2025 Cool Assistant • Kurdistan Region")
