# app.py · Cool Assistant — Accurate Browser GPS Survey
import datetime as dt
import requests
import streamlit as st
from auth import handle_authentication

# ───────── CONFIG ─────────
st.set_page_config(page_title="Cool Assistant Survey", layout="centered")

# ───────── AUTHENTICATION ─────────
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
state.setdefault("location", "")
state.setdefault("latlon", None)
state.setdefault("feeling", None)
state.setdefault("issues", set())

# ───────── JAVASCRIPT GEOLOCATION INJECTION ─────────
def get_browser_location():
    js_code = """
    <script>
    function sendLocation(pos) {
        const lat = pos.coords.latitude.toFixed(6);
        const lon = pos.coords.longitude.toFixed(6);
        const coords = {lat, lon};
        const input = window.parent.document.querySelector('input[data-testid="stSessionState-hidden"]');
        if (input) {
            input.value = JSON.stringify(coords);
            input.dispatchEvent(new Event("input", {bubbles: true}));
        }
    }
    function noLocation(err) { console.warn('ERROR(' + err.code + '): ' + err.message); }
    navigator.geolocation.getCurrentPosition(sendLocation, noLocation);
    </script>
    """
    placeholder = st.empty()
    placeholder.markdown(js_code, unsafe_allow_html=True)
    coords = st.text_input("hidden", "", key="hidden", label_visibility="collapsed")
    if coords:
        return eval(coords)
    return None

# ───────── REVERSE GEOCODING ─────────
def reverse_geocode(lat, lon):
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
    try:
        r = requests.get(url, timeout=5, headers={"User-Agent": "coolassistant"}).json()
        addr = r.get("address", {})
        city = addr.get("city") or addr.get("town") or addr.get("village", "")
        region = addr.get("state", "")
        country = addr.get("country", "")
        name = ", ".join(p for p in [city, region, country] if p)
        return name or f"{lat:.3f}, {lon:.3f}"
    except:
        return f"{lat:.3f}, {lon:.3f}"

# ───────── SURVEY PAGE ─────────
st.title("🌡️ Weather Feeling Survey")

# 1️⃣ LOCATION AUTO-FILL
st.markdown("#### 📍 Your Location")
if not state.location:
    location_data = get_browser_location()
    if location_data:
        lat, lon = location_data['lat'], location_data['lon']
        state.latlon = (lat, lon)
        state.location = reverse_geocode(lat, lon)
        st.toast(f"Detected location: {state.location}", icon="📍")

state.location = st.text_input("Location", value=state.location, key="location_manual")

if not state.location:
    st.info("Please allow location access or enter manually.")

# 2️⃣ FEELING BUTTONS
st.markdown("#### 😊 How do you feel right now?")
feelings = ["😃 Good", "😐 Neutral", "☹️ Uncomfortable", "😫 Bad"]
cols = st.columns(len(feelings))
for i, f in enumerate(feelings):
    selected = state.feeling == f
    if cols[i].button(f, key=f"feel_{i}", type="primary" if selected else "secondary"):
        state.feeling = f
if state.feeling:
    st.success(f"Selected: {state.feeling}")

# 3️⃣ ISSUES TOGGLE
st.markdown("#### 🌪️ What’s bothering you?")
issues = ["🔥 Heat", "🌪️ Dust", "💨 Wind", "🏭 Pollution", "💧 Humidity",
          "☀️ UV", "⚡ Storms", "🌧️ Rain", "❄️ Cold", "🌫️ Fog"]
icol = st.columns(2)
for i, issue in enumerate(issues):
    picked = issue in state.issues
    label = ("✅ " if picked else "☐ ") + issue
    if icol[i % 2].button(label, key=f"issue_{i}", type="primary" if picked else "secondary"):
        state.issues.discard(issue) if picked else state.issues.add(issue)
if state.issues:
    st.info("Issues: " + ", ".join(state.issues))

# 4️⃣ SUBMIT BUTTON
ready = bool(state.location.strip()) and state.feeling
if st.button("🚀 Submit Response", type="primary", disabled=not ready):
    response = {
        "Timestamp": dt.datetime.now().isoformat(),
        "User": user.email,
        "Location": state.location,
        "Coords": state.latlon,
        "Feeling": state.feeling,
        "Issues": ", ".join(state.issues),
    }
    # TODO: save response
    st.success("Thank you! Your feedback was recorded.")
    st.json(response)

# ───────── FOOTER ─────────
st.markdown("---")
st.caption("© 2025 Cool Assistant • Kurdistan Region")
