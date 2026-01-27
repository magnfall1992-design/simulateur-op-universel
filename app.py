import streamlit as st
import pandas as pd

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Simulateur OP Universel", layout="wide")

st.title("🏭 Simulateur Omni-Processor (Outil d'Aide à la Décision)")
st.markdown("""
**Modélisation technico-économique universelle pour la valorisation thermique des boues.**
Cet outil permet de simuler n'importe quelle technologie (Combustion, Pyrolyse, Gazéification) en ajustant les paramètres d'intrants et de pré-traitement.
""")

# --- 1. BARRE LATÉRALE : PARAMÈTRES (INPUTS) ---
with st.sidebar:
    st.header("1. Gisement & Intrants")
    
    # SECTION BOUES
    st.subheader("💩 Boues de Vidange")
    vol_boue = st.number_input("Volume Boue liquide (m3/jour)", value=30.0)
    hum_boue_initiale = st.slider("Humidité Initiale Boue (%)", 80, 99, 97)
    
    # SECTION CO-SUBSTRATS (OPTIONNEL)
    st.subheader("➕ Co-Substrats (Optionnel)")
    use_msw = st.checkbox("Ajout Déchets Solides (MSW) ?", value=True, help="Cochez si la technologie accepte les ordures ménagères")
    
    if use_msw:
        masse_org = st.number_input("Masse Organique (kg/jour)", value=5000.0)
        hum_org_initiale = st.slider("Humidité Organique (%)", 0, 90, 70)
        masse_plastique = st.number_input("Plastique / CSR (kg/jour)", value=500.0, help="Carburant à haut pouvoir calorifique")
    else:
        masse_org = 0
        hum_org_initiale = 0
        masse_plastique = 0

    st.header("2. Configuration Technologie")
    
    # PRÉ-TRAITEMENT MÉCANIQUE
    st.subheader("⚙️ Pré-traitement")
    type_pretraitement = st.selectbox("Type de Déshydratation", 
                                      ["Presse à Vis (Standard)", "Séchage Solaire + Mécanique", "Aucun (Direct Four)"])
    
    hum_sortie_pretraitement = 80 # Valeur par défaut (Presse à vis)
    if type_pretraitement == "Séchage Solaire + Mécanique":
        hum_sortie_pretraitement = st.slider("Humidité cible après pré-traitement (%)", 10, 80, 25, help="Ex: Ankur avec séchage solaire descend très bas")
    elif type_pretraitement == "Presse à Vis (Standard)":
        hum_sortie_pretraitement = st.slider("Humidité sortie presse (%)", 50, 90, 80)
    else:
        hum_sortie_pretraitement = hum_boue_initiale # Pas de changement

    st.header("3. Modèle Économique")
    prix_elec = st.number_input("Prix Électricité ($/kWh)", value=0.15)
    prix_eau = st.number_input("Prix Eau Distillée ($/L)", value=0.02)

# --- 2. MOTEUR DE CALCUL UNIVERSEL ---

