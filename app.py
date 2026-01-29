import streamlit as st
import pandas as pd
import os

# --- 0. CONFIGURATION & STYLE ---
st.set_page_config(
    page_title="OP Architect V5 - Final",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS for better mobile display and tab styling
st.markdown("""
<style>
    .main > div {padding-top: 2rem;}
    .stTabs [data-baseweb="tab-list"] {gap: 2px;}
    .stTabs [data-baseweb="tab"] {height: 50px; white-space: pre-wrap;}
    /* Highlight contact info */
    .contact-box {
        padding: 15px;
        background-color: #f0f2f6;
        border-radius: 10px;
        border-left: 5px solid #2e7bcf;
        margin-top: 10px;
        font-size: 14px;
    }
    .contact-header {
        font-weight: bold;
        color: #2e7bcf;
        margin-bottom: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- 1. USER GUIDE ---
with st.expander("ℹ️ **START GUIDE: How to use this tool?**", expanded=False):
    st.markdown("""
    1. **Open the sidebar** on the left.
    2. **Fill in the sections** (Sludge Quality, Logistics, Financials).
    3. **The tool calculates** the best fit (Ankur, SSP, or Janicki).
    4. **View Results:** Check the tabs for Technical Diagrams and Contacts.
    """)

# --- 2. SIDEBAR: INPUTS ---
with st.sidebar:
    st.title("🎛️ Project Settings")

    # --- SECTION A: QUALITY ---
    st.header("1. Sludge Characterization")
    
    type_boue = st.selectbox(
        "Sludge Type", 
        ["Fecal Sludge (Domestic)", "Activated Sludge (WWTP)", "Industrial Sludge"],
        help="Impacts calorific value and technology choice."
    )

    ts_percent = st.slider(
        "Dry Solids Content (TS) %", 
        min_value=1.0, max_value=90.0, value=5.0, step=0.5,
        help="1-5%: Liquid | 20-30%: Paste | 80%+: Dried"
    )
    
    heavy_metals = st.toggle(
        "Heavy Metals Presence?", 
        value=False,
        help="Blocks SSP/Bricks if active."
    )

    vol_boue = st.number_input("Daily Volume (m³/day)", value=40.0, step=5.0)

    st.write("---")

    # --- SECTION B: LOGISTICS ---
    st.header("2. Infrastructure & Logistics")
    
    mode_collecte = st.radio(
        "Collection Method", 
        ["Trucks / Voluntary Drop-off", "Sewer Network (Direct)"]
    )
    
    has_station = st.radio(
        "Is there an EXISTING Plant?",
        ["No (Greenfield)", "Yes (Existing WWTP/FSTP)"]
    )
    is_station_existante = True if has_station == "Yes (Existing WWTP/FSTP)" else False

    st.write("---")

    # --- SECTION C: FINANCIALS ---
    with st.expander("3. Financial Data (Optional)"):
        prix_elec = st.number_input("Elec. Price ($/kWh)", value=0.15)
        capex_manual = st.number_input("Max Budget ($)", value=0)
        
        # Hidden inputs for calculation
        masse_msw = 0; hum_msw = 0; lhv_msw = 0
        ajout_msw = st.checkbox("Add Municipal Waste?", value=False)
        if ajout_msw:
            masse_msw = st.number_input("Waste Mass (kg)", value=2000.0)
            lhv_msw = 18.0

    # --- DEVELOPER CREDITS ---
    st.write("---")
    st.markdown("### 👨‍💻 Developer & Contact")
    st.markdown("**Mansour Fall**")
    st.markdown("📧 [magnfall1992@gmail.com](mailto:magnfall1992@gmail.com)")
    st.caption("For clarifications or orientation.")

# --- 3. CALCULATION ENGINE ---

def run_simulation():
    # 1. Mass Balance
    masse_boue = vol_boue * 1000
    ms_boue = masse_boue * (ts_percent / 100.0)
    eau_boue = masse_boue - ms_boue
    ms_msw = masse_msw; total_dry = ms_boue + ms_msw; total_water = eau_boue
    
    # 2. Energy Balance
    energy_in = (ms_boue * 12.0) + (ms_msw * lhv_msw)
    energy_net = energy_in - (total_water * 3.2)
    
    # 3. CANDIDATE DEFINITIONS (UPDATED CONTACTS)
    # ---------------------------------------------------------
    # IMAGES: Ensure you have 'ankur_diagram.png', 'ssp_diagram.png', 
    # and 'janicki_diagram.png' in the same folder as this script.
    # ---------------------------------------------------------
    
    opt_ankur_complet = {
        "Tech": "ANKUR INTEGRATED (Full)", 
        "Score": 0, 
        "Desc": "Replaces a WWTP. Treats water & sludge (Waste to Energy).",
        "Contact_Name": "Jignesh Shah",
        "Contact_Email": "jignesh.shah@ankurscientific.com",
        "Image": "ankur_diagram.png" 
    }
    
    opt_ankur_basic = {
        "Tech": "ANKUR BASIC", 
        "Score": 0, 
        "Desc": "Energy module only. Requires pre-dried sludge.",
        "Contact_Name": "Jignesh Shah",
        "Contact_Email": "jignesh.shah@ankurscientific.com",
        "Image": "ankur_diagram.png"
    }
    
    opt_ssp = {
        "Tech": "THESVORES (SSP)", 
        "Score": 0, 
        "Desc": "Materials (Bricks/Pavers). Simple & Robust.",
        "Contact_Name": "Saibal (SSP Pvt Ltd)",
        "Contact_Email": "sg1965@ssp.co.in",
        "Image": "ssp_diagram.png"
    }
    
    opt_incin = {
        "Tech": "INCINERATOR (Omni Processor)", 
        "Score": 0, 
        "Desc": "High-tech incineration (Janicki/Sedron).",
        "Contact_Name": "Matthew Bartholow (Sedron)",
        "Contact_Email": "matthew.bartholow@janicki.com",
        "Image": "janicki_diagram.png"
    }

    # 4. DECISION TREE
    logic_msg = ""
    
    if mode_collecte == "Sewer Network (Direct)":
        if is_station_existante and type_boue == "Activated Sludge (WWTP)":
            logic_msg = "Sewer + WWTP ➔ Incinerator recommended."
            opt_incin["Score"] = 95
            opt_ankur_basic["Score"] = 60
        else:
            logic_msg = "Sewer Standard ➔ Incinerator preferred."
            opt_incin["Score"] = 80
            opt_ankur_complet["Score"] = 50
    else: # Trucks
        if is_station_existante:
            logic_msg = "Trucks + Existing Plant ➔ Add-on (Ankur Basic/SSP)."
            opt_ankur_basic["Score"] = 90
            opt_ssp["Score"] = 85
            opt_ankur_complet["Score"] = 20
        else:
            logic_msg = "Trucks + Greenfield ➔ Turnkey Solution (Ankur Integrated)."
            opt_ankur_complet["Score"] = 95
            opt_incin["Score"] = 60
            opt_ankur_basic["Score"] = 0
            opt_ssp["Score"] = 20

    if heavy_metals:
        opt_ssp["Score"] = 0
        opt_ssp["Desc"] += " ⛔ REJECTED (METALS)"

    # Sort
    recos = [opt_ankur_complet, opt_ankur_basic, opt_ssp, opt_incin]
    recos.sort(key=lambda x: x["Score"], reverse=True)
    best = recos[0]

    # 5. Finance
    capex = capex_manual if capex_manual > 0 else 500000 # Default
    elec_prod = max(0, (energy_net / 3.6) * 0.25)
    income = elec_prod * prix_elec
    profit = income - (capex * 0.08 / 365)

    return {
        "Best": best, "Recos": recos, "Logique": logic_msg,
        "Finances": {"CAPEX": capex, "Profit": profit}
    }

# --- 4. RESULTS INTERFACE ---

try:
    data = run_simulation()
    best = data["Best"]

    st.markdown(f"### 🎯 Recommendation: **{best['Tech']}**")
    
    # TABS
    tab1, tab2, tab3 = st.tabs(["📊 Overview & Synoptic", "💰 Financials", "⚙️ Tech Comparison"])

    with tab1:
        st.success(f"**Selected: {best['Tech']}**")
        st.caption(f"Reasoning: {data['Logique']}")
        
        col_img, col_info = st.columns([2, 1])
        
        with col_img:
            st.markdown("#### 🖼️ Process Flow Diagram")
            # Image Handler
            img_path = best["Image"]
            # Check file existence
            if os.path.exists(img_path):
                st.image(img_path, caption=f"Synoptic: {best['Tech']}", use_container_width=True)
            else:
                # Placeholder + Instruction
                st.warning(f"
