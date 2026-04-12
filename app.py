"""
Bruce's Data Viz Tool
Drag & drop data files → instant visualizations for non-data scientists
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import io
import sys

st.set_page_config(
    page_title="Bruce's Data Viz Tool",
    page_icon="📊",
    layout="wide"
)

# ── Custom CSS ──────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A5F;
        text-align: center;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #6C757D;
        text-align: center;
        margin-bottom: 2rem;
    }
    .upload-box {
        border: 2px dashed #1E3A5F;
        border-radius: 12px;
        padding: 3rem 2rem;
        text-align: center;
        background: #F8F9FA;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #1E3A5F;
        color: white;
        border-radius: 10px;
        padding: 1rem 1.5rem;
        text-align: center;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        border-radius: 8px 8px 0 0;
    }
</style>
""", unsafe_allow_html=True)

# ── Header ──────────────────────────────────────────────────
st.markdown('<p class="main-header">📊 Bruce\'s Data Viz Tool</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Drag & drop your data — get instant insights. No coding required.</p>', unsafe_allow_html=True)

# ── File Upload ─────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "📁 Upload your CSV or Excel file",
    type=["csv", "xlsx", "xls"],
    help="Supported: .csv, .xlsx, .xls"
)

df = None

if uploaded_file is not None:
    try:
        if uploaded_file.name.endswith(".csv"):
            df = pd.read_csv(uploaded_file)
        else:
            df = pd.read_excel(uploaded_file)
        
        st.success(f"✅ Loaded `{uploaded_file.name}` — {df.shape[0]} rows × {df.shape[1]} columns")
    except Exception as e:
        st.error(f"❌ Failed to load file: {e}")
        st.stop()
else:
    st.info("👆 Upload a file above to get started")
    st.stop()

# ── Auto-detect column types ─────────────────────────────────
def get_column_type(series):
    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"
    elif pd.api.types.is_numeric_dtype(series):
        return "numeric"
    else:
        return "categorical"

df.columns = df.columns.str.strip()

col_types = {col: get_column_type(df[col]) for col in df.columns}
num_cols = [c for c, t in col_types.items() if t == "numeric"]
cat_cols = [c for c, t in col_types.items() if t == "categorical"]
date_cols = [c for c, t in col_types.items() if t == "datetime"]

# ── Sidebar: Data Summary ────────────────────────────────────
with st.sidebar:
    st.header("📋 Data Summary")
    
    st.metric("Rows", df.shape[0])
    st.metric("Columns", df.shape[1])
    st.metric("Numeric cols", len(num_cols))
    
    st.subheader("Column Types")
    for col, ctype in col_types.items():
        emoji = {"numeric": "🔢", "datetime": "📅", "categorical": "🏷️"}[ctype]
        st.write(f"{emoji} `{col}` — {ctype}")

# ── Quick Stats ─────────────────────────────────────────────
st.subheader("📈 Quick Statistics")
tab_stat, tab_head = st.tabs(["📊 Statistics", "🔍 Data Preview"])

with tab_stat:
    if len(num_cols) > 0:
        st.dataframe(df[num_cols].describe(), use_container_width=True)
    else:
        st.info("No numeric columns found for statistics.")

with tab_head:
    st.dataframe(df.head(10), use_container_width=True)

st.divider()

# ── Visualization Section ───────────────────────────────────
st.subheader("🎨 Visualizations")

viz_tab1, viz_tab2, viz_tab3 = st.tabs(["📈 Time Series", "�散 Scatter Plot", "📊 Statistics"])

