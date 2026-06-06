import streamlit as st
import urllib.request
import json
from sklearn.ensemble import RandomForestClassifier
import numpy as np
import folium
from streamlit_folium import folium_static
from streamlit_js_eval import get_geolocation

# --- 1. YOUR CUSTOM ML MODEL (DO NOT CHANGE) ---
X = [
    [9,110,1.8],[8,150,2.1],[8,130,1.5],[7,160,2.8],[6,120,2.0],
    [5,175,3.5],[5,190,3.8],[4,200,4.1],[3,350,5.8],[3,380,6.2],
    [2,400,7.0],[2,420,6.8],[8,140,1.9],[7,155,2.5],[6,165,3.0],
    [4,210,4.5],[3,310,5.5],[9,105,1.6],[5,180,3.2],[4,195,4.0],
    [9,120,2.0],[8,125,1.7],[9,115,1.4],[8,135,2.2],[9,108,1.3],
    [7,145,2.7],[6,125,2.1],[7,150,2.9],[6,135,2.4],[7,140,2.6],
    [4,188,3.6],[5,178,3.4],[4,192,4.3],[5,182,3.8],[4,198,4.1],
    [3,360,6.0],[2,410,7.2],[3,370,5.9],[2,430,7.5],[1,450,8.0],
    [2,415,7.8],[1,440,8.5],[3,355,6.1],[2,395,7.3],[1,460,9.0],
    [3,345,5.7],[2,385,6.9],[1,470,8.8],[3,375,6.3],[2,390,8.1],
]
y = [3,3,3,2,2,1,1,1,0,0,0,0,3,2,1,1,0,3,1,1,
     3,3,3,3,3,2,2,2,2,2,1,1,1,1,1,0,0,0,0,0,
     0,0,0,0,0,0,0,0,0,0]

model = RandomForestClassifier(n_estimators=200, random_state=42)
model.fit(X, y)

# --- 2. PROFESSIONAL UI SETUP ---
st.set_page_config(page_title="VSP-1 Geological Intelligence", page_icon="🌍", layout="wide")

st.title("VSP-1")
st.subheader("Geological Intelligence System")
st.caption("Founded by Vishal Pawar | Powered by USGS Live Data + Machine Learning")
st.divider()

# --- 3. LIVE SENSOR BRIDGE (NEW) ---
loc = get_geolocation()

st.subheader("Site Analysis")
col1, col2 = st.columns(2)

with col1:
    if loc:
        
if loc and 'coords' in loc and loc['coords']:
    lat = loc['coords']['latitude']
    lon = loc['coords']['longitude']
