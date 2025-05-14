# app.py – کۆول ئاسیستەنت • ڕاپرسی هەست + Heat-Map
import datetime as dt, requests, psycopg2, streamlit as st, folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from auth import handle_authentication

PG_URL = ("postgresql://cool_owner:npg_jpi5LdZUbvw1@"
          "ep-frosty-tooth-a283lla4-pooler.eu-central-1.aws.neon.tech/cool?sslmode=require")
TABLE = "survey_responses"

# ---------- بنکەدراو ----------
def ensure_table():
    with psycopg2.connect(PG_URL) as c:
        c.cursor().execute(f"""CREATE TABLE IF NOT EXISTS {TABLE}(
          ts TIMESTAMPTZ, user_email TEXT,
          lat DOUBLE PRECISION, lon DOUBLE PRECISION,
          feeling TEXT, issues TEXT);""")

def save_row(r):
    ensure_table()
    with psycopg2.connect(PG_URL) as c:
        c.cursor().execute(
            f"""INSERT INTO {TABLE}
                (ts,user_email,lat,lon,feeling,issues)
                VALUES (%(ts)s,%(user)s,%(lat)s,%(lon)s,%(feeling)s,%(issues)s);""", r)
    st.toast("✅ تۆمار کرا")

def fetch_rows(limit=1000):
    ensure_table()
    with psycopg2.connect(PG_URL) as c:
        cur = c.cursor()
        cur.execute(f"SELECT lat,lon,feeling FROM {TABLE} ORDER BY ts DESC LIMIT %s;", (limit,))
        return cur.fetchall()

# ---------- ستریم‌لیت ----------
st.set_page_config("کۆول ئاسیستەنت", layout="centered")
handle_authentication(); user = st.experimental_user
sv = st.session_state
sv.setdefault("page", "survey"); sv.setdefault("feeling", None)
sv.setdefault("issues", set()); sv.setdefault("latlon", None)

def color_card(col, emo):
    return f"<div style='background:{col};color:#fff;width:60px;height:60px;" \
           f"display:flex;align-items:center;justify-content:center;" \
           f"border-radius:8px;font-size:28px;'>{emo}</div>"

# ---------- ناوبەری لاپەڕە ----------
with st.sidebar:
    st.image("https://raw.githubusercontent.com/AIforimpact22/coolassistant/main/input/cool_logo.png", width=180)
    for lbl, key in [("📝 ڕاپرسی", "survey"), ("🗺️ نەخشە", "map"), ("ℹ️ دەربارە", "about")]:
        if st.button(lbl, type="primary" if sv.page == key else "secondary"):
            sv.page = key
    st.markdown("---"); st.write("👤", user.email); st.button("دەرچوون", on_click=st.logout)

# ═════════════ ١. ڕاپرسی ═════════════
if sv.page == "survey":
    st.title("🌡️ ڕاپرسی هەست بە هەوا")

    st.markdown("#### ١. هەستت؟ (ئیمۆجی کلیک بکە)")
    emojis = ["😃", "😐", "☹️", "😫"]; cols = st.columns(4)
    for i, e in enumerate(emojis):
        if cols[i].button(e, key=f"emo{i}", type="primary" if sv.feeling == e else "secondary"):
            sv.feeling = e
    if sv.feeling:
        st.success(f"{sv.feeling}")

    st.markdown("#### ٢. کێشەکانی هەوا (ئارا)")
    all_iss = ["🔥 گەرما","🌪️ خۆڵبارین","💨 با","🏭 پیسبوونی هەوا","💧 شێداری",
               "☀️ تیشکی خوَر","⚡ بروسک","🌧️ باران","❄️ ساردی","🌫️ بۆنی ناخۆش"]
    for i, iss in enumerate(all_iss):
        sel = iss in sv.issues
        if st.button(("✅ " if sel else "☐ ") + iss, key=f"iss{i}",
                     type="primary" if sel else "secondary"):
            sv.issues.discard(iss) if sel else sv.issues.add(iss)

    if sv.feeling:
        st.markdown("#### ٣. لە نەخشە کلیک بکە بۆ دیاریکردنی شوێن")
        m = folium.Map(location=[36.2, 44.0], zoom_start=6)
        if sv.latlon: folium.Marker(sv.latlon).add_to(m)
        clk = st_folium(m, height=380, use_container_width=True)
        if clk and clk.get("last_clicked"):
            sv.latlon = (clk["last_clicked"]["lat"], clk["last_clicked"]["lng"])
            st.toast("شوێن دیاریکرا", icon="📍")
        if sv.latlon:
            st.success(f"lat {sv.latlon[0]:.3f}, lon {sv.latlon[1]:.3f}")

    if st.button("🚀 ناردن", disabled=not (sv.feeling and sv.latlon), type="primary"):
        save_row(dict(ts=dt.datetime.utcnow(), user=user.email,
                      lat=sv.latlon[0], lon=sv.latlon[1],
                      feeling=sv.feeling, issues=", ".join(sorted(sv.issues))))
        st.success("سوپاس بۆ بەشداریکردن!")
        sv.feeling, sv.issues, sv.latlon = None, set(), None
        sv.page = "map"

# ═════════════ ٢. Heat-Map ═════════════
elif sv.page == "map":
    st.title("🗺️ Heat-Map ی هەستەکان")
    rows = fetch_rows()
    if not rows:
        st.info("هێشتا هیچ دێتەیەک نییە.")
    else:
        weight = {"😃": 1, "😐": 0.66, "☹️": 0.33, "😫": 0}
        heat = [[lat, lon, weight.get(feel.split()[0], 0.5)] for lat, lon, feel in rows]

        # لێژەند لە سەر
        lg_cols = st.columns(4)
        for c, (col, emo) in zip(lg_cols, [("green","😃"),("blue","😐"),("orange","☹️"),("red","😫")]):
            c.markdown(color_card(col, emo), unsafe_allow_html=True)

        # نقشه
        mp = folium.Map(location=[36.2, 44.0], zoom_start=6)
        HeatMap(heat,
                gradient={"0":"red","0.33":"orange","0.66":"blue","1":"green"},
                min_opacity=0.25,max_opacity=0.9,radius=35,blur=20).add_to(mp)
        st_folium(mp, height=550, use_container_width=True)

# ═════════════ ٣. دەربارە ═════════════
else:
    st.title("ℹ️ دەربارەی کۆول ئاسیستەنت")
    st.markdown("پروجەیێک بۆ کۆکردنەوەی هەستەکانی خەڵک بە کەشوهەوا بۆ پلانسازی و پاراستنی تەندروستی.")
    st.image("https://raw.githubusercontent.com/AIforimpact22/coolassistant/main/input/cool_logo.png", width=230)
    st.subheader("پەیوەندی"); st.markdown("[hawkar.geoscience@gmail.com](mailto:hawkar.geoscience@gmail.com)")

st.markdown("---"); st.caption("© 2025 Cool Assistant • هەرێمی کوردستان")
