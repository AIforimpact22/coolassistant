# map.py – heat-map logic with larger-view options
import psycopg2, streamlit as st, folium
from folium.plugins import HeatMap, Fullscreen
from streamlit_folium import st_folium

PG_URL = ("postgresql://cool_owner:npg_jpi5LdZUbvw1@"
          "ep-frosty-tooth-a283lla4-pooler.eu-central-1.aws.neon.tech/cool?sslmode=require")
TABLE = "survey_responses"


def fetch_rows(limit: int = 1000):
    with psycopg2.connect(PG_URL) as con, con.cursor() as cur:
        cur.execute(f"""
            SELECT lat, lon, feeling
              FROM {TABLE}
          ORDER BY ts DESC
             LIMIT %s;""", (limit,))
        return cur.fetchall()


def show_heatmap():
    st.title("🗺️ نەخشەی هەستەکان بەرامبەر بە کەشوهەوا")

    # optional large view toggle
    big_view = st.toggle("🔍 View larger map", value=False)

    rows = fetch_rows()
    if not rows:
        st.info("هێشتا هیچ دێتەیەک نییە.")
        return

    weights = {"😃": 1, "😐": 0.66, "☹️": 0.33, "😫": 0}
    heat = [[lat, lon, weights.get(feel.split()[0], 0.5)]
            for lat, lon, feel in rows]

    # legend
    lg_cols = st.columns(4)
    for c, (color, emo) in zip(
        lg_cols, [("green", "😃"), ("blue", "😐"), ("orange", "☹️"), ("red", "😫")]
    ):
        c.markdown(
            f"<div style='background:{color};color:#fff;width:60px;height:60px;"
            f"display:flex;align-items:center;justify-content:center;border-radius:8px;"
            f"font-size:28px;'>{emo}</div>",
            unsafe_allow_html=True,
        )

    # folium map
    mp = folium.Map(location=[36.2, 44.0], zoom_start=6)
    HeatMap(
        heat,
        gradient={"0": "red", "0.33": "orange", "0.66": "blue", "1": "green"},
        min_opacity=0.25,
        max_opacity=0.9,
        radius=35,
        blur=20,
    ).add_to(mp)

    # fullscreen control (⤢ icon)
    Fullscreen(position="topright").add_to(mp)

    st_folium(
        mp,
        height=800 if big_view else 550,    # bigger height when toggled
        use_container_width=True
    )
