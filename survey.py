# survey.py – هەست و کێشەی کەشوهەوا (limit: 1 row / 12 h)
import datetime as dt
import psycopg2
import streamlit as st
import folium
from streamlit_folium import st_folium

PG_URL = ("postgresql://cool_owner:npg_jpi5LdZUbvw1@"
          "ep-frosty-tooth-a283lla4-pooler.eu-central-1.aws.neon.tech/"
          "cool?sslmode=require")
TABLE = "survey_responses"


def _has_recent(email: str) -> tuple[bool, dt.datetime | None]:
    """Return (True, last_ts) if this user has submitted within 12 h."""
    with psycopg2.connect(PG_URL) as con, con.cursor() as cur:
        cur.execute(
            f"""SELECT MAX(ts) FROM {TABLE}
                 WHERE user_email = %s
                   AND ts > NOW() - INTERVAL '12 hours';""",
            (email,),
        )
        last_ts = cur.fetchone()[0]
        return (last_ts is not None, last_ts)


def show(save_row_fn, user_email: str) -> None:
    """Render the survey form.  Deny if user already submitted in last 12 h."""
    sv = st.session_state
    sv.setdefault("feeling", None)
    sv.setdefault("issues", set())
    sv.setdefault("latlon", None)

    # ----- 12-hour limit check -----
    blocked, last_time = _has_recent(user_email)
    if blocked:
        st.warning(
            f"👋 {user_email}، تۆ پێشتر لە {last_time:%Y-%m-%d %H:%M} "
            "داخڵتی کردووە. دەتوانیت دووبارە دوای ٢٤ کاتژمێر وەڵام بدەیت."
        )
        return   # don’t show the form

    # ---------- Title ----------
    st.title("نەخشەی هەستمان بەرامبەر بە کەشوهەوا")

    # ١- هەست
    st.markdown("#### هەستت چۆنە بەرامبەر بە کەشوهەوا؟")
    emojis = ["😃", "😐", "☹️", "😫"]
    cols = st.columns(4)
    for i, emo in enumerate(emojis):
        if cols[i].button(
            emo,
            key=f"fe{emo}",
            type="primary" if sv.feeling == emo else "secondary",
        ):
            sv.feeling = emo
    if sv.feeling:
        st.success(sv.feeling)

    # ٢- کێشەکان
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
    for i, (e, lab) in enumerate(issue_defs):
        full = f"{e} {lab}"
        picked = full in sv.issues
        if st.button(("✅ " if picked else "☐ ") + full,
                     key=f"iss{i}",
                     type="primary" if picked else "secondary"):
            sv.issues.discard(full) if picked else sv.issues.add(full)

    # ٣- شوێن
    if sv.feeling:
        st.markdown("#### کلیک بکە لە نەخشە بۆ دیاریکردنی شوێنت")
        m = folium.Map(location=[36.2, 44.0], zoom_start=6)
        if sv.latlon:
            folium.Marker(sv.latlon).add_to(m)
        res = st_folium(m, height=380, use_container_width=True)
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
        # reset
        sv.feeling, sv.issues, sv.latlon = None, set(), None
        st.session_state.page = "map"
