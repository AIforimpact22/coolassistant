# solar.py
import streamlit as st

def show():
    # Constants
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
    DEFAULT_SYSTEM_LOSS_PERCENTAGE = 20

    # Cost and environmental assumptions (customize for your region)
    AVG_PANEL_PRICE_PER_WATT = 0.5       # USD/W (panel only)
    AVG_SYSTEM_PRICE_PER_WATT = 1.2      # USD/W (installed)
    AVG_PANEL_WATT_PER_M2 = 180          # W per m² typical
    CO2_PER_KWH_GRID = 0.7               # kg CO₂ per kWh from grid

    st.title("🔆 Solar System Calculator")
    st.write("Estimate your required solar panel system for your location in Kurdistan.")

    col1, col2 = st.columns(2)
    with col1:
        city = st.selectbox("Select City (Kurdistan Region)", CITY_OPTIONS, index=0)
        peak_sun_hours = KURDISTAN_CITIES_PEAK_SUN_HOURS[city] if city != "None" else DEFAULT_PEAK_SUN_HOURS
    with col2:
        system_loss = st.number_input("System Losses (%)", min_value=0, max_value=50, value=DEFAULT_SYSTEM_LOSS_PERCENTAGE, step=1)

    st.markdown(f"*Peak Sun Hours*: **{peak_sun_hours if peak_sun_hours else 'N/A'}** hours/day")
    st.markdown(f"*System Loss*: **{system_loss}%**")

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

    st.markdown("---")
    if st.session_state["devices"] and peak_sun_hours and system_loss < 100:
        total_energy_wh = sum(d["power"] * d["usage"] for d in st.session_state["devices"])
        system_loss_factor = 1 - (system_loss / 100)
        if system_loss_factor <= 0:
            st.error("System loss is 100% or more. Please adjust.")
        else:
            energy_required_from_panels = total_energy_wh / system_loss_factor
            required_panel_capacity_w = energy_required_from_panels / peak_sun_hours

            # --- New Calculations ---
            panel_price = required_panel_capacity_w * AVG_PANEL_PRICE_PER_WATT
            system_price = required_panel_capacity_w * AVG_SYSTEM_PRICE_PER_WATT
            annual_energy_kwh = required_panel_capacity_w * peak_sun_hours * 365 / 1000
            area_m2 = required_panel_capacity_w / AVG_PANEL_WATT_PER_M2
            annual_co2_saving = annual_energy_kwh * CO2_PER_KWH_GRID / 1000

            # --- Output Section ---
            st.success("## Solar System Estimate")
            st.write(f"**Total Daily Energy Need:** {total_energy_wh:.2f} Wh/day")
            st.write(f"**Recommended Solar Panel Capacity:** {required_panel_capacity_w:.2f} W")
            st.write(f"**Estimated Panel Price:** ${panel_price:,.2f} (USD, panels only)")
            st.write(f"**Estimated Total System Price:** ${system_price:,.2f} (USD, full install)")
            st.write(f"**Estimated Annual Energy Production:** {annual_energy_kwh:,.0f} kWh/year")
            st.write(f"**Estimated Panel Area Required:** {area_m2:.2f} m²")
            st.write(f"**Estimated CO₂ Savings:** {annual_co2_saving:.2f} tons/year (vs. typical grid)")

            st.caption("Panel capacity is DC rating. Actual output varies by location, weather, and installation.")
            st.caption("All cost and environmental estimates are for guidance only. Consult a professional for precise figures.")
    else:
        st.info("Add at least one device and select city to see results.")

    st.markdown("---")
    st.caption("Estimates are for guidance only. Consult a professional for exact sizing.")
