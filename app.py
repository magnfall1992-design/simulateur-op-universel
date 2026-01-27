import streamlit as st
import pandas as pd

# --- 0. CONFIGURATION GLOBALE ---
st.set_page_config(page_title="Universal OP Architect", layout="wide")

# CSS pour un look professionnel
st.markdown("""
<style>
    .metric-card {background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin: 5px;}
    .main-header {font-size: 2.5em; color: #2c3e50;}
</style>
""", unsafe_allow_html=True)

st.title("🏭 OP Architect: Advanced Decision Support System")
st.markdown("""
**Comprehensive modeling tool for Fecal Sludge Valorization.**
Integrates technical constraints (Moisture, LHV), Logistics, and Financial Modeling (CAPEX/OPEX).
*Benchmarked Technologies: SSSP (India), Ankur (India), Janicki/Sedron (USA).*
""")

# --- 1. SIDEBAR : PARAMÉTRAGE AVANCÉ ---
with st.sidebar:
    st.header("1. Feedstock & Logistics")
    
    # GISEMENT
    vol_boue = st.number_input("Daily Volume (m3/day)", value=40.0, step=5.0, help="Volume of sludge arriving at the plant.")
    humidite = st.slider("Moisture Content (%)", 30, 99, 95, help="95-99%: Raw Septage (Trucks). 30-50%: Dried Sludge.")
    
    type_boue = st.selectbox("Sludge Type", 
                             ["Fecal Sludge (Domestic)", "Industrial / Toxic Sludge", "WWTP Activated Sludge"],
                             help="Industrial sludge implies Heavy Metals -> Requires SSSP (Vitrification).")
    
    st.write("---")
    
    # CO-SUBSTRATS (L'ingrédient secret d'Ankur)
    st.header("2. Co-Substrates (Booster)")
    ajout_msw = st.checkbox("Enable MSW Co-processing?", value=False)
    
    if ajout_msw:
        masse_msw = st.number_input("Solid Waste Mass (kg/day)", value=2000.0)
        hum_msw = st.slider("Waste Moisture (%)", 0, 60, 20)
        lhv_msw = st.slider("Waste Caloric Value (MJ/kg)", 10.0, 35.0, 18.0, help="18 MJ/kg = Mix Plastic/Biomass")
    else:
        masse_msw = 0
        hum_msw = 0
        lhv_msw = 0

    st.write("---")
    
    # PARAMÈTRES FINANCIERS
    st.header("3. Financial Assumptions")
    tipping_fee = st.number_input("Tipping Fee ($/m3)", value=0.50, help="Revenue collected per truck dumping sludge.")
    
    c1, c2 = st.columns(2)
    with c1:
        prix_elec = st.number_input("Elec Price ($/kWh)", value=0.15)
    with c2:
        prix_pave = st.number_input("Paver Price ($/u)", value=0.60)
        
    capex_manual = st.number_input("Custom CAPEX ($)", value=0, help="Leave 0 for Auto-Estimation based on Scale.")

    # STRATÉGIE
    st.header("4. Strategic Priority")
    cible = st.radio("Primary Goal", 
                     ["Energy Profitability (kWh)", "Zero Liquid Discharge (ZLD)", "Materials (Construction)"])

# --- 2. MOTEUR DE CALCUL (The Brain) ---

def run_simulation():
    # A. BILAN DE MASSE (MASS BALANCE)
    # Boues
    masse_liquide_boue = vol_boue * 1000
    masse_seche_boue = masse_liquide_boue * (1 - humidite/100)
    eau_boue = masse_liquide_boue - masse_seche_boue
    
    # MSW
    masse_seche_msw = masse_msw * (1 - hum_msw/100)
    eau_msw = masse_msw - masse_seche_msw
    
    total_dry_mass = masse_seche_boue + masse_seche_msw
    total_water = eau_boue + eau_msw
