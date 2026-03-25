import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px

st.set_page_config(
    page_title="FTSE 100 Diversity Index",
    page_icon="📊",
    layout="wide"
)

st.title("FTSE 100 Diversity Index")
st.markdown(
    """
    This app presents a diversity index built from FTSE 100 diversity indicators.
    Scores were constructed using min-max normalisation, direction adjustment for pay-gap metrics,
    and equal weighting across indicators.
    """
)

# -----------------------------
# Load and prepare data
# -----------------------------
@st.cache_data
def load_data():
    df = pd.read_excel("FTSE100 Index _ Data.xlsx", sheet_name="diversity_indicators")
    df = df.replace("MISSING", np.nan)

    id_cols = ["company_name", "ticker"]
    indicator_cols = [col for col in df.columns if col not in id_cols]

    df[indicator_cols] = df[indicator_cols].apply(pd.to_numeric, errors="coerce")
    df[indicator_cols] = df[indicator_cols].fillna(0)

    scaled_df = df.copy()

    for col in indicator_cols:
        min_value = scaled_df[col].min()
        max_value = scaled_df[col].max()

        if max_value - min_value != 0:
            scaled_df[col] = (scaled_df[col] - min_value) / (max_value - min_value)
        else:
            scaled_df[col] = 0.0

    reverse_scaled_cols = [
        "equality_gender_pay",
        "equality_gender_pay_previous",
        "equality_bame_pay",
        "equality_lgbt_pay",
        "equality_disability_pay",
        "equality_gender_bonus",
    ]

    for col in reverse_scaled_cols:
        if col in scaled_df.columns:
            scaled_df[col] = 1 - scaled_df[col]

    scaled_df["diversity_score"] = scaled_df[indicator_cols].mean(axis=1)
    scaled_df["rank"] = scaled_df["diversity_score"].rank(
        ascending=False, method="min"
    ).astype(int)

    scaled_df = scaled_df.sort_values(by="rank").reset_index(drop=True)

    return df, scaled_df, indicator_cols


df, scaled_df, indicator_cols = load_data()

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.header("Explore")
company_list = scaled_df["company_name"].tolist()
selected_company = st.sidebar.selectbox("Select a company", company_list)

show_top_n = st.sidebar.slider("Top / Bottom N companies", min_value=5, max_value=20, value=10)

# -----------------------------
# Top metrics
# -----------------------------
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Number of companies", len(scaled_df))

with col2:
    st.metric("Highest score", f"{scaled_df['diversity_score'].max():.3f}")

with col3:
    st.metric("Lowest score", f"{scaled_df['diversity_score'].min():.3f}")

# -----------------------------
# Ranking table
# -----------------------------
st.subheader("Full Ranking Table")
ranking_display = scaled_df[["rank", "company_name", "ticker", "diversity_score"]].copy()
ranking_display["diversity_score"] = ranking_display["diversity_score"].round(3)
st.dataframe(ranking_display, use_container_width=True)

# -----------------------------
# Top and bottom charts
# -----------------------------
top_n = scaled_df.sort_values(by="diversity_score", ascending=False).head(show_top_n)
bottom_n = scaled_df.sort_values(by="diversity_score", ascending=True).head(show_top_n)

col4, col5 = st.columns(2)

with col4:
    st.subheader(f"Top {show_top_n} Companies")
    fig_top = px.bar(
        top_n,
        x="company_name",
        y="diversity_score",
        hover_data=["rank", "ticker"],
        title=f"Top {show_top_n} FTSE 100 Companies by Diversity Score"
    )
    fig_top.update_layout(xaxis_title="Company", yaxis_title="Diversity Score")
    st.plotly_chart(fig_top, use_container_width=True)

with col5:
    st.subheader(f"Bottom {show_top_n} Companies")
    fig_bottom = px.bar(
        bottom_n,
        x="company_name",
        y="diversity_score",
        hover_data=["rank", "ticker"],
        title=f"Bottom {show_top_n} FTSE 100 Companies by Diversity Score"
    )
    fig_bottom.update_layout(xaxis_title="Company", yaxis_title="Diversity Score")
    st.plotly_chart(fig_bottom, use_container_width=True)

# -----------------------------
# Score distribution
# -----------------------------
st.subheader("Distribution of Diversity Scores")
fig_dist = px.histogram(
    scaled_df,
    x="diversity_score",
    nbins=20,
    title="Distribution of Diversity Scores"
)
fig_dist.update_layout(xaxis_title="Diversity Score", yaxis_title="Frequency")
st.plotly_chart(fig_dist, use_container_width=True)

# -----------------------------
# Company detail section
# -----------------------------
st.subheader("Company-Level View")

company_row_scaled = scaled_df[scaled_df["company_name"] == selected_company].iloc[0]
company_row_raw = df[df["company_name"] == selected_company].iloc[0]

col6, col7, col8 = st.columns(3)

with col6:
    st.metric("Selected company", company_row_scaled["company_name"])

with col7:
    st.metric("Rank", int(company_row_scaled["rank"]))

with col8:
    st.metric("Diversity score", f"{company_row_scaled['diversity_score']:.3f}")

indicator_table = pd.DataFrame({
    "indicator": indicator_cols,
    "raw_value": [company_row_raw[col] for col in indicator_cols],
    "scaled_value": [company_row_scaled[col] for col in indicator_cols]
})
indicator_table["scaled_value"] = indicator_table["scaled_value"].round(3)

st.dataframe(indicator_table, use_container_width=True)

st.subheader(f"Indicator Profile: {selected_company}")
fig_company = px.bar(
    indicator_table.sort_values("scaled_value", ascending=False),
    x="indicator",
    y="scaled_value",
    title=f"Scaled Indicator Scores for {selected_company}"
)
fig_company.update_layout(
    xaxis_title="Indicator",
    yaxis_title="Scaled Value",
    xaxis_tickangle=-60
)
st.plotly_chart(fig_company, use_container_width=True)

# -----------------------------
# Methodology section
# -----------------------------
st.subheader("Methodology")
st.markdown(
    """
    - Missing values labelled as `MISSING` were converted to `NaN`, then treated as zero contribution.
    - All indicators were converted to numeric values.
    - Min-max normalisation was applied to place all indicators on a 0–1 scale.
    - Pay-gap style indicators were reversed so that higher values consistently reflect stronger diversity performance.
    - The final diversity score was calculated as the mean of all scaled indicators.
    - Companies were ranked from highest to lowest diversity score.
    """
)