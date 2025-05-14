# app.py – کۆول ئاسیستەنت • ڕاپرسی هەست + نەخشە + دەربارە (ئیمۆجی تەنها)
import datetime as dt, requests, psycopg2, streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
from auth import handle_authentication

# ───────── بنکەدراو ─────────
PG_URL = ("postgresql://cool_owner:npg_jpi5LdZUbvw1@"
          "ep-frosty-tooth-a283lla4-pooler.eu-central-1.aws.neon.tech/"
          "cool?sslmode=require")
TABLE = "survey_responses"

def ensure_table():
    with psycopg2.connect(PG_URL) as con:
        con.cursor().execute(f"""CREATE TABLE IF NOT EXISTS {TABLE}(
            ts TIMESTAMPTZ,user_email TEXT,location TEXT,
            lat DOUBLE PRECISION,lon DOUBLE PRECISION,
            feeling TEXT,issues TEXT );""")

def save_row(row: dict):
    ensure_table()
    with psycopg2.connect(PG_URL) as con:
        con.cursor().execute(
            f"""INSERT INTO {TABLE}
            (ts,user_email,location,lat,lon,feeling,issues)
            VALUES (%(ts)s,%(user)s,%(location)s,%(lat)s,%(lon)s,
                    %(feeling)s,%(issues)s);""", row)
    st.toast("✅ وەڵامەکەت تۆمار کرا")

def fetch_rows(limit=500):
    ensure_table()
    with psycopg2.connect(PG_URL) as con:
        cur = con.cursor()
        cur.execute(f"""SELECT ts,location,lat,lon,feeling,issues
                        FROM {TABLE} ORDER BY ts DESC LIMIT %s;""",(limit,))
        return cur.fetchall()

# ───────── ستریملیت و سیشن ─────────
st.set_page_config("کۆول ئاسیستەنت", layout="centered")
handle_authentication(); user = st.experimental_user
sv = st.session_state
sv.setdefault("page","survey"); sv.setdefault("feeling",None)
sv.setdefault("issues",set()); sv.setdefault("latlon",None)
sv.setdefault("loc_name","")

# ───────── بەشی لاپەڕەکان ─────────
with st.sidebar:
    st.image("https://raw.githubusercontent.com/AIforimpact22/coolassistant/main/input/cool_logo.png",
             width=180)
    def nav(lbl,key):
        if st.button(lbl, type="primary" if sv.page==key else "secondary"):
            sv.page=key
    nav("📝 ڕاپرسی","survey"); nav("🗺️ نەخشەی هەست","map"); nav("ℹ️ دەربارە","about")
    st.markdown("---"); st.write("👤",user.email); st.button("دەرچوون", on_click=st.logout)

# ───────── یارمەتییەکان ─────────
def reverse_geocode(lat,lon):
    try:
        a=requests.get(
          f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json",
          timeout=5,headers={"User-Agent":"coolassistant"}).json()["address"]
        city=a.get("city") or a.get("town") or a.get("village") or ""
        return ", ".join(x for x in (city,a.get("state",""),a.get("country","")) if x) or f"{lat:.2f},{lon:.2f}"
    except: return f"{lat:.2f},{lon:.2f}"

