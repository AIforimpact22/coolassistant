# contribution.py – show the current user's contribution history
import psycopg2, streamlit as st
import pandas as pd

PG_URL = ("postgresql://cool_owner:npg_jpi5LdZUbvw1@"
          "ep-frosty-tooth-a283lla4-pooler.eu-central-1.aws.neon.tech/cool?sslmode=require")
TABLE  = "survey_responses"


def _fetch_rows(email: str, limit: int = 200):
    """Return a list of the user’s rows (newest first)."""
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
    """Render the contribution dashboard for the given user e-mail."""
    st.title("📊 Your contribution history")

    rows = _fetch_rows(email)
    if not rows:
        st.info("You have not submitted any feedback yet.")
        return

    # Summary
    st.subheader("Summary")
    df = pd.DataFrame(rows, columns=["timestamp", "lat", "lon", "feeling", "issues"])
    st.write(f"Total submissions: **{len(df):,}**")
    st.write(f"Last submission: **{df['timestamp'].max()}**")

    # Feeling counts
    counts = df["feeling"].str.split().str[0].value_counts()  # only emoji part
    st.bar_chart(counts)

    # Detailed table (hide index for clarity)
    st.subheader("Recent submissions")
    st.dataframe(df.style.hide(axis="index"), use_container_width=True)
