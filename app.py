# app.py – کۆول ئاسیستەنت • ڕاپرسی هەست بە هەوا + نەخشە + دەربارە (کوردی سۆرانی)
import datetime as dt
import requests
import psycopg2
import streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from auth import handle_authentication

# ───────── پێوستەکانى بنکەدراو ─────────
PG_URL = (
    "postgresql://cool_owner:npg_jpi5LdZUbvw1@"
    "ep-frosty-tooth-a283lla4-pooler.eu-central-1.aws.neon.tech/"
    "cool?sslmode=require"
)
TABLE = "survey_responses"


def ensure_table():
    with psycopg2.connect(PG_URL) as con:
        con.cursor().execute(
            f"""
            CREATE TABLE IF NOT EXISTS {TABLE}(
                ts TIMESTAMPTZ,
                user_email TEXT,
                location TEXT,
                lat DOUBLE PRECISION,
                lon DOUBLE PRECISION,
                feeling TEXT,
                issues TEXT
            );"""
        )


def save_row(row: dict):
    ensure_table()
    insert = f"""
        INSERT INTO {TABLE}
            (ts,user_email,location,lat,lon,feeling,issues)
        VALUES (%(ts)s,%(user)s,%(location)s,%(lat)s,%(lon)s,
                %(feeling)s,%(issues)s);"""
    try:
        with psycopg2.connect(PG_URL) as con:
            con.cursor().execute(insert, row)
        st.toast("🔒 هەڵگرت بەسەلامەتی", icon="✅")
    except Exception as e:
        st.error(f"کێشە لە بنکەدراو: {e}")


def fetch_rows(limit: int = 500):
    ensure_table()
    with psycopg2.connect(PG_URL) as con:
        cur = con.cursor()
        cur.execute(
            f"SELECT ts,location,lat,lon,feeling,issues "
            f"FROM {TABLE} ORDER BY ts DESC LIMIT %s;", (limit,)
        )
        return cur.fetchall()


# ───────── ستریم لیت و چوونەژوورەوە ─────────
st.set_page_config(page_title="کۆول ئاسیستەنت", layout="centered")
handle_authentication()
user = st.experimental_user

# ───────── نیشانەکارى لاپەرەیەکان ─────────
with st.sidebar:
    st.image(
        "https://github.com/AIforimpact22/coolassistant/blob/main/input/cool_logo.png?raw=true",
        width=180,
    )

    if "page" not in st.session_state:
        st.session_state.page = "survey"

    def nav(label, key):
        if st.button(label, type="primary" if st.session_state.page == key else "secondary"):
            st.session_state.page = key

    nav(" ڕاپرسی 📝", "survey")
    nav(" نەخشەی هەستەکان 🗺️", "map")
    nav(" دەربارە ℹ️", "about")

    st.markdown("---")
    st.subheader("هەژماری بەکارهێنەر")
    st.write(user.email)
    st.button("دەرچوون", on_click=st.logout)

# ───────── هەلبژاردنە سەرەکییەکان ─────────
sv = st.session_state
sv.setdefault("feeling", None)
sv.setdefault("issues", set())
sv.setdefault("latlon", None)
sv.setdefault("loc_name", "")

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

