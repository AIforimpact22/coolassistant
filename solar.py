# solar.py – Solar System Calculator page for Cool Assistant
import streamlit as st

# You can adapt this dictionary as needed, or import from your constants.
KURDISTAN_CITIES_PEAK_SUN_HOURS = {
    "None": None,
    "Erbil": 5.4,
    "Sulaimani": 5.1,
    "Duhok": 5.7,
    "Halabja": 5.2,
    "Kirkuk": 5.5,
}
CITY_OPTIONS = list(KURDISTAN_CITIES_PEAK_SUN_HOURS.keys())
DEFAULT_PEAK_SUN_HOURS = 5.4
DEFAULT_SYSTEM_LOSS_PERCENTAGE = 20  # e.g., 20%

st.title("🔆 Solar System Calculator")
st.write("Estimate your required solar panel system for your location in Kurdistan.")

# --- Select city and parameters ---
col1, col2 = st.columns(2)
with col1:
    city = st.selectbox("Select City (Kurdistan Region)", CITY_OPTIONS, index=0)
    peak_sun_hours = KURDISTAN_CITIES_PEAK_SUN_HOURS[city] if city != "None" else DEFAULT_PEAK_SUN_HOURS
with col2:
    system_loss = st.number_input("System Losses (%)", min_value=0, max_value=50, value=DEFAULT_SYSTEM_LOSS_PERCENTAGE, step=1)

st.markdown(f"*Peak Sun Hours*: **{peak_sun_hours if peak_sun_hours else 'N/A'}** hours/day")
st.markdown(f"*System Loss*: **{system_loss}%**")

# --- Device entry ---
st.subheader("Add Your Devices")
if "devices" not in st.session_state:
    st.session_state["devices"] = []

with st.form("add_device_form", clear_on_submit=True):
    device_name = st.text_input("Device Name")
    power_watts = st.number_input("Power (W)", min_value=1, step=1)
    usage_hours = st.number_input("Daily Usage (Hours)", min_value=0.1, step=0.1, format="%.1f")
    add_device = st.form_submit_button("Add Device")
    if add_device and device_name and power_watts > 0 and usage_hours > 0:
        st.session_state["devices"].append({
            "name": device_name,
            "power": power_watts,
            "usage": usage_hours,
        })

# Device list and remove option
if st.session_state["devices"]:
    st.write("#### Devices List")
    for i, d in enumerate(st.session_state["devices"]):
        col1, col2, col3, col4 = st.columns([3,2,2,1])
        col1.write(f"**{d['name']}**")
        col2.write(f"{d['power']} W")
        col3.write(f"{d['usage']} hr")
        if col4.button("❌", key=f"del_{i}"):
            st.session_state["devices"].pop(i)
            st.experimental_rerun()

# --- Calculation ---
st.markdown("---")
if st.session_state["devices"] and peak_sun_hours and system_loss < 100:
    total_energy_wh = sum(d["power"] * d["usage"] for d in st.session_state["devices"])
    system_loss_factor = 1 - (system_loss / 100)
    if system_loss_factor <= 0:
        st.error("System loss is 100% or more. Please adjust.")
    else:
        energy_required_from_panels = total_energy_wh / system_loss_factor
        required_panel_capacity_w = energy_required_from_panels / peak_sun_hours
        st.success("## Solar System Estimate")
        st.write(f"**Total Daily Energy Need:** {total_energy_wh:.2f} Wh/day")
        st.write(f"**Recommended Solar Panel Capacity:** {required_panel_capacity_w:.2f} W")
        st.caption("Panel capacity is DC rating. Actual output varies by location, weather, and installation.")
else:
    st.info("Add at least one device and select city to see results.")

st.markdown("---")
st.caption("Estimates are for guidance only. Consult a professional for exact sizing.")
