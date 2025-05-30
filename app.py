# app.py – Cool Assistant with Only Solar Calculator & About Pages
import streamlit as st
st.set_page_config("Cool Assistant", layout="centered")

from auth import handle_authentication
import about, solar

APP_URL = "https://coolassistant.streamlit.app"   # public link to share

handle_authentication()
user = st.experimental_user

# Sidebar
st.sidebar.image(
    "https://raw.githubusercontent.com/AIforimpact22/coolassistant/main/input/cool_logo.png",
    width=180,
)

# Only these two pages
PAGES = [
    ("🔆 ووزەی خۆر", "solar"),
    ("ℹ️ دەربارە", "about"),
]

if "page" not in st.session_state:
    st.session_state.page = "solar"          # default page is solar

for label, key in PAGES:
    if st.sidebar.button(label, type="primary" if st.session_state.page == key else "secondary"):
        st.session_state.page = key

st.sidebar.markdown("---")
st.sidebar.write("👤", user.email)
st.sidebar.button("دەرچوون", on_click=st.logout)

# Share section
st.sidebar.markdown("---")
st.sidebar.subheader("📤 هاوبەشکردن")

mailto = ("mailto:?subject=Cool%20Assistant&body=" +
          st.experimental_user.email if hasattr(st.experimental_user, 'email') else "" +
          f"\n\nکۆول ئاسیستەنت سەیری بکە:\n{APP_URL}")
wa = "https://wa.me/?text=" + APP_URL

st.sidebar.markdown(f"[📧 بە ئیمەیڵ]({mailto})")
st.sidebar.markdown(f"[💬 واتسئاپ]({wa})")
st.sidebar.code(APP_URL, language="bash")

# Router
page = st.session_state.page
if page == "solar":
    solar.show()
else:
    about.show_about()

st.markdown("---")
st.caption("© 2025 Cool Assistant • هەرێمی کوردستان")
