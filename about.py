# about.py – static info page
import streamlit as st

def show_about() -> None:
    """Display the project description & contact info."""
    st.title("ℹ️ دەربارەی Cool Assistant")

    st.markdown(
        "کۆول ئاسیستەنت داتای هەستی خەڵک لە بەرامبەر بە کەشوهەوا بەشێوەی نەخشە دەردەخات "
        "بۆ یارمەتیدانی پلانسازی شار و خزمەتگوزاری تەندروستی."
    )

    st.image(
        "https://raw.githubusercontent.com/AIforimpact22/coolassistant/main/input/cool_logo.png",
        width=230,
    )

    st.subheader("پەیوەندی")
    st.markdown("[hawkar.geoscience@gmail.com](mailto:hawkar.geoscience@gmail.com)")
