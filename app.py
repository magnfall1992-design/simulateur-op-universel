import streamlit as st
import pandas as pd

# --- 0. CONFIGURATION & STYLE ---
st.set_page_config(
    page_title="OP Architect V3",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS for better mobile display (centering titles, padding)
st.markdown("""
<style>
    .main > div {padding-top: 2rem;}
    .stTabs [data-baseweb="tab-list"] {gap: 2px;}
    .stTabs [data-baseweb="tab"] {height: 50px; white-space: pre-wrap;}
</style>
""", unsafe_allow_html=True)

# --- 1. USER GUIDE (Visible on Mobile & Desktop) ---
with st.expander("ℹ️ **START GUIDE: How to use this tool?**", expanded=True):
    st.markdown("""
    1. **Open the sidebar** on the left (click `>` on mobile).
    2. **Fill in the sections** in order: Sludge Quality, Infrastructure, then Financials.
    3. **The tool automatically calculates** the best fit among:
       * *Ankur* (Energy), *SSP/Thesvores* (Materials), or *Incinerator* (Mass Treatment).
    4. **Navigate the tabs below** to see financial and technical results.
    """)

# --- 2. SIDEBAR: INPUTS ---
with st.sidebar:
    st.title("🎛️ Project Settings")
    st.info("👈 Adjust these sliders to define your scenario.")

    # --- SECTION A: QUALITY ---
    st.header("1. Sludge Characterization")
    
    type_boue = st.selectbox(
        "Sludge Type", 
        ["Fecal Sludge (Domestic)", "Activated Sludge (WWTP)", "Industrial Sludge"],
        help="Sludge type impacts calorific value and incinerator choice."
    )

    ts_percent = st.slider(
        "Dry Solids Content (TS) %", 
        min_value=1.0, max_value=90.0, value=5.0, step=0.5,
        help="Concentration of solid matter.\n- 1-5%: Liquid (Vacuum truck)\n- 20-30%: Paste (Belt press output)\n- 80%+: Dried"
    )
    
    heavy_metals = st.toggle(
        "Heavy Metals Presence?", 
        value=False,
        help="Enable this if industries discharge into the network. This blocks certain valorizations (SSP Bricks)."
    )

    vol_boue = st.number_input(
        "Daily Volume (m³/day)", 
        value=40.0, step=5.0,
        help="Total volume entering the facility daily."
    )

    st.write("---")

    # --- SECTION B: LOGISTICS (CORE LOGIC) ---
    st.header("2. Infrastructure & Logistics")
    
    mode_collecte = st.radio(
        "Collection Method", 
        ["Trucks / Voluntary Drop-off", "Sewer Network (Direct)"],
        help="If 'Sewer', sludge arrives continuously. If 'Trucks', it arrives in batches."
    )
    
    has_station = st.radio(
        "Is there an EXISTING Treatment Plant?",
        ["No (Greenfield / Empty Land)", "Yes (Existing WWTP/FSTP)"],
        help="If 'Yes', we propose add-on modules (Ankur Basic). If 'No', we propose a full solution (Ankur Integrated)."
    )
    is_station_existante = True if has_station == "Yes (Existing WWTP/FSTP)" else False

    st.write("---")

    # --- SECTION C: OPTIONAL ---
    with st.expander("3. Co-Substrates (Optional)"):
        ajout_msw = st.checkbox("Co-process Municipal Solid Waste?", value=False)
        if ajout_msw:
            masse_msw = st.number_input("Waste Mass (kg/day)", value=2000.0)
            hum_msw = st.slider("Waste Moisture (%)", 0, 60, 20)
            lhv_msw = st.number_input("Waste LHV (MJ/kg)", value=18.0)
        else:
            masse_msw = 0; hum_msw = 0; lhv_msw = 0

    with st.expander("4. Financial Data"):
        prix_elec = st.number_input("Electricity Sales Price ($/kWh)", value=0.15)
        capex_manual = st.number_input("Max Budget ($ - leave 0 if unknown)", value=0)

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
    
    ms_msw = masse_msw * (1 - hum_msw/100)
    eau_msw = masse_msw - ms_msw
    
    total_dry = ms_boue + ms_msw
    total_water = eau_boue + eau_msw
    
    # 2. Energy Balance
    energy_in = (ms_boue * 12.0) + (ms_msw * lhv_msw)
    energy_evap = total_water * 3.2 
    energy_net = energy_in - energy_evap
    
    # 3. Selection Logic
    logic_msg = ""
    
    # Candidate Definitions
    opt_ankur_complet = {"Tech": "ANKUR INTEGRATED (Full)", "Score": 0, "Desc": "Replaces a WWTP (6-7 months timeline). Treats both water and sludge."}
    opt_ankur_basic = {"Tech": "ANKUR BASIC", "Score": 0, "Desc": "Energy module only. Requires pre-dried sludge (no dehydrator included)."}
    opt_ssp = {"Tech": "THESVORES (SSP)", "Score": 0, "Desc": "Valorization into materials (Bricks/Pavers). Simple and robust."}
    opt_incin = {"Tech": "INCINERATOR (Omni Processor)", "Score": 0, "Desc": "High-tech solution for large volumes or Activated Sludge."}

    # DECISION TREE
    
    # CASE 1 : SEWER NETWORK
    if mode_collecte == "Sewer Network (Direct)":
        if is_station_existante and type_boue == "Activated Sludge (WWTP)":
            logic_msg = "Sewer + WWTP (Activated Sludge) ➔ Incinerator recommended."
            opt_incin["Score"] = 95
            opt_ankur_basic["Score"] = 60 # Possible if solar drying exists
        else:
            logic_msg = "Standard Sewer ➔ Incinerator preferred."
            opt_incin["Score"] = 80
            opt_ankur_complet["Score"] = 50

    # CASE 2 : TRUCKS (VACUUM TANKERS)
    else: 
        if is_station_existante:
            logic_msg = "Trucks + Existing Plant ➔ Add-on needed (Ankur Basic or SSP)."
            opt_ankur_basic["Score"] = 90
            opt_ssp["Score"] = 85
            opt_ankur_complet["Score"] = 20 # Redundant to build a new plant
        else:
            logic_msg = "Trucks + Empty Land ➔ 'Turnkey' solution required (Ankur Integrated)."
            opt_ankur_complet["Score"] = 95
            opt_incin["Score"] = 60
            opt_ankur_basic["Score"] = 0 # Impossible without infrastructure
            opt_ssp["Score"] = 20 # Too complex to manage alone without treated water

    # HEAVY METALS CONSTRAINT
    if heavy_metals:
        opt_ssp["Score"] = 0 # FORBIDDEN: We don't make bricks with metals
        opt_ssp["Desc"] += " ⛔ REJECTED (METALS)"
        logic_msg += " | ⚠️ SSP Disqualified (Metals)."

    # SORTING
    recos = [opt_ankur_complet, opt_ankur_basic, opt_ssp, opt_incin]
    recos.sort(key=lambda x: x["Score"], reverse=True)
    best = recos[0]

    # 4. Financial Estimation (Simplified Model)
    capex = capex_manual if capex_manual > 0 else 0
    if capex == 0:
        if best["Tech"] == "ANKUR INTEGRATED (Full)": capex = 900000 + (vol_boue * 6500)
        elif best["Tech"] == "ANKUR BASIC": capex = 450000 + (vol_boue * 4000)
        elif "INCINERATOR" in best["Tech"]: capex = 2500000 + (vol_boue * 12000)
        else: capex = 300000 + (vol_boue * 3000) # SSP

    elec_prod = max(0, (energy_net / 3.6) * 0.25) if "ANKUR" in best["Tech"] or "INCINERATOR" in best["Tech"] else 0
    income = elec_prod * prix_elec
    opex = capex * 0.08 / 365
    profit = income - opex

    return {
        "Best": best,
        "Recos": recos,
        "Logique": logic_msg,
        "Masse": {"Eau": total_water, "Sec": total_dry},
        "Finances": {"CAPEX": capex, "OPEX": opex, "Income": income, "Profit": profit, "Elec": elec_prod}
    }

# --- 4. RESULTS INTERFACE (TABS) ---

try:
    data = run_simulation()
    best = data["Best"]
    fin = data["Finances"]

    st.markdown(f"### 🎯 Recommendation: **{best['Tech']}**")
    st.caption(f"Logic: {data['Logique']}")

    # TABS for Mobile UX
    tab1, tab2, tab3 = st.tabs(["📊 Overview", "💰 Financial Analysis", "⚙️ Technical Details"])

    with tab1:
        st.success(f"**Selected Solution: {best['Tech']}**")
        st.info(f"ℹ️ {best['Desc']}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Relevance Score", f"{best['Score']}/100")
        with col2:
            if "ANKUR" in best['Tech']:
                st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Biomass_gasification_plant.jpg/320px-Biomass_gasification_plant.jpg", caption="Ankur Concept (Illustration)")
            elif "SSP" in best['Tech']:
                st.markdown("🧱 **Output:** Construction Materials (Pavers/Bricks)")

        st.warning("Check 'Financial' and 'Technical' tabs for details.")

    with tab2:
        st.header("Estimated Profitability")
        c1, c2, c3 = st.columns(3)
        c1.metric("Investment (CAPEX)", f"${int(fin['CAPEX']):,}")
        c2.metric("Daily OPEX", f"${int(fin['OPEX'])}")
        c3.metric("Daily Net Profit", f"${int(fin['Profit'])}", delta_color="normal" if fin['Profit']>0 else "inverse")
        
        st.bar_chart(pd.DataFrame({
            "Type": ["Electricity Sales", "OPEX Costs"],
            "Amount ($)": [fin['Income'], fin['OPEX']]
        }).set_index("Type"))

    with tab3:
        st.header("Technical Comparison")
        df = pd.DataFrame(data["Recos"])
        st.dataframe(df[["Tech", "Score", "Desc"]], hide_index=True, use_container_width=True)
        
        st.subheader("Mass Balance")
        st.write(f"- Dry Matter (Fuel/Material): **{int(data['Masse']['Sec'])} kg/day**")
        st.write(f"- Water to Treat/Evaporate: **{int(data['Masse']['Eau'])} Liters/day**")
        
        if heavy_metals:
            st.error("🚨 ALERT: Heavy metals detected. SSP solution blocked for safety reasons.")

except Exception as e:
    st.error(f"Error: {e}")
