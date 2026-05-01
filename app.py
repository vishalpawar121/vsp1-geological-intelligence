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
        lat = loc['coords']['latitude']
        lon = loc['coords']['longitude']
        location = st.text_input("Location Name", f"GPS Locked: {lat}, {lon}")
        st.success("🛰️ Satellite Signal Verified")
    else:
        location = st.text_input("Location Name", "Pune, Maharashtra")
        lat, lon = 18.5204, 73.8567 # Default Pune
    
    soil_type = st.selectbox("Soil Type", ["Black Cotton Soil","Soft Clay","Alluvial","Sandy","Hard Rock","Granite Rock","Mixed","Rocky"])
    project_type = st.selectbox("Project Type", ["Residential Housing","Commercial Building","Bridge / Road","Smart City District","Hospital","Industrial Facility"])

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

# --- UI Setup ---
st.title("VSP-1 Automated Analysis")

# Logic to get Location (Placeholder for your GPS logic)
lat, lon = 18.4391, 73.8148 

# 2. AUTOMATION LOGIC
if st.button("Auto-Fetch Parameters"):
    # Here you would normally find the nearest neighbor in your dataset
    # For this example, we'll assume it detected "Dhayari"
    site_info = REGION_DATA.get("Dhayari")
    
    st.session_state['soil_strength'] = site_info['soil_strength']
    st.session_state['water_depth'] = site_info['water_table']
    st.session_state['seismic'] = get_seismic_risk(lat, lon)

# 3. DYNAMIC SLIDERS
# Using session_state allows the code to "auto-set" the slider positions
seismic_val = st.slider("Seismic Risk", 1, 10, value=st.session_state.get('seismic', 1))
soil_val = st.slider("Soil Strength (kPa)", 80, 500, value=st.session_state.get('soil_strength', 80))
water_val = st.slider("Water Table Depth (m)", 0.5, 10.0, value=st.session_state.get('water_depth', 0.5))

if st.button("ANALYSE SITE"):
    st.success(f"Analysing site at {lat}, {lon} with Soil Strength: {soil_val} kPa")
import streamlit as st

# 1. GEOLOGICAL DATABASE (Expand this as you gather more data)
REGION_DATA = {
    "Dhayari": {
        "soil_strength": 401, 
        "water_table": 3.50, 
        "seismic": 5, 
        "soil_index": 0  # 0: Black Cotton
    },
    "Kothrud": {
        "soil_strength": 450, 
        "water_table": 8.20, 
        "seismic": 4, 
        "soil_index": 1  # 1: Hard Rock
    }
}

# 2. INITIALIZE SESSION STATE (Prevents errors on first load)
if 'soil_val' not in st.session_state:
    st.session_state.soil_val = 80
if 'water_val' not in st.session_state:
    st.session_state.water_val = 10.0
if 'seismic_val' not in st.session_state:
    st.session_state.seismic_val = 1
if 'soil_type_idx' not in st.session_state:
    st.session_state.soil_type_idx = 0

# --- UI HEADER ---
st.title("VSP-1 Geological Intelligence System")
st.markdown("---")

# 3. LOCATION DATA (Your GPS Logic)
lat, lon = 18.4391951, 73.8148597 
st.info(f"📍 GPS Locked: {lat}, {lon}")

# 4. AUTOMATION TRIGGER
if st.button("✨ AUTO-FETCH SITE PARAMETERS"):
    # Logic: If coordinates are near Dhayari, fetch Dhayari data
    # (In the future, use a geocoder here)
    data = REGION_DATA["Dhayari"]
    
    # Update Session State
    st.session_state.soil_val = data['soil_strength']
    st.session_state.water_val = data['water_table']
    st.session_state.seismic_val = data['seismic']
    st.session_state.soil_type_idx = data['soil_index']
    st.success("Parameters updated for Dhayari Region!")

st.markdown("---")

# 5. DYNAMIC INPUTS (Linked to Session State)
soil_options = ["Black Cotton Soil", "Hard Rock/Murrum", "Silt/Clay"]
soil_type = st.selectbox("Soil Type", options=soil_options, index=st.session_state.soil_type_idx)

seismic_val = st.slider("Seismic Risk (1-10)", 1, 10, value=st.session_state.seismic_val)
soil_val = st.slider("Soil Strength (kPa)", 80, 500, value=st.session_state.soil_val)
water_val = st.slider("Water Table Depth (m)", 0.5, 10.0, value=st.session_state.water_val)

# 6. INTELLIGENT ANALYSIS
if st.button("ANALYSE SITE", type="primary"):
    st.subheader("Final Geotechnical Report")
    
    # Risk Calculation Logic
    if soil_type == "Black Cotton Soil" and water_val < 4.0:
        st.error("🚨 CRITICAL RISK: High expansion potential. Specialized foundation (Under-reamed piles) required.")
    elif soil_val > 400:
        st.success("✅ STABLE: High bearing capacity. Standard isolated footings recommended.")
    else:
        st.warning("⚠️ MODERATE: Deep excavation recommended to reach stable strata.")

    st.write(f"**Analysis Summary:** Site at {lat}, {lon} shows {soil_type} with a bearing capacity of {soil_val} kPa.")
    
