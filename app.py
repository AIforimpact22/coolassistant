# app.py – Cool Assistant • map-first home, DB, hourly clean, share links
import datetime as dt, urllib.parse, psycopg2, streamlit as st
from auth import handle_authentication

import map, survey, contribution, about

PG_URL = ("postgresql://cool_owner:npg_jpi5LdZUbvw1@"
          "ep-frosty-tooth-a283lla4-pooler.eu-central-1.aws.neon.tech/"
          "cool?sslmode=require")
TABLE   = "survey_responses"
APP_URL = "https://coolassistant.streamlit.app"   # public link to share
# ───────────────── DB helpers ─────────────────
def ensure_table():
    with psycopg2.connect(PG_URL) as con, con.cursor() as cur:
        cur.execute(f"""CREATE TABLE IF NOT EXISTS {TABLE}(
            ts TIMESTAMPTZ,
            user_email TEXT,
            lat DOUBLE PRECISION,
            lon DOUBLE PRECISION,
            feeling TEXT,
            issues TEXT);""")

def save_row(row: dict):
    ensure_table()
    with psycopg2.connect(PG_URL) as con, con.cursor() as cur:
        cur.execute(
            f"""INSERT INTO {TABLE}
                 (ts,user_email,lat,lon,feeling,issues)
               VALUES (%(ts)s,%(user)s,%(lat)s,%(lon)s,
                       %(feeling)s,%(issues)s);""", row)
    st.toast("✅ تۆمار کرا")

@st.cache_data(ttl=3600, show_spinner=False)
def auto_clean():
    ensure_table()
    with psycopg2.connect(PG_URL) as con, con.cursor() as cur:
        cur.execute(f"""
WITH dup AS (
  SELECT ctid
  FROM (
      SELECT ctid,
             ts - LAG(ts) OVER (PARTITION BY user_email ORDER BY ts) AS diff
      FROM {TABLE}
  ) q
  WHERE diff IS NOT NULL AND diff < INTERVAL '24 hours'
)
DELETE FROM {TABLE} WHERE ctid IN (SELECT ctid FROM dup);""")
        con.commit()
auto_clean()
# ───────────────── Streamlit shell ─────────────────
st.set_page_config("Cool Assistant", layout="centered")
handle_authentication()
user = st.experimental_user
# ───────────────── Sidebar ─────────────────
st.sidebar.image(
    "https://raw.githubusercontent.com/AIforimpact22/coolassistant/main/input/cool_logo.png",
    width=180,
)

# Map first, then survey, history, about
PAGES = [("🗺️ نەخشەکەم",  "map"),
         ("📝 هەستەکەم",  "survey"),
         ("📊 مێژووم",    "history"),
         ("ℹ️ دەربارە",   "about")]

if "page" not in st.session_state:
    st.session_state.page = "map"          # default is map now

for label, key in PAGES:
    if st.sidebar.button(label,
                         type="primary" if st.session_state.page == key else "secondary"):
        st.session_state.page = key

st.sidebar.markdown("---")
st.sidebar.write("👤", user.email)
st.sidebar.button("دەرچوون", on_click=st.logout)

# Share section
st.sidebar.markdown("---")
st.sidebar.subheader("📤 هاوبەشکردن")

mailto = ("mailto:?subject=Cool%20Assistant&body=" +
          urllib.parse.quote(f"سڵاو!\n\nکۆول ئاسیستەنت سەیری بکە:\n{APP_URL}"))
wa     = "https://wa.me/?text=" + urllib.parse.quote(APP_URL)

st.sidebar.markdown(f"[📧 بە ئیمەیڵ]({mailto})")
st.sidebar.markdown(f"[💬 واتسئاپ]({wa})")
st.sidebar.code(APP_URL, language="bash")

# ───────────────── Router ─────────────────
page = st.session_state.page
if page == "map":
    map.show_heatmap()
elif page == "survey":
    survey.show(save_row, user.email)
elif page == "history":
    contribution.show_history(user.email)
else:
    about.show_about()

st.markdown("---")
st.caption("© 2025 Cool Assistant • هەرێمی کوردستان")
