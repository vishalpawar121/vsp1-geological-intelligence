import streamlit as st
import urllib.request
import json
from sklearn.ensemble import RandomForestClassifier
import folium
from streamlit_folium import folium_static
from streamlit_js_eval import get_geolocation
import plotly.graph_objects as go

# --- PAGE CONFIG (MUST BE FIRST) ---
st.set_page_config(
    page_title="VSP-1 Geological Intelligence",
    page_icon="G",
    layout="wide"
)

# --- 1. CUSTOM ML MODEL ---
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

# --- 2. SIDEBAR CONFIGURATION ---
st.sidebar.header("Site Configuration")

location = st.sidebar.text_input("Location Name", value="Pune, Maharashtra")
soil_types = ["Black Cotton Soil", "Soft Clay", "Alluvial", "Sandy", "Hard Rock", "Granite Rock", "Mixed", "Rocky"]
selected_soil = st.sidebar.selectbox("Soil Type", soil_types, index=0)

project_types = [
    "Residential Housing / Skyscrapers",
    "Smart City Districts",
    "Bridge / Road Infrastructures",
    "Hospital / Critical Care Facility",
    "Industrial Warehouse"
]
selected_project = st.sidebar.selectbox("Project Type", project_types, index=0)

# Risk parameters in sidebar
seismic = st.sidebar.slider("Seismic Risk (1-10)", 1, 10, 5)
strength = st.sidebar.slider("Soil Strength (kPa)", 80, 500, 175)
water = st.sidebar.slider("Water Table Depth (m)", 0.5, 10.0, 3.5)

# --- 3. MAIN PAGE HEADER ---
st.title("VSP-1")
st.subheader("Geological Intelligence System")
st.caption("Founded by Vishal Pawar | Powered by USGS Live Data + Machine Learning")
st.markdown("---")

# --- 4. METRICS DISPLAY (GAUGES) ---
col1, col2, col3 = st.columns(3)

