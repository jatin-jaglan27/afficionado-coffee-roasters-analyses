import streamlit as st
import pandas as pd
import plotly.express as px

# ------------------------------
# PAGE CONFIG
# ------------------------------
st.set_page_config(page_title="Coffee Sales Dashboard", layout="wide")

st.title("☕ Coffee Sales Analytics Dashboard")
st.caption("Time-Based Performance & Customer Behavior Analysis")

# ------------------------------
# LOAD DATA
# ------------------------------
@st.cache_data
def load_data():
    return pd.read_csv("Aficionado Coffee Roasters data.csv")

df = load_data()

# ------------------------------
# DATA CLEANING
# ------------------------------
df = df.drop_duplicates()
df = df.dropna(subset=["transaction_time", "transaction_qty", "unit_price"])

df["transaction_time"] = pd.to_datetime(df["transaction_time"], errors="coerce")

df = df[(df["transaction_qty"] > 0) & (df["unit_price"] > 0)]

# ------------------------------
# FEATURE ENGINEERING
# ------------------------------
df["revenue"] = df["transaction_qty"] * df["unit_price"]
df["hour"] = df["transaction_time"].dt.hour
df["day"] = df["transaction_time"].dt.day_name()
df["date"] = df["transaction_time"].dt.date
df["week"] = df["transaction_time"].dt.isocalendar().week

# Day order fix
day_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
df["day"] = pd.Categorical(df["day"], categories=day_order, ordered=True)

# Time bucket
def time_bucket(h):
    if 6 <= h <= 11: return "Morning"
    elif 12 <= h <= 16: return "Afternoon"
    elif 17 <= h <= 21: return "Evening"
    else: return "Late Hours"

df["time_bucket"] = df["hour"].apply(time_bucket)

# Weekday vs Weekend
df["day_type"] = df["day"].apply(lambda x: "Weekend" if x in ["Saturday","Sunday"] else "Weekday")

# ------------------------------
# SIDEBAR FILTERS
# ------------------------------
st.sidebar.header("🔍 Filters")

store_filter = st.sidebar.multiselect(
    "Store Location",
    df["store_location"].unique(),
    default=df["store_location"].unique()
)

day_filter = st.sidebar.multiselect(
    "Day of Week",
    day_order,
    default=day_order
)

hour_range = st.sidebar.slider("Hour Range", 0, 23, (0, 23))

metric_choice = st.sidebar.radio("Metric", ["Revenue", "Quantity"])

metric_col = "revenue" if metric_choice == "Revenue" else "transaction_qty"

# Apply filters
filtered_df = df[
    (df["store_location"].isin(store_filter)) &
    (df["day"].isin(day_filter)) &
    (df["hour"] >= hour_range[0]) &
    (df["hour"] <= hour_range[1])
]

# ------------------------------
# KPI SECTION
# ------------------------------
st.markdown("## 📊 Key Metrics")

col1, col2, col3 = st.columns(3)

col1.metric(f"Total {metric_choice}", f"{filtered_df[metric_col].sum():,.0f}")
col2.metric("Transactions", len(filtered_df))
col3.metric("Avg Order Value", f"{filtered_df['revenue'].mean():,.2f}")

# ------------------------------
# TABS
# ------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📈 Sales Trend",
    "📅 Day Analysis",
    "⏰ Time Analysis",
    "🏪 Location Analysis"
])

# ------------------------------
# SALES TREND
# ------------------------------
with tab1:
    st.subheader("Daily Sales Trend")

    daily = filtered_df.groupby("date")[metric_col].sum().reset_index()
    st.plotly_chart(px.line(daily, x="date", y=metric_col, markers=True), use_container_width=True)

    st.subheader("Weekly Trend")

    weekly = filtered_df.groupby("week")[metric_col].sum().reset_index()
    st.plotly_chart(px.bar(weekly, x="week", y=metric_col,
                           color_discrete_sequence=px.colors.sequential.Brwnyl),
                    use_container_width=True)

# ------------------------------
# DAY ANALYSIS
# ------------------------------
with tab2:
    st.subheader("Average Revenue by Day")

    avg_day = filtered_df.groupby("day")["revenue"].mean().reset_index().sort_values("day")
    st.plotly_chart(px.bar(avg_day, x="day", y="revenue",
                           color="day",
                           color_discrete_sequence=px.colors.sequential.Brwnyl),
                    use_container_width=True)

    st.subheader("Weekday vs Weekend")

    weekend = filtered_df.groupby("day_type")[metric_col].sum().reset_index()
    st.plotly_chart(px.pie(weekend, names="day_type", values=metric_col),
                    use_container_width=True)

# ------------------------------
# TIME ANALYSIS
# ------------------------------
with tab3:
    st.subheader("Hourly Demand")

    hourly = filtered_df.groupby("hour")[metric_col].sum().reset_index()
    st.plotly_chart(px.line(hourly, x="hour", y=metric_col, markers=True),
                    use_container_width=True)

    st.subheader("Time Bucket Analysis")

    bucket = filtered_df.groupby("time_bucket")[metric_col].sum().reset_index()
    st.plotly_chart(px.bar(bucket, x="time_bucket", y=metric_col,
                           color="time_bucket",
                           color_discrete_sequence=px.colors.sequential.Brwnyl),
                    use_container_width=True)

# ------------------------------
# LOCATION ANALYSIS
# ------------------------------
with tab4:
    st.subheader("Store Comparison")

    store_data = filtered_df.groupby("store_location")[metric_col].sum().reset_index()
    st.plotly_chart(px.bar(store_data, x="store_location", y=metric_col,
                           color="store_location"),
                    use_container_width=True)

    st.subheader("Hourly Heatmap")

    heatmap = filtered_df.pivot_table(
        values=metric_col,
        index="day",
        columns="hour",
        aggfunc="sum"
    )

    st.plotly_chart(px.imshow(heatmap, color_continuous_scale="Oranges"),
                    use_container_width=True)

# ------------------------------
# INTERACTIVE TABLES
# ------------------------------
st.markdown("## 🔎 Data Explorer")

search = st.text_input("Search Store/Product")

table_df = filtered_df.copy()

if search:
    table_df = table_df[
        table_df["store_location"].str.contains(search, case=False, na=False)
    ]

st.dataframe(table_df, use_container_width=True)

# ------------------------------
# LOCATION TABLE
# ------------------------------
st.markdown("## 🏪 Store Performance Table")

loc_table = filtered_df.groupby("store_location").agg({
    "revenue":"sum",
    "transaction_qty":"sum"
}).reset_index().sort_values("revenue", ascending=False)

st.dataframe(loc_table)

# ------------------------------
# DAY TABLE
# ------------------------------
st.markdown("## 📅 Day Performance Table")

day_table = filtered_df.groupby("day").agg({
    "revenue":"sum",
    "transaction_qty":"sum"
}).reset_index().sort_values("day")

st.dataframe(day_table)

# ------------------------------
# DOWNLOAD OPTION
# ------------------------------
st.download_button(
    "⬇️ Download Data",
    filtered_df.to_csv(index=False),
    file_name="coffee_data.csv",
    mime="text/csv"
)
