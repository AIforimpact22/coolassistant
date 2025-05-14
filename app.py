# app.py – کۆول ئاسیستەنت • ڕاپرسی هەست + نەخشەی ئینته‌رپۆلەیشن + دەربارە
import datetime as dt, requests, psycopg2, streamlit as st, folium
from folium.plugins import MarkerCluster, HeatMap
from streamlit_folium import st_folium
from auth import handle_authentication

# ───────── بنکەدراو ─────────
PG_URL=("postgresql://cool_owner:npg_jpi5LdZUbvw1@"
        "ep-frosty-tooth-a283lla4-pooler.eu-central-1.aws.neon.tech/"
        "cool?sslmode=require")
TABLE="survey_responses"
def ensure_table():
    with psycopg2.connect(PG_URL) as con:
        con.cursor().execute(f"""CREATE TABLE IF NOT EXISTS {TABLE}(
         ts TIMESTAMPTZ,user_email TEXT,location TEXT,
         lat DOUBLE PRECISION,lon DOUBLE PRECISION,
         feeling TEXT,issues TEXT);""")
def save_row(r):
    ensure_table()
    with psycopg2.connect(PG_URL) as con:
        con.cursor().execute(
          f"""INSERT INTO {TABLE}
              (ts,user_email,location,lat,lon,feeling,issues)
              VALUES (%(ts)s,%(user)s,%(location)s,%(lat)s,%(lon)s,
                      %(feeling)s,%(issues)s);""",r)
    st.toast("✅ تۆمار کرا")
def fetch_rows(limit=1000):
    ensure_table()
    with psycopg2.connect(PG_URL) as con:
        cur=con.cursor()
        cur.execute(f"""SELECT lat,lon,feeling,location
                        FROM {TABLE} ORDER BY ts DESC LIMIT %s;""",(limit,))
        return cur.fetchall()

# ───────── ستریم‌لیت ─────────
st.set_page_config("کۆول ئاسیستەنت", layout="centered")
handle_authentication(); user=st.experimental_user
sv=st.session_state
sv.setdefault("page","survey"); sv.setdefault("feeling",None)
sv.setdefault("issues",set()); sv.setdefault("latlon",None); sv.setdefault("loc_name","")

# ───────── لاپەڕەکان ─────────
with st.sidebar:
    st.image("https://raw.githubusercontent.com/AIforimpact22/coolassistant/main/input/cool_logo.png", width=180)
    def nav(lbl,key): 
        if st.button(lbl,type="primary" if sv.page==key else "secondary"): sv.page=key
    nav("📝 ڕاپرسی","survey"); nav("🗺️ نەخشە","map"); nav("ℹ️ دەربارە","about")
    st.markdown("---"); st.write("👤",user.email); st.button("دەرچوون", on_click=st.logout)

def reverse_geocode(lat,lon):
    try:
        a=requests.get(f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json",
                       timeout=5,headers={"User-Agent":"coolassistant"}).json()["address"]
        city=a.get("city")or a.get("town")or a.get("village")or""
        return ", ".join(x for x in (city,a.get("state",""),a.get("country","")) if x) or f"{lat:.2f},{lon:.2f}"
    except: return f"{lat:.2f},{lon:.2f}"

