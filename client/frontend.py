import requests
import streamlit as st
import plotly
import pandas as pd
import plotly.express as px

st.write('Test')

API_BASE_URL = "http://127.0.0.1:5000/api"

st.set_page_config(page_title="Water Quality", layout="wide")
st.sidebar.title("Controls")
api_base = st.sidebar.text_input("API Base URL", API_BASE_URL)

col_time = st.sidebar.container()
with col_time:
    st.markdown("**Date/Time Range (ISO)**")
    start = st.text_input("Start (e.g., 2024-07-01T00:00:00)", value="")
    end   = st.text_input("End (e.g., 2024-08-01T00:00:00)", value="")

st.sidebar.markdown("---")
st.sidebar.markdown("**Numeric Filters**")
min_temp = st.sidebar.number_input("Min Temperature (°C)", value=None, placeholder="auto", step=0.1, format="%.3f")
max_temp = st.sidebar.number_input("Max Temperature (°C)", value=None, placeholder="auto", step=0.1, format="%.3f")
min_sal  = st.sidebar.number_input("Min Salinity (ppt)", value=None, placeholder="auto", step=0.1, format="%.3f")
max_sal  = st.sidebar.number_input("Max Salinity (ppt)", value=None, placeholder="auto", step=0.1, format="%.3f")
min_odo  = st.sidebar.number_input("Min ODO (mg/L)", value=None, placeholder="auto", step=0.1, format="%.3f")
max_odo  = st.sidebar.number_input("Max ODO (mg/L)", value=None, placeholder="auto", step=0.1, format="%.3f")

st.sidebar.markdown("---")
limit = st.sidebar.slider("Total Items", min_value=10, max_value=1000, value=200, step=10)
skip  = st.sidebar.number_input("Items Per Page", min_value=0, value=0, step=10)

method = st.sidebar.selectbox("Outlier method", options=["iqr", "zscore"], index=0)
k_val  = st.sidebar.number_input("Method parameter (k)", value=1.5 if method=="iqr" else 3.0, step=0.1, format="%.2f")

st.sidebar.markdown("---")


def build_params(prefix=None):
    params = {}
    if start: params["start"] = start
    if end:   params["end"] = end
    if min_temp is not None: params["min_temp"] = min_temp
    if max_temp is not None: params["max_temp"] = max_temp
    if min_sal  is not None: params["min_sal"]  = min_sal
    if max_sal  is not None: params["max_sal"]  = max_sal
    if min_odo  is not None: params["min_odo"]  = min_odo
    if max_odo  is not None: params["max_odo"]  = max_odo
    if prefix == "obs":
        params["limit"] = limit
        params["skip"]  = skip
    return params

@st.cache_data(ttl=30, show_spinner=False)
def fetch_json(url, params):
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    return r.json()

def to_df(items):
    if not items:
        return pd.DataFrame()
    df = pd.DataFrame(items)

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    return df

# main container

st.title("Water Quality")

try:
    health = requests.get(f"{api_base}/health", timeout=5).json()
    st.caption(f"API status: {health.get('status','unknown')}")
except Exception as e:
    st.error(f"Could not reach API at {api_base}. Make sure the Flask app is running (api.py).")
    st.stop()

with st.spinner("Loading Observations"):
    obs_json = fetch_json(f"{api_base}/observations", build_params(prefix="obs"))
items = obs_json.get("items", [])
df = to_df(items)

st.subheader(f"Observations ({obs_json.get('count', 0)})")
st.dataframe(df, use_container_width=True, height=300)

TEMP_COL = "Temperature (c)"
SAL_COL  = "Salinity (ppt)"
ODO_COL  = "ODO mg/L"
LAT_COL  = "Latitude"
LON_COL  = "Longitude"

chart_cols = st.columns(3)

if not df.empty:

    # temp linechart
    if "timestamp" in df.columns and TEMP_COL in df.columns:
        fig_line = px.line(
            df.sort_values("timestamp"),
            x="timestamp",
            y=TEMP_COL,
            title="Temperature over Time",
        )
        chart_cols[0].plotly_chart(fig_line, use_container_width=True)

    # salinity histogram
    if SAL_COL in df.columns:
        fig_hist = px.histogram(
            df,
            x=SAL_COL,
            nbins=30,
            title="Salinity Distribution",
        )
        chart_cols[1].plotly_chart(fig_hist, use_container_width=True)

    # temp vs salinity scatter plot
    if TEMP_COL in df.columns and SAL_COL in df.columns:
        color_col = ODO_COL if ODO_COL in df.columns else None
        fig_scatter = px.scatter(
            df,
            x=TEMP_COL,
            y=SAL_COL,
            color=color_col,
            title="Temperature vs Salinity" + (" (colored by ODO)" if color_col else ""),
        )
        chart_cols[2].plotly_chart(fig_scatter, use_container_width=True)

    # map
    if LAT_COL in df.columns and LON_COL in df.columns:
        df_map = df.dropna(subset=[LAT_COL, LON_COL]).copy()
        try:
            df_map[LAT_COL] = pd.to_numeric(df_map[LAT_COL], errors="coerce")
            df_map[LON_COL] = pd.to_numeric(df_map[LON_COL], errors="coerce")
            df_map = df_map.dropna(subset=[LAT_COL, LON_COL])
        except Exception:
            pass
        if not df_map.empty:
            fig_geo = px.scatter_mapbox(
                df_map,
                lat=LAT_COL,
                lon=LON_COL,
                zoom=16.7,
                mapbox_style="open-street-map",
                hover_data= [TEMP_COL, SAL_COL, ODO_COL, "timestamp"],
                title="Track (Latitude/Longitude)",
            )
            # fig_geo.update_geos(fitbounds="locations")
            st.plotly_chart(fig_geo, use_container_width=True)

st.markdown("---")
st.subheader("Summary Statistics")
with st.spinner("Loading Statistics"):
    stats_json = fetch_json(f"{api_base}/stats", build_params())
st.json(stats_json)


st.markdown("---")
st.subheader("Outliers")
field_choice = st.selectbox("Field", ["temperature", "salinity", "odo"], index=0, key="field")
params = build_params()
params.update({"field": field_choice, "method": method, "k": k_val})

with st.spinner("Computing Outliers"):
    out_json = fetch_json(f"{api_base}/outliers", params)

st.caption(f"Flagged records: {out_json.get('count', 0)}")
out_df = to_df(out_json.get("items", []))
st.dataframe(out_df, use_container_width=True, height=250)