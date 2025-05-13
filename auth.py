import streamlit as st


def handle_authentication() -> None:
    """Show a custom Google-sign-in page until the visitor is authenticated."""

    # ── 1)  If the visitor is NOT logged in ──────────────────────────────
    if not st.experimental_user.is_logged_in:
        # Minimal CSS – hide Streamlit chrome & center login box
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

        # Branded login UI
        st.markdown('<div class="login-container">', unsafe_allow_html=True)

        # (Optional) logo — swap URL or remove line
        st.markdown(
            '<img src="https://raw.githubusercontent.com/Hakari-Bibani/photo/refs/heads/main/logo/hasar1.png" width="180">',
            unsafe_allow_html=True,
        )

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

        # Actual OAuth trigger
        st.button("Log in with Google", on_click=st.login, use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)
        st.stop()  # Halt execution until logged in

    # ── 2)  Authenticated: return silently to caller (app.py) ────────────
