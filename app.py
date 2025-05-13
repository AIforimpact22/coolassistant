# app.py – کۆول ئاسیستەنت • ڕاپرسی هەست بە کەشوهەوا + نەخشەی هەستەکان + دەربارە
import datetime as dt
import requests, psycopg2, streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from auth import handle_authentication

# ───────── بنکەدراو ─────────
PG_URL = (
    "postgresql://cool_owner:npg_jpi5LdZUbvw1@"
    "ep-frosty-tooth-a283lla4-pooler.eu-central-1.aws.neon.tech/"
    "cool?sslmode=require"
)
TABLE = "survey_responses"


def ensure_table():
    with psycopg2.connect(PG_URL) as con:
        con.cursor().execute(
            f"""CREATE TABLE IF NOT EXISTS {TABLE}(
                 ts TIMESTAMPTZ,
                 user_email TEXT,
                 location TEXT,
                 lat DOUBLE PRECISION,
                 lon DOUBLE PRECISION,
                 feeling TEXT,
                 issues TEXT);"""
        )


def save_row(row: dict):
    ensure_table()
    with psycopg2.connect(PG_URL) as con:
        con.cursor().execute(
            f"""INSERT INTO {TABLE}
                (ts,user_email,location,lat,lon,feeling,issues)
                VALUES (%(ts)s,%(user)s,%(location)s,%(lat)s,%(lon)s,
                        %(feeling)s,%(issues)s);""",
            row,
        )
    st.toast("✅ وەڵامەکەت تۆمار کرا")


def fetch_rows(limit: int = 500):
    ensure_table()
    with psycopg2.connect(PG_URL) as con:
        cur = con.cursor()
        cur.execute(
            f"""SELECT ts,location,lat,lon,feeling,issues
                FROM {TABLE}
                ORDER BY ts DESC LIMIT %s;""",
            (limit,),
        )
        return cur.fetchall()


# ───────── ستریم‌لیت ─────────
st.set_page_config("کۆول ئاسیستەنت", layout="centered")
handle_authentication()
user = st.experimental_user

# ───────── نیشانەکارى لاپەرەکان ─────────
with st.sidebar:
    st.image(
        "https://github.com/AIforimpact22/coolassistant/blob/main/input/cool_logo.png?raw=true",
        width=180,
    )

    if "page" not in st.session_state:
        st.session_state.page = "survey"

    def nav(txt, key):
        if st.button(txt, type="primary" if st.session_state.page == key else "secondary"):
            st.session_state.page = key

    nav("📝 ڕاپرسی", "survey")
    nav("🗺️ نەخشەی هەستەکان", "map")
    nav("ℹ️ دەربارە", "about")

    st.markdown("---")
    st.write("👤", user.email)
    st.button("دەرچوون", on_click=st.logout)

# ───────── یارمەتییەکان ─────────
def reverse_geocode(lat, lon):
    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json"
    try:
        a = requests.get(
            url, timeout=5, headers={"User-Agent": "coolassistant"}
        ).json().get("address", {})
        city = a.get("city") or a.get("town") or a.get("village") or ""
        region, country = a.get("state", ""), a.get("country", "")
        return ", ".join(x for x in (city, region, country) if x) or f"{lat:.3f},{lon:.3f}"
    except Exception:
        return f"{lat:.3f},{lon:.3f}"


# ───────── سیشن‌ستەیت ─────────
sv = st.session_state
sv.setdefault("feeling", None)
sv.setdefault("issues", set())
sv.setdefault("latlon", None)
sv.setdefault("loc_name", "")

