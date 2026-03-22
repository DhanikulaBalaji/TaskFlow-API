import streamlit as st
import requests
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

API_URL = "http://localhost:8000"

st.set_page_config(page_title="TaskFlow Dashboard", layout="wide")
st.title("TaskFlow API Dashboard")

try:
    metrics_response = requests.get(f"{API_URL}/metrics", timeout=5)
    metrics_data = metrics_response.json()
except Exception:
    st.error("Could not connect to TaskFlow API. Make sure the API is running on localhost:8000")
    st.stop()

if not metrics_data:
    st.info("No telemetry data yet. Make some API requests first.")
    st.stop()

col1, col2 = st.columns(2)

endpoints = list(metrics_data.keys())
request_counts = [v["request_count"] for v in metrics_data.values()]
avg_times = [v["average_response_time"] for v in metrics_data.values()]
error_rates = [v["error_rate"] for v in metrics_data.values()]

with col1:
    st.subheader("Request Count per Endpoint")
    fig1 = px.bar(x=endpoints, y=request_counts, labels={"x": "Endpoint", "y": "Count"})
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.subheader("Average Response Time (s)")
    fig2 = px.bar(x=endpoints, y=avg_times, labels={"x": "Endpoint", "y": "Time (s)"})
    st.plotly_chart(fig2, use_container_width=True)

col3, col4 = st.columns(2)

with col3:
    st.subheader("Error Rate per Endpoint")
    fig3 = px.bar(x=endpoints, y=error_rates, labels={"x": "Endpoint", "y": "Error Rate"})
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.subheader("Status Code Distribution")
    all_codes = {}
    for v in metrics_data.values():
        for code, count in v["status_codes"].items():
            all_codes[code] = all_codes.get(code, 0) + count
    if all_codes:
        fig4 = px.pie(names=list(all_codes.keys()), values=list(all_codes.values()))
        st.plotly_chart(fig4, use_container_width=True)

st.subheader("Raw Metrics Data")
df = pd.DataFrame([
    {"Endpoint": k, "Requests": v["request_count"], "Avg Response Time": v["average_response_time"],
     "Errors": v["error_count"], "Error Rate": v["error_rate"]}
    for k, v in metrics_data.items()
])
st.dataframe(df, use_container_width=True)

if st.button("Refresh Metrics"):
    st.rerun()
