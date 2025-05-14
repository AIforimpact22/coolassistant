# map.py – Improved Heatmap logic for Cool Assistant (averaging one input/user/day)
import psycopg2
import streamlit as st
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import pandas as pd

PG_URL = ("postgresql://cool_owner:npg_jpi5LdZUbvw1@"
          "ep-frosty-tooth-a283lla4-pooler.eu-central-1.aws.neon.tech/cool?sslmode=require")

# Fetch data with timestamps and user_email
def fetch_rows(limit=2000):
    with psycopg2.connect(PG_URL) as c:
        cur = c.cursor()
        cur.execute("""
            SELECT ts, user_email, lat, lon, feeling
            FROM survey_responses
            ORDER BY ts DESC LIMIT %s;
        """, (limit,))
        return cur.fetchall()

# Show heatmap with averaged daily input per user
def show_heatmap():
    st.title("🗺️ نەخشەی هەستەکان (Average هەست/user/day)")

    rows = fetch_rows()
    if not rows:
        st.info("هێشتا هیچ داتایەک نییە.")
        return

    # Prepare dataframe
    df = pd.DataFrame(rows, columns=['ts', 'user_email', 'lat', 'lon', 'feeling'])
    df['ts'] = pd.to_datetime(df['ts']).dt.tz_convert('Asia/Baghdad')

    # Extract only emoji and map to numeric weights
    emoji_weights = {"😃": 1, "😐": 0.66, "☹️": 0.33, "😫": 0}
    df['feeling'] = df['feeling'].str[0].map(emoji_weights)

    # Calculate mean feeling & mean location per user per day
    df['day'] = df['ts'].dt.date
    daily_avg = df.groupby(['user_email', 'day']).agg({
        'lat': 'mean',
        'lon': 'mean',
        'feeling': 'mean'
    }).reset_index()

    # Prepare heatmap data
    heat_data = daily_avg[['lat', 'lon', 'feeling']].values.tolist()

    # Show Legend
    lg_cols = st.columns(4)
    legend_data = [("green", "😃"), ("blue", "😐"), ("orange", "☹️"), ("red", "😫")]
    for c, (col, emo) in zip(lg_cols, legend_data):
        c.markdown(
            f"<div style='background:{col};color:#fff;width:60px;height:60px;"
            "display:flex;align-items:center;justify-content:center;border-radius:8px;"
            f"font-size:28px;'>{emo}</div>",
            unsafe_allow_html=True
        )

    # Heatmap visualization
    mp = folium.Map(location=[36.2, 44.0], zoom_start=6)
    HeatMap(
        heat_data,
        gradient={"0": "red", "0.33": "orange", "0.66": "blue", "1": "green"},
        min_opacity=0.25,
        max_opacity=0.9,
        radius=35,
        blur=20
    ).add_to(mp)

    st_folium(mp, height=550, use_container_width=True)
