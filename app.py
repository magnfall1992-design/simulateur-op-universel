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
    score_op = 5
    if vol_boue > 80: score_op += 5
    if humidite < 80: score_op += 3 
    if cible == "Zero Liquid Discharge (ZLD)": score_op += 2
    recos.append({"Tech": "JANICKI / SEDRON", "Score": score_op, "Type": "Water/Energy"})
    
    recos.sort(key=lambda x: x["Score"], reverse=True)
    best_tech = recos[0]

    # --- C. FINANCIAL ENGINE (ECONOMICS) ---
    
    # 1. CAPEX ESTIMATION (If 0) - Rule of thumb curves
    if capex_manual > 0:
        capex = capex_manual
    else:
        if "SSSP" in best_tech['Tech']:
            capex = 250000 + (vol_boue * 8000) # Modular is cheaper start
        elif "JANICKI" in best_tech['Tech']:
            capex = 1500000 + (vol_boue * 15000) # Heavy infra
        else:
            capex = 100000 + (vol_boue * 5000) # Low tech Ankur
            
    # 2. REVENUE STREAMS (Daily)
    rev_tipping = vol_boue * tipping_fee
    rev_products = 0
    yield_metric = ""
    
    if "SSSP" in best_tech['Tech']:
        # Materials
        paves_qty = total_dry_mass * 0.3
        rev_products = paves_qty * prix_pave
        yield_metric = f"{int(paves_qty/vol_boue)} Pavers / m3 sludge"
    else:
        # Energy
        if energy_net > 0:
            elec_prod = (energy_net / 3.6) * 0.15
            rev_products = elec_prod * prix_elec
            yield_metric = f"{round(elec_prod/vol_boue, 1)} kWh / m3 sludge"
        else:
            yield_metric = "Negative Energy Balance"

    daily_income = rev_tipping + rev_products
    
    # 3. OPEX (Daily)
    daily_labor = labor_cost / 30
    daily_maintenance = (capex * (maintenance_rate/100)) / 365
    daily_fuel = 0
    if energy_net < 0:
        missing_mj = abs(energy_net)
        # Cost of fuel to compensate (approx diesel price)
        daily_fuel = (missing_mj / 35) * 1.0 # 1$ per liter approx
        
    daily_expense = daily_labor + daily_maintenance + daily_fuel
    
    # 4. ROI METRICS
    daily_profit = daily_income - daily_expense
    annual_profit = daily_profit * 300 # 300 operating days
    payback_years = capex / annual_profit if annual_profit > 0 else 999
    
    return {
        "Mass_Dry": total_
