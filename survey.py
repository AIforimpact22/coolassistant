# survey.py – هەست و کێشەی کەشوهەوا (one row / 24 h)
import datetime as dt
import psycopg2, streamlit as st, folium
from streamlit_folium import st_folium

PG_URL = ("postgresql://cool_owner:npg_jpi5LdZUbvw1@"
          "ep-frosty-tooth-a283lla4-pooler.eu-central-1.aws.neon.tech/cool?sslmode=require")
TABLE = "survey_responses"


def _has_recent(email: str) -> bool:
    with psycopg2.connect(PG_URL) as con, con.cursor() as cur:
        cur.execute(
            f"""SELECT 1
                  FROM {TABLE}
                 WHERE user_email = %s
                   AND ts > NOW() - INTERVAL '24 hours'
              LIMIT 1;""",
            (email,),
        )
        return cur.fetchone() is not None


def show(save_row_fn, user_email: str) -> None:
    sv = st.session_state
    sv.setdefault("feeling", None)
    sv.setdefault("issues", set())
    sv.setdefault("latlon", None)

    if _has_recent(user_email):
        st.warning("👋 تەواوە! پێشتر لە ماوەی ٢٤ کاتژمێر وەڵامەکەت تۆمار کراوە.")
        return

    st.title("نەخشەی هەستمان بەرامبەر بە کەشوهەوا")

    # ١ – feeling
    st.markdown("#### هەستت چۆنە بەرامبەر بە کەشوهەوا؟")
    emojis = ["😃", "😐", "☹️", "😫"]
    cols = st.columns(4)
    for i, emo in enumerate(emojis):
        if cols[i].button(emo, key=f"emo{i}",
                          type="primary" if sv.feeling == emo else "secondary"):
            sv.feeling = emo
    if not sv.feeling:
        return   # wait until a feeling is chosen

    st.success(sv.feeling)

    # ٢ – issues (only if NOT happy)
    if sv.feeling != "😃":
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

    # ٣ – location picker
    st.markdown("#### کلیک بکە لە نەخشە بۆ دیاریکردنی شوێنت")
    mp = folium.Map(location=[36.2, 44.0], zoom_start=6)
    if sv.latlon:
        folium.Marker(sv.latlon).add_to(mp)
    res = st_folium(mp, height=380, use_container_width=True)
    if res and res.get("last_clicked"):
        sv.latlon = (res["last_clicked"]["lat"], res["last_clicked"]["lng"])
        st.toast("شوێن دیاریکرا", icon="📍")
    if not sv.latlon:
        return

    st.success(f"{sv.latlon[0]:.3f}, {sv.latlon[1]:.3f}")

    # ٤ – submit
    if st.button("🚀 ناردن", type="primary"):
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
        st.session_state.page = "map"
