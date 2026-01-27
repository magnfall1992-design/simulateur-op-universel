import streamlit as st
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Universal OP Architect", layout="wide")

st.title("🏭 OP Architect: Universal Decision Support Tool")
st.markdown("""
**Strategic sizing and technology selection platform for sludge valorization.**
Integrates industrial logic: *Zero Liquid Discharge (ZLD)*, *Waste-to-Energy*, and *Waste-to-Material*.
*Based on SSSP, Ankur, and Janicki/Sedron standards.*
""")

# --- 1. SIDEBAR: FEEDSTOCK & STRATEGY ---
with st.sidebar:
    st.header("1. Feedstock Sizing")
    
    # VOLUME
    vol_boue = st.number_input("Daily Volume (m3/day)", value=40.0, step=5.0)
    
    # SLUDGE TYPE
    type_boue = st.selectbox("Sludge Nature", 
                             ["Fecal Sludge (FSM)", "Industrial / Toxic Sludge", "Activated Sludge (WWTP)"])
    
    # CONSISTENCY & LOGISTICS
    st.write("---")
    mode_apport = st.radio("Logistics / Input Method", ["Liquid (Direct Truck Disposal)", "Pasty/Solid (Dried/Thickened)"])
    
    if mode_apport == "Liquid (Direct Truck Disposal)":
        ts_boue = st.slider("Total Solids (TS %)", 0.5, 10.0, 2.5, help="Raw liquid sludge from vacuum trucks.")
    else:
        ts_boue = st.slider("Total Solids (TS %)", 15.0, 90.0, 30.0, help="Sludge from drying beds or mechanical dewatering.")

    # CO-SUBSTRATES
    st.header("2. Co-Substrates")
    ajout_msw = st.checkbox("Add Municipal Solid Waste (MSW)?", value=False)
    if ajout_msw:
        masse_msw = st.number_input("Waste Mass (kg/day)", value=2000.0)
    else:
        masse_msw = 0

    st.header("3. Strategic Goals")
    cible = st.radio("Project Priority", ["Energy Profitability (Electricity)", "Zero Liquid Discharge (ZLD)", "Materials (Pavers/Bricks)"])

# --- 2. INTELLIGENCE ENGINE ---

def analyse_scenarios():
    recos = []
    
    # TOTAL DRY MASS
    ms_boue = (vol_boue * 1000) * (ts_boue/100)
    ms_msw = masse_msw * 0.7 
    ms_totale = ms_boue + ms_msw
    
    # --- RULE 1: SCALE SEGMENTATION ---
    if vol_boue < 30:
        segment = "SMALL SCALE (<30 m3)"
        tech_base = "Pyrolysis / Ankur Small"
        desc = "Compact solutions. Energy generation is challenging. Priority is sanitation and volume reduction."
    elif 30 <= vol_boue < 90:
        segment = "MEDIUM SCALE (30-90 m3)"
        tech_base = "Modular / SSSP"
        desc = "Ideal zone for modular solutions (e.g., SSSP). Mixed valorization (Energy or Construction Materials)."
    else:
        segment = "LARGE SCALE (>90 m3)"
        tech_base = "Incineration / Janicki Large"
        desc = "Heavy infrastructure. Economies of scale allow for massive electricity or distilled water production."

    # --- RULE 2: TECHNOLOGY SCORING ---
    
    # SCENARIO A: SSSP (THESVORES)
    score_sssp = 5
    if type_boue == "Industrial / Toxic Sludge": 
        score_sssp += 5
    if cible == "Materials (Pavers/Bricks)": 
        score_sssp += 5
    if cible == "Zero Liquid Discharge (ZLD)": 
        score_sssp += 3
    if 30 <= vol_boue < 100: 
        score_sssp += 2
    
    recos.append({
        "Tech": "SSSP (THESVORES Tech)",
        "Type": "Turbo Drying + Vitrification",
        "Score": score_sssp,
        "Advantage": "🛡️ Zero Liquid Discharge (ZLD) + Pavers. Best for toxic/industrial sludge.",
        "Output": "Pavers / Bricks",
        "Liquid Discharge": "NONE (Internal Recycle)"
    })

    # SCENARIO B: ANKUR / PYROLYSIS
    score_ankur = 5
    if ajout_msw: 
        score_ankur += 4
    if mode_apport == "Liquid (Direct Truck Disposal)": 
        score_ankur += 3
    if vol_boue < 50: 
        score_ankur += 2
    
    recos.append({
        "Tech": "ANKUR SCIENTIFIC (Cox's Bazar Model)",
        "Type": "Screw Press + Hybrid Pyrolysis",
        "Score": score_ankur,
        "Advantage": "🔥 Robust for liquid inputs thanks to mechanical dewatering & MSW co-firing.",
        "Output": "Electricity + Ash",
        "Liquid Discharge": "YES (Press Filtrate)"
    })

    # SCENARIO C: JANICKI / SEDRON
    score_op = 5
    if vol_boue > 80: 
        score_op += 5
    if ts_boue > 20: 
        score_op += 3
    if cible == "Zero Liquid Discharge (ZLD)": 
        score_op += 2
    
    recos.append({
        "Tech": "JANICKI / SEDRON (Omni Processor)",
        "Type": "Steam Combustion / Incineration",
        "Score": score_op,
        "Advantage": "💧 Massive production of Distilled Water. Industrial Standard.",
        "Output": "Distilled Water + Elec",
        "Liquid Discharge": "NONE (Total Evaporation)"
    })

    recos.sort(key=lambda x: x["Score"], reverse=True)
    return segment, desc, recos, ms_totale

# --- 3. DASHBOARD DISPLAY ---

segment, desc, recos, ms_totale