with col1:
    fig1 = go.Figure(go.Indicator(
        mode="gauge+number",
        value=seismic,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Seismic Risk (1-10)"},
        gauge={'axis': {'range': [None, 10]}, 'bar': {'color': "#FF4B4B"}}
    ))
    fig1.update_layout(height=220, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    fig2 = go.Figure(go.Indicator(
        mode="gauge+number",
        value=strength,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Soil Strength (kPa)"},
        gauge={'axis': {'range': [None, 500]}, 'bar': {'color': "#1C83E1"}}
    ))
    fig2.update_layout(height=220, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig2, use_container_width=True)

with col3:
    fig3 = go.Figure(go.Indicator(
        mode="gauge+number",
        value=water,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Water Table Depth (m)"},
        gauge={'axis': {'range': [None, 20]}, 'bar': {'color': "#00D4B2"}}
    ))
    fig3.update_layout(height=220, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(fig3, use_container_width=True)

# --- 5. SATELLITE MAP VISUALIZATION ---
st.markdown("---")
st.subheader("Site Visualizer")

# Get GPS location or use default
loc = get_geolocation()
if loc and 'coords' in loc and loc['coords']:
    lat = loc['coords']['latitude']
    lon = loc['coords']['longitude']
    st.success("Satellite Signal Verified")
else:
    lat, lon = 18.5204, 73.8567  # Default Pune

m = folium.Map(
    location=[lat, lon],
    zoom_start=15,
    tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
    attr='Google-Hybrid'
)
folium.Marker([lat, lon], icon=folium.Icon(color='red', icon='eye-open')).add_to(m)
folium_static(m, height=300)

# --- 6. ANALYSIS BUTTON & RESULTS ---
st.markdown("---")

# Initialize session state variables for self-evolution
if 'telemetry_logs' not in st.session_state:
    st.session_state.telemetry_logs = []
if 'dynamic_safety_modifier' not in st.session_state:
    st.session_state.dynamic_safety_modifier = 1.0
if 'system_version' not in st.session_state:
    st.session_state.system_version = 1.0

if st.button("ANALYSE SITE", type="primary", use_container_width=True):
    # Get ML prediction
    prediction = model.predict([[seismic, strength, water]])[0]
    confidence = model.predict_proba([[seismic, strength, water]])[0]
    conf_pct = round(max(confidence) * 100, 1)
    score = round((10 - seismic) * 3 + (strength / 100) * 2 + water * 1.5, 2)

    # Risk mapping
    risk_labels = {
        0: "LOW RISK",
        1: "MODERATE RISK",
        2: "HIGH RISK",
        3: "CRITICAL RISK"
    }
    risk_label = risk_labels[prediction]

    # Display status
    if prediction == 0:
        st.success(f"Status - {risk_label} | VSP Score: {score} | ML Confidence: {conf_pct}%")
    elif prediction == 1:
        st.warning(f"Status - {risk_label} | VSP Score: {score} | ML Confidence: {conf_pct}%")
    else:
        st.error(f"Status - {risk_label} | VSP Score: {score} | ML Confidence: {conf_pct}%")

    # Structural recommendations with robotic construction specifications
    depth = round(2.0 + water * 0.3, 1) if prediction == 0 else round(5.0 + water * 0.6, 1)
    foundation = "Deep Piling Foundation" if prediction >= 2 else "Shallow Spread Footing"

    result_col1, result_col2 = st.columns(2)

    with result_col1:
        st.subheader("🔍 Site Geology Summary")
        st.info(f"""
        * **Target Location:** {location}
        * **Identified Strata:** {selected_soil}
        * **Intended Use Case:** {selected_project}
        """)
        
        st.markdown("---")
        st.subheader("🌐 AI System Evolution Watchdog")
        st.caption(f"Active Core Engine State: v{st.session_state.system_version}")
        
        # Telemetry Simulator UI inside Column 1
        sim_action = st.radio(
            "Simulate Robotic / Human Feedback Loop:",
            ["Robot Confirmed: Structural Parameters Optimal", "Robot Override: Ground Drift Detected (Requesting Safety Boost)"]
        )
        
        if st.button("Transmit Telemetry & Run Sandbox Optimization"):
            action_key = "Accepted" if "Optimal" in sim_action else "Overridden"
            # Log observation data
            st.session_state.telemetry_logs.append({"project": selected_project, "action": action_key})
            
            # Analyze telemetry buffer for autonomous self-patching
            overrides = [l for l in st.session_state.telemetry_logs if l["action"] == "Overridden"]
            if len(st.session_state.telemetry_logs) >= 3 and (len(overrides) / len(st.session_state.telemetry_logs)) > 0.5:
                # Recursive Self-Improvement triggered in background sandbox
                st.session_state.dynamic_safety_modifier += 0.25
                st.session_state.system_version = round(st.session_state.system_version + 0.1, 2)
                st.session_state.telemetry_logs = [] # Reset memory buffer after patch deployment
                st.success(f"System Optimized! Upgraded to Engine Core v{st.session_state.system_version}")
                st.rerun()
            else:
                st.info("Telemetry analyzed. Parameters stable within current sandbox safety envelopes.")

    with result_col2:
        st.subheader("🏗️ Multihazard Safety & Structural Directive")
        
        # --- COMPLETE INTERLOCKING MULTIHAZARD & ROBOTIC LOGIC ---
        if "Residential" in selected_project:
            seismic_tech = "Base Isolation System using heavy-duty laminate rubber and lead core bearings"
            water_defense = "Elevated Plinth Beam Architecture with sub-surface French Drains"
            wind_spec = "Symmetrical Concrete Shear Walls designed for twisting forces up to 140 km/h"
            factor_safety_base = 1.5
            geometry_3d = "Concentric Hollow Hexagonal Prisms for optimal load distribution"
            robot_toolpath = "Continuous spiral extrusion path to eliminate cold-joint structural weak points"
            robotic_survival_mech = "Internal lattice voids for automated vertical reinforcement bar insertion"
            
        elif "Smart City" in selected_project:
            seismic_tech = "Tuned Mass Dampers paired with flexible rubberized underground utility conduit loops"
            water_defense = "Sponge-City Protocol using permeable concrete roads and automated storm sump gates"
            wind_spec = "Aerodynamic Facade Geometry with curved corners to break up destructive wind vortices"
            factor_safety_base = 2.5
            geometry_3d = "Voronoi Tessellation Structures to distribute macro urban mechanical stresses dynamically"
            robot_toolpath = "Multi-axis robotic arm printing interlocking block grids with self-aligning joints"
            robotic_survival_mech = "Dual-wall extrusion creating a fifty millimeter internal utility isolation cavity"
            
        elif "Bridge" in selected_project:
            seismic_tech = "Seismic Dampeners and Expansion Decks allowing independent lane swaying without collapse"
            water_defense = "Heavy Rip-Rap Armouring interlocking stones to prevent underwater pier scouring"
            wind_spec = "Aerodynamic Box-Girder Decks acting like an inverted wing to stay pressed down and stable"
            factor_safety_base = 2.2
            geometry_3d = "Hyperbolic Paraboloids and Catenary Arches keeping concrete under pure compression"
            robot_toolpath = "Spatial multi-dimensional printing along principal tension stress trajectories"
            robotic_survival_mech = "Post-tensioned internal cable channels running directly through printed hollow sections"
            
        elif "Hospital" in selected_project:
            seismic_tech = "Active Mass Dampers and completely independent structural expansion joints between wings"
            water_defense = "100-Year Flood Line Clearance keeping critical generators strictly on the first floor or higher"
            wind_spec = "Category V Hurricane Armor Shell with missile-grade shatterproof structural glazing"
            factor_safety_base = 3.0
            geometry_3d = "Double-Curved Monolithic Geodesic Dome completely eliminating wall-to-roof seams"
            robot_toolpath = "Spherical coordinate toolpath utilizing a central climbing gantry system"
            robotic_survival_mech = "Interlocking triple-layer printed matrix filled with shock-absorbing polymers"
            
        else: # Default Industrial Frameworks
            seismic_tech = "Ductile Cross-Braced Steel Framing layouts to absorb shockwaves"
            water_defense = "Wide open perimeter catch-basins and high-volume gravity drainage outfalls"
            wind_spec = "Heavy-Duty Anchor Bolt Base-Plates and roof up-lift protection brackets"
            factor_safety_base = 1.8
            geometry_3d = "Modular Rectangular Portal Frames with engineered structural ribbing layouts"
            robot_toolpath = "Linear orthogonal layering with high-volume deposition print nozzles"
            robotic_survival_mech = "Integrated base-plate anchor anchorages printed directly into footings"

        # Apply Recursive Self-Evolving Modifier to the Safety Multiplier
        calculated_safety = round(factor_safety_base * st.session_state.dynamic_safety_modifier, 2)
        factor_safety = f"{calculated_safety}x Structural Safety Multiplier (Evolved)"

        st.success(f"""
        * **Recommended Foundation:** {foundation}
        * **Target Depth:** {depth}m
        * **⚡ Earthquake Shield:** {seismic_tech}
        * **🌊 Flood Defense:** {water_defense}
        * **💨 Wind Load Engineering:** {wind_spec}
        * **🛡️ Safety Factor:** {factor_safety}
        """)

    # --- 3D ROBOTIC SPECIFICATIONS PRINTED TO DASHBOARD BELOW ---
    st.markdown("---")
    st.subheader("🤖 Autonomous Robotic 3D Construction Parameters")
    r_col1, r_col2, r_col3 = st.columns(3)
    with r_col1:
        st.info(f"📐 **Target 3D Geometry:**\n{geometry_3d}")
    with r_col2:
        st.info(f"⚙️ **Robotic Toolpath Matrix:**\n{robot_toolpath}")
    with r_col3:
        st.info(f"🛡️ **Robotic Mitigations:**\n{robotic_survival_mech}")

    # --- ENTERPRISE PDF GENERATION ENGINE ---
    st.markdown("---")
    st.subheader("📄 Enterprise Deliverables")

    from fpdf import FPDF

    class VSP1Report(FPDF):
        def header(self):
            self.set_fill_color(0, 128, 128)
            self.rect(0, 0, 210, 35, 'F')
            self.set_text_color(255, 255, 255)
            self.set_font('Helvetica', 'B', 22)
            self.cell(0, 10, 'VSP-1 GEOLOGICAL INTELLIGENCE SYSTEM', ln=True, align='L')
            self.set_font('Helvetica', 'I', 10)
            self.cell(0, 5, 'Automated Engineering Feasibility Brief and Risk Matrix', ln=True, align='L')
            self.ln(15)

        def footer(self):
            self.set_y(-15)
            self.set_font('Helvetica', 'I', 8)
            self.set_text_color(128, 128, 128)
            self.cell(0, 10, f'Page {self.page_no()} | Engine Version: v{st.session_state.system_version}', align='C')

    pdf = VSP1Report()
    pdf.add_page()
    pdf.set_margins(15, 20, 15)

    pdf.set_text_color(33, 33, 33)
    pdf.set_font('Helvetica', 'B', 16)
    pdf.cell(0, 10, f'Geotechnical Assessment: {location}', ln=True)
    pdf.set_draw_color(0, 128, 128)
    pdf.line(15, 47, 195, 47)
    pdf.ln(5)

    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_fill_color(240, 242, 246)
    
    pdf.cell(45, 8, ' Target Location:', border=1, fill=True)
    pdf.set_font('Helvetica', '', 11)
    pdf.cell(135, 8, f' {location}', border=1, ln=True)
    
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(45, 8, ' Identified Soil:', border=1, fill=True)
    pdf.set_font('Helvetica', '', 11)
    pdf.cell(135, 8, f' {selected_soil}', border=1, ln=True)

    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(45, 8, ' Project Framework:', border=1, fill=True)
    pdf.set_font('Helvetica', '', 11)
    pdf.cell(135, 8, f' {selected_project}', border=1, ln=True)

    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(45, 8, ' Evaluated Risk:', border=1, fill=True)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(200, 30, 30)
    pdf.cell(135, 8, f' {risk_label} (VSP Score: {score})', border=1, ln=True)
    
    pdf.ln(8)

    pdf.set_text_color(33, 33, 33)
    pdf.set_font('Helvetica', 'B', 14)
    pdf.cell(0, 10, 'Multihazard and Robotic Engineering Specifications', ln=True)
    pdf.ln(2)

    specs = [
        ("Foundation Design", f"{foundation} at target depth of {depth}m"),
        ("Seismic Shielding Strategy", seismic_tech),
        ("Flood and Hydrological Defense", water_defense),
        ("Wind Force Engineering Spec", wind_spec),
        ("Structural Safety Multiplier", factor_safety),
        ("Robotic 3D Target Geometry", geometry_3d),
        ("Robotic G-Code Toolpath Guidance", robot_toolpath),
        ("Robotic Structural Adaptation", robotic_survival_mech)
    ]

    for title, detail in specs:
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(0, 102, 102)
        pdf.cell(0, 6, f'- {title}', ln=True)
        pdf.set_font('Helvetica', '', 11)
        pdf.set_text_color(50, 50, 50)
        pdf.multi_cell(0, 6, f'  {detail}')
        pdf.ln(2)

    # Output the PDF as bytes
    pdf_bytes = pdf.output(dest='S').encode('latin-1')

    st.download_button(
        label="Download Professional Feasibility Report (PDF)",
        data=pdf_bytes,
        file_name=f"VSP1_Geological_Report_{location.replace(' ', '_')}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
else:
    st.info("Adjust parameters in the left sidebar and click ANALYSE SITE to run your assessment.")

# --- 7. LIVE USGS MONITORING ---
st.markdown("---")
st.subheader("LIVE SEISMIC MONITORING - USGS")

try:
    url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/significant_month.geojson"
    response = urllib.request.urlopen(url, timeout=5)
    data = json.loads(response.read().decode())
    st.write(f"Global earthquakes tracked: {len(data['features'])}")
except Exception as e:
    st.warning(f"Live data updating... (Error: {str(e)})")

st.caption("VSP-1 Geological Intelligence System | Founded by Vishal Pawar | 2026")
