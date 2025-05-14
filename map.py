# map.py – switchable interpolation demo
import io, base64
import numpy as np
import psycopg2, streamlit as st, folium
from folium.plugins import HeatMap, Fullscreen
from PIL import Image
from streamlit_folium import st_folium

PG_URL = ("postgresql://cool_owner:npg_jpi5LdZUbvw1@"
          "ep-frosty-tooth-a283lla4-pooler.eu-central-1.aws.neon.tech/cool?sslmode=require")
TABLE = "survey_responses"


def fetch_rows(limit=2000):
    with psycopg2.connect(PG_URL) as con, con.cursor() as cur:
        cur.execute(f"""
            SELECT lat, lon, feeling
              FROM {TABLE}
          ORDER BY ts DESC
             LIMIT %s;""", (limit,))
        return cur.fetchall()


def idw_grid(points, values, bbox, res=200, power=2):
    """
    Make an inverse-distance-weighted raster (NumPy only).
    points : (N,2) array of [lat,lon]
    values : (N,)     weight values (0-1)
    bbox   : [minLat,maxLat,minLon,maxLon]
    """
    yi, xi = np.linspace(bbox[0], bbox[1], res), np.linspace(bbox[2], bbox[3], res)
    X, Y    = np.meshgrid(xi, yi)
    grid    = np.zeros_like(X, dtype=float)
    denom   = np.zeros_like(X, dtype=float)

    for (lat, lon), v in zip(points, values):
        d2 = (X - lon) ** 2 + (Y - lat) ** 2   # lat/lon ≈ euclidean at small extents
        # avoid zero division
        w  = 1.0 / np.maximum(d2, 1e-12) ** (power / 2)
        grid  += w * v
        denom += w
    grid /= denom
    return grid  # 0-1 floats


def grid_to_png(grid, cmap=('red', 'orange', 'blue', 'green')):
    """Convert 0-1 grid → RGBA PNG bytes with simple 4-colour ramp."""
    lut = np.array([
        (255,   0,   0),      # red   (worst)
        (255, 165,   0),      # orange
        ( 30, 144, 255),      # blue
        ( 34, 139,  34)       # green (best)
    ], dtype=np.uint8)
    idx = (grid * (len(lut) - 1)).astype(int)
    rgb = lut[idx]
    img = Image.fromarray(rgb, mode="RGB").convert("RGBA")
    img.putalpha(150)   # semi-transparent
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def show_heatmap():
    st.title("🗺️ نەخشەی هەستەکان بەرامبەر بە کەشوهەوا")

    interp = st.selectbox("Interpolation method",
                          ("Kernel heat-map", "IDW surface"))

    rows = fetch_rows()
    if not rows:
        st.info("No data yet.")
        return

    # map base
    m = folium.Map(location=[36.2, 44.0], zoom_start=6)
    Fullscreen().add_to(m)

    # common legend
    weights = {"😃": 1, "😐": 0.66, "☹️": 0.33, "😫": 0}
    lg_cols = st.columns(4)
    for c, (col, emo) in zip(
        lg_cols, [("green", "😃"), ("blue", "😐"), ("orange", "☹️"), ("red", "😫")]
    ):
        c.markdown(
            f"<div style='background:{col};color:#fff;width:60px;height:60px;"
            f"display:flex;align-items:center;justify-content:center;border-radius:8px;"
            f"font-size:28px;'>{emo}</div>",
            unsafe_allow_html=True,
        )

    # points & values
    pts = np.array([[lat, lon] for lat, lon, _ in rows])
    vals = np.array([weights.get(f.split()[0], 0.5) for _, _, f in rows])

    if interp == "Kernel heat-map":
        HeatMap(
            np.column_stack((pts, vals)),
            gradient={"0": "red", "0.33": "orange", "0.66": "blue", "1": "green"},
            min_opacity=0.25, max_opacity=0.9, radius=35, blur=20
        ).add_to(m)

    else:  # IDW
        bbox = [pts[:, 0].min(), pts[:, 0].max(), pts[:, 1].min(), pts[:, 1].max()]
        grid = idw_grid(pts, vals, bbox, res=300)
        png  = grid_to_png(grid)

        # overlay as ImageOverlay
        folium.raster_layers.ImageOverlay(
            image=f"data:image/png;base64,{base64.b64encode(png).decode()}",
            bounds=[[bbox[0], bbox[2]], [bbox[1], bbox[3]]],
            opacity=0.8,
            interactive=False,
        ).add_to(m)

    st_folium(m, height=650, use_container_width=True)
