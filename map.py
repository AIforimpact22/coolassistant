# map.py – Heatmap logic for Cool Assistant
import psycopg2, streamlit as st, folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium

PG_URL = ("postgresql://cool_owner:npg_jpi5LdZUbvw1@"
          "ep-frosty-tooth-a283lla4-pooler.eu-central-1.aws.neon.tech/cool?sslmode=require")

def fetch_rows(limit=1000):
    with psycopg2.connect(PG_URL) as c:
        cur = c.cursor()
        cur.execute(f"SELECT lat,lon,feeling FROM survey_responses ORDER BY ts DESC LIMIT %s;", (limit,))
        return cur.fetchall()

def show_heatmap():
    st.title("🗺️ نەخشەی هەستەکان بەرامبەر بە کەشوهەوا")
    rows = fetch_rows()
    if not rows:
        st.info("هێشتا هیچ دێتەیەک نییە.")
        return

    weight = {"😃":1, "😐":0.66, "☹️":0.33, "😫":0}
    heat = [[lat, lon, weight.get(feel[0], 0.5)] for lat, lon, feel in rows]

    # Legend at top
    lg_cols = st.columns(4)
    for c, (col, emo) in zip(lg_cols, [("green","😃"),("blue","😐"),("orange","☹️"),("red","😫")]):
        c.markdown(f"<div style='background:{col};color:#fff;width:60px;height:60px;"
                   f"display:flex;align-items:center;justify-content:center;border-radius:8px;"
                   f"font-size:28px;'>{emo}</div>", unsafe_allow_html=True)

    # Heatmap
    mp = folium.Map(location=[36.2, 44.0], zoom_start=6)
    HeatMap(heat, gradient={"0":"red","0.33":"orange","0.66":"blue","1":"green"},
            min_opacity=0.25,max_opacity=0.9,radius=35,blur=20).add_to(mp)
    st_folium(mp, height=550, use_container_width=True)
