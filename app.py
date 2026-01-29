import streamlit as st
import pandas as pd
import os

# --- 0. CONFIGURATION ---
st.set_page_config(page_title="OP Architect V7", page_icon="🏭", layout="wide")

# CSS pour le style des cartes de contact
st.markdown("""
<style>
    .contact-box {
        padding: 15px;
        background-color: #f0f2f6;
        border-radius: 10px;
        border-left: 5px solid #2e7bcf;
        margin-top: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 1. INITIALISATION ---
masse_msw = 0
hum_msw = 0
lhv_msw = 0

# --- 2. SIDEBAR (Paramètres) ---
with st.sidebar:
    st.title("🎛️ Project Settings")
    
    # Section Qualité
    st.header("1. Sludge Characterization")
    type_boue = st.selectbox("Sludge Type", ["Fecal Sludge (Domestic)", "Activated Sludge (WWTP)", "Industrial Sludge"])
    ts_percent = st.slider("Dry Solids Content (TS) %", 1.0, 90.0, 5.0, 0.5)
    heavy_metals = st.checkbox("Heavy Metals Presence?", value=False)
    vol_boue = st.number_input("Daily Volume (m³/day)", value=40.0, step=5.0)

    st.write("---")
    
    # Section Logistique
    st.header("2. Infrastructure")
    mode_collecte = st.radio("Collection Method", ["Trucks", "Sewer Network"])
    has_station = st.radio("Existing Plant?", ["No (Greenfield)", "Yes (Existing)"])
    is_station_existante = True if has_station == "Yes (Existing)" else False

    st.write("---")
    
    # Section Finance & Déchets
    with st.expander("3. Financials & Waste"):
        prix_elec = st.number_input("Elec. Price ($/kWh)", value=0.15)
        capex_manual = st.number_input("Max Budget ($)", value=0)
        
        if st.checkbox("Add Municipal Waste?", value=False):
            masse_msw = st.number_input("Waste Mass (kg)", value=2000.0)
            lhv_msw = 18.0

    st.write("---")
    
    # Crédits Développeur
    st.markdown("### 👨‍💻 Developer")
    st.markdown("**Mansour Fall**")
    st.markdown("magnfall1992@gmail.com")

# --- 3. MOTEUR DE CALCUL ---

# Bilan Masse
masse_boue = vol_boue * 1000
ms_boue = masse_boue * (ts_percent / 100.0)
eau_boue = masse_boue - ms_boue
total_dry = ms_boue + masse_msw
total_water = eau_boue

# Bilan Énergie
energy_in = (ms_boue * 12.0) + (masse_msw * lhv_msw)
energy_net = energy_in - (total_water * 3.2)

# --- 4. DÉFINITION DES SOLUTIONS (Données & Contacts) ---
opt_ankur_full = {
    "Tech": "ANKUR INTEGRATED (Full)", "Score": 0,
    "Desc": "Replaces WWTP. Treats water & sludge (Waste to Energy).",
    "Contact": "Jignesh Shah", "Email": "jignesh.shah@ankurscientific.com",
    "Image": "ankur_diagram.png"
}
opt_ankur_basic = {
    "Tech": "ANKUR BASIC", "Score": 0,
    "Desc": "Energy module only. Needs dry sludge/pre-treatment.",
    "Contact": "Jignesh Shah", "Email": "jignesh.shah@ankurscientific.com",
    "Image": "ankur_diagram.png"
}
opt_ssp = {
    "Tech": "THESVORES (SSP)", "Score": 0,
    "Desc": "Materials valorization (Bricks). Simple & Robust.",
    "Contact": "Saibal (SSP Pvt Ltd)", "Email": "sg1965@ssp.co.in",
    "Image": "ssp_diagram.png"
}
opt_janicki = {
    "Tech": "INCINERATOR (Omni Processor)", "Score": 0,
    "Desc": "High-tech incineration (Janicki/Sedron).",
    "Contact": "Matthew Bartholow", "Email": "matthew.bartholow@janicki.com",
    "Image": "janicki_diagram.png"
}

# --- 5. LOGIQUE DÉCISIONNELLE ---
logic_msg = ""

if mode_collecte == "Sewer Network":
    # Cas Réseau
    if is_station_existante and type_boue == "Activated Sludge (WWTP)":
        logic_msg = "Scenario: Sewer + WWTP (Activated Sludge) -> Incinerator recommended."
        opt_janicki["Score"] = 95
        opt_ankur_basic["Score"] = 60
    else:
        logic_msg = "Scenario: Sewer Standard -> Incinerator preferred."
        opt_janicki["Score"] = 80
        opt_ankur_full["Score"] = 50
else: 
    # Cas Camions
    if is_station_existante:
        logic_msg = "Scenario: Trucks + Existing Plant -> Add-on (Ankur Basic or SSP)."
        opt_ankur_basic["Score"] = 90
        opt_ssp["Score"] = 85
        opt_ankur_full["Score"] = 20 # Pénalité car doublon avec la station
    else:
        logic_msg = "Scenario: Trucks + Greenfield -> Turnkey Solution (Ankur Full)."
        opt_ankur_full["Score"] = 95
        opt_janicki["Score"] = 60
        opt_ankur_basic["Score"] = 0 # Impossible sans station
        opt_ssp["Score"] = 20 # Trop complexe à gérer seul

# Contrainte Métaux Lourds
if heavy_metals:
    opt_ssp["Score"] = 0
    opt_ssp["Desc"] += " (⛔ REJECTED: HEAVY METALS)"
    logic_msg += " | SSP rejected due to metals."

# Classement
recos = [opt_ankur_full, opt_ankur
