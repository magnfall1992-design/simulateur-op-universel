import streamlit as st
import pandas as pd

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Universal OP Simulator", layout="wide")

st.title("🏭 Omni-Processor Simulator (Decision Support Tool)")
st.markdown("""
**Universal techno-economic modeling for thermal treatment of sludge.**
This tool simulates various technologies (Combustion, Pyrolysis, Gasification) by adjusting feedstock and pre-treatment parameters.
""")

# --- 1. SIDEBAR: INPUTS ---
with st.sidebar:
    st.header("1. Feedstock & Inputs")
    
    # SECTION: FECAL SLUDGE
    st.subheader("💩 Fecal Sludge (FS)")
    vol_boue = st.number_input("FS Volume (m3/day)", value=30.0)
    hum_boue_initiale = st.slider("Initial FS Moisture (%)", 80, 99, 97)
    
    # SECTION: CO-SUBSTRATES
    st.subheader("➕ Co-Substrates (Optional)")
    use_msw = st.checkbox("Add Solid Waste (MSW)?", value=True, help="Check this if the tech accepts Municipal Solid Waste")
    
    if use_msw:
        masse_org = st.number_input("Organic Waste Mass (kg/day)", value=5000.0)
        hum_org_initiale = st.slider("Organic Moisture (%)", 0, 90, 70)
        masse_plastique = st.number_input("Plastic / RDF (kg/day)", value=500.0, help="High calorific value fuel (Booster)")
    else:
        masse_org = 0
        hum_org_initiale = 0
        masse_plastique = 0

    st.header("2. Technology Configuration")
    
    # PRE-TREATMENT
    st.subheader("⚙️ Pre-treatment")
    type_pretraitement = st.selectbox("Dewatering Method", 
                                      ["Screw Press (Standard)", "Solar Drying + Mechanical", "None (Direct to Furnace)"])
    
    hum_sortie_pretraitement = 80 # Default
    if type_pretraitement == "Solar Drying + Mechanical":
        hum_sortie_pretraitement = st.slider("Target Moisture after Pre-treatment (%)", 10, 80, 25, help="E.g., Ankur with sun drying goes very low")
    elif type_pretraitement == "Screw Press (Standard)":
        hum_sortie_pretraitement = st.slider("Moisture after Press (%)", 50, 90, 80)
    else:
        hum_sortie_pretraitement = hum_boue_initiale # No change

    st.header("3. Economic Model")
    prix_elec = st.number_input("Electricity Price ($/kWh)", value=0.15)
    prix_eau = st.number_input("Distilled Water Price ($/L)", value=0.02)

# --- 2. CALCULATION ENGINE ---

