import streamlit as st
import pandas as pd

# --- 0. CONFIGURATION ET STYLE ---
st.set_page_config(
    page_title="OP Architect V3",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS pour améliorer l'affichage sur mobile (centrage des titres, padding)
st.markdown("""
<style>
    .main > div {padding-top: 2rem;}
    .stTabs [data-baseweb="tab-list"] {gap: 2px;}
    .stTabs [data-baseweb="tab"] {height: 50px; white-space: pre-wrap;}
</style>
""", unsafe_allow_html=True)

# --- 1. GUIDE UTILISATEUR (Visible sur mobile et desktop) ---
with st.expander("ℹ️ **GUIDE DE DÉMARRAGE : Comment utiliser cet outil ?**", expanded=True):
    st.markdown("""
    1. **Ouvrez le menu à gauche** (sur mobile, cliquez sur la flèche `>`).
    2. **Remplissez les sections** dans l'ordre : Qualité des boues, Infrastructure, puis Finance.
    3. **L'outil calcule automatiquement** la meilleure solution entre :
       * *Ankur* (Énergie), *SSP/Thesvores* (Matériaux), ou *Incinérateur* (Traitement de masse).
    4. **Naviguez dans les onglets ci-dessous** pour voir les résultats financiers et techniques.
    """)

# --- 2. SIDEBAR: INPUTS (AVEC AIDES EXPLICITES) ---
with st.sidebar:
    st.title("🎛️ Paramètres du Projet")
    st.info("👈 Commencez par régler ces curseurs pour définir votre scénario.")

    # --- SECTION A: QUALITÉ ---
    st.header("1. Caractérisation de la Boue")
    
    type_boue = st.selectbox(
        "Quel type de boue ?", 
        ["Boues de Vidange (Domestique)", "Boues Activées (STEP)", "Boues Industrielles"],
        help="Le type de boue influence le pouvoir calorifique et le choix de l'incinérateur."
    )

    ts_percent = st.slider(
        "Taux de Siccité (TS) %", 
        min_value=1.0, max_value=90.0, value=5.0, step=0.5,
        help="C'est la concentration en matière solide.\n- 1-5% : Boue liquide (camion hydrocureur)\n- 20-30% : Boue pâteuse (sortie de filtre)\n- 80%+ : Boue séchée"
    )
    
    heavy_metals = st.toggle(
        "Présence de Métaux Lourds ?", 
        value=False,
        help="Activez ceci si des industries rejettent dans le réseau. Cela bloque certaines valorisations (briques SSP)."
    )

    vol_boue = st.number_input(
        "Volume à traiter (m³/jour)", 
        value=40.0, step=5.0,
        help="Volume total entrant dans l'usine chaque jour."
    )

    st.write("---")

    # --- SECTION B: LOGISTIQUE (CŒUR DE LA LOGIQUE) ---
    st.header("2. Infrastructure & Logistique")
    
    mode_collecte = st.radio(
        "Comment les boues arrivent-elles ?", 
        ["Camions / Apport Volontaire", "Réseau d'Égout (Direct)"],
        help="Si 'Réseau', la boue arrive en continu. Si 'Camions', elle arrive par lots."
    )
    
    has_station = st.radio(
        "Y a-t-il DÉJÀ une station de traitement ?",
        ["Non (Terrain nu)", "Oui (Station existante)"],
        help="Si 'Oui', nous proposons des modules complémentaires (Ankur Basique). Si 'Non', nous proposons une solution complète (Ankur Intégré)."
    )
    is_station_existante = True if has_station == "Oui (Station existante)" else False

    st.write("---")

    # --- SECTION C: OPTIONNEL ---
    with st.expander("3. Ajout de Déchets (Optionnel)"):
        ajout_msw = st.checkbox("Co-traiter des ordures ménagères ?", value=False)
        if ajout_msw:
            masse_msw = st.number_input("Masse Déchets (kg/jour)", value=2000.0)
            hum_msw = st.slider("Humidité Déchets (%)", 0, 60, 20)
            lhv_msw = st.number_input("PCI Déchets (MJ/kg)", value=18.0)
        else:
            masse_msw = 0; hum_msw = 0; lhv_msw = 0

    with st.expander("4. Données Financières"):
        prix_elec = st.number_input("Prix de vente Élec ($/kWh)", value=0.15)
        capex_manual = st.number_input("Budget Max ($ - laisser 0 si inconnu)", value=0)

# --- 3. MOTEUR DE CALCUL ---

def run_simulation():
    # 1. Bilan Massique
    masse_boue = vol_boue * 1000
    ms_boue = masse_boue * (ts_percent / 100.0)
    eau_boue = masse_boue - ms_boue
    
    ms_msw = masse_msw * (1 - hum_msw/100)
    eau_msw = masse_msw - ms_msw
    
    total_dry = ms_boue + ms_msw
    total_water = eau_boue + eau_msw
    
    # 2. Bilan Énergie
    energy_in = (ms_boue * 12.0) + (ms_msw * lhv_msw)
    energy_evap = total_water * 3.2 
    energy_net = energy_in - energy_evap
    
    # 3. Logique de Sélection
    logic_msg = ""
    
    # Définition des candidats
    opt_ankur_complet = {"Tech": "ANKUR COMPLET (Intégré)", "Score": 0, "Desc": "Remplace une STEP (Délai 6-7 mois). Traite l'eau et la boue."}
    opt_ankur_basic = {"Tech": "ANKUR BASIQUE", "Score": 0, "Desc": "Module Énergie seul. Nécessite des boues déjà déshydratées."}
    opt_ssp = {"Tech": "THESVORES (SSP)", "Score": 0, "Desc": "Valorisation en matériaux/briques. Simple et robuste."}
    opt_incin = {"Tech": "INCINÉRATEUR (Omni Processor)", "Score": 0, "Desc": "Haute technologie pour grands volumes ou boues activées."}

    # ARBRE DE DÉCISION
    
    # CAS 1 : RÉSEAU
    if mode_collecte == "Réseau d'Égout (Direct)":
        if is_station_existante and type_boue == "Boues Activées (STEP)":
            logic_msg = "Réseau + Station (Boues Activées) ➔ Incinérateur recommandé."
            opt_incin["Score"] = 95
            opt_ankur_basic["Score"] = 60 # Possible si séchage solaire existant
        else:
            logic_msg = "Réseau standard ➔ Incinérateur préféré."
            opt_incin["Score"] = 80
            opt_ankur_complet["Score"] = 50

    # CAS 2 : CAMIONS (VIDANGEURS)
    else: 
        if is_station_existante:
            logic_msg = "Camions + Station Existante ➔ Complément (Ankur Basique ou SSP)."
            opt_ankur_basic["Score"] = 90
            opt_ssp["Score"] = 85
            opt_ankur_complet["Score"] = 20 # Inutile de refaire une station
        else:
            logic_msg = "Camions + Terrain Nu ➔ Solution 'Clé en main' requise (Ankur Complet)."
            opt_ankur_complet["Score"] = 95
            opt_incin["Score"] = 60
            opt_ankur_basic["Score"] = 0 # Impossible sans infra
            opt_ssp["Score"] = 20 # Trop complexe à gérer seul sans eau traitée

    # CONTRAINTE MÉTAUX LOURDS
    if heavy_metals:
        opt_ssp["Score"] = 0 # INTERDIT : On ne fait pas de briques avec des métaux
        opt_ssp["Desc"] += " ⛔ REJETÉ (MÉTAUX)"
        logic_msg += " | ⚠️ SSP Disqualifié (Métaux)."

    # TRI
    recos = [opt_ankur_complet, opt_ankur_basic, opt_ssp, opt_incin]
    recos.sort(key=lambda x: x["Score"], reverse=True)
    best = recos[0]

    # 4. Estimation Financière (Modelisation simplifiée)
    capex = capex_manual if capex_manual > 0 else 0
    if capex == 0:
        if best["Tech"] == "ANKUR COMPLET (Intégré)": capex = 900000 + (vol_boue * 6500)
        elif best["Tech"] == "ANKUR BASIQUE": capex = 450000 + (vol_boue * 4000)
        elif "INCINÉRATEUR" in best["Tech"]: capex = 2500000 + (vol_boue * 12000)
        else: capex = 300000 + (vol_boue * 3000) # SSP

    elec_prod = max(0, (energy_net / 3.6) * 0.25) if "ANKUR" in best["Tech"] or "INCINÉRATEUR" in best["Tech"] else 0
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

# --- 4. INTERFACE RÉSULTATS (TABS) ---

try:
    data = run_simulation()
    best = data["Best"]
    fin = data["Finances"]

    st.markdown(f"### 🎯 Recommandation : **{best['Tech']}**")
    st.caption(f"Motif : {data['Logique']}")

    # Utilisation des TABS pour une meilleure expérience mobile
    tab1, tab2, tab3 = st.tabs(["📊 Vue d'ensemble", "💰 Analyse Financière", "⚙️ Détails Techniques"])

    with tab1:
        st.success(f"**Solution Retenue : {best['Tech']}**")
        st.info(f"ℹ️ {best['Desc']}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Score de Pertinence", f"{best['Score']}/100")
        with col2:
            if "ANKUR" in best['Tech']:
                st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Biomass_gasification_plant.jpg/320px-Biomass_gasification_plant.jpg", caption="Concept Ankur (Illustration)")
            elif "SSP" in best['Tech']:
                st.markdown("🧱 **Sortie :** Matériaux de construction (Pavés/Briques)")

        st.warning("Vérifiez les onglets 'Finance' et 'Technique' pour les détails.")

    with tab2:
        st.header("Rentabilité Estimée")
        c1, c2, c3 = st.columns(3)
        c1.metric("Investissement (CAPEX)", f"${int(fin['CAPEX']):,}")
        c2.metric("Coûts Ops (jour)", f"${int(fin['OPEX'])}")
        c3.metric("Profit Net (jour)", f"${int(fin['Profit'])}", delta_color="normal" if fin['Profit']>0 else "inverse")
        
        st.bar_chart(pd.DataFrame({
            "Type": ["Revenus Élec.", "Dépenses Ops."],
            "Montant ($)": [fin['Income'], fin['OPEX']]
        }).set_index("Type"))

    with tab3:
        st.header("Comparatif Technique")
        df = pd.DataFrame(data["Recos"])
        st.dataframe(df[["Tech", "Score", "Desc"]], hide_index=True, use_container_width=True)
        
        st.subheader("Bilan Matière")
        st.write(f"- Matière Sèche (Combustible/Matériau) : **{int(data['Masse']['Sec'])} kg/jour**")
        st.write(f"- Eau à traiter/évaporer : **{int(data['Masse']['Eau'])} Litres/jour**")
        
        if heavy_metals:
            st.error("🚨 ALERTE : Métaux lourds détectés. La solution SSP a été bloquée par sécurité.")

except Exception as e:
    st.error(f"Erreur : {e}")
