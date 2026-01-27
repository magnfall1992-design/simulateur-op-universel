import streamlit as st
import pandas as pd

# --- 0. CONFIGURATION ---
st.set_page_config(page_title="Universal OP Architect", layout="wide")

st.title("🏭 OP Architect: Advanced Decision Support")
st.markdown("""
**Comprehensive Tool for Fecal Sludge Valorization.**
*Covers: SSSP (Materials/ZLD), Ankur (Hybrid Energy), Janicki (Incineration).*
""")

# --- 1. SIDEBAR: INPUTS ---
with st.sidebar:
    st.header("1. Feedstock & Logistics")
    vol_boue = st.number_input("Daily Volume (m3/day)", value=40.0, step=5.0)
    humidite = st.slider("Moisture Content (%)", 30, 99, 95)
    type_boue = st.selectbox("Sludge Type", 
                             ["Fecal Sludge (Domestic)", "Industrial / Toxic Sludge", "WWTP Activated Sludge"])
    
    st.write("---")
    st.header("2. Co-Substrates")
    ajout_msw = st.checkbox("Enable MSW Co-processing?", value=False)
    if ajout_msw:
        masse_msw = st.number_input("Solid Waste Mass (kg/day)", value=2000.0)
        hum_msw = st.slider("Waste Moisture (%)", 0, 60, 20)
        lhv_msw = st.number_input("Waste LHV (MJ/kg)", value=18.0)
    else:
        masse_msw = 0
        hum_msw = 0
        lhv_msw = 0

    st.write("---")
    st.header("3. Financials")
    tipping_fee = st.number_input("Tipping Fee ($/m3)", value=0.50)
    prix_elec = st.number_input("Elec Price ($/kWh)", value=0.15)
    prix_pave = st.number_input("Paver Price ($/unit)", value=0.60)
    capex_manual = st.number_input("Custom CAPEX ($)", value=0)

    st.header("4. Strategy")
    cible = st.radio("Priority", ["Energy Profitability", "Zero Liquid Discharge (ZLD)", "Materials (Construction)"])

# --- 2. CALCULATIONS ---

def run_simulation():
    # A. MASS BALANCE
    masse_boue = vol_boue * 1000
    ms_boue = masse_boue * (1 - humidite/100)
    eau_boue = masse_boue - ms_boue
    
    ms_msw = masse_msw * (1 - hum_msw/100)
    eau_msw = masse_msw - ms_msw
    
    total_dry = ms_boue + ms_msw
    total_water = eau_boue + eau_msw
    
    # B. ENERGY BALANCE
    energy_in = (ms_boue * 12.0) + (ms_msw * lhv_msw)
    energy_evap = total_water * 3.2 # MJ required to evaporate water
    energy_net = energy_in - energy_evap
    
    # C. RECOMMENDATION
    recos = []
    
    # SSSP Logic
    s_sssp = 5
    if type_boue == "Industrial / Toxic Sludge": s_sssp += 10
    if cible == "Materials (Construction)": s_sssp += 8
    if cible == "Zero Liquid Discharge (ZLD)": s_sssp += 5
    if 30 <= vol_boue <= 100: s_sssp += 3
    recos.append({"Tech": "SSSP (THESVORES)", "Score": s_sssp, "Type": "Materials"})
    
    # Ankur Logic
    s_ankur = 5
    if ajout_msw: s_ankur += 6
    if vol_boue < 50: s_ankur += 4
    recos.append({"Tech": "ANKUR SCIENTIFIC", "Score": s_ankur, "Type": "Hybrid Energy"})
    
    # Janicki Logic
    s_op = 5
    if vol_boue > 80: s_op += 8
    if humidite < 80: s_op += 4
    if cible == "Zero Liquid Discharge (ZLD)": s_op += 4
    recos.append({"Tech": "JANICKI / SEDRON", "Score": s_op, "Type": "Incineration"})
    
    recos.sort(key=lambda x: x["Score"], reverse=True)
    best = recos[0]
    
    # D. FINANCIALS
    # CAPEX
    if capex_manual > 0:
        capex = capex_manual
    elif "SSSP" in best['Tech']:
        capex = 300000 + (vol_boue * 7000)
    elif "JANICKI" in best['Tech']:
        capex = 2000000 + (vol_boue * 10000)
    else:
        capex = 150000 + (vol_boue * 5000)
        
    # INCOME
    inc_tipping = vol_boue * tipping_fee
    inc_prod = 0
    prod_txt = ""
    
    if "SSSP" in best['Tech']:
        qty = total_dry * 0.3 * 4 # Approx pavers
        inc_prod = qty * prix_pave
        prod_txt = f"{int(qty)} Pavers"
    elif energy_net > 0:
        kwh = (energy_net / 3.6) * 0.20
        net_kwh = max(0, kwh - (100 + vol_boue*2))
        inc_prod = net_kwh * prix_elec
        prod_txt = f"{int(net_kwh)} kWh"
    else:
        prod_txt = "0 (Energy Deficit)"
        
    daily_income = inc_tipping + inc_prod
    
    # EXPENSE
    fuel_cost = 0
    if energy_net < 0:
        fuel_cost = (abs(energy_net) / 35) * 1.0 # Fuel to burn wet sludge
        
    daily_opex = 100 + ((capex*0.05)/365) + fuel_cost # Labor + Maint + Fuel
    daily_profit = daily_income - daily_opex
    
    roi = capex / (daily_profit * 300) if daily_profit > 0 else 99.9
    
    return {
        "Mass_Dry": total_dry,
        "Mass_Water": total_water,
        "Energy_Net": energy_net,
        "Best": best,
        "Recos": recos,
        "Fin": {
            "CAPEX": capex,
            "Income": daily_income,
            "OPEX": daily_opex,
            "Profit": daily_profit,
            "ROI": roi,
            "Prod": prod_txt,
            "Fuel_Cost": fuel_cost
        }
    }

# --- 3. DASHBOARD ---
try:
    data = run_simulation()
    fin = data["Fin"]
    best = data["Best"]

    # TOP BANNER
    st.success(f"🏆 Recommended Technology: **{best['Tech']}** (Score: {best['Score']})")
    
    # KPIS
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("CAPEX Est.", f"${int(fin['CAPEX']):,}")
    k2.metric("Daily Profit", f"${int(fin['Profit'])}", delta_color="normal" if fin['Profit']>0 else "inverse")
    k3.metric("ROI (Payback)", f"{fin['ROI']:.1f} Years")
    k4.metric("Production", fin['Prod'])

    st.markdown("---")

    # CHARTS
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("💰 Financial Overview")
        chart_data = pd.DataFrame({
            "Category": ["Income (Sales+Fees)", "OPEX (Costs)"],
            "Amount": [fin['Income'], fin['OPEX']]
        })
        st.bar_chart(chart_data.set_index("Category"))
        if fin['Fuel_Cost'] > 0:
            st.error(f"⚠️ High Moisture Alert! Fuel Cost: ${int(fin['Fuel_Cost'])}/day")

    with c2:
        st.subheader("⚖️ Mass Balance")
        mass_data = pd.DataFrame({
            "Type": ["Water (To Evaporate)", "Dry Solids (Fuel)"],
            "Kg/Day": [data['Mass_Water'], data['Mass_Dry']]
        })
        st.bar_chart(mass_data.set_index("Type"))

    # STRATEGY TABLE
    st.subheader("📊 Strategic Comparison")
    st.dataframe(pd.DataFrame(data["Recos"]), use_container_width=True)

except Exception as e:
    st.error(f"An error occurred: {e}")
