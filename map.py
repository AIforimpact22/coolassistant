# map.py – Improved Heatmap logic for Cool Assistant (average 1 input/user/day, no NaNs)
import psycopg2
import streamlit as st
import folium
from folium.plugins import HeatMap
from streamlit_folium import st_folium
import pandas as pd
import numpy as np

PG_URL = (
    "postgresql://cool_owner:npg_jpi5LdZUbvw1@"
    "ep-frosty-tooth-a283lla4-pooler.eu-central-1.aws.neon.tech/cool?sslmode=require"
)

# Fetch data from the database
def fetch_rows(limit=2000):
    with psycopg2.connect(PG_URL) as c:
        cur = c.cursor()
        cur.execute("""
            SELECT ts, user_email, lat, lon, feeling
            FROM survey_responses
            ORDER BY ts DESC LIMIT %s;
        """, (limit,))
        return cur.fetchall()

# Show heatmap with daily averages per user
def show_heatmap():
    st.title("🗺️ نەخشەی هەستەکان (Average هەست/user/day)")

    rows = fetch_rows()
    if not rows:
        st.info("هێشتا هیچ داتایەک نییە.")
        return

    # Data preparation
    df = pd.DataFrame(rows, columns=['ts', 'user_email', 'lat', 'lon', 'feeling'])

    # Convert timestamps to local timezone
    df['ts'] = pd.to_datetime(df['ts']).dt.tz_convert('Asia/Baghdad')
    df['day'] = df['ts'].dt.date

    # Extract emoji and map to numeric weights, handling all cases explicitly
    emoji_weights = {"😃": 1, "😐": 0.66, "☹️": 0.33, "😫": 0}
    df['emoji'] = df['feeling'].str.extract(r'(😃|😐|☹️|😫)', expand=False)
    df['weight'] = df['emoji'].map(emoji_weights)

    # Drop rows with any missing data
    df.dropna(subset=['lat', 'lon', 'weight'], inplace=True)

    # Compute daily mean per user
    daily_avg = df.groupby(['user_email', 'day'], as_index=False).agg({
        'lat': 'mean',
        'lon': 'mean',
        'weight': 'mean'
    })

    # Remove any remaining NaNs after aggregation
    daily_avg.dropna(subset=['lat', 'lon', 'weight'], inplace=True)

    # Ensure data is ready for HeatMap
    heat_data = daily_avg[['lat', 'lon', 'weight']].to_numpy()

    if heat_data.size == 0:
        st.info("هێشتا هیچ داتایەک بەردەست نییە بۆ نیشاندان.")
        return

    # Legend visualization
    lg_cols = st.columns(4)
    legend_data = [("green", "😃"), ("blue", "😐"), ("orange", "☹️"), ("red", "😫")]
    for c, (col, emo) in zip(lg_cols, legend_data):
        c.markdown(
            f"<div style='background:{col};color:#fff;width:60px;height:60px;"
            "display:flex;align-items:center;justify-content:center;border-radius:8px;"
            f"font-size:28px;'>{emo}</div>",
            unsafe_allow_html=True
        )

    # Heatmap generation
    mp = folium.Map(location=[36.2, 44.0], zoom_start=6)
    HeatMap(
        heat_data,
        gradient={0: "red", 0.33: "orange", 0.66: "blue", 1: "green"},
        min_opacity=0.25,
        max_opacity=0.9,
        radius=35,
        blur=20
    ).add_to(mp)

    st_folium(mp, height=550, use_container_width=True)
