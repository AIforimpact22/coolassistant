# about.py – static info page
import streamlit as st

def show_about() -> None:
    """Display the project description & contact info."""
    st.title("ℹ️ دەربارەی Cool Assistant")

    st.markdown(
        """
        **Cool Assistant** is a solar and energy advisory tool for the Kurdistan Region.
        It helps users estimate their solar panel needs (with and without battery storage)
        and get personalized tips to reduce energy consumption—all tailored for local conditions.

        This tool is developed and maintained by **Hawkar Ali Abdulhaq**, PhD candidate specializing in Geothermal Energy.

        _The project also supports mapping and understanding community feedback on weather and energy usage to assist in sustainable planning for urban and health services._
        """
    )

    st.image(
        "https://raw.githubusercontent.com/AIforimpact22/coolassistant/main/input/cool_logo.png",
        width=230,
    )

    st.subheader("Contact / پەیوەندی")
    st.markdown("[hawkar.geoscience@gmail.com](mailto:hawkar.geoscience@gmail.com)")