# =============================================================================
#                                ڕاپرسی
# =============================================================================
if sv.page == "survey":
    st.title(" ڕاپرسی هەست بە کەشوهەوا 🌡️")

    # 1 - هەست
    st.markdown("### ١. هەستت لەگەڵ هەوای ئێستا چۆنە؟")
    feelings = ["😃 باشم", "😐 ئاسایی", "☹️ خۆشم نیە", "😫 زۆر باشم"]
    fcols = st.columns(len(feelings))
    for i, lab in enumerate(feelings):
        if fcols[i].button(lab, key=f"feel_{i}", type="primary" if sv.feeling == lab else "secondary"):
            sv.feeling = lab
    if sv.feeling:
        st.success(f"هەستت هەڵبژێردرا: {sv.feeling}")

    # 2 - کێشەکان
    st.markdown("### ٢. کامە کێشەی کەشوهەوا تۆ نیگەران دەکات؟ (زیاتر لە یەك دانە دەتوانی هەڵبژێری)")
    issues_all = [
        "🔥 گەرمای زۆر", "🌪️ خۆڵبارین", "💨 با", "🏭 پیسبوونی هەوا",
        "💧 شێداری", "☀️ تیشکی خوَر", "⚡  بروسك ",
        "🌧️ باران", "❄️ ساردی", "🌫️ تەمە"
    ]
    icol = st.columns(2)
    for i, iss in enumerate(issues_all):
        picked = iss in sv.issues
        lab = ("✅ " if picked else "☐ ") + iss
        if icol[i % 2].button(lab, key=f"iss_{i}", type="primary" if picked else "secondary"):
            sv.issues.discard(iss) if picked else sv.issues.add(iss)
    if sv.issues:
        st.info("کێشە هەڵبژێردراوەکان: " + ", ".join(sorted(sv.issues)))

    # 3 - نەخشە (پاش هەست)
    if sv.feeling:
        st.markdown("### ٣. لە نەخشە کلیک بکە بۆ دیاریکردنی شوێنەکەت")
        fmap = folium.Map(location=[36.2, 44.0], zoom_start=6)
        if sv.latlon:
            folium.Marker(sv.latlon, tooltip=sv.loc_name).add_to(fmap)
        out = st_folium(fmap, height=380, use_container_width=True)
        if out and out.get("last_clicked"):
            lat, lon = out["last_clicked"]["lat"], out["last_clicked"]["lng"]
            if sv.latlon != (lat, lon):
                sv.latlon = (lat, lon)
                sv.loc_name = reverse_geocode(lat, lon)
                st.toast(f"شوێن هەڵبژێردرا: {sv.loc_name}", icon="📍")
        if sv.latlon:
            st.success(f"شوێن: {sv.loc_name}")

    # 4 - ناردن
    ready = sv.feeling and sv.latlon
    if st.button("🚀 ناردنی وەڵام", disabled=not ready, type="primary"):
        row = {
            "ts": dt.datetime.utcnow(),
            "user": user.email,
            "location": sv.loc_name,
            "lat": sv.latlon[0],
            "lon": sv.latlon[1],
            "feeling": sv.feeling,
            "issues": ", ".join(sorted(sv.issues)),
        }
        save_row(row)
        st.success("سپاس! وەڵامت تۆمار کرا.")
        sv.feeling, sv.issues, sv.latlon, sv.loc_name = None, set(), None, ""

    st.markdown("---")
    st.caption("© 2025 Cool Assistant • هەرێمی کوردستان")

# =============================================================================
#                                نەخشەى هەست
# =============================================================================
elif sv.page == "map":
    st.title("🗺️ نەخشەی هەستەکان (ڕوونووسی بەکارهێنەران)")

    data = fetch_rows()
    if not data:
        st.info("هێشتا وەڵام نییە؛ تکایە لە بابەتی ڕاپرسی وەڵام بدە.")
    else:
        colrs = {"😃 باشم": "green", "😐 ئاسایی": "blue",
                 "☹️ خۆشم نیە": "orange", "😫 زۆر کێشم": "red"}
        mm = folium.Map(location=[36.2, 44.0], zoom_start=6)
        clust = MarkerCluster().add_to(mm)
        for ts, loc, lat, lon, feel, iss in data:
            folium.CircleMarker(
                location=[lat, lon],
                radius=6,
                color=colrs.get(feel, "gray"),
                fill=True,
                fill_color=colrs.get(feel, "gray"),
                fill_opacity=0.8,
                tooltip=f"{loc}\n{feel}\n{iss}"
            ).add_to(clust)
        st_folium(mm, height=550, use_container_width=True)

    st.markdown("---")
    st.caption("© 2025 Cool Assistant • هەرێمی کوردستان")

# =============================================================================
#                                دەربارە
# =============================================================================
else:
    st.title("ℹ️ دەربارەی Cool Assistant")
    st.markdown("""
**کۆول ئاسیستەنت** هەست و وەکۆڵەی بەکارهێنەران دەکۆمەڵێت بۆ ئەوەی زانین
هەوا چۆن کاریگەرییان لەسەر تندرستی و ئەرەقی خەڵک دەکات.

### بۆچی گرنگە؟
* 🌳 شاری سارد و ساغ بەهێنرێت  
* 🏠 ماڵ و بینای گونجاو بۆ هەوا دروست بکرێت  
* 🩺 ئامادەکردنی خزمەتگوزاری تەندروستی بەر لە هه‌تاوی زۆر یان خەسوولە  
* 🌡️ ئاگاداری و هەست بەرز بکرێت بۆ گۆڕانکاری گەورەی ئاوارە

### پاراستنی نهێنی
* شوێن بە تیکردنی خۆت دیاریدەکەیت؛ هیچ ژمارەی IP یان GPS بە تۇڕە نەهەڵگریت.  
* زانیاریەکان تەنها بۆ توێژینەوەی گشتی بەکار دەهێنرێن.
""")
    st.image(
        "https://github.com/AIforimpact22/coolassistant/blob/main/input/cool_logo.png?raw=true",
        width=260,
    )
    st.subheader("پەیوەندی")
    st.markdown("[hawkar.geoscience@gmail.com](mailto:hawkar.geoscience@gmail.com)")
    st.markdown("---")
    st.caption("© 2025 Cool Assistant • هەرێمی کوردستان")
