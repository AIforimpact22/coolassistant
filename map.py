# map.py – heat-map with clickable legend → jump to survey
import psycopg2, streamlit as st, folium, numpy as np, urllib.parse
from folium.plugins import HeatMap, Fullscreen
from streamlit_folium import st_folium

PG_URL = ("postgresql://cool_owner:npg_jpi5LdZUbvw1@"
          "ep-frosty-tooth-a283lla4-pooler.eu-central-1.aws.neon.tech/cool?sslmode=require")
TABLE = "survey_responses"

def fetch_rows(limit=1000):
    with psycopg2.connect(PG_URL) as con, con.cursor() as cur:
        cur.execute(f"SELECT lat,lon,feeling FROM {TABLE} ORDER BY ts DESC LIMIT %s;", (limit,))
        return cur.fetchall()

def show_heatmap():
    st.title("🗺️ نەخشەی هەستەکان بەرامبەر بە کەشوهەوا")

    big_view = st.toggle("🔍 View larger map", value=False)

    rows = fetch_rows()
    if not rows:
        st.info("هێشتا هیچ دێتەیەک نییە.")
        return

    weights = {"😃": 1, "😐": 0.66, "☹️": 0.33, "😫": 0}
    heat = [[lat, lon, weights.get(feel.split()[0], 0.5)]
            for lat, lon, feel in rows]

    # ---------- clickable legend ------------
    legend_defs = [("green", "😃"), ("blue", "😐"), ("orange", "☹️"), ("red", "😫")]
    lg_cols = st.columns(len(legend_defs))
    for col, (color, emo) in zip(lg_cols, legend_defs):
        html_box = (
            f"<div style='background:{color};color:#fff;width:60px;height:60px;"
            f"display:flex;align-items:center;justify-content:center;"
            f"border-radius:8px;font-size:28px;'>{emo}</div>"
        )
        # render colored square
        col.markdown(html_box, unsafe_allow_html=True)
        # clickable button under it
        if col.button(f"Select {emo}", key=f"legend_{emo}", type="secondary"):
            st.session_state.feeling = emo    # preset for survey
            st.session_state.page    = "survey"
            st.experimental_rerun()            # jump to survey immediately

    # ---------- folium heat-map ------------
    mp = folium.Map(location=[36.2, 44.0], zoom_start=6)
    HeatMap(
        heat,
        gradient={"0": "red", "0.33": "orange", "0.66": "blue", "1": "green"},
        min_opacity=0.25, max_opacity=0.9, radius=35, blur=20,
    ).add_to(mp)
    Fullscreen().add_to(mp)

    st_folium(mp, height=800 if big_view else 550, use_container_width=True)
