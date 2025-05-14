# survey.py – survey page only
import datetime as dt
import streamlit as st
import folium
from streamlit_folium import st_folium

def show(save_row_fn, user_email: str) -> None:
    """Render the survey and write via the provided save_row_fn(dict)."""
    sv = st.session_state
    sv.setdefault("feeling", None)
    sv.setdefault("issues", set())
    sv.setdefault("latlon", None)

    st.title("🌡️ Weather-feeling survey")

    # 1 – feeling
    st.markdown("#### How do you feel about the weather?")
    emojis = ["😃", "😐", "☹️", "😫"]
    cols = st.columns(4)
    for i, e in enumerate(emojis):
        if cols[i].button(e, key=f"emo{i}",
                          type="primary" if sv.feeling == e else "secondary"):
            sv.feeling = e
    if sv.feeling:
        st.success(sv.feeling)

    # 2 – issues (optional)
    st.markdown("#### Any weather issue bothering you? (optional)")
    all_issues = ["🔥 Heat","🌪️ Dust","💨 Wind","🏭 Air pollution","💧 Humidity",
                  "☀️ Sun-glare","⚡ Storm","🌧️ Rain","❄️ Cold","🌫️ Bad smell"]
    for i, iss in enumerate(all_issues):
        picked = iss in sv.issues
        if st.button(("✅ " if picked else "☐ ") + iss,
                     key=f"iss{i}", type="primary" if picked else "secondary"):
            sv.issues.discard(iss) if picked else sv.issues.add(iss)

    # 3 – location picker
    if sv.feeling:
        st.markdown("#### Click on the map to set your location")
        mp = folium.Map(location=[36.2, 44.0], zoom_start=6)
        if sv.latlon:
            folium.Marker(sv.latlon).add_to(mp)
        res = st_folium(mp, height=380, use_container_width=True)
        if res and res.get("last_clicked"):
            sv.latlon = (res["last_clicked"]["lat"], res["last_clicked"]["lng"])
            st.toast("Location selected", icon="📍")
        if sv.latlon:
            st.success(f"{sv.latlon[0]:.3f}, {sv.latlon[1]:.3f}")

    # 4 – submit
    if st.button("🚀 Submit", disabled=not (sv.feeling and sv.latlon), type="primary"):
        save_row_fn(dict(
            ts=dt.datetime.utcnow(),
            user=user_email,
            lat=sv.latlon[0],
            lon=sv.latlon[1],
            feeling=sv.feeling,
            issues=", ".join(sorted(sv.issues)),
        ))
        st.success("Thanks for contributing!")
        sv.feeling, sv.issues, sv.latlon = None, set(), None
        st.session_state.page = "map"   # redirect to heat-map