else:
    lat = 18.5204  # Default Pune Latitude
    lon = 73.8567  # Default Pune Longitude
    
        location = st.text_input("Location Name", f"GPS Locked: {lat}, {lon}")
        st.success("🛰️ Satellite Signal Verified")
    else:
        location = st.text_input("Location Name", "Pune, Maharashtra")
        lat, lon = 18.5204, 73.8567 # Default Pune
    
    soil_type = st.selectbox("Soil Type", ["Black Cotton Soil","Soft Clay","Alluvial","Sandy","Hard Rock","Granite Rock","Mixed","Rocky"])
    project_type = st.selectbox("Project Type", ["Residential Housing","Commercial Building","Bridge / Road","Smart city# Make sure this 'if' line touches the very left wall of your screen:
if loc and 'coords' in loc and loc['coords']:
    lat = loc['coords']['latitude']   # <-- Hit TAB once before typing this line
    lon = loc['coords']['longitude']  # <-- Hit TAB once before typing this line
else:                                 # <-- This line touches the left wall again
    lat = 18.5204                     # <-- Hit TAB once before typing this line
    lon = 73.8567                     # <-- Hit TAB once before typing this line
ty District","Hospital","Industrial Facility"])

with col2:
    # --- 4. SATELLITE HYBRID VISUALIZER (NEW) ---
    st.markdown("**Site Visualizer**")
    m = folium.Map(location=[lat, lon], zoom_start=15, 
                   tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', 
                   attr='Google-Hybrid')
    folium.Marker([lat, lon], icon=folium.Icon(color='red', icon='eye-open')).add_to(m)
    folium_static(m, height=250)

# --- 5. RISK PARAMETERS ---
st.divider()
colA, colB, colC = st.columns(3)
with colA:
    seismic = st.slider("Seismic Risk (1-10)", 1, 10, 5)
with colB:
    strength = st.slider("Soil Strength (kPa)", 80, 500, 175)
with colC:
    water = st.slider("Water Table Depth (m)", 0.5, 10.0, 3.5)

# --- 6. ANALYSE LOGIC ---
if st.button("ANALYSE SITE", type="primary"):
    prediction = model.predict([[seismic, strength, water]])[0]
    confidence = model.predict_proba([[seismic, strength, water]])[0]
    conf_pct = round(max(confidence) * 100, 1)
    score = round((10-seismic)*3 + (strength/100)*2 + water*1.5, 2)

    risk_labels = {0: "LOW RISK", 1: "MODERATE RISK", 2: "HIGH RISK", 3: "CRITICAL RISK"}
    risk_colors = {0: "green", 1: "orange", 2: "red", 3: "violet"}

    st.divider()
    risk_label = risk_labels[prediction]
    
    if prediction == 0: st.success(f"{risk_label} | VSP Score: {score} | ML Confidence: {conf_pct}%")
    elif prediction == 1: st.warning(f"{risk_label} | VSP Score: {score} | ML Confidence: {conf_pct}%")
    else: st.error(f"{risk_label} | VSP Score: {score} | ML Confidence: {conf_pct}%")

    # Structural Recommendations logic remains the same
    depth = round(2.0 + water*0.3, 1) if prediction == 0 else round(5.0 + water*0.6, 1)
    foundation = "Standard Foundation" if prediction == 0 else "Deep Pile Foundation"
    
    col3, col4 = st.columns(2)
    with col3:
        st.markdown("**SITE GEOLOGY**")
        st.write(f"Location: {location} | Soil: {soil_type}")
    with col4:
        st.markdown("**STRUCTURAL RECOMMENDATION**")
        st.write(f"Foundation: {foundation} | Depth: {depth}m")

# --- 7. LIVE USGS MONITORING ---
st.divider()
st.markdown("**LIVE SEISMIC MONITORING — USGS**")
try:
    url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_month.geojson"
    response = urllib.request.urlopen(url, timeout=5)
    data = json.loads(response.read().decode())
    st.write(f"Global earthquakes tracked: {len(data['features'])}")
except:
    st.write("Live data updating...")

st.caption("VSP-1 Geological Intelligence System | Founded by Vishal Pawar | 2026")
import streamlit as st
import requests

# 1. Mock Database for Soil/Water Table based on regions
# In a production app, use a GeoJSON file or a PostGIS database
REGION_DATA = {
    "Dhayari": {"soil_strength": 401, "water_table": 3.50, "soil_type": "Black Cotton Soil"},
    "Kothrud": {"soil_strength": 450, "water_table": 8.20, "soil_type": "Hard Rock/Murrum"},
}

def get_seismic_risk(lat, lon):
    # Example: Integration with USGS or a local seismic hazard map
    # For now, we'll return a calculated value based on known zones
    return 5 # Default for Pune (Zone III)
# ==============================================================================
# --- NEW ENTERPRISE DASHBOARD CODE (PASTED AT LINE 131) ---
# ==============================================================================

# 1. Page Configuration (Makes the app look professional and wide)
st.set_page_config(layout="wide")

# 2. Sidebar Configuration Panel (Moves inputs to the left panel)
st.sidebar.header("📍 Site Configuration")

location = st.sidebar.text_input("Location Name", value="Pune, Maharashtra")

soil_types = ["Black Cotton Soil", "Alluvial Soil", "Laterite Soil", "Red Soil"]
selected_soil = st.sidebar.selectbox("Soil Type", soil_types, index=0)

project_types = ["Residential Housing", "Commercial Complex", "Industrial Warehouse"]
selected_project = st.sidebar.selectbox("Project Type", project_types, index=0)

analyse_button = st.sidebar.button("📊 ANALYSE SITE", use_container_width=True)


# 3. Main Page Header & Clean Divider
st.title("VSP-1")
st.subheader("Geological Intelligence System")
st.markdown("---")


# 4. Metrics & Circular Gauge Charts Display
# (We use default metrics here; you can tie them to your ML predictions next!)
seismic_risk = 5.0
soil_strength = 175  
water_table = 3.5    

import plotly.graph_objects as go

col1, col2, col3 = st.columns(3)

with col1:
    fig1 = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = seismic_risk,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Seismic Risk (1-10)"},
        gauge = {'axis': {'range': [None, 10]}, 'bar': {'color': "#FF4B4B"}}
    ))
    fig1.update_layout(height=220, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    fig2 = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = soil_strength,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Soil Strength (kPa)"},
        gauge = {'axis': {'range': [None, 500]}, 'bar': {'color': "#1C83E1"}}
    ))
    fig2.update_layout(height=220, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig2, use_container_width=True)

with col3:
    fig3 = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = water_table,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "Water Table Depth (m)"},
        gauge = {'axis': {'range': [None, 20]}, 'bar': {'color': "#00D4B2"}}
    ))
    fig3.update_layout(height=220, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig3, use_container_width=True)


st.markdown("---")


# 5. Output Results Panel & PDF Generator
if analyse_button:
    # Business-ready Status Banner
    st.warning("⚠️ **MODERATE RISK** | VSP Score: **23.75** | Data Reliability Score: **High**")
    
    result_col1, result_col2 = st.columns(2)
    
    with result_col1:
        st.subheader("🔍 Site Geology Summary")
        st.info(f"""
        * **Target Location:** {location}
        * **Identified Strata:** {selected_soil}
        * **Intended Use Case:** {selected_project}
        """)
        
    with result_col2:
        st.subheader("🏗️ Structural Engineering Directive")
        st.success("""
        * **Recommended Foundation:** Deep Pile Foundation
        * **Target Depth:** 7.1 meters
        * **Engineering Note:** Bypasses upper swelling layers of Black Cotton Soil to reach safe load-bearing strata.
        """)
    
    st.markdown("---")
    
    # B2B Feature: PDF Report Downloader
    st.subheader("📄 Enterprise Deliverables")
    mock_pdf_data = f"VSP-1 Geological Feasibility Report\nLocation: {location}\nFoundation Recommendation: Deep Pile (7.1m)"
    
    st.download_button(
        label="📥 Download Professional Feasibility Report (PDF)",
        data=mock_pdf_data,
        file_name=f"VSP1_Report_{location.replace(' ', '_')}.txt",
        mime="text/plain",
        use_container_width=True
    )
else:
    st.info("💡 Adjust parameters in the left sidebar and click **ANALYSE SITE** to run your geological assessment model.")

    
