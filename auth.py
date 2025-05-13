import streamlit as st

RAW_LOGO_URL = (
    "https://raw.githubusercontent.com/AIforimpact22/coolassistant/main/input/cool_logo.png"
)


def handle_authentication() -> None:
    """Show a custom Google-sign-in page until the visitor is authenticated."""
    if not st.experimental_user.is_logged_in:
        # ---------- minimal CSS ----------
        st.markdown(
            """
            <style>
                #MainMenu, header, footer {visibility: hidden;}
                .main .block-container {padding-top:0; padding-bottom:0;}
                .login-container {
                    display:flex; flex-direction:column; align-items:center;
                    padding-top:12vh; text-align:center;
                }
                div.stButton > button:first-child {
                    background:white; border:1px solid #ddd; border-radius:8px;
                    padding:0.5rem 1rem; font-size:16px; font-weight:500;
                    box-shadow:0 2px 5px rgba(0,0,0,0.15); transition:0.2s;
                }
                div.stButton > button:hover {
                    box-shadow:0 4px 8px rgba(0,0,0,0.25); background:#fafafa;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # ---------- branded login UI ----------
        st.markdown('<div class="login-container">', unsafe_allow_html=True)

        # Display logo (use raw URL so the image loads correctly)
        st.image(RAW_LOGO_URL, width=180)

        st.markdown(
            """
            <h2 style='margin:1.2rem 0; font-weight:600'>
                Sign in to Cool Assistant
            </h2>
            <p style='color:#666; margin-bottom:1.5rem'>
                Continue with your Google account
            </p>
            """,
            unsafe_allow_html=True,
        )

        st.button("Log in with Google", on_click=st.login, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()  # halt execution until logged in
