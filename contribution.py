# contribution.py – show current user's recent submissions only
import psycopg2, streamlit as st
import pandas as pd

PG_URL = ("postgresql://cool_owner:npg_jpi5LdZUbvw1@"
          "ep-frosty-tooth-a283lla4-pooler.eu-central-1.aws.neon.tech/cool?sslmode=require")
TABLE = "survey_responses"


def _fetch_rows(email: str, limit: int = 200):
    """Return recent rows for this user (newest first)."""
    with psycopg2.connect(PG_URL) as con, con.cursor() as cur:
        cur.execute(
            f"""SELECT ts, lat, lon, feeling, issues
                  FROM {TABLE}
                 WHERE user_email = %s
              ORDER BY ts DESC
                 LIMIT %s;""",
            (email, limit),
        )
        return cur.fetchall()


def show_history(email: str) -> None:
    """Render the ‘My history’ page for the logged-in user."""
    st.title("📊 دوایین بەشداریکردنت")

    rows = _fetch_rows(email)
    if not rows:
        st.info("You have not submitted any feedback yet.")
        return

    df = pd.DataFrame(rows, columns=["timestamp", "latitude", "longitude", "feeling", "issues"])
    st.dataframe(df.style.hide(axis="index"), use_container_width=True)
