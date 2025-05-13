import os
import random
import requests
import streamlit as st
from auth import handle_authentication


# ────────── Page-wide settings ──────────
st.set_page_config(page_title="Cool Assistant • Home Dashboard", layout="wide")

# ────────── Require login ──────────
handle_authentication()          # blocks until user signs in
user = st.experimental_user      # now authenticated

# ────────── Sidebar ──────────
with st.sidebar:
    st.subheader("Account")
    st.write(user.email)         # remove if you prefer anonymity
    st.button("Log out", on_click=st.logout, use_container_width=True)

# ────────── Main dashboard ──────────
st.title("🏠 Cool Assistant • Summer Dust & Heat Helper")

# 1) Current weather (OpenWeatherMap)
API_KEY = os.getenv("OPENWEATHER_API_KEY")   # set in env / Streamlit secrets
LOCATION = "Erbil"
if API_KEY:
    url = (
        f"https://api.openweathermap.org/data/2.5/weather?"
        f"q={LOCATION}&appid={API_KEY}&units=metric"
    )
    data = requests.get(url, timeout=8).json()
    temp_c = data["main"]["temp"]
    description = data["weather"][0]["description"].title()
    st.metric("Temperature", f"{temp_c:.1f} °C", help=description)
else:
    st.info("Add your OpenWeatherMap key to the OPENWEATHER_API_KEY env variable.")

# 2) Quick daily tip
st.subheader("💡 Daily Tip")
TIPS = [
    "Close windows & curtains during the hottest hours (12 – 4 pm).",
    "Hang damp cotton curtains to naturally cool incoming air.",
    "Seal door gaps with weather-stripping to keep dust out.",
]
st.write(random.choice(TIPS))

# 3) Feedback form
with st.expander("Send feedback or suggestions"):
    st.write("Tell us how we can improve Cool Assistant!")
    feedback = st.text_area("Feedback", placeholder="Your idea…")
    if st.button("Submit"):
        st.success("Thanks for your feedback!")  # hook into DB / Sheets later

# (Add AQI or dust-storm alerts once an AQI API is wired in)
