# app.py – Cool Assistant • survey + hourly auto-clean + heat-map
import datetime as dt, psycopg2, streamlit as st, folium
from streamlit_folium import st_folium
from auth import handle_authentication
import map         # heat-map logic lives here

PG_URL = (
    "postgresql://cool_owner:npg_jpi5LdZUbvw1@"
    "ep-frosty-tooth-a283lla4-pooler.eu-central-1.aws.neon.tech/cool?sslmode=require"
)
TABLE = "survey_responses"

# ───────── DB helpers ─────────
def ensure_table() -> None:
    with psycopg2.connect(PG_URL) as con, con.cursor() as cur:
        cur.execute(
            f"""CREATE TABLE IF NOT EXISTS {TABLE} (
                    ts TIMESTAMPTZ,
                    user_email TEXT,
                    lat DOUBLE PRECISION,
                    lon DOUBLE PRECISION,
                    feeling TEXT,
                    issues TEXT
                );"""
        )

def save_row(row: dict) -> None:
    ensure_table()
    with psycopg2.connect(PG_URL) as con, con.cursor() as cur:
        cur.execute(
            f"""INSERT INTO {TABLE}
                   (ts,user_email,lat,lon,feeling,issues)
                 VALUES (%(ts)s,%(user)s,%(lat)s,%(lon)s,
                         %(feeling)s,%(issues)s);""",
            row,
        )
    st.toast("✅ saved")

# ───────── hourly cleaner (keeps earliest row in each 24 h window) ─────────
@st.cache_data(ttl=3600, show_spinner=False)
def auto_clean() -> None:
    """Run once per hour: drop rows by same user <24 h apart (keep earliest)."""
    ensure_table()
    with psycopg2.connect(PG_URL) as con, con.cursor() as cur:
        cur.execute(f"""
WITH to_del AS (
    SELECT ctid
    FROM (
        SELECT ctid,
               ts,
               user_email,
               ts - LAG(ts) OVER (PARTITION BY user_email ORDER BY ts) AS diff
        FROM {TABLE}
    ) q
    WHERE diff IS NOT NULL AND diff < INTERVAL '24 hours'
)
DELETE FROM {TABLE}
WHERE ctid IN (SELECT ctid FROM to_del);
""")
        con.commit()

auto_clean()   # will actually run only once per hour

# ───────── Streamlit setup ─────────
st.set_page_config("Cool Assistant", layout="centered")
handle_authentication()
user = st.experimental_user
sv = st.session_state
sv.setdefault("page", "survey")
sv.setdefault("feeling", None)
sv.setdefault("issues", set())
sv.setdefault("latlon", None)

# ───────── sidebar nav ─────────
with st.sidebar:
    st.image(
        "https://raw.githubusercontent.com/AIforimpact22/coolassistant/main/input/cool_logo.png",
        width=180,
    )
    for label, key in [("📝 Survey", "survey"),
                       ("🗺️ Map", "map"),
                       ("ℹ️ About", "about")]:
        if st.button(label, type="primary" if sv.page == key else "secondary"):
            sv.page = key
    st.markdown("---")
    st.write("👤", user.email)
    st.button("Log out", on_click=st.logout)

# ═════════════ 1. Survey ═════════════
if sv.page == "survey":
    st.title("🌡️ Weather-feeling survey")
    st.markdown("#### How do you feel about the weather? (click an emoji)")
    emojis = ["😃", "😐", "☹️", "😫"]
    cols = st.columns(4)
    for i, e in enumerate(emojis):
        if cols[i].button(e, key=f"e{i}", type="primary" if sv.feeling == e else "secondary"):
            sv.feeling = e
    if sv.feeling:
        st.success(sv.feeling)

    st.markdown("#### Any weather issue bothering you? (optional)")
    issues_all = ["🔥 Heat", "🌪️ Dust", "💨 Wind", "🏭 Air pollution", "💧 Humidity",
                  "☀️ Sun-glare", "⚡ Storm", "🌧️ Rain", "❄️ Cold", "🌫️ Bad smell"]
    for i, iss in enumerate(issues_all):
        pick = iss in sv.issues
        if st.button(("✅ " if pick else "☐ ") + iss, key=f"iss{i}",
                     type="primary" if pick else "secondary"):
            sv.issues.discard(iss) if pick else sv.issues.add(iss)

    # location picker
    if sv.feeling:
        st.markdown("#### Click on the map to set your location")
        m = folium.Map(location=[36.2, 44.0], zoom_start=6)
        if sv.latlon:
            folium.Marker(sv.latlon).add_to(m)
        res = st_folium(m, height=380, use_container_width=True)
        if res and res.get("last_clicked"):
            sv.latlon = (res["last_clicked"]["lat"], res["last_clicked"]["lng"])
            st.toast("Location selected", icon="📍")
        if sv.latlon:
            st.success(f"{sv.latlon[0]:.3f}, {sv.latlon[1]:.3f}")

    if st.button("🚀 Submit", disabled=not (sv.feeling and sv.latlon), type="primary"):
        save_row(dict(
            ts=dt.datetime.utcnow(), user=user.email,
            lat=sv.latlon[0], lon=sv.latlon[1],
            feeling=sv.feeling, issues=", ".join(sorted(sv.issues)),
        ))
        st.success("Thanks for contributing!")
        sv.feeling, sv.issues, sv.latlon = None, set(), None
        sv.page = "map"

# ═════════════ 2. Map (heat-map) ═════════════
elif sv.page == "map":
    map.show_heatmap()

# ═════════════ 3. About ═════════════
else:
    st.title("ℹ️ About Cool Assistant")
    st.markdown(
        "Crowd-sourced weather-feeling data to help planners and public-health teams."
    )
    st.image(
        "https://raw.githubusercontent.com/AIforimpact22/coolassistant/main/input/cool_logo.png",
        width=230,
    )
    st.subheader("Contact")
    st.markdown("[hawkar.geoscience@gmail.com](mailto:hawkar.geoscience@gmail.com)")

st.markdown("---")
st.caption("© 2025 Cool Assistant • Kurdistan Region")
