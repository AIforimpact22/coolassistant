# app.py – کۆول ئاسیستەنت • ڕاپرسی هەست + Heat-Map  (تەنها lat/lon)
import datetime as dt, requests, psycopg2, streamlit as st, folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from auth import handle_authentication

# ───────── بنکەدراو ─────────
PG_URL = ("postgresql://cool_owner:npg_jpi5LdZUbvw1@"
          "ep-frosty-tooth-a283lla4-pooler.eu-central-1.aws.neon.tech/"
          "cool?sslmode=require")
TABLE = "survey_responses"

def ensure_table():
    """داتابێس دروست بکە ئەگەر بوونی نییە (location بەکاری ناھێنێت)."""
    with psycopg2.connect(PG_URL) as c:
        c.cursor().execute(f"""
          CREATE TABLE IF NOT EXISTS {TABLE}(
            ts TIMESTAMPTZ,
            user_email TEXT,
            lat DOUBLE PRECISION,
            lon DOUBLE PRECISION,
            feeling TEXT,
            issues TEXT);""")

def save_row(row):
    ensure_table()
    with psycopg2.connect(PG_URL) as c:
        c.cursor().execute(
            f"""INSERT INTO {TABLE}
                (ts,user_email,lat,lon,feeling,issues)
                VALUES (%(ts)s,%(user)s,%(lat)s,%(lon)s,
                        %(feeling)s,%(issues)s);""", row)
    st.toast("✅ وەڵام تۆمار کرا")

def fetch_rows(limit=1000):
    """lat, lon, feeling لە داتابێس وەرگرە."""
    ensure_table()
    with psycopg2.connect(PG_URL) as c:
        cur = c.cursor()
        cur.execute(f"""SELECT lat,lon,feeling
                        FROM {TABLE} ORDER BY ts DESC LIMIT %s;""",(limit,))
        return cur.fetchall()

# ───────── ستریم‌لیت ─────────
st.set_page_config("کۆول ئاسیستەنت",layout="centered")
handle_authentication(); user = st.experimental_user
state = st.session_state
state.setdefault("page","survey"); state.setdefault("feeling",None)
state.setdefault("issues",set()); state.setdefault("latlon",None)

# ───────── لاپەڕەکان ─────────
with st.sidebar:
    st.image("https://raw.githubusercontent.com/AIforimpact22/coolassistant/main/input/cool_logo.png",width=180)
    for lbl,key in [("📝 ڕاپرسی","survey"),("🗺️ نەخشە","map"),("ℹ️ دەربارە","about")]:
        if st.button(lbl,type="primary" if state.page==key else "secondary"):
            state.page=key
    st.markdown("---"); st.write("👤",user.email); st.button("دەرچوون",on_click=st.logout)

# ═════════════ ١. ڕاپرسی ═════════════
if state.page=="survey":
    st.title("🌡️ ڕاپرسی هەست بە هەوا")
    st.markdown("#### ١. هەستت چییە؟ (ئیمۆجی کلیک بکە)")
    emos=["😃","😐","☹️","😫"]; cols=st.columns(4)
    for i,e in enumerate(emos):
        if cols[i].button(e,key=f"emo{i}",type="primary" if state.feeling==e else "secondary"):
            state.feeling=e
    if state.feeling: st.success(f"{state.feeling}")

    st.markdown("#### ٢. کێشەکان (هەلبژاردنی ئارەزوومەندانە)")
    all_iss=["🔥 گەرما","🌪️ خۆڵبارین","💨 با","🏭 پیسبوونی هەوا","💧 شێداری",
             "☀️ تیشکی خوَر","⚡ بروسک","🌧️ باران","❄️ ساردی","🌫️ بۆنی ناخۆش"]
    for i,iss in enumerate(all_iss):
        sel=iss in state.issues
        if st.button(("✅ " if sel else "☐ ")+iss,key=f"iss{i}",
                     type="primary" if sel else "secondary"):
            state.issues.discard(iss) if sel else state.issues.add(iss)

    if state.feeling:
        st.markdown("#### ٣. لە نەخشە کلیک بکە بۆ دیاریکردنی شوێنت")
        m=folium.Map(location=[36.2,44.0],zoom_start=6)
        if state.latlon: folium.Marker(state.latlon).add_to(m)
        click=st_folium(m,height=380,use_container_width=True)
        if click and click.get("last_clicked"):
            state.latlon=(click["last_clicked"]["lat"],click["last_clicked"]["lng"])
            st.toast("شوێن دیاریکرا",icon="📍")
        if state.latlon: st.success(f"lat {state.latlon[0]:.3f}, lon {state.latlon[1]:.3f}")

    if st.button("🚀 ناردن",disabled=not(state.feeling and state.latlon),type="primary"):
        save_row(dict(ts=dt.datetime.utcnow(),user=user.email,
                      lat=state.latlon[0],lon=state.latlon[1],
                      feeling=state.feeling,issues=", ".join(sorted(state.issues))))
        st.success("سوپاس بۆ بەشداریکردن!")
        state.feeling=None; state.issues=set(); state.latlon=None; state.page="map"

# ═════════════ ٢. Heat-Map ═════════════
elif state.page=="map":
    st.title("🗺️ Heat-Map ی هەستەکان")
    data=fetch_rows()
    if not data: st.info("هێشتا داتایەک نییە.")
    else:
        scale={"😃":3,"😐":2,"☹️":1,"😫":0}
        heat=[[lat,lon,scale.get(feel,1)] for lat,lon,feel in data]
        mp=folium.Map(location=[36.2,44.0],zoom_start=6)
        HeatMap(heat,gradient={0:"red",0.33:"orange",0.66:"blue",1:"green"},
                min_opacity=0.25,max_opacity=0.9,radius=35,blur=20).add_to(mp)
        legend="""<div style='position:fixed;bottom:25px;left:25px;z-index:9999;
                 background:#fff;padding:6px 10px;border-radius:8px;'>
        <b>ڕەنگەکان</b><br>
        <i style='background:green;width:14px;height:14px;display:inline-block;'></i> 😃<br>
        <i style='background:blue;width:14px;height:14px;display:inline-block;'></i> 😐<br>
        <i style='background:orange;width:14px;height:14px;display:inline-block;'></i> ☹️<br>
        <i style='background:red;width:14px;height:14px;display:inline-block;'></i> 😫</div>"""
        mp.get_root().html.add_child(folium.Element(legend))
        st_folium(mp,height=560,use_container_width=True)

# ═════════════ ٣. دەربارە ═════════════
else:
    st.title("ℹ️ دەربارەی کۆول ئاسیستەنت")
    st.markdown("پروجەیەک بۆ کۆکردنەوەی هەستەکانی خەڵک بە کەشوهەوا بۆ پلانسازی شار و پاراستنی تەندروستی.")
    st.image("https://raw.githubusercontent.com/AIforimpact22/coolassistant/main/input/cool_logo.png",width=230)
    st.subheader("پەیوەندی"); st.markdown("[hawkar.geoscience@gmail.com](mailto:hawkar.geoscience@gmail.com)")

st.markdown("---"); st.caption("© 2025 Cool Assistant • هەرێمی کوردستان")
