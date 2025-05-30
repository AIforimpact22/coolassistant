# solar.py
import streamlit as st
import requests
import json
import psycopg2

def save_estimate_to_db(
    user_email, city, peak_sun_hours, system_loss_percentage,
    total_energy_wh, required_panel_capacity_w, estimated_system_price_usd,
    annual_energy_kwh, panel_area_m2, annual_co2_saving_tons, devices_json
):
    PG_URL = (
        "postgresql://cool_owner:npg_jpi5LdZUbvw1@"
        "ep-frosty-tooth-a283lla4-pooler.eu-central-1.aws.neon.tech/"
        "cool?sslmode=require"
    )
    insert_query = """
    INSERT INTO solar_estimates (
        user_email, city, peak_sun_hours, system_loss_percentage,
        total_energy_wh, required_panel_capacity_w, estimated_system_price_usd,
        annual_energy_kwh, panel_area_m2, annual_co2_saving_tons, devices
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    );
    """
    with psycopg2.connect(PG_URL) as con, con.cursor() as cur:
        cur.execute(insert_query, (
            user_email, city, peak_sun_hours, system_loss_percentage,
            total_energy_wh, required_panel_capacity_w, estimated_system_price_usd,
            annual_energy_kwh, panel_area_m2, annual_co2_saving_tons, devices_json
        ))
        con.commit()

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
    # Set city-specific system loss values (update as needed)
    KURDISTAN_CITIES_SYSTEM_LOSS = {
        "None": 20,
        "Erbil": 18,
        "Sulaimani": 21,
        "Duhok": 17,
        "Halabja": 20,
        "Kirkuk": 19,
    }
    CITY_OPTIONS = list(KURDISTAN_CITIES_PEAK_SUN_HOURS.keys())
    DEFAULT_PEAK_SUN_HOURS = 5.4

    # Regional assumptions for Kurdistan (2023–2025)
    AVG_SYSTEM_PRICE_PER_WATT = 1.0      # USD/W (turnkey system, typical)
    AVG_PANEL_WATT_PER_M2 = 180          # W per m² typical
    CO2_PER_KWH_GRID = 0.7               # kg CO₂ per kWh from grid

    st.title("🔆 Solar System Calculator")
    st.write("Estimate your required solar panel system for your location in Kurdistan.")

    city = st.selectbox("Select City (Kurdistan Region)", CITY_OPTIONS, index=0)
    peak_sun_hours = KURDISTAN_CITIES_PEAK_SUN_HOURS[city] if city != "None" else DEFAULT_PEAK_SUN_HOURS
    system_loss = KURDISTAN_CITIES_SYSTEM_LOSS.get(city, 20)

    st.markdown(f"*Peak Sun Hours*: **{peak_sun_hours if peak_sun_hours else 'N/A'}** hours/day")

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
            st.error("System loss is 100% or more. Please adjust your city.")
        else:
            energy_required_from_panels = total_energy_wh / system_loss_factor
            required_panel_capacity_w = energy_required_from_panels / peak_sun_hours

            # --- Calculations ---
            system_price = required_panel_capacity_w * AVG_SYSTEM_PRICE_PER_WATT
            annual_energy_kwh = required_panel_capacity_w * peak_sun_hours * 365 / 1000
            area_m2 = required_panel_capacity_w / AVG_PANEL_WATT_PER_M2
            annual_co2_saving = annual_energy_kwh * CO2_PER_KWH_GRID / 1000

            # --- Output Section ---
            st.success("## Solar System Estimate")
            st.write(f"**Total Daily Energy Need:** {total_energy_wh:.2f} Wh/day")
            st.write(f"**Recommended Solar Panel Capacity:** {required_panel_capacity_w:.2f} W")
            st.write(f"**Estimated Total System Price:** ${system_price:,.2f} (USD, full install, no battery)")
            st.write(f"**Estimated Annual Energy Production:** {annual_energy_kwh:,.0f} kWh/year")
            st.write(f"**Estimated Panel Area Required:** {area_m2:.2f} m²")
            st.write(f"**Estimated CO₂ Savings:** {annual_co2_saving:.2f} tons/year (vs. typical grid)")

            st.caption("Panel capacity is DC rating. Actual output varies by location, weather, and installation.")
            st.caption("All cost and environmental estimates are for guidance only. Consult a professional for precise figures.")

            # Save button
            if st.button("💾 Save My Estimate"):
                try:
                    user_email = st.experimental_user.email if hasattr(st.experimental_user, "email") else "unknown"
                    devices_json = json.dumps(st.session_state["devices"])
                    save_estimate_to_db(
                        user_email, city, peak_sun_hours, system_loss,
                        total_energy_wh, required_panel_capacity_w, system_price,
                        annual_energy_kwh, area_m2, annual_co2_saving, devices_json
                    )
                    st.success("Your estimate has been saved! ✅")
                except Exception as e:
                    st.error(f"Failed to save to database: {e}")

            # --------------- Gemini Suggestion Button ---------------
            st.markdown("---")
            if st.button("💡 Suggest Ways to Reduce Consumption"):
                devices_text = ", ".join(
                    f"{d['name']} ({d['power']}W, {d['usage']}h/day)" for d in st.session_state["devices"]
                )
                prompt = (
                    f"These are the household devices used by a resident in Kurdistan, Iraq: {devices_text}. "
                    "Briefly recommend energy-efficient or low-consumption alternative devices that can help this user reduce electricity usage."
                )

                api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=AIzaSyBQvqNT4wtKsh2WDvVcpgZHCVsLyAOw9dk"
                headers = {"Content-Type": "application/json"}
                body = {
                    "contents": [{"parts": [{"text": prompt}]}]
                }

                try:
                    response = requests.post(api_url, headers=headers, data=json.dumps(body), timeout=30)
                    response.raise_for_status()
                    data = response.json()
                    tip = data["candidates"][0]["content"]["parts"][0]["text"]
                    st.info("**Gemini Suggestion:**\n\n" + tip)
                except Exception as e:
                    st.error("Sorry, Gemini could not provide a tip at this moment.")
    else:
        st.info("Add at least one device and select city to see results.")

    st.markdown("---")
    st.caption("Estimates are for guidance only. Consult a professional for exact sizing.")
