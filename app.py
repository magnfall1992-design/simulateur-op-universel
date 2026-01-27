import streamlit as st
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Universal OP Architect", layout="wide")

st.title("🏭 OP Architect: Universal Decision Support Tool")
st.markdown("""
**Strategic sizing, technology selection, and financial modeling for sludge valorization.**
*Covers: SSSP (Materials), Ankur (Hybrid), Janicki (Incineration).*
""")

# --- 1. SIDEBAR: INPUTS ---
with st.sidebar:
    st.header("1. Feedstock Characteristics")
    vol_boue = st.number_input("Daily Volume (m3/day)", value=40.0, step=5.0)
    humidite = st.slider("Moisture Content (%)", 0, 99, 95, help="95-99% = Raw Septage. 20-40% = Dried Sludge.")
    type_boue = st.selectbox("Sludge Nature", ["Fecal Sludge (FSM)", "Industrial / Toxic Sludge", "Activated Sludge (WWTP)"])
    
    st.write("---")
    st.header("2. Co-Substrates")
    ajout_msw = st.checkbox("Add Municipal Solid Waste (MSW)?", value=False)
    if ajout_msw:
        masse_msw = st.number_input("Waste Mass (kg/day)", value=2000.0)
        hum_msw = st.slider("Waste Moisture (%)", 0, 80, 30)
    else:
        masse_msw = 0
        hum_msw = 0

    st.header("3. Strategic Goals")
    cible = st.radio("Project Priority", ["Energy Profitability (Electricity)", "Zero Liquid Discharge (ZLD)", "Materials (Pavers/Bricks)"])
    
    st.write("---")
    st.header("4. Financial Parameters (The Economics)")
    
    # REVENUS (INCOME)
    st.subheader("💰 Income Sources")
    tipping_fee = st.number_input("Tipping Fee ($/m3)", value=0.5, help="Fee paid by trucks to dump sludge (Ref: Senegal ~0.5$/m3)")
    prix_elec = st.number_input("Elec Price ($/kWh)", value=0.15)
    prix_pave = st.number_input("Paver Price ($/unit)", value=0.50, help="If Materials option selected")
    carbon_credit = st.number_input("Carbon Credit ($/ton CO2)", value=0.0, help="Optional")

    # COÛTS (COSTS)
    st.subheader("💸 Costs (CAPEX/OPEX)")
    capex_manual = st.number_input("Estimated CAPEX ($)", value=0, help="Leave 0 for auto-estimation based on volume")
    labor_cost = st.number_input("Labor Cost ($/month)", value=3000.0, help="Total staff salary")
    maintenance_rate = st.slider("Maintenance (% of CAPEX/yr)", 1, 10, 5)

# --- 2. CALCULATION ENGINE ---

def run_simulation():
    # --- A. MASS & ENERGY BALANCE ---
    masse_totale_boue = vol_boue * 1000
    masse_seche_boue = masse_totale_boue * (1 - humidite/100)
    eau_boue = masse_totale_boue - masse_seche_boue
    
    masse_seche_msw = masse_msw * (1 - hum_msw/100)
    eau_msw = masse_msw - masse_seche_msw
    
    total_dry_mass = masse_seche_boue + masse_seche_msw
    total_water = eau_boue + eau_msw
    
    # Energy Calculation
    lhv_boue = 12.0
    lhv_msw = 16.0 
    energy_in = (masse_seche_boue * lhv_boue) + (masse_seche_msw * lhv_msw)
    energy_evap = total_water * 3.0
    energy_net = energy_in - energy_evap
    
    # --- B. RECOMMENDATION LOGIC ---
    recos = []
    
    # SSSP Logic
    score_sssp = 5
    if type_boue == "Industrial / Toxic Sludge": score_sssp += 5
    if cible == "Materials (Pavers/Bricks)": score_sssp += 5
    if cible == "Zero Liquid Discharge (ZLD)": score_sssp += 3
    if 30 <= vol_boue < 100: score_sssp += 2
    recos.append({"Tech": "SSSP (THESVORES)", "Score": score_sssp, "Type": "Materials"})

    # ANKUR Logic
    score_ankur = 5
    if humidite > 85 and ajout_msw: score_ankur += 5 
    if vol_boue < 50: score_ankur += 2
    recos.append({"Tech": "ANKUR SCIENTIFIC", "Score": score_ankur, "Type": "Energy"})

    # JANICKI Logic
    score_op =