# ═════════════ ١. ڕاپرسی ═════════════
if sv.page=="survey":
    st.title("🌡️ ڕاپرسی هەست بە هەوا")
    st.markdown("#### ١. هەستت لەگەڵ کەشوهەوای ئێستا؟")
    emo=["😃","😐","☹️","😫"]; cols=st.columns(4)
    for i,e in enumerate(emo):
        if cols[i].button(e,key=f"e{i}",type="primary" if sv.feeling==e else "secondary"):
            sv.feeling=e
    if sv.feeling: st.success(f"هەست: {sv.feeling}")

    st.markdown("#### ٢. کێشەکانی هەوا کە تۆ نیگارانت دەکات؟")
    all_iss=["🔥 گەرما","🌪️ خۆڵبارین","💨 با","🏭 پیسبوونی هەوا","💧 شێداری",
             "☀️ تیشکی خوَر","⚡ بروسک","🌧️ باران","❄️ ساردی","🌫️ بۆنی ناخۆش"]
    icol=st.columns(2)
    for i,iss in enumerate(all_iss):
        sel=iss in sv.issues
        if icol[i%2].button(("✅ " if sel else "☐ ")+iss,key=f"is{i}",
                            type="primary" if sel else "secondary"):
            sv.issues.discard(iss) if sel else sv.issues.add(iss)
    if sv.issues: st.info(", ".join(sorted(sv.issues)))

    if sv.feeling:
        st.markdown("#### ٣. شوێنت دیاری بکە")
        m=folium.Map(location=[36.2,44.0],zoom_start=6)
        if sv.latlon: folium.Marker(sv.latlon,tooltip=sv.loc_name).add_to(m)
        click=st_folium(m,height=380,use_container_width=True)
        if click and click.get("last_clicked"):
            lat,lon=click["last_clicked"]["lat"],click["last_clicked"]["lng"]
            if sv.latlon!=(lat,lon):
                sv.latlon=(lat,lon); sv.loc_name=reverse_geocode(lat,lon)
                st.toast(f"{sv.loc_name}",icon="📍")
        if sv.latlon: st.success(sv.loc_name)

    if st.button("🚀 ناردن",disabled=not(sv.feeling and sv.latlon),type="primary"):
        save_row(dict(ts=dt.datetime.utcnow(),user=user.email,location=sv.loc_name,
                      lat=sv.latlon[0],lon=sv.latlon[1],
                      feeling=sv.feeling,issues=", ".join(sorted(sv.issues))))
        st.success("سپاس بۆ بەشداریکردن!")
        sv.clear(); sv.page="map"

# ═════════════ ٢. نەخشەی ئینته‌رپۆلەیشن ═════════════
elif sv.page=="map":
    st.title("🗺️ نەخشەی هەستەکان (Heat-Map)")
    rows=fetch_rows()
    if not rows: st.info("هێشتا هیچ داتایەک نییە.")
    else:
        value_map={"😃":3,"😐":2,"☹️":1,"😫":0}
        heat_data=[[lat,lon,value_map.get(feel,1)] for lat,lon,feel,_ in [(r[0],r[1],r[2],r[3]) for _,_,lat,lon,feel,_ in rows]]
        mp=folium.Map(location=[36.2,44.0],zoom_start=6)
        HeatMap(heat_data,gradient={0:"red",0.33:"orange",0.66:"blue",1:"green"},
                min_opacity=0.2,max_opacity=0.8,radius=35,blur=18).add_to(mp)

        # لێژەند
        legend="""
        <div style="position: fixed; bottom: 25px; left: 25px; z-index:9999;
             background: rgba(255,255,255,0.85); padding:8px 12px; border-radius:8px;">
        <b>ڕەنگەکان (ئینته‌رپۆلەیشن)</b><br>
        <i style='background:green;width:14px;height:14px;display:inline-block;'></i> 😃<br>
        <i style='background:blue;width:14px;height:14px;display:inline-block;'></i> 😐<br>
        <i style='background:orange;width:14px;height:14px;display:inline-block;'></i> ☹️<br>
        <i style='background:red;width:14px;height:14px;display:inline-block;'></i> 😫
        </div>"""
        mp.get_root().html.add_child(folium.Element(legend))
        st_folium(mp,height=560,use_container_width=True)

# ═════════════ ٣. دەربارە ═════════════
else:
    st.title("ℹ️ دەربارە")
    st.markdown("""
کۆول ئاسیستەنت هەستە بەکارهێنەران لەسەر کەشوهەوا کۆ دەکات بۆ یارمەتیدان بە پلانسازی شار و چاكسازی ژیان.
""")
    st.image("https://raw.githubusercontent.com/AIforimpact22/coolassistant/main/input/cool_logo.png",width=230)
    st.subheader("پەیوەندی"); st.markdown("[hawkar.geoscience@gmail.com](mailto:hawkar.geoscience@gmail.com)")

st.markdown("---"); st.caption("© 2025 Cool Assistant • هەرێمی کوردستان")
