
import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(
    page_title="Japanese Insurance Nayose",
    page_icon="🔎",
    layout="wide"
)

BASE_DIR = Path(__file__).resolve().parent
report_path = BASE_DIR / "nayose_matching_report.csv"
review_path = BASE_DIR / "nayose_review.csv"

st.title("Japanese Insurance Nayose Matching Dashboard")
st.caption("Synthetic customer matching and review")

if not report_path.exists():
    st.error("Matching report not found. Run nayose_matching.py first.")
    st.stop()

report = pd.read_csv(report_path, dtype=str).fillna("")

score_columns = [
    "name_score", "kanji_score", "kana_score",
    "romaji_score", "address_score",
    "phone_score", "overall_score"
]

for column in score_columns:
    if column in report.columns:
        report[column] = pd.to_numeric(
            report[column], errors="coerce"
        ).fillna(0)

col1, col2, col3, col4 = st.columns(4)

col1.metric("Source Customers", report["source_customer_id"].nunique())
col2.metric("Target Customers", report["target_customer_id"].nunique())
col3.metric("Pairs Compared", len(report))
col4.metric(
    "Pairs to Review",
    int((report["match_category"] == "Review Required").sum())
)

st.divider()
st.subheader("Match Category Summary")

summary = report["match_category"].value_counts()
st.bar_chart(summary)

st.divider()
st.subheader("Search and Filter")

categories = sorted(report["match_category"].unique())
selected = st.multiselect(
    "Match category",
    categories,
    default=categories
)

search = st.text_input("Search customer ID or name")

filtered = report[
    report["match_category"].isin(selected)
].copy()

if search.strip():
    columns = [
        "source_customer_id", "source_name_kanji",
        "source_name_kana", "source_name_romaji",
        "target_customer_id", "target_name_kanji",
        "target_name_kana", "target_name_romaji"
    ]

    mask = pd.Series(False, index=filtered.index)
    for column in columns:
        if column in filtered.columns:
            mask |= filtered[column].str.contains(
                search.strip(), case=False, regex=False
            )
    filtered = filtered[mask]

filtered = filtered.sort_values(
    "overall_score", ascending=False
)

st.write(f"Candidate pairs: {len(filtered)}")
st.dataframe(filtered, use_container_width=True, hide_index=True)

st.download_button(
    "Download filtered results as CSV",
    data=filtered.to_csv(index=False).encode("utf-8-sig"),
    file_name="nayose_filtered_results.csv",
    mime="text/csv"
)

st.divider()
st.subheader("Manual Review")

if review_path.exists():
    review = pd.read_csv(review_path, dtype=str).fillna("")
    if review.empty:
        st.success("No candidates currently require review.")
    else:
        st.dataframe(review, use_container_width=True, hide_index=True)
else:
    st.warning("Review report not found. Run nayose_matching.py first.")

st.caption(
    "Demo uses synthetic data. Similarity scores do not prove identity."
)