# =============================================================================
#                              ١. ڕاپرسی
# =============================================================================
if sv.page == "survey":
    st.title("🌡️ ڕاپرسی هەست بە کەشوهەوا")

    # هەست
    st.markdown("#### ١. هەستت لەگەڵ هەوای ئێستا چۆنە؟")
    feelings = ["😃 باشم", "😐 ئاسایی", "☹️ خۆشم نیە", "😫 زۆر کێشم"]
    fcols = st.columns(4)
    for i, f in enumerate(feelings):
        if fcols[i].button(f, key=f"f{i}", type="primary" if sv.feeling == f else "secondary"):
            sv.feeling = f
    if sv.feeling:
        st.success(f"هەستت: {sv.feeling}")

    # کێشەکان
    st.markdown("#### ٢. کام کێشە هەوایەت تێدەکات؟")
    all_issues = [
        "🔥 گەرما", "🌪️ خۆڵبارین", "💨 با",
        "🏭 پیسبوونی هەوا", "💧 شێداری", "☀️ تیشکی خوَر",
        "⚡ بروسک", "🌧️ باران", "❄️ ساردی", "🌫️ تەمە"
    ]
    icol = st.columns(2)
    for i, iss in enumerate(all_issues):
        pick = iss in sv.issues
        lab = ("✅ " if pick else "☐ ") + iss
        if icol[i % 2].button(lab, key=f"is{i}", type="primary" if pick else "secondary"):
            sv.issues.discard(iss) if pick else sv.issues.add(iss)
    if sv.issues:
        st.info("کێشەکان: " + ", ".join(sorted(sv.issues)))

    # نەخشە
    if sv.feeling:
        st.markdown("#### ٣. کلیک بکە لە نەخشە بۆ دیاریکردنی شوێن")
        m = folium.Map(location=[36.2, 44.0], zoom_start=6)
        if sv.latlon:
            folium.Marker(sv.latlon, tooltip=sv.loc_name).add_to(m)
        res = st_folium(m, height=380, use_container_width=True)
        if res and res.get("last_clicked"):
            lat, lon = res["last_clicked"]["lat"], res["last_clicked"]["lng"]
            if sv.latlon != (lat, lon):
                sv.latlon = (lat, lon)
                sv.loc_name = reverse_geocode(lat, lon)
                st.toast(f"شوێن: {sv.loc_name}", icon="📍")
        if sv.latlon:
            st.success(f"شوێن دیاریکراو: {sv.loc_name}")

    # ناردن
    if st.button("🚀 ناردن", disabled=not (sv.feeling and sv.latlon), type="primary"):
        row = dict(
            ts=dt.datetime.utcnow(),
            user=user.email,
            location=sv.loc_name,
            lat=sv.latlon[0],
            lon=sv.latlon[1],
            feeling=sv.feeling,
            issues=", ".join(sorted(sv.issues)),
        )
        save_row(row)
        st.success("سپاس بۆ بەشداریکردن!")
        sv.feeling, sv.issues, sv.latlon, sv.loc_name = None, set(), None, ""

# =============================================================================
#                              ٢. نەخشەی هەستەکان
# =============================================================================
elif sv.page == "map":
    st.title("🗺️ نەخشەی هەستەکان (real-time)")

    data = fetch_rows()
    if not data:
        st.info("هێشتا هیچ وەڵامێک نییە.")
    else:
        # ڕەنگەکان و هەستەکان
        colormap = {
            "😃 باشم": "green",
            "😐 ئاسایی": "blue",
            "☹️ خۆشم نیە": "orange",
            "😫 زۆر کێشم": "red",
        }
        mp = folium.Map(location=[36.2, 44.0], zoom_start=6)
        cluster = MarkerCluster().add_to(mp)
        for ts, loc, lat, lon, feel, issues in data:
            folium.CircleMarker(
                location=[lat, lon],
                radius=6,
                color=colormap.get(feel, "gray"),
                fill=True,
                fill_color=colormap.get(feel, "gray"),
                fill_opacity=0.85,
                tooltip=f"{loc}\n{feel}\n{issues}",
            ).add_to(cluster)

        # لێژەند
        legend_html = """
        <div style="
             position: fixed; bottom: 30px; left: 30px; z-index:9999;
             background: rgba(255,255,255,0.85); padding: 6px 10px;
             border-radius:8px; font-size:14px;">
          <b>ڕەنگەکان</b><br>
          <i style='background:green;width:12px;height:12px;display:inline-block;'></i> 😃 باشم<br>
          <i style='background:blue;width:12px;height:12px;display:inline-block;'></i> 😐 ئاسایی<br>
          <i style='background:orange;width:12px;height:12px;display:inline-block;'></i> ☹️ خۆشم نیە<br>
          <i style='background:red;width:12px;height:12px;display:inline-block;'></i> 😫 زۆر کێشم
        </div>
        """
        mp.get_root().html.add_child(folium.Element(legend_html))
        st_folium(mp, height=560, use_container_width=True)

# =============================================================================
#                                   ٣. دەربارە
# =============================================================================
else:
    st.title("ℹ️ دەربارەی کۆول ئاسیستەنت")
    st.markdown("""
کۆول ئاسیستەنت هەستە بەکارهێنەران دەکۆمەڵێت بۆ بەرزکردنەوەی ئاگاداری
لەبارەی کاریگەری هەوا و چۆنیەتی چارەسەرکردنی کێشەکان.

* 🌳 یارمەتیدەدات شاره‌وانی کان شارێکی سارد و ساغ دیزاین بکەن  
* 🏠 هاوکاری دەکات بۆ دروستکردنی ماڵ و بینای گونجاو بۆ هەوا  
* 🩺 خزمەتگوزاری تەندروستی دەتوانێ مرۆڤ پاراستنی پێشبین بکات  
""")
    st.image(
        "https://github.com/AIforimpact22/coolassistant/blob/main/input/cool_logo.png?raw=true",
        width=250,
    )
    st.subheader("پەیوەندی")
    st.markdown("[hawkar.geoscience@gmail.com](mailto:hawkar.geoscience@gmail.com)")

st.markdown("---")
st.caption("© 2025 Cool Assistant • هەرێمی کوردستان")
