# survey.py – هەست و کێشەی کەشوهەوا
import datetime as dt
import streamlit as st
import folium
from streamlit_folium import st_folium


def show(save_row_fn, user_email: str) -> None:
    """Show survey UI; call save_row_fn(row_dict) on submit."""
    sv = st.session_state
    sv.setdefault("feeling", None)
    sv.setdefault("issues", set())
    sv.setdefault("latlon", None)

    # ───────── سەردێڕ ─────────
    st.title("نەخشەی هەستمان بەرامبەر بە کەشوهەوا")

    # ١-هەست
    st.markdown("#### هەستت چۆنە بەرامبەر بە کەشوهەوا؟")
    emojis = ["😃", "😐", "☹️", "😫"]
    cols = st.columns(4)
    for i, emo in enumerate(emojis):
        if cols[i].button(emo,
                          key=f"emo{i}",
                          type="primary" if sv.feeling == emo else "secondary"):
            sv.feeling = emo
    if sv.feeling:
        st.success(sv.feeling)

    # ٢-کێشەکان (ئارا)
    st.markdown("#### کام لەم ڕووداوانەی کەشوهەوا بێزارت دەکات؟")
    issue_defs = [
        ("🔥", "گەرما"),
        ("🌪️", "خۆڵبارین"),
        ("💨", "ڕەشەبا"),
        ("🏭", "پیسبوونی هەوا"),
        ("⚡", "زریان"),
        ("🌧️", "باران"),
        ("❄️", "سەرما"),
        ("🌫️", "بۆنی ناخۆش"),
    ]
    for i, (emoji, label) in enumerate(issue_defs):
        full = f"{emoji} {label}"
        picked = full in sv.issues
        if st.button(("✅ " if picked else "☐ ") + full,
                     key=f"iss{i}",
                     type="primary" if picked else "secondary"):
            sv.issues.discard(full) if picked else sv.issues.add(full)

    # ٣- شوێن
    if sv.feeling:
        st.markdown("#### کلیک بکە لە نەخشە بۆ دیاریکردنی شوێنت")
        mp = folium.Map(location=[36.2, 44.0], zoom_start=6)
        if sv.latlon:
            folium.Marker(sv.latlon).add_to(mp)
        res = st_folium(mp, height=380, use_container_width=True)
        if res and res.get("last_clicked"):
            sv.latlon = (res["last_clicked"]["lat"], res["last_clicked"]["lng"])
            st.toast("شوێن دیاریکرا", icon="📍")
        if sv.latlon:
            st.success(f"{sv.latlon[0]:.3f}, {sv.latlon[1]:.3f}")

    # ٤- ناردن
    if st.button("🚀 ناردن",
                 disabled=not (sv.feeling and sv.latlon),
                 type="primary"):
        save_row_fn(dict(
            ts=dt.datetime.utcnow(),
            user=user_email,
            lat=sv.latlon[0],
            lon=sv.latlon[1],
            feeling=sv.feeling,
            issues=", ".join(sorted(sv.issues)),
        ))
        st.success("سوپاس بۆ بەشداریکردن!")
        sv.feeling, sv.issues, sv.latlon = None, set(), None
        st.session_state.page = "map"   # redirect
