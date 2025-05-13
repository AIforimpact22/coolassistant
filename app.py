# app.py · Cool Assistant – Real-Time Weather Feeling Survey
import streamlit as st
import datetime as dt
from auth import handle_authentication
import pandas as pd

# ───────────── CONFIG ─────────────
st.set_page_config(page_title="Cool Assistant Survey", layout="centered")

# ───────────── AUTH ─────────────
handle_authentication()
user = st.experimental_user

# ───────────── SIDEBAR ─────────────
with st.sidebar:
    st.image(
        "https://github.com/AIforimpact22/coolassistant/blob/main/input/cool_logo.png?raw=true",
        width=200,
    )
    st.markdown("---")
    st.subheader("Logged in as")
    st.write(user.email)
    st.button("Log out", on_click=st.logout)

# ───────────── MAIN PAGE ─────────────
st.title("🌡️ Weather Feeling Survey")

st.markdown(
    "Tell us how you're feeling about the **current weather** in your location."
)

# Location Input
location = st.text_input("📍 Your Location", placeholder="City, Neighborhood, or Area")

# Weather Feeling
feeling = st.radio(
    "😊 How do you feel about the weather right now?",
    ["😃 Good", "😐 Neutral", "☹️ Uncomfortable", "😫 Bad"],
    horizontal=True,
)

# Main Issue
main_issue = st.multiselect(
    "🌡️ What's bothering you the most right now?",
    [
        "🔥 High Temperature",
        "🌪️ Dust",
        "💨 Strong Wind",
        "🏭 Air Pollution",
        "💧 Humidity",
        "☀️ UV Exposure",
        "⚡️ Thunderstorms",
        "🌧️ Rain",
        "❄️ Cold Temperature",
        "🌫️ Fog or Low Visibility",
    ],
)

# Submit Button
if st.button("Submit Response", type="primary"):
    timestamp = dt.datetime.now().isoformat()

    response = {
        "Timestamp": timestamp,
        "User": user.email,
        "Location": location,
        "Feeling": feeling,
        "Main Issues": ", ".join(main_issue),
    }

    # Store or log response here. As a placeholder, we show it.
    st.success("✅ Thanks for sharing your feedback!")
    st.json(response)

# ───────────── FOOTER ─────────────
st.markdown("---")
st.caption("© 2025 Cool Assistant • Kurdistan Region")