def calculer_performance():
    # --- A. BILAN DE MASSE (EAU vs MATIÈRE SÈCHE) ---
    
    # 1. Boues
    ms_boue = (vol_boue * 1000) * (1 - hum_boue_initiale/100) # Matière Sèche (kg)
    
    # Calcul de la masse entrant dans le four après pré-traitement
    # Formule : Masse_Totale = MS / (1 - Humidité_Cible)
    if hum_sortie_pretraitement < 100:
        masse_entree_four_boue = ms_boue / (1 - hum_sortie_pretraitement/100)
    else:
        masse_entree_four_boue = ms_boue # Cas théorique impossible mais pour éviter div/0
        
    eau_retiree_pretraitement = (vol_boue * 1000) - masse_entree_four_boue
    
    # 2. Co-Substrats (Si activés)
    ms_org = masse_org * (1 - hum_org_initiale/100)
    # Hypothèse : Les déchets organiques sèchent un peu à l'air libre ou via le système
    # On applique le même ratio de séchage si "Séchage Solaire" est activé, sinon standard
    hum_org_four = 25 if "Solaire" in type_pretraitement else hum_org_initiale
    masse_entree_four_org = ms_org / (1 - hum_org_four/100) if ms_org > 0 else 0
    
    # --- B. BILAN THERMIQUE (ÉNERGIE) ---
    
    # PCI (Valeurs standards MJ/kg sec)
    pci_boue = 12.0
    pci_org = 14.0
    pci_plastique = 35.0
    
    # Énergie DISPONIBLE (Combustible)
    E_boue = ms_boue * pci_boue
    E_org = ms_org * pci_org
    E_plastique = masse_plastique * pci_plastique
    E_total_in = E_boue + E_org + E_plastique
    
    # Énergie REQUISE (Pour évaporer l'eau restante dans le four)
    # L'eau qui rentre dans le four est celle qui reste dans la boue + celle des déchets organiques
    eau_dans_four_boue = masse_entree_four_boue - ms_boue
    eau_dans_four_org = masse_entree_four_org - ms_org
    eau_totale_a_evaporer = eau_dans_four_boue + eau_dans_four_org
    
    # Coût énergétique évaporation (Latente + Pertes) ~ 3.0 MJ/kg d'eau
    E_evap = eau_totale_a_evaporer * 3.0
    
    # --- C. RÉSULTATS NETS ---
    E_net = E_total_in - E_evap
    
    # Conversion en Électricité
    rendement_systeme = 0.15 # Moyenne industrielle (Turbine vapeur ou Moteur gaz)
    if E_net > 0:
        prod_elec_kwh = (E_net / 3.6) * rendement_systeme
        conso_interne = 150 + (vol_boue * 2) # Estimation conso pompes/moteurs
        elec_net_export = prod_elec_kwh - conso_interne
        status = "✅ Excédentaire (Auto-suffisant)"
        couleur_status = "green"
    else:
        elec_net_export = (E_net / 3.6) # Chiffre négatif = besoin fuel
        status = "❌ Déficitaire (Besoin carburant externe)"
        couleur_status = "red"

    # Production Eau (Condensation)
    eau_produite = eau_totale_a_evaporer * 0.85 # 85% de récupération
    
    return {
        "Masse Sèche Boue (kg)": round(ms_boue),
        "Eau retirée avant four (L)": round(eau_retiree_pretraitement),
        "Énergie Input (MJ)": round(E_total_in),
        "Énergie Evap (MJ)": round(E_evap),
        "Élec Net (kWh/j)": round(elec_net_export, 1),
        "Eau Distillée (L/j)": round(eau_produite),
        "Revenu ($/j)": round((elec_net_export * prix_elec) + (eau_produite * prix_eau), 2) if elec_net_export > 0 else 0,
        "Status": status,
        "Couleur": couleur_status
    }

# --- 3. TABLEAU DE BORD (DASHBOARD) ---
res = calculer_performance()

# Affichage des KPI
kpi1, kpi2, kpi3 = st.columns(3)
kpi1.metric("Électricité Nette Exportable", f"{res['Élec Net (kWh/j)']} kWh/j", delta_color="normal" if res['Élec Net (kWh/j)']>0 else "inverse")
kpi2.metric("Eau Distillée Produite", f"{res['Eau Distillée (L/j)']} L/j")
kpi3.metric("Revenu Journalier Est.", f"{res['Revenu ($/j)']} $")

st.markdown(f"### Bilan Global : :{res['Couleur']}[{res['Status']}]")

# Graphiques
c1, c2 = st.columns(2)

with c1:
    st.subheader("💧 Bilan Hydrique")
    st.info(f"""
    Le défi principal est l'eau. Voici comment elle est gérée par la technologie choisie :
    * **Eau initiale :** {vol_boue*1000} Litres
    * **Retirée par Pré-traitement :** {res['Eau retirée avant four (L)']} Litres (Économie d'énergie)
    * **Évaporée dans le four :** {res['Eau Distillée (L/j)']/0.85:.0f} Litres
    """)

with c2:
    st.subheader("🔥 Bilan Énergétique")
    # Données pour le graphique
    data_energy = {
        "Apport (Boues)": res["Masse Sèche Boue (kg)"] * 12,
        "Apport (Co-Substrats)": (st.session_state.masse_org if 'masse_org' in st.session_state else 0) * 14 + (st.session_state.masse_plastique if 'masse_plastique' in st.session_state else 0) * 35,
        "Consommation (Séchage)": -res["Énergie Evap (MJ)"]
    }
    st.bar_chart(pd.Series(data_energy))

# Section Explicative
with st.expander("ℹ️ Comment simuler différents fabricants ?"):
    st.markdown("""
    * **Pour simuler ANKUR (Modèle Cox's Bazar) :**
        * Activez "Ajout Déchets Solides".
        * Mettez Plastique = 500 kg.
        * Pré-traitement = "Séchage Solaire + Mécanique".
    * **Pour simuler JANICKI / SEDRON (Omni Processor standard) :**
        * Désactivez "Ajout Déchets Solides" (ou mettez des valeurs faibles).
        * Pré-traitement = "Presse à Vis (Standard)" ou "Séchage Thermique".
        * L'OP compte souvent sur un séchage thermique interne très performant.
    * **Pour simuler un PYROLYSEUR simple :**
        * Il faut une boue très sèche. Choisissez "Séchage Solaire" avec une cible à 20-30% d'humidité.
    """)
