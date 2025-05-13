# app.py – Cool Assistant (Survey + About in one file)
import datetime as dt
import requests
import psycopg2
import streamlit as st
import folium
from streamlit_folium import st_folium
from auth import handle_authentication

# ───────── DATABASE CONFIG ─────────
PG_URL = (
    "postgresql://cool_owner:npg_jpi5LdZUbvw1@"
    "ep-frosty-tooth-a283lla4-pooler.eu-central-1.aws.neon.tech/cool?sslmode=require"
)
TABLE = "survey_responses"


def save_to_db(row: dict):
    create = f"""CREATE TABLE IF NOT EXISTS {TABLE}(
        ts TIMESTAMPTZ,
        user_email TEXT,
        location TEXT,
        lat DOUBLE PRECISION,
        lon DOUBLE PRECISION,
        feeling TEXT,
        issues TEXT
    );"""
    insert = f"""INSERT INTO {TABLE}
        (ts,user_email,location,lat,lon,feeling,issues)
        VALUES (%(ts)s,%(user)s,%(location)s,%(lat)s,%(lon)s,%(feeling)s,%(issues)s);"""
    try:
        with psycopg2.connect(PG_URL) as conn:
            with conn.cursor() as cur:
                cur.execute(create)
                cur.execute(insert, row)
        st.toast("Saved to database ✅")
    except Exception as e:
        st.error(f"Database error: {e}")


# ───────── STREAMLIT CONFIG ─────────
st.set_page_config(page_title="Cool Assistant", layout="centered")
handle_authentication()
user = st.experimental_user

# ───────── SIDEBAR NAVIGATION ─────────
with st.sidebar:
    st.image(
        "https://github.com/AIforimpact22/coolassistant/blob/main/input/cool_logo.png?raw=true",
        width=180,
    )
    if "page" not in st.session_state:
        st.session_state.page = "survey"

    # Navigation buttons
    if st.button("📝 Survey", type="primary" if st.session_state.page == "survey" else "secondary"):
        st.session_state.page = "survey"
    if st.button("ℹ️ About", type="primary" if st.session_state.page == "about" else "secondary"):
        st.session_state.page = "about"

    st.markdown("---")
    st.subheader("Account")
    st.write(user.email)
    st.button("Log out", on_click=st.logout)

# ───────── COMMON HELPERS ─────────
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

# ───────── SURVEY SESSION VARS ─────────
survey = st.session_state
survey.setdefault("feeling", None)
survey.setdefault("issues", set())
survey.setdefault("latlon", None)
survey.setdefault("loc_name", "")

# =============================================================================
#                                SURVEY PAGE
# =============================================================================
if st.session_state.page == "survey":
    st.title("🌡️ Weather Feeling Survey")

    # 1 Feeling
    st.markdown("### 1. How do you feel about the weather right now?")
    feelings = ["😃 Good", "😐 Neutral", "☹️ Uncomfortable", "😫 Bad"]
    fcols = st.columns(len(feelings))
    for i, lab in enumerate(feelings):
        sel = survey.feeling == lab
        if fcols[i].button(lab, key=f"feel_{i}", type="primary" if sel else "secondary"):
            survey.feeling = lab
    if survey.feeling:
        st.success(f"Feeling: **{survey.feeling}**")

    # 2 Issues
    st.markdown("### 2. What's bothering you? (toggle)")
    all_iss = ["🔥 Heat","🌪️ Dust","💨 Wind","🏭 Pollution","💧 Humidity",
               "☀️ UV","⚡ Storms","🌧️ Rain","❄️ Cold","🌫️ Fog"]
    icol = st.columns(2)
    for i, iss in enumerate(all_iss):
        pick = iss in survey.issues
        lab = ("✅ " if pick else "☐ ") + iss
        if icol[i%2].button(lab, key=f"iss_{i}", type="primary" if pick else "secondary"):
            survey.issues.discard(iss) if pick else survey.issues.add(iss)
    if survey.issues:
        st.info("Issues: " + ", ".join(sorted(survey.issues)))

    # 3 Map (after feeling chosen)
    if survey.feeling:
        st.markdown("### 3. Click map to set exact location")
        fmap = folium.Map(location=[36.2, 44.0], zoom_start=6)
        if survey.latlon:
            folium.Marker(survey.latlon, tooltip=survey.loc_name).add_to(fmap)
        res = st_folium(fmap, height=380, use_container_width=True)
        if res and res.get("last_clicked"):
            lat, lon = res["last_clicked"]["lat"], res["last_clicked"]["lng"]
            if survey.latlon != (lat, lon):
                survey.latlon = (lat, lon)
                survey.loc_name = reverse_geocode(lat, lon)
                st.toast(f"Location set: {survey.loc_name}", icon="📍")
        if survey.latlon:
            st.success(f"Location: {survey.loc_name}")

    # Submit
    ready = survey.feeling and survey.latlon
    if st.button("🚀 Submit", disabled=not ready, type="primary"):
        row = {
            "ts": dt.datetime.utcnow(),
            "user": user.email,
            "location": survey.loc_name,
            "lat": survey.latlon[0],
            "lon": survey.latlon[1],
            "feeling": survey.feeling,
            "issues": ", ".join(sorted(survey.issues)),
        }
        save_to_db(row)
        st.success("🎉 Thank you! Your feedback was saved.")

    st.markdown("---")
    st.caption("© 2025 Cool Assistant • Kurdistan Region")

# =============================================================================
#                                ABOUT PAGE
# =============================================================================
else:
    st.title("🌍 About Cool Assistant")
    st.markdown("""
**Cool Assistant** collects real-time feedback on how weather conditions (heat, dust, humidity, etc.)
affect people. By combining these subjective reports with objective weather data
we help:

* 🌳 **Urban planners** design cooler, healthier cities  
* 🏠 **Engineers & architects** build better-adapted homes  
* 🩺 **Public-health teams** anticipate heatstroke, respiratory issues, allergies  
* 🌡️ **Communities** raise awareness and adapt to climate change
""")

    st.image("https://github.com/AIforimpact22/coolassistant/blob/main/input/cool_logo.png?raw=true", width=250)

    st.subheader("🔒 Privacy First")
    st.markdown("""
* Location is **only** what you select on the map—never guessed.  
* Data is stored securely and used only for aggregated analysis.
""")

    st.subheader("📧 Contact")
    st.markdown("[info@coolassistant.org](mailto:info@coolassistant.org)")

    st.markdown("---")
    st.caption("© 2025 Cool Assistant • Kurdistan Region")