# ═════════════ ١. ڕاپرسی ═════════════
if sv.page=="survey":
    st.title("🌡️ ڕاپرسی هەسەت بە هەوا")
    # هەست بە ئیمۆجی
    st.markdown("#### ١. هەستت لەگەڵ کەشوهەوای ئێستا چۆنە؟؟")
    emojis=["😃","😐","☹️","😫"]
    cols=st.columns(4)
    for i,e in enumerate(emojis):
        if cols[i].button(e, key=f"e{i}", type="primary" if sv.feeling==e else "secondary"):
            sv.feeling=e
    if sv.feeling: st.success(f"هەستت: {sv.feeling}")

    # کێشەکان
    st.markdown("#### ٢. کێشەکانی هەوا کە تۆ نیگارانت دەکات؟")
    issues=["🔥 گەرما","🌪️ خۆڵبارین","💨 با","🏭 پیسبوونی هەوا","💧 شێداری",
            "☀️ تیشکی خوَر","⚡ بروسک","🌧️ باران","❄️ ساردی","🌫️ تەمە"]
    icol=st.columns(2)
    for i,iss in enumerate(issues):
        sel=iss in sv.issues
        if icol[i%2].button(("✅ " if sel else "☐ ")+iss, key=f"is{i}",
                            type="primary" if sel else "secondary"):
            sv.issues.discard(iss) if sel else sv.issues.add(iss)
    if sv.issues: st.info("کێشەکان: "+", ".join(sorted(sv.issues)))

    # نەخشە
    if sv.feeling:
        st.markdown("#### ٣. شوێنت دیاری بکە")
        m=folium.Map(location=[36.2,44.0],zoom_start=6)
        if sv.latlon: folium.Marker(sv.latlon,tooltip=sv.loc_name).add_to(m)
        r=st_folium(m,height=380,use_container_width=True)
        if r and r.get("last_clicked"):
            lat,lon=r["last_clicked"]["lat"],r["last_clicked"]["lng"]
            if sv.latlon!=(lat,lon):
                sv.latlon=(lat,lon); sv.loc_name=reverse_geocode(lat,lon)
                st.toast(f"شوێن: {sv.loc_name}",icon="📍")
        if sv.latlon: st.success(f"شوێن: {sv.loc_name}")

    # ناردن
    if st.button("🚀 ناردن", disabled=not(sv.feeling and sv.latlon), type="primary"):
        save_row(dict(ts=dt.datetime.utcnow(),user=user.email,location=sv.loc_name,
                      lat=sv.latlon[0],lon=sv.latlon[1],
                      feeling=sv.feeling,issues=", ".join(sorted(sv.issues))))
        st.success("سپاس بۆ بەشداریکردن!")
        sv.feeling=None; sv.issues=set(); sv.latlon=None; sv.loc_name=""

# ═════════════ ٢. نەخشە ═════════════
elif sv.page=="map":
    st.title("🗺️ نەخشەی هەستەکان – بەکارهێنەری ئێستا")
    rows=fetch_rows()
    if not rows: st.info("هێشتا هیچ داتایەک نییە.")
    else:
        colormap={"😃":"green","😐":"blue","☹️":"orange","😫":"red"}
        mp=folium.Map(location=[36.2,44.0],zoom_start=6)
        mc=MarkerCluster().add_to(mp)
        for ts,loc,lat,lon,feel,iss in rows:
            folium.CircleMarker([lat,lon],radius=6,color=colormap.get(feel,"gray"),
                fill=True,fill_color=colormap.get(feel,"gray"),fill_opacity=0.85,
                tooltip=f"{loc}\n{feel}\n{iss}").add_to(mc)
        # لێژەند
        legend="""
        <div style="position: fixed; bottom: 30px; left: 30px; z-index:9999;
             background: rgba(255,255,255,0.85); padding: 6px 10px; border-radius:8px;">
        <b>ڕەنگەکان</b><br>
        <i style='background:green;width:12px;height:12px;display:inline-block;'></i> 😃<br>
        <i style='background:blue;width:12px;height:12px;display:inline-block;'></i> 😐<br>
        <i style='background:orange;width:12px;height:12px;display:inline-block;'></i> ☹️<br>
        <i style='background:red;width:12px;height:12px;display:inline-block;'></i> 😫
        </div>
        """
        mp.get_root().html.add_child(folium.Element(legend))
        st_folium(mp,height=560,use_container_width=True)

# ═════════════ ٣. دەربارە ═════════════
else:
    st.title("ℹ️ دەربارەی کۆول ئاسیستەنت")
    st.markdown("""
کۆول ئاسیستەنت هەستە بەکارهێنەران لەسەر کەشوهەوا دەکۆمەڵێت بۆ یارمەتیدان بە
پلانکردنی شار، چارەسەرکردنی کێشەی گەرما و خەسوولە، و بەرزکردنەوەی ئاگاداری.
""")
    st.image("https://raw.githubusercontent.com/AIforimpact22/coolassistant/main/input/cool_logo.png",
             width=240)
    st.subheader("پەیوەندی")
    st.markdown("[hawkar.geoscience@gmail.com](mailto:hawkar.geoscience@gmail.com)")

st.markdown("---")
st.caption("© 2025 Cool Assistant • هەرێمی کوردستان")
