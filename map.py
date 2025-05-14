# map.py – Heatmap logic with 24-hour user limit for Cool Assistant
import psycopg2, streamlit as st, folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
from datetime import datetime, timedelta

PG_URL = ("postgresql://cool_owner:npg_jpi5LdZUbvw1@"
          "ep-frosty-tooth-a283lla4-pooler.eu-central-1.aws.neon.tech/cool?sslmode=require")

def fetch_rows(limit=1000):
    with psycopg2.connect(PG_URL) as c:
        cur = c.cursor()
        cur.execute("SELECT lat, lon, feeling FROM survey_responses ORDER BY ts DESC LIMIT %s;", (limit,))
        return cur.fetchall()

def user_can_submit(user_email):
    """Check if user already submitted within the past 24 hours."""
    with psycopg2.connect(PG_URL) as c:
        cur = c.cursor()
        cur.execute("""
            SELECT ts FROM survey_responses 
            WHERE user_email = %s 
            ORDER BY ts DESC LIMIT 1;""",
            (user_email,))
        row = cur.fetchone()
        if row:
            last_submission = row[0]
            return (datetime.utcnow() - last_submission) > timedelta(hours=24)
        return True  # No prior submissions found

def show_heatmap():
    st.title("🗺️ نەخشەی هەستەکان بەرامبەر بە کەشوهەوا")

    # Check submission eligibility
    user_email = st.experimental_user.email
    can_submit = user_can_submit(user_email)

    if not can_submit:
        st.warning("⚠️ تەنها یەک وەڵام لە هەر ٢٤ کاتژمێر بەردەستە.")

    rows = fetch_rows()
    if not rows:
        st.info("هێشتا هیچ داتایەک نییە.")
        return

    weight = {"😃": 1, "😐": 0.66, "☹️": 0.33, "😫": 0}
    heat = [[lat, lon, weight.get(feel[0], 0.5)] for lat, lon, feel in rows]

    # Legend at top
    lg_cols = st.columns(4)
    for c, (col, emo) in zip(lg_cols, [("green", "😃"), ("blue", "😐"), ("orange", "☹️"), ("red", "😫")]):
        c.markdown(f"""
            <div style='background:{col};color:#fff;width:60px;height:60px;
            display:flex;align-items:center;justify-content:center;border-radius:8px;font-size:28px;'>
            {emo}</div>""", unsafe_allow_html=True)

    # Heatmap visualization
    mp = folium.Map(location=[36.2, 44.0], zoom_start=6)
    HeatMap(
        heat,
        gradient={"0": "red", "0.33": "orange", "0.66": "blue", "1": "green"},
        min_opacity=0.25,
        max_opacity=0.9,
        radius=35,
        blur=20
    ).add_to(mp)

    st_folium(mp, height=550, use_container_width=True)
