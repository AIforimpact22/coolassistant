# map.py – heat-map + big-view toggle + survey redirect
import psycopg2, streamlit as st, folium
from folium.plugins import HeatMap, Fullscreen
from streamlit_folium import st_folium

PG_URL = ("postgresql://cool_owner:npg_jpi5LdZUbvw1@"
          "ep-frosty-tooth-a283lla4-pooler.eu-central-1.aws.neon.tech/cool?sslmode=require")
TABLE  = "survey_responses"


# ───────── fetch recent rows ─────────
def fetch_rows(limit: int = 1000):
    with psycopg2.connect(PG_URL) as con, con.cursor() as cur:
        cur.execute(
            f"""SELECT lat, lon, feeling
                  FROM {TABLE}
              ORDER BY ts DESC
                 LIMIT %s;""",
            (limit,),
        )
        return cur.fetchall()


# ───────── safe rerun helper ─────────
def _safe_rerun():
    """Streamlit >=1.28 has st.rerun(); older versions use experimental."""
    if hasattr(st, "rerun"):
        st.rerun()
    else:
        st.experimental_rerun()


# ───────── main UI ─────────
def show_heatmap():
    st.title("🗺️ نەخشەی هەستەکان بەرامبەر بە کەشوهەوا")

    big = st.toggle("🔍 View larger map", value=False)

    rows = fetch_rows()
    if not rows:
        st.info("هێشتا هیچ دێتەیەک نییە.")
        return

    weights = {"😃": 1, "😐": 0.66, "☹️": 0.33, "😫": 0}
    heat = [[lat, lon, weights.get(feel.split()[0], 0.5)]
            for lat, lon, feel in rows]

    # ───── legend ─────
    for col, emo, slot in zip(
            ["green", "blue", "orange", "red"],
            ["😃", "😐", "☹️", "😫"],
            st.columns(4)):
        slot.markdown(
            f"<div style='background:{col};color:#fff;width:60px;height:60px;"
            "display:flex;align-items:center;justify-content:center;border-radius:8px;"
            "font-size:28px;'>"
            f"{emo}</div>",
            unsafe_allow_html=True,
        )

    # ───── Folium map ─────
    m = folium.Map(location=[36.2, 44.0], zoom_start=6)
    HeatMap(
        heat,
        gradient={"0": "red", "0.33": "orange", "0.66": "blue", "1": "green"},
        min_opacity=0.25,
        max_opacity=0.9,
        radius=35,
        blur=20,
    ).add_to(m)
    Fullscreen(position="topright").add_to(m)

    st_folium(
        m,
        height=800 if big else 550,
        use_container_width=True
    )

    # ───── jump to survey ─────
    if st.button("📝 بەشداربە لە ڕاپرسی", type="primary"):
        st.session_state.page = "survey"
        _safe_rerun()
