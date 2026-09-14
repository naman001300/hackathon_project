import pandas as pd
import plotly.express as px
import streamlit as st

from review_pipeline import analyze_reviews


st.set_page_config(page_title="Review Analyzer", page_icon="📊", layout="wide")

st.title("Customer Review Analyzer")
st.caption("Upload a cleaned review CSV to analyse sentiment and customer themes.")

uploaded_file = st.file_uploader("Upload reviews_clean.csv", type=["csv"])

if uploaded_file is None:
    st.info("Upload a CSV with review_id and review_text columns to begin.")
    st.stop()

try:
    dataframe = pd.read_csv(uploaded_file)
except Exception as error:
    st.error(f"Could not read the CSV: {error}")
    st.stop()

required_columns = {"review_id", "review_text"}
missing_columns = required_columns - set(dataframe.columns)
if missing_columns:
    st.error(f"Missing required columns: {', '.join(sorted(missing_columns))}")
    st.stop()

result = analyze_reviews(dataframe.to_dict("records"))
summary = result["sentiment_summary"]
quality = result["quality"]

metric_columns = st.columns(4)
metric_columns[0].metric("Reviews", result["total_reviews"])
metric_columns[1].metric("Positive", summary["positive"])
metric_columns[2].metric("Negative", summary["negative"])
metric_columns[3].metric("PII redacted", quality["pii_redacted_count"])

left_column, right_column = st.columns(2)

with left_column:
    sentiment_data = pd.DataFrame(
        {"sentiment": list(summary.keys()), "count": list(summary.values())}
    )
    st.subheader("Sentiment")
    st.plotly_chart(
        px.bar(
            sentiment_data,
            x="sentiment",
            y="count",
            color="sentiment",
            color_discrete_map={
                "positive": "#15803d",
                "neutral": "#64748b",
                "negative": "#dc2626",
            },
        ),
        use_container_width=True,
    )

with right_column:
    theme_data = pd.DataFrame(
        [{"theme": item["name"], "count": item["count"]} for item in result["themes"]]
    )
    st.subheader("Common themes")
    if theme_data.empty:
        st.info("No themes found.")
    else:
        st.plotly_chart(
            px.bar(theme_data, x="theme", y="count", color="theme"),
            use_container_width=True,
        )

st.subheader("Theme examples")
for theme in result["themes"]:
    with st.expander(f'{theme["name"].title()} ({theme["count"]})'):
        for example in theme["examples"]:
            st.write(f'**{example["review_id"]}:** {example["text"]}')

st.subheader("Processed reviews")
review_data = pd.DataFrame(result["reviews"])
if not review_data.empty:
    review_data["themes"] = review_data["themes"].apply(
        lambda themes: ", ".join(themes)
    )
st.dataframe(review_data, use_container_width=True, hide_index=True)

if quality["invalid_rows"]:
    st.warning(f'{quality["invalid_rows"]} rows were skipped as invalid.')