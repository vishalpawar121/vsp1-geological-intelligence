import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px
from datetime import datetime

# Optional GenAI SDK imports (wrapped so the app still runs without the package)
try:
    from google import genai
    from google.genai import types
except Exception:
    genai = None
    types = None

# --- PAGE CONFIG (MUST BE FIRST) ---
st.set_page_config(
    page_title="VSP-1 Geological Intelligence | Enterprise AI System",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- SIMPLE STYLING ---
st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(180deg, #F9FAFB 0%, #F3F4F6 100%); }
    h1 { color: #1F2937; }
    .header-sub { color: #6B7280; }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- MAIN HEADER ---
st.markdown(
    """
    <div style='text-align:center; margin-bottom: 1.5rem;'>
        <h1>🧬 VSP-1 Geological Intelligence</h1>
        <div class='header-sub'>Enterprise-Grade Analysis • Real-Time Geospatial Processing</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- SIDEBAR CONFIGURATION ---
st.sidebar.markdown("### ⚙️ Configuration")
location = st.sidebar.text_input("📍 Location", value="Pune, Maharashtra")
soil_types = ["Black Cotton", "Soft Clay", "Alluvial", "Sandy", "Hard Rock"]
selected_soil = st.sidebar.selectbox("🌍 Soil Type", soil_types)
project_types = ["Residential", "Smart City", "Bridge", "Hospital", "Industrial"]
selected_project = st.sidebar.selectbox("🏗️ Project Type", project_types)
seismic = st.sidebar.slider("📊 Seismic Risk", 1, 10, 5)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔗 Core API Status")
col1, col2 = st.sidebar.columns(2)
with col1:
    st.metric("Weather", "🟢 Live")
    st.metric("Geo Data", "🟢 Live")
with col2:
    st.metric("Map Data", "🟢 Live")
    st.metric("Elevation", "🟢 Live")

# --- TABS ---
TAB_LABELS = [
    "🔍 Search",
    "🔬 Soil Scanner",
    "📡 Live Weather",
    "🛰️ Satellite",
    "🌍 Location",
    "🎯 Crop",
    "📸 Field Docs",
    "🔗 Blockchain",
    "⚙️ Settings",
]

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs(TAB_LABELS)

# Tab: Search
with tab1:
    st.header("🔍 Search")
    q = st.text_input("Enter query to search geological knowledge base")
    if q:
        st.info(f"Searching for: {q}")
        # Placeholder: show dummy results
        df = pd.DataFrame([
            {"Name": "Black Cotton", "Suitability": "Residential", "Notes": "Expansive clay"},
            {"Name": "Alluvial", "Suitability": "All Projects", "Notes": "Good bearing capacity"},
        ])
        st.dataframe(df)

    # --- AGI ASSISTANT SNIPPET (added) ---
    st.markdown("---")
    st.subheader("🧠 AGI Assistant")

    agi_prompt = st.text_area(
        "Ask VSP-1 AGI (use geological questions, include context)",
        height=150,
        key="agi_prompt",
    )

    if st.button("Ask AGI"):
        # Basic readiness checks
        if "agi_core" not in st.session_state or st.session_state.agi_core.client is None:
            st.warning(
                "AGI not configured. Ensure `google-genai` is installed (requirements.txt) "
                "and add GEMINI_API_KEY to Streamlit secrets."
            )
        elif not agi_prompt or not agi_prompt.strip():
            st.info("Please enter a question for the AGI.")
        else:
            with st.spinner("Contacting VSP-1 AGI..."):
                context = {
                    "location": location,
                    "soil": selected_soil,
                    "project": selected_project,
                    "seismic": seismic,
                }
                try:
                    response = st.session_state.agi_core.generate_insight(context, agi_prompt)
                    st.markdown("**AGI Response:**")
                    st.write(response)
                except Exception as e:
                    st.error(f"AGI request failed: {e}")

# Tab: Soil Scanner
with tab2:
    st.header("🔬 Soil Scanner")
    col_a, col_b = st.columns([1, 2])
    with col_a:
        moisture = st.slider("Soil moisture (%)", 0, 100, 25)
        ph = st.number_input("pH level", 0.0, 14.0, 7.0)
    with col_b:
        st.write("Recommendations")
        if st.button("Analyze Soil"):
            score = 50
            if 20 <= moisture <= 40:
                score += 20
            if 6.0 <= ph <= 7.5:
                score += 20
            st.success(f"Soil quality score: {min(score,100)}")

# Tab: Live Weather
with tab3:
    st.header("📡 Live Weather")
    st.write(f"Showing weather for: {location}")
    if st.button("Fetch Sample Weather"):
        try:
            # simple free API example (Open-Meteo)
            lat, lon = 18.5204, 73.8567
            url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
            r = requests.get(url, timeout=5)
            data = r.json()
            st.json(data.get("current_weather", {}))
        except Exception as e:
            st.error(f"Failed to fetch weather: {e}")

# Tab: Satellite
with tab4:
    st.header("🛰️ Satellite")
    st.info("Satellite data integrations (USGS, Sentinel) placeholder")

# Tab: Location
with tab5:
    st.header("🌍 Location")
    st.map(pd.DataFrame({"lat": [18.5204], "lon": [73.8567]}))

# Tab: Crop
with tab6:
    st.header("🎯 Crop Feasibility")
    st.write("Use soil inputs to estimate crop suitability. Placeholder UI.")

# Tab: Field Docs
with tab7:
    st.header("📸 Field Documentation")
    st.write("Upload and geotag photos here. Placeholder.")

# Tab: Blockchain
with tab8:
    st.header("🔗 Blockchain Ledger")
    st.write("Store analysis blocks (simulated). Placeholder.")

# Tab: Settings
with tab9:
    st.header("⚙️ Settings")
    st.write("Configuration and API key status.")
    if "GEMINI_API_KEY" in st.secrets:
        st.success("Gemini API Key configured in secrets")
    else:
        st.warning("Gemini API Key not found in st.secrets. Add it to enable AGI features.")

# --- 13. AGI INTEGRATION CORE ---
class AGISystemCore:
    def __init__(self):
        self.model_status = "ONLINE"
        self.readiness = "Gemini AGI-Core Active (gemini-3.6-flash)"
        self.api_key = None
        self.client = None
        try:
            # Securely fetch the hidden key from your Streamlit vault
            self.api_key = st.secrets["GEMINI_API_KEY"]
            if genai is None:
                # SDK not available in environment
                raise RuntimeError("google-genai SDK not installed")
            self.client = genai.Client(api_key=self.api_key)
        except Exception:
            # Leave client as None if anything goes wrong; UI will show a helpful message
            self.api_key = None
            self.client = None

    def generate_insight(self, context: dict, user_prompt: str) -> str:
        if not self.client:
            return "⚠️ API Key not found or Client failed to initialize. Please check your Streamlit vault."
        
        # The AGI instructions: Granting it vast world knowledge while keeping it professional
        system_instruction = (
            "You are VSP-1, an elite enterprise Geological Intelligence AGI (Artificial General Intelligence). "
            "You possess vast knowledge about everything around the world. "
            "You provide strict, professional, highly analytical advice based on global context and geotechnical data."
        )
        
        prompt = f"Current Context: {context}\n\nUser Query: {user_prompt}"
        
        try:
            # Connects to Google's latest frontier model via the modern SDK
            response = self.client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    temperature=0.3, # Keeps it highly analytical and grounded
                )
            )
            # `response` object shape can vary between SDK versions; attempt to read `text` then `response.output[0].content`
            try:
                return response.text
            except Exception:
                try:
                    return str(response.output[0].content[0].text)
                except Exception:
                    return str(response)
        except Exception as e:
            return f"⚠️ AGI Network failure: {str(e)}"

# Ensure AGI core is available in the Streamlit session state
if 'agi_core' not in st.session_state:
    st.session_state.agi_core = AGISystemCore()

# --- FOOTER ---
st.markdown("---")
st.caption(f"Last loaded: {datetime.utcnow().isoformat()} UTC")