def calculate_performance():
    # --- A. MASS BALANCE (WATER vs DRY MATTER) ---
    
    # 1. Fecal Sludge
    ms_boue = (vol_boue * 1000) * (1 - hum_boue_initiale/100) # Dry Matter (kg)
    
    # Mass entering furnace after pre-treatment
    if hum_sortie_pretraitement < 100:
        masse_entree_four_boue = ms_boue / (1 - hum_sortie_pretraitement/100)
    else:
        masse_entree_four_boue = ms_boue
        
    eau_retiree_pretraitement = (vol_boue * 1000) - masse_entree_four_boue
    
    # 2. Co-Substrates
    ms_org = masse_org * (1 - hum_org_initiale/100)
    # Hypothesis: Organics dry similarly if Solar Drying is active
    hum_org_four = 25 if "Solar" in type_pretraitement else hum_org_initiale
    masse_entree_four_org = ms_org / (1 - hum_org_four/100) if ms_org > 0 else 0
    
    # --- B. THERMAL BALANCE (ENERGY) ---
    
    # LHV (Lower Heating Value - MJ/kg dry)
    pci_boue = 12.0
    pci_org = 14.0
    pci_plastique = 35.0
    
    # Energy INPUT (Available Fuel)
    E_boue = ms_boue * pci_boue
    E_org = ms_org * pci_org
    E_plastique = masse_plastique * pci_plastique
    E_total_in = E_boue + E_org + E_plastique
    
    # Energy REQUIRED (To evaporate remaining water in furnace)
    eau_dans_four_boue = masse_entree_four_boue - ms_boue
    eau_dans_four_org = masse_entree_four_org - ms_org
    eau_totale_a_evaporer = eau_dans_four_boue + eau_dans_four_org
    
    # Energy cost for evaporation (Latent heat + Losses) ~ 3.0 MJ/kg water
    E_evap = eau_totale_a_evaporer * 3.0
    
    # --- C. NET RESULTS ---
    E_net = E_total_in - E_evap
    
    # Electricity Conversion
    rendement_systeme = 0.15 # Industrial average
    if E_net > 0:
        prod_elec_kwh = (E_net / 3.6) * rendement_systeme
        conso_interne = 150 + (vol_boue * 2) # Internal consumption estimate
        elec_net_export = prod_elec_kwh - conso_interne
        status = "✅ Surplus (Self-sufficient)"
        couleur_status = "green"
    else:
        elec_net_export = (E_net / 3.6) # Negative = needs fuel
        status = "❌ Deficit (Needs external fuel)"
        couleur_status = "red"

    # Water Production (Condensation)
    eau_produite = eau_totale_a_evaporer * 0.85 # 85% recovery rate
    
    return {
        "FS Dry Mass (kg)": round(ms_boue),
        "Water removed pre-furnace (L)": round(eau_retiree_pretraitement),
        "Energy Input (MJ)": round(E_total_in),
        "Energy Evap (MJ)": round(E_evap),
        "Net Elec (kWh/day)": round(elec_net_export, 1),
        "Distilled Water (L/day)": round(eau_produite),
        "Revenue ($/day)": round((elec_net_export * prix_elec) + (eau_produite * prix_eau), 2) if elec_net_export > 0 else 0,
        "Status": status,
        "Color": couleur_status
    }

# --- 3. DASHBOARD ---
res = calculate_performance()

# KPI Display
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Net Exportable Electricity", f"{res['Net Elec (kWh/day)']} kWh/day", delta_color="normal" if res['Net Elec (kWh/day)']>0 else "inverse")
kpi2.metric("Distilled Water Produced", f"{res['Distilled Water (L/day)']} L/day")
kpi3.metric("Est. Daily Revenue", f"{res['Revenue ($/day)']} $")

st.markdown(f"### Global Balance: :{res['Color']}[{res['Status']}]")

# Charts
c1, c2 = st.columns(2)

with c1:
    st.subheader("💧 Water Balance")
    st.info(f"""
    Water management is the main challenge. Here is how it is handled:
    * **Initial Water:** {vol_boue*1000} Liters
    * **Removed by Pre-treatment:** {res['Water removed pre-furnace (L)']} Liters (Energy saving)
    * **Evaporated in Furnace:** {res['Distilled Water (L/day)']/0.85:.0f} Liters
    """)

with c2:
    st.subheader("🔥 Energy Balance")
    data_energy = {
        "Input (Fecal Sludge)": res["FS Dry Mass (kg)"] * 12,
        "Input (Co-Substrates)": (st.session_state.masse_org if 'masse_org' in st.session_state else 0) * 14 + (st.session_state.masse_plastique if 'masse_plastique' in st.session_state else 0) * 35,
        "Consumption (Drying)": -res["Energy Evap (MJ)"]
    }
    st.bar_chart(pd.Series(data_energy))

# Explanation Section
with st.expander("ℹ️ How to simulate different manufacturers?"):
    st.markdown("""
    * **To simulate ANKUR (Cox's Bazar Model):**
        * Enable "Add Solid Waste".
        * Set Plastic = 500 kg.
        * Pre-treatment = "Solar Drying + Mechanical".
    * **To simulate JANICKI / SEDRON (Standard Omni Processor):**
        * Disable "Add Solid Waste" (or keep values low).
        * Pre-treatment = "Screw Press (Standard)" or "None" (if integrated drying).
    * **To simulate a basic PYROLYZER:**
        * Requires very dry sludge. Choose "Solar Drying" with target moisture < 30%.
    """)
