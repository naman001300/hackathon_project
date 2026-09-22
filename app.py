import pandas as pd
import plotly.express as px
import streamlit as st

from review_pipeline import analyze_reviews


st.set_page_config(page_title="ReviewPulse | Review Intelligence", page_icon="✦", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');

:root { --ink:#eaf1ff; --muted:#94a3b8; --panel:rgba(18,29,54,.82); --line:rgba(148,163,184,.15); --cyan:#42d9ff; --violet:#9b87f5; }
.stApp { background: radial-gradient(circle at 8% -12%, #223d7c 0, transparent 28%), radial-gradient(circle at 94% 7%, #512c70 0, transparent 25%), #09111f; color:var(--ink); font-family:'Manrope',sans-serif; }
[data-testid="stHeader"] { background:transparent; }
.block-container { max-width:1420px; padding:2.4rem 3rem 4rem; }
[data-testid="stSidebar"] { background:linear-gradient(180deg,#0e1930,#0a1120); border-right:1px solid var(--line); }
[data-testid="stSidebar"] > div:first-child { padding-top:2.2rem; }
h1,h2,h3 { font-family:'Manrope',sans-serif !important; letter-spacing:-.04em !important; color:#f8fbff !important; }
h2 { font-size:1.18rem !important; margin-top:2rem !important; }
.hero { padding:1.9rem 2rem; border:1px solid rgba(99,211,255,.23); border-radius:24px; background:linear-gradient(110deg,rgba(24,52,102,.88),rgba(49,32,83,.68)); box-shadow:0 20px 50px rgba(0,0,0,.2); margin-bottom:1.25rem; }
.eyebrow { color:var(--cyan); text-transform:uppercase; letter-spacing:.16em; font:500 .7rem 'DM Mono',monospace; margin-bottom:.55rem; }
.hero h1 { font-size:2.6rem !important; margin:0 !important; line-height:1.1; }
.hero p { color:#b7c6df; margin:.65rem 0 0; max-width:680px; font-size:.98rem; }
.source-pill { display:inline-block; margin-top:1rem; border:1px solid rgba(156,135,245,.35); background:rgba(155,135,245,.12); color:#d8d0ff; border-radius:999px; padding:.35rem .75rem; font:500 .69rem 'DM Mono',monospace; }
[data-testid="stMetric"] { background:var(--panel); border:1px solid var(--line); border-radius:17px; padding:1rem 1.1rem; min-height:115px; box-shadow:0 8px 28px rgba(0,0,0,.14); }
[data-testid="stMetricLabel"] { color:#9fb0ca !important; font-size:.74rem; text-transform:uppercase; letter-spacing:.08em; }
[data-testid="stMetricValue"] { color:#f6f9ff !important; font-size:1.75rem; }
[data-testid="stExpander"] { background:var(--panel); border:1px solid var(--line); border-radius:14px; margin-bottom:.65rem; overflow:hidden; }
[data-testid="stExpander"] summary { padding:.75rem .25rem; font-weight:700; }
.stPlotlyChart { border:1px solid var(--line); background:var(--panel); border-radius:18px; padding:.4rem; }
.stDataFrame { border:1px solid var(--line); border-radius:14px; overflow:hidden; }
.evidence { border-left:3px solid var(--cyan); background:rgba(45,71,118,.18); padding:.8rem 1rem; border-radius:0 10px 10px 0; margin:.65rem 0; color:#d8e3f5; }
.evidence-meta { color:#8ea3c3; font:500 .71rem 'DM Mono',monospace; margin-bottom:.35rem; }
.section-note { color:#95a9c5; margin-top:-.35rem; font-size:.86rem; }
.stButton > button { border-radius:10px; border:1px solid rgba(66,217,255,.4); background:rgba(66,217,255,.1); color:#cff7ff; }
div[data-baseweb="select"] > div, [data-testid="stFileUploader"] section { background:#101c34 !important; border-color:var(--line) !important; }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### ✦ ReviewPulse")
    st.caption("PRODUCT INTELLIGENCE CONSOLE")
    st.divider()
    st.markdown("#### Data source")
    uploaded = st.file_uploader("Upload review CSV", type="csv", label_visibility="collapsed")
    st.caption("Recognises `review`, `review_text`, `rating`, `date`, and `app_name` automatically.")
    st.divider()
    st.markdown("#### Analysis guardrails")
    st.caption("✓ PII scrubbed before display\n\n✓ Theme evidence retained\n\n✓ Sentiment drift monitored")

try:
    source = pd.read_csv(uploaded) if uploaded else pd.read_csv("reviews_clean.csv")
except Exception as error:
    st.error(f"Could not read the CSV: {error}")
    st.stop()

def find_column(options):
    return next((column for column in options if column in source.columns), None)

text_col = find_column(["review_text", "review", "text", "content", "comment"])
if not text_col:
    st.error("No review text column found. Add `review_text`, `review`, `text`, `content`, or `comment`.")
    st.stop()

id_col, rating_col = find_column(["review_id", "_id", "id"]), find_column(["rating", "score", "stars"])
date_col, product_col = find_column(["date", "created_at", "at"]), find_column(["product", "app_name", "product_name"])
label_col = find_column(["sentiment_label", "label", "sentiment"])
records = [{"review_id": row.get(id_col, index + 1), "review_text": row.get(text_col), "rating": row.get(rating_col) if rating_col else None, "date": row.get(date_col) if date_col else None, "product": row.get(product_col) if product_col else None, "sentiment_label": row.get(label_col) if label_col else None} for index, row in source.iterrows()]
result = analyze_reviews(records)
summary, quality, validation, drift = result["sentiment_counts"], result["quality"], result["validation"], result["drift"]
source_name = "your uploaded dataset" if uploaded else "bundled 10K review dataset"

st.markdown(f"""
<div class="hero">
  <div class="eyebrow">Customer feedback intelligence</div>
  <h1>Find what customers are<br>really telling you.</h1>
  <p>Turn unstructured reviews into clear product signals, while preserving traceability and protecting customer privacy.</p>
  <div class="source-pill">● LIVE ANALYSIS · {source_name.upper()}</div>
</div>
""", unsafe_allow_html=True)

cols = st.columns(5)
cols[0].metric("Reviews analysed", f"{result['total_reviews']:,}")
cols[1].metric("Positive signals", f"{summary['positive']:,}")
cols[2].metric("Negative signals", f"{summary['negative']:,}")
cols[3].metric("PII protected", f"{quality['pii_redacted_count']:,}")
cols[4].metric("Validation accuracy", f"{validation['accuracy']:.0%}" if validation["accuracy"] is not None else "Needs labels", help="Against a sentiment_label column, or a rating-derived proxy label.")

chart_theme = dict(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(family="Manrope", color="#c8d5ea"), margin=dict(l=15, r=15, t=20, b=15), height=330)
left, right = st.columns(2, gap="large")
with left:
    st.subheader("Sentiment landscape")
    st.markdown('<div class="section-note">A quick read on the overall customer mood.</div>', unsafe_allow_html=True)
    frame = pd.DataFrame({"Sentiment": list(summary), "Reviews": list(summary.values())})
    fig = px.bar(frame, x="Sentiment", y="Reviews", color="Sentiment", text="Reviews", color_discrete_map={"positive":"#3ddc97", "neutral":"#8fa4c8", "negative":"#ff6b81"})
    fig.update_layout(**chart_theme, showlegend=False); fig.update_traces(textposition="outside", marker_line_width=0)
    st.plotly_chart(fig, use_container_width=True)
with right:
    st.subheader("What people talk about")
    st.markdown('<div class="section-note">The recurring product areas inside customer conversations.</div>', unsafe_allow_html=True)
    themes = pd.DataFrame([{"Theme": item["name"].title(), "Reviews": item["count"]} for item in result["themes"]])
    fig = px.bar(themes.sort_values("Reviews"), x="Reviews", y="Theme", orientation="h", text="Reviews", color="Reviews", color_continuous_scale=["#34496f", "#43d7ff"])
    fig.update_layout(**chart_theme, coloraxis_showscale=False); fig.update_traces(textposition="outside", marker_line_width=0)
    st.plotly_chart(fig, use_container_width=True)

st.subheader("Evidence, not guesswork")
st.markdown('<div class="section-note">Every finding links back to protected customer language and the trigger terms used to classify it.</div>', unsafe_allow_html=True)
for theme in result["themes"]:
    with st.expander(f"{theme['name'].title()}  ·  {theme['count']:,} reviews"):
        for example in theme["examples"]:
            matched = ", ".join(example["signals"]) or "contextual match"
            st.markdown(f'<div class="evidence"><div class="evidence-meta">REVIEW {example["review_id"]} · {example["sentiment"].upper()} · SIGNALS: {matched}</div>{example["text"]}</div>', unsafe_allow_html=True)

if result["trend"]:
    st.subheader("Mood over time")
    st.markdown('<div class="section-note">Trend visibility helps product teams spot rising complaints before they become churn.</div>', unsafe_allow_html=True)
    trend = pd.DataFrame(result["trend"]).melt(id_vars="month", var_name="Sentiment", value_name="Reviews")
    fig = px.line(trend, x="month", y="Reviews", color="Sentiment", markers=True, color_discrete_map={"positive":"#3ddc97", "neutral":"#8fa4c8", "negative":"#ff6b81"})
    fig.update_layout(**chart_theme, legend=dict(orientation="h", y=1.15), xaxis_title=None, yaxis_title="Reviews")
    st.plotly_chart(fig, use_container_width=True)
    drift_label = f"{drift['score']:.3f}" if drift["score"] is not None else "N/A"
    st.info(f"Drift monitor · **{drift['status']}** · Jensen-Shannon divergence: **{drift_label}**. This compares the first and second halves of dated reviews.")

with st.expander("Quality & model notes"):
    st.write(f"Valid rows: {quality['valid_rows']:,} · Skipped: {quality['invalid_rows']:,} · Labelled validation rows: {validation['labelled_sample_size']:,}")
    st.caption("The offline lexicon model is deliberately explainable. Use a human-labelled sample before production decisions; rating-derived labels are only a proxy.")

st.subheader("Review audit trail")
st.markdown('<div class="section-note">All displayed text has already passed through PII redaction.</div>', unsafe_allow_html=True)
audit = pd.DataFrame(result["reviews"])
if not audit.empty:
    audit["themes"] = audit["themes"].apply(", ".join)
    audit["sentiment_signals"] = audit["sentiment_signals"].apply(", ".join)
    st.dataframe(audit[["review_id", "date", "product", "rating", "sentiment", "sentiment_signals", "themes", "text"]], use_container_width=True, hide_index=True, height=420)
