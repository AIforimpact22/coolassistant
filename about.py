# about.py – Cool Assistant
import streamlit as st

st.set_page_config(page_title="About Cool Assistant", layout="centered")

# ─────────────── HEADER ────────────────
st.title("🌍 About Cool Assistant")

# ─────────────── WHAT IS THIS APP ────────────────
st.markdown("""
Cool Assistant collects **real-time feedback** from users like you about how you're experiencing the weather—such as heat, dust, humidity, and more. 

Your feedback is then visualized on an interactive **"Feeling Map"**, showing exactly how people across different locations are affected by current weather conditions.
""")

st.image("https://github.com/AIforimpact22/coolassistant/blob/main/input/cool_logo.png?raw=true", width=250)

# ─────────────── WHY IT MATTERS ────────────────
st.subheader("🤔 Why is this important?")

st.markdown("""
Understanding how weather conditions impact people's comfort and wellbeing helps communities, planners, and decision-makers take better actions, such as:

- 🌳 **Urban Planning**: Improve city design by understanding which areas are more vulnerable to heat, dust, or pollution.
- 🏠 **Building Design**: Help architects and engineers build homes and buildings better suited to the local climate.
- 🌡️ **Climate Awareness**: Raise awareness about climate conditions and motivate communities toward proactive climate adaptation measures.
- 🩺 **Public Health**: Enable health services to better prepare and respond to weather-related health concerns, such as heatstroke, respiratory issues, and allergies.

Simply put:  
Your individual feelings, combined with feedback from your community, can help make **your city or region healthier, more comfortable, and more resilient to weather changes**.
""")

# ─────────────── PRIVACY NOTE ────────────────
st.subheader("🔒 Privacy First")
st.markdown("""
- **Location accuracy**: Your location is based entirely on the position you select—never guessed or tracked without your consent.
- **Data use**: We use your responses only to visualize and analyze weather impact; your personal data remains secure and private.
""")

# ─────────────── CONTACT ────────────────
st.markdown("---")
st.markdown("""
**Questions or feedback?**

📧 **[Contact us](mailto:hawkar.geoscience@gmail.com)**  
""")

st.caption("© 2025 Cool Assistant • Kurdistan Region")

