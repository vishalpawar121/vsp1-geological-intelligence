import streamlit as st
import urllib.request
import json
from sklearn.ensemble import RandomForestClassifier
import numpy as np

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

st.set_page_config(
    page_title="VSP-1 Geological Intelligence",
    page_icon="🌍",
    layout="centered"
)

st.title("VSP-1")
st.subheader("Geological Intelligence System")
st.caption("Founded by Vishal Pawar | Powered by USGS Live Data + Machine Learning")
st.divider()

st.subheader("Site Analysis")

col1, col2 = st.columns(2)

with col1:
    location = st.text_input("Location Name", "Pune, Maharashtra")
    soil_type = st.selectbox("Soil Type", [
        "Black Cotton Soil","Soft Clay","Alluvial",
        "Sandy","Hard Rock","Granite Rock","Mixed","Rocky"
    ])
    project_type = st.selectbox("Project Type", [
        "Residential Housing","Commercial Building",
        "Bridge / Road","Smart City District",
        "Hospital","Industrial Facility"
    ])

with col2:
    seismic = st.slider("Seismic Risk (1-10)", 1, 10, 5)
    strength = st.slider("Soil Strength (kPa)", 80, 500, 175)
    water = st.slider("Water Table Depth (m)", 0.5, 10.0, 3.5)

if st.button("ANALYSE SITE", type="primary"):

    prediction = model.predict([[seismic, strength, water]])[0]
    confidence = model.predict_proba([[seismic, strength, water]])[0]
    conf_pct = round(max(confidence) * 100, 1)
    score = round((10-seismic)*3 + (strength/100)*2 + water*1.5, 2)

    risk_labels = {
        0: "LOW RISK",
        1: "MODERATE RISK",
        2: "HIGH RISK",
        3: "CRITICAL RISK"
    }

    risk_colors = {
        0: "green",
        1: "orange",
        2: "red",
        3: "violet"
    }

    st.divider()

    risk_color = risk_colors[prediction]
    risk_label = risk_labels[prediction]

    if prediction == 0:
        st.success(f"{risk_label} | VSP Score: {score} | ML Confidence: {conf_pct}%")
    elif prediction == 1:
        st.warning(f"{risk_label} | VSP Score: {score} | ML Confidence: {conf_pct}%")
    else:
        st.error(f"{risk_label} | VSP Score: {score} | ML Confidence: {conf_pct}%")

    if prediction >= 2:
        depth = round(5.0 + water*0.6, 1)
        foundation = "Deep Pile Foundation"
        material = "M40 Nano-Concrete + Steel Piles"
    elif prediction == 1:
        depth = round(3.0 + water*0.4, 1)
        foundation = "Reinforced Foundation"
        material = "M30 Concrete + Steel"
    else:
        depth = round(2.0 + water*0.3, 1)
        foundation = "Standard Foundation"
        material = "M25 Concrete"

    if seismic >= 7:
        seismic_design = "Full seismic isolation required"
    elif seismic >= 5:
        seismic_design = "Seismic resistant frame required"
    else:
        seismic_design = "Standard seismic precautions"

    col3, col4 = st.columns(2)

    with col3:
        st.markdown("**SITE GEOLOGY**")
        st.write(f"Location: {location}")
        st.write(f"Soil Type: {soil_type}")
        st.write(f"Seismic Zone: {seismic}/10")
        st.write(f"Soil Strength: {strength} kPa")
        st.write(f"Water Table: {water}m")

    with col4:
        st.markdown("**STRUCTURAL RECOMMENDATION**")
        st.write(f"Foundation: {foundation}")
        st.write(f"Depth: {depth}m")
        st.write(f"Material: {material}")
        st.write(f"Seismic Design: {seismic_design}")
        st.write(f"Project: {project_type}")

    st.divider()
    st.markdown("**LIVE SEISMIC MONITORING — USGS**")

    try:
        url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_month.geojson"
        response = urllib.request.urlopen(url, timeout=5)
        data = json.loads(response.read().decode())
        quakes = data["features"]
        st.write(f"Global earthquakes tracked: {len(quakes)}")
        for q in quakes[:3]:
            p = q["properties"]
            st.write(f"M{p['mag']} — {p['place']}")
    except:
        st.write("Live data updating...")

    st.divider()
    st.caption("VSP-1 Geological Intelligence System | Founded by Vishal Pawar | 2026")