# ── Time Series ──────────────────────────────────────────────
with viz_tab1:
    st.markdown("**Select columns for time series visualization**")
    
    x_col = st.selectbox("X-axis (usually time/date)", date_cols if date_cols else df.columns.tolist(), key="ts_x")
    y_col = st.selectbox("Y-axis (value to plot)", num_cols if num_cols else ["(no numeric columns)"], key="ts_y")
    
    if x_col and y_col and y_col != "(no numeric columns)":
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            height = st.slider("Chart height (px)", 300, 800, 450, key="ts_h")
        with col2:
            color_col = st.selectbox("Group by (optional)", ["None"] + cat_cols, key="ts_color")
        
        color_arg = color_col if color_col != "None" else None
        
        fig = px.line(
            df, x=x_col, y=y_col,
            color=color_arg,
            title=f"{y_col} over {x_col}",
            height=height,
            markers=True
        )
        fig.update_layout(
            template="plotly_white",
            title_font_size=18,
            legend_title_text=color_arg if color_arg else None
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Download
        buf = io.StringIO()
        fig.write_html(buf)
        st.download_button("📥 Download HTML", buf.getvalue(), f"{y_col}_timeseries.html", "text/html", key="dl_ts")
    else:
        st.warning("⚠️ Need at least one date/datetime column and one numeric column for time series.")

# ── Scatter Plot ─────────────────────────────────────────────
with viz_tab2:
    st.markdown("**Explore relationships between two numeric variables**")
    
    sc_x = st.selectbox("X-axis", num_cols if num_cols else df.columns.tolist(), key="sc_x")
    sc_y = st.selectbox("Y-axis", num_cols if num_cols else ["(no numeric columns)"], key="sc_y")
    sc_color = st.selectbox("Color by (optional)", ["None"] + cat_cols, key="sc_color")
    sc_size = st.selectbox("Size by (optional)", ["None"] + num_cols, key="sc_size")
    
    if sc_y != "(no numeric columns)":
        col1, col2 = st.columns([1, 1])
        with col1:
            height = st.slider("Chart height (px)", 300, 800, 500, key="sc_h")
        with col2:
            show_reg = st.checkbox("Show regression line", value=False, key="sc_reg")
        
        color_arg = sc_color if sc_color != "None" else None
        size_arg = sc_size if sc_size != "None" else None
        
        fig = px.scatter(
            df, x=sc_x, y=sc_y,
            color=color_arg,
            size=size_arg,
            title=f"{sc_y} vs {sc_x}",
            height=height,
            opacity=0.7
        )
        
        if show_reg and color_arg is None:
            fig.update_layout(shapes=[
                dict(
                    type="line",
                    x0=df[sc_x].min(), x1=df[sc_x].max(),
                    y0=df[sc_x].min() * (df[sc_y].std() / df[sc_x].std()) + df[sc_y].mean() - (df[sc_x].std() / df[sc_x].std()) * df[sc_x].mean(),
                    y1=df[sc_x].max() * (df[sc_y].std() / df[sc_x].std()) + df[sc_y].mean() - (df[sc_x].std() / df[sc_x].std()) * df[sc_x].mean(),
                    line=dict(color="red", width=2, dash="dot")
                )
            ])
        
        fig.update_layout(template="plotly_white", title_font_size=18)
        st.plotly_chart(fig, use_container_width=True)
        
        buf = io.StringIO()
        fig.write_html(buf)
        st.download_button("📥 Download HTML", buf.getvalue(), f"{sc_y}_vs_{sc_x}_scatter.html", "text/html", key="dl_sc")
    else:
        st.warning("⚠️ Need at least two numeric columns for scatter plot.")

# ── Statistics Plots ─────────────────────────────────────────
with viz_tab3:
    st.markdown("**Distribution & statistical visualizations**")
    
    stat_type = st.selectbox(
        "Choose chart type",
        [
            "📊 Histogram (Distribution)",
            "📦 Box Plot (Distribution by Category)",
            "🎯 Density Plot",
            "📈 Bar Chart (Categorical counts)",
            "🔥 Correlation Heatmap"
        ],
        key="stat_type"
    )
    
    col1, col2 = st.columns([1, 2])
    with col1:
        height = st.slider("Chart height (px)", 300, 700, 450, key="stat_h")
    
    if stat_type == "📊 Histogram (Distribution)":
        hist_col = st.selectbox("Select column", num_cols if num_cols else df.columns.tolist(), key="hist_col")
        bins = st.slider("Number of bins", 5, 100, 30, key="hist_bins")
        
        fig = px.histogram(
            df, x=hist_col, nbins=bins,
            title=f"Distribution of {hist_col}",
            height=height,
            color_discrete_sequence=["#1E3A5F"]
        )
        fig.update_layout(template="plotly_white", bargap=0.1)
        st.plotly_chart(fig, use_container_width=True)
        
    elif stat_type == "📦 Box Plot (Distribution by Category)":
        val_col = st.selectbox("Value column (numeric)", num_cols, key="box_val")
        cat_col = st.selectbox("Category column", cat_cols if cat_cols else df.columns.tolist(), key="box_cat")
        
        fig = px.box(
            df, x=cat_col, y=val_col,
            title=f"{val_col} by {cat_col}",
            height=height,
            color=cat_col,
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        fig.update_layout(template="plotly_white", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
    elif stat_type == "🎯 Density Plot":
        dense_col = st.selectbox("Select column", num_cols if num_cols else df.columns.tolist(), key="dense_col")
        
        fig = px.histogram(
            df, x=dense_col, nbins=50,
            title=f"Density of {dense_col}",
            height=height,
            histnorm="density",
            color_discrete_sequence=["#4C78A8"]
        )
        fig.update_layout(template="plotly_white", bargap=0.05)
        st.plotly_chart(fig, use_container_width=True)
        
    elif stat_type == "📈 Bar Chart (Categorical counts)":
        bar_col = st.selectbox("Select column", cat_cols if cat_cols else df.columns.tolist(), key="bar_col")
        top_n = st.slider("Show top N categories", 5, 50, 20, key="bar_top")
        
        top_cats = df[bar_col].value_counts().head(top_n)
        fig = px.bar(
            x=top_cats.index, y=top_cats.values,
            title=f"Top {top_n} {bar_col}",
            height=height,
            color=top_cats.values,
            color_continuous_scale="Blues"
        )
        fig.update_layout(template="plotly_white", xaxis_title=bar_col, yaxis_title="Count", showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
        
    elif stat_type == "🔥 Correlation Heatmap":
        if len(num_cols) < 2:
            st.warning("⚠️ Need at least 2 numeric columns for correlation heatmap.")
        else:
            corr = df[num_cols].corr()
            fig = px.imshow(
                corr,
                text_auto=True,
                title="Correlation Heatmap",
                height=height,
                color_continuous_scale="RdBu_r",
                aspect="auto"
            )
            fig.update_layout(template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
            
            buf = io.StringIO()
            fig.write_html(buf)
            st.download_button("📥 Download HTML", buf.getvalue(), "correlation_heatmap.html", "text/html", key="dl_corr")

st.divider()

# ── Export Data ──────────────────────────────────────────────
with st.expander("📤 Export Processed Data"):
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            "📄 Download as CSV",
            df.to_csv(index=False).encode(),
            f"processed_data.csv",
            "text/csv"
        )
    with col2:
        st.download_button(
            "📗 Download as Excel",
            df.to_excel(index=False, engine="openpyxl"),
            f"processed_data.xlsx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

st.caption("Built with Streamlit + Plotly · Bruce's Data Viz Tool")
