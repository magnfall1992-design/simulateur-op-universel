import streamlit as st
import pandas as pd
import os

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="OP Architect V8 (English)", page_icon="🏭", layout="wide")

# CSS for Contact Cards and Headers
st.markdown("""
<style>
    .contact-card {
        padding: 20px;
        background-color: #f8f9fa;
        border-radius: 10px;
        border-left: 5px solid #007bff;
        margin-bottom: 20px;
    }
    .main-header {
        font-size: 30px;
        font-weight: bold;
        color: #1f2937;
        margin-bottom: 20px;
        border-bottom: 2px solid #e5e7eb;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. SIDEBAR (INPUTS) ---
with st.sidebar:
    st.title("🎛️ Settings")
    
    # Integrated Guide
    with st.expander("ℹ️ How it works?", expanded=False):
        st.write("1. Set Sludge Quality.")
        st.write("2. Choose Logistics (Trucks/Sewer).")
        st.write("3. The tool picks the best tech.")

    st.header("1. Characterization")
    type_boue = st.selectbox("Sludge Type", ["Fecal Sludge (Domestic)", "Activated Sludge (WWTP)", "Industrial Sludge"])
    ts_percent = st.slider("Dry Solids Content (TS %)", 1.0, 90.0, 5.0, 0.5)
    heavy_metals = st.checkbox("Heavy Metals Presence?", value=False)
    vol_boue = st.number_input("Volume (m³/day)", value=40.0, step=5.0)

    st.header("2. Infrastructure")
    mode_collecte = st.radio("Collection Method", ["Trucks", "Sewer Network"])
    has_station = st.radio("Existing Plant?", ["No (Greenfield)", "Yes (Existing Plant)"])
    is_station_existante = True if has_station == "Yes (Existing Plant)" else False

    st.header("3. Financials (Optional)")
    prix_elec = st.number_input("Elec. Price ($/kWh)", value=0.15)
    capex_manual = st.number_input("Max Budget ($)", value=0)
    
    st.markdown("---")
    st.markdown("### 👨‍💻 Developer")
    st.markdown("**Mansour Fall**")
    st.markdown("magnfall1992@gmail.com")

# --- 3. CALCULATIONS (Outside Sidebar) ---

# Default variables
masse_msw = 0
lhv_msw = 18.0

# Mass Balance
masse_boue = vol_boue * 1000
ms_boue = masse_boue * (ts_percent / 100.0)
eau_boue = masse_boue - ms_boue
total_dry = ms_boue 
total_water = eau_boue

# Energy Balance
energy_in = (ms_boue * 12.0)
energy_net = energy_in - (total_water * 3.2)

# --- 4. SOLUTION DEFINITIONS ---
opt_ankur_full = {
    "Tech": "ANKUR INTEGRATED (Full)", "Score": 0,
    "Desc": "Replaces a WWTP. Treats Water + Sludge (Waste to Energy).",
    "Contact": "Jignesh Shah", "Email": "jignesh.shah@ankurscientific.com",
    "Image": "ankur_diagram.png"
}
opt_ankur_basic = {
    "Tech": "ANKUR BASIC", "Score": 0,
    "Desc": "Energy Module Only. Requires pre-dried sludge.",
    "Contact": "Jignesh Shah", "Email": "jignesh.shah@ankurscientific.com",
    "Image": "ankur_diagram.png"
}
opt_ssp = {
    "Tech": "THESVORES (SSP)", "Score": 0,
    "Desc": "Material Valorization (Bricks/Pavers). Simple & Robust.",
    "Contact": "Saibal (SSP Pvt Ltd)", "Email": "sg1965@ssp.co.in",
    "Image": "ssp_diagram.png"
}
opt_janicki = {
    "Tech": "INCINERATOR (Omni Processor)", "Score": 0,
    "Desc": "High-Tech Incineration (Janicki/Sedron).",
    "Contact": "Matthew Bartholow", "Email": "matthew.bartholow@janicki.com",
    "Image": "janicki_diagram.png"
}

# --- 5. DECISION LOGIC ---
logic_msg = ""

if mode_collecte == "Sewer Network":
    if is_station_existante and type_boue == "Activated Sludge (WWTP)":
        logic_msg = "Sewer + Activated Sludge -> Incinerator recommended."
        opt_janicki["Score"] = 95
        opt_ankur_basic["Score"] = 60
    else:
        logic_msg = "Standard Sewer -> Incinerator preferred."
        opt_janicki["Score"] = 80
        opt_ankur_full["Score"] = 50
else: # Trucks
    if is_station_existante:
        logic_msg = "Trucks + Existing Plant -> Add-on (Ankur Basic or SSP)."
        opt_ankur_basic["Score"] = 90
        opt_ssp["Score"] = 85
        opt_ankur_full["Score"] = 20
    else:
        logic_msg = "Trucks + Greenfield -> Full Solution (Ankur Full)."
        opt_ankur_full["Score"] = 95
        opt_janicki["Score"] = 60
        opt_ankur_basic["Score"] = 0
        opt_ssp["Score"] = 20

if heavy_metals:
    opt_ssp["Score"] = 0
    logic_msg += " (SSP Rejected: Heavy Metals)"

# Sorting
recos = [opt_ankur_full, opt_ankur_basic, opt_ssp, opt_janicki]
recos.sort(key=lambda x: x["Score"], reverse=True)
best = recos[0]

# Financials
capex = capex_manual if capex_manual > 0 else 500000
elec_prod = max(0, (energy_net / 3.6) * 0.25)
income = elec_prod * prix_elec
profit = income - (capex * 0.08 / 365)

# --- 6. MAIN DISPLAY ---

# Main Title
st.markdown('<div class="main-header">📊 ANALYSIS RESULTS</div>', unsafe_allow_html=True)

# Result Banner
st.success(f"🏆 Best Solution: **{best['Tech']}**")
st.info(f"💡 Logic: {logic_msg}")

# Tabs
tab1, tab2, tab3 = st.tabs(["🖼️ Overview", "💰 Financials", "⚙️ Details"])

with tab1:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Process Diagram")
        # Image Handling
        if os.path.exists(best["Image"]):
            st.image(best["Image"], use_container_width=True)
        else:
            st.warning(f"Missing Image: {best['Image']}")
            st.caption("Please upload the diagram file to the folder.")

    with col2:
        st.markdown("### Manufacturer Contact")
        st.markdown(f"""
        <div class="contact-card">
            <h4>👤 {best['Contact']}</h4>
            <p>📧 <a href="mailto:{best['Email']}">{best['Email']}</a></p>
            <hr>
            <p><b>Score:</b> {best['Score']}/100</p>
        </div>
        """, unsafe_allow_html=True)
        st.write(f"**Description:** {best['Desc']}")

with tab2:
    m1, m2, m3 = st.columns(3)
    m1.metric("Est. CAPEX", f"${int(capex):,}")
    m2.metric("Daily Profit", f"${int(profit):,}")
    m3.metric("Elec. Prod", f"{int(elec_prod):,} kWh")

with tab3:
    st.write("### Score Comparison")
    # Simple dataframe creation for display
    df_data = [{"Tech": r["Tech"], "Score": r["Score"], "Email": r["Email"]} for r in recos]
    st.table(pd.DataFrame(df_data))
