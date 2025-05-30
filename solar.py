import streamlit as st
import requests
import json
import psycopg2

def save_estimate_to_db(
    user_email, city, peak_sun_hours, system_loss_percentage,
    total_energy_wh, required_panel_capacity_w, estimated_system_price_usd,
    annual_energy_kwh, panel_area_m2, annual_co2_saving_tons, devices_json,
    scenario, battery_kwh=None, battery_price_usd=None, total_system_price_with_battery_usd=None
):
    PG_URL = (
        "postgresql://cool_owner:npg_jpi5LdZUbvw1@"
        "ep-frosty-tooth-a283lla4-pooler.eu-central-1.aws.neon.tech/"
        "cool?sslmode=require"
    )
    # Add battery fields if present, else null
    insert_query = """
    INSERT INTO solar_estimates (
        user_email, city, peak_sun_hours, system_loss_percentage,
        total_energy_wh, required_panel_capacity_w, estimated_system_price_usd,
        annual_energy_kwh, panel_area_m2, annual_co2_saving_tons, devices,
        scenario, battery_kwh, battery_price_usd, total_system_price_with_battery_usd
    ) VALUES (
        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
    );
    """
    with psycopg2.connect(PG_URL) as con, con.cursor() as cur:
        cur.execute(insert_query, (
            user_email, city, peak_sun_hours, system_loss_percentage,
            total_energy_wh, required_panel_capacity_w, estimated_system_price_usd,
            annual_energy_kwh, panel_area_m2, annual_co2_saving_tons, devices_json,
            scenario, battery_kwh, battery_price_usd, total_system_price_with_battery_usd
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

    AVG_SYSTEM_PRICE_PER_WATT = 1.0      # USD/W (turnkey system, typical)
    AVG_BATTERY_PRICE_PER_KWH = 220      # USD/kWh (battery pack & inverter, typical for region, 2024)
    AVG_PANEL_WATT_PER_M2 = 180
    CO2_PER_KWH_GRID = 0.7

    st.title("🔆 Solar System Calculator")
    st.write("Estimate your required solar panel system for your location in Kurdistan.")

    # Choose scenario
    scenario = st.radio(
        "System Scenario",
        ["Without Battery (Grid-Tied)", "With Battery Backup"],
        horizontal=True,
        help="Choose whether your solar system will include a battery for backup power or not."
    )

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
            system_price = required_panel_capacity_w * AVG_SYSTEM_PRICE_PER_WATT
            annual_energy_kwh = required_panel_capacity_w * peak_sun_hours * 365 / 1000
            area_m2 = required_panel_capacity_w / AVG_PANEL_WATT_PER_M2
            annual_co2_saving = annual_energy_kwh * CO2_PER_KWH_GRID / 1000

            # --- Battery scenario calculations ---
            battery_kwh = battery_price_usd = total_system_price_with_battery = None
            if scenario == "With Battery Backup":
                # Suggest 1 day of backup (you can change this logic)
                battery_kwh = round(total_energy_wh / 1000, 2)
                battery_price_usd = round(battery_kwh * AVG_BATTERY_PRICE_PER_KWH, 2)
                total_system_price_with_battery = round(system_price + battery_price_usd, 2)

            # --- Output Section ---
            st.markdown("### 🌞 Solar System Results")
            with st.container():
                col1, col2 = st.columns(2, gap="large")
                with col1:
                    st.metric("Total Daily Energy Need", f"{total_energy_wh:,.0f} Wh/day")
                    st.metric("Recommended Panel Capacity", f"{required_panel_capacity_w:,.0f} W")
                    st.metric("Annual Energy Production", f"{annual_energy_kwh:,.0f} kWh/year")
                    if scenario == "With Battery Backup":
                        st.metric("Recommended Battery Size", f"{battery_kwh:.2f} kWh")
                with col2:
                    st.metric("Estimated System Price", f"${system_price:,.0f} USD")
                    st.metric("Panel Area Needed", f"{area_m2:.2f} m²")
                    st.metric("CO₂ Savings", f"{annual_co2_saving:.2f} tons/year")
                    if scenario == "With Battery Backup":
                        st.metric("Estimated Battery Price", f"${battery_price_usd:,.0f} USD")
                        st.metric("Total System Price (With Battery)", f"${total_system_price_with_battery:,.0f} USD")

            st.caption("Panel capacity is DC rating. "
                "Actual output varies by location, weather, and installation.")
            st.caption("All cost and environmental estimates are for guidance only. "
                "Consult a professional for precise figures.")

            # Save button
            st.markdown("---")
            if st.button("💾 Save My Estimate"):
                try:
                    user_email = st.experimental_user.email if hasattr(st.experimental_user, "email") else "unknown"
                    devices_json = json.dumps(st.session_state["devices"])
                    save_estimate_to_db(
                        user_email, city, peak_sun_hours, system_loss,
                        total_energy_wh, required_panel_capacity_w, system_price,
                        annual_energy_kwh, area_m2, annual_co2_saving, devices_json,
                        scenario,
                        battery_kwh, battery_price_usd, total_system_price_with_battery
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
