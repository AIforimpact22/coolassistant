# app.py – Cool Assistant • nav + DB + hourly clean
import datetime as dt
import psycopg2, streamlit as st
from auth import handle_authentication

import survey
import map
import contribution   # “میژووم”

PG_URL = ("postgresql://cool_owner:npg_jpi5LdZUbvw1@"
          "ep-frosty-tooth-a283lla4-pooler.eu-central-1.aws.neon.tech/"
          "cool?sslmode=require")
TABLE = "survey_responses"

# ───────── DB helpers ─────────
def ensure_table():
    with psycopg2.connect(PG_URL) as con, con.cursor() as cur:
        cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE}(
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
                       %(feeling)s,%(issues)s);""",
            row)
    st.toast("✅ تۆمار کرا")

# ───────── hourly cleaner ─────────
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

# ───────── Streamlit shell ─────────
st.set_page_config("Cool Assistant", layout="centered")
handle_authentication()
user = st.experimental_user

# ───────── sidebar nav ─────────
st.sidebar.image(
    "https://raw.githubusercontent.com/AIforimpact22/coolassistant/main/input/cool_logo.png",
    width=180,
)

# label (Kurdish) , internal page-key
PAGES = [("📝 هەستەکەم",   "survey"),
         ("🗺️ نەخشەکەم",  "map"),
         ("📊 مێژووم",    "history"),
         ("ℹ️ دەربارە",   "about")]

if "page" not in st.session_state:
    st.session_state.page = "survey"

for label, key in PAGES:
    if st.sidebar.button(label,
                         type="primary" if st.session_state.page == key else "secondary"):
        st.session_state.page = key

st.sidebar.markdown("---")
st.sidebar.write("👤", user.email)
st.sidebar.button("دەرچوون", on_click=st.logout)

page = st.session_state.page

# ───────── router ─────────
if page == "survey":
    survey.show(save_row, user.email)

elif page == "map":
    map.show_heatmap()

elif page == "history":
    contribution.show_history(user.email)

else:   # about
    st.title("ℹ️ دەربارەی Cool Assistant")
    st.markdown("داتای هەست و کێشەی خەڵک لە کەشوهەوا کۆدەکات بۆ یارمەتیدانی پلانسازی و تەندروستی.")
    st.image(
        "https://raw.githubusercontent.com/AIforimpact22/coolassistant/main/input/cool_logo.png",
        width=230,
    )
    st.subheader("پەیوەندی")
    st.markdown("[hawkar.geoscience@gmail.com](mailto:hawkar.geoscience@gmail.com)")

st.markdown("---")
st.caption("© 2025 Cool Assistant • هەرێمی کوردستان")
