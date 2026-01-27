import streamlit as st
import pandas as pd

# --- CONFIGURATION ---
st.set_page_config(page_title="Universal OP Architect", layout="wide")

st.title("🏭 OP Architect : L'Outil de Décision Universel")
st.markdown("""
**Plateforme de dimensionnement et de choix technologique pour la valorisation des boues.**
Intègre les logiques industrielles : *Zero Liquid Discharge (ZLD)*, *Waste-to-Energy*, et *Waste-to-Material*.
*Basé sur les standards SSSP, Ankur et Janicki/Sedron.*
""")

# --- 1. BARRE LATÉRALE : LE GISEMENT ---
with st.sidebar:
    st.header("1. Dimensionnement (Gisement)")
    
    # VOLUME (Le facteur décisif selon le Survey Report)
    vol_boue = st.number_input("Volume Journalier (m3/jour)", value=40.0, step=5.0)
    
    # TYPE DE BOUE
    type_boue = st.selectbox("Nature de la Boue", 
                             ["Boue de Vidange (FSM)", "Boue Industrielle / Toxique", "Boue de STEP (Activée)"])
    
    # CONSISTANCE
    st.write("---")
    mode_apport = st.radio("Logistique d'Entrée", ["Liquide (Camion Direct)", "Pâteuse/Solide (Déjà séchée)"])
    
    if mode_apport == "Liquide (Camion Direct)":
        ts_boue = st.slider("Taux de Solides (TS %)", 0.5, 10.0, 2.5, help="Boue liquide brute.")
    else:
        ts_boue = st.slider("Taux de Solides (TS %)", 15.0, 90.0, 30.0, help="Boue sortie de lits de séchage.")

    # CO-SUBSTRATS
    st.header("2. Co-Substrats")
    ajout_msw = st.checkbox("Ajout Déchets Ménagers ?", value=False)
    if ajout_msw:
        masse_msw = st.number_input("Masse Déchets (kg/jour)", value=2000.0)
    else:
        masse_msw = 0

    st.header("3. Objectifs Stratégiques")
    cible = st.radio("Priorité du Projet", ["Rentabilité Énergétique (Élec)", "Zéro Rejet Liquide (ZLD)", "Matériaux (Pavés/Briques)"])

# --- 2. MOTEUR D'INTELLIGENCE (Règles du Survey Report) ---

def analyser_scenarios():
    recos = []
    
    # MASSE SÈCHE TOTALE (Le vrai juge de paix)
    ms_boue = (vol_boue * 1000) * (ts_boue/100)
    ms_msw = masse_msw * 0.7 # Hypothèse 30% eau
    ms_totale = ms_boue + ms_msw
    
    # --- RÈGLE 1 : L'ÉCHELLE (SCALE) ---
    if vol_boue < 30:
        segment = "PETIT VOLUME (<30m3)"
        tech_base = "Pyrolyse / Ankur Small"
        desc = "Solutions compactes. La valorisation énergétique est difficile. Priorité au traitement sanitaire."
    elif 30 <= vol_boue < 90:
        segment = "VOLUME MOYEN (30-90m3)"
        tech_base = "Modulaire / SSSP"
        desc = "Zone idéale pour les solutions modulaires type SSSP. Valorisation mixte (Énergie ou Matériaux)."
    else:
        segment = "GRAND VOLUME (>90m3)"
        tech_base = "Incinération / Janicki Large"
        desc = "Économies d'échelle possibles. Production massive d'électricité ou d'eau distillée."

    # --- RÈGLE 2 : LA TECHNOLOGIE ---
    
    # SCÉNARIO A : SSSP (THESVORES) - ZLD & Matériaux
    # Fort si : Boue Industrielle OU Cible = Matériaux OU Cible = ZLD
    score_sssp = 5
    if type_boue == "Boue Industrielle / Toxique": score_sssp += 5 # Bloque les métaux
    if cible == "Matériaux (Pavés/Briques)": score_sssp += 5
    if cible == "Zéro Rejet Liquide (ZLD)": score_sssp += 3
    if 30 <= vol_boue < 100: score_sssp += 2 # Sweet spot SSSP
    
    recos.append({
        "Tech": "SSSP (Technologie THESVORES)",
        "Type": "Séchage Turbo + Vitrification",
        "Score": score_sssp,
        "Avantage": "🛡️ Zéro Rejet Liquide (ZLD) + Pavés Autobloquants. Idéal pour boues toxiques.",
        "Produit": "Pavés / Briques",
        "Rejet Liquide": "NON (Recyclé interne)"
    })

    # SCÉNARIO B : ANKUR / PYROLYSE - Mixte
    # Fort si : Petit volume ET Ajout MSW (pour chauffer)
    score_ankur = 5
    if ajout_msw: score_ankur += 4 # Ankur aime le mélange
    if mode_apport == "Liquide (Camion Direct)": score_ankur += 3 # Gère bien le liquide via presse
    if vol_boue < 50: score_ankur += 2
    
    recos.append({
        "Tech": "ANKUR SCIENTIFIC (Modèle Cox's Bazar)",
        "Type": "Presse à Vis + Pyrolyse Hybride",
        "Score": score_ankur,
        "Avantage": "🔥 Robuste pour les entrants liquides grâce au co-traitement déchets.",
        "Produit": "Électricité + Cendres",
        "Rejet Liquide": "OUI (Filtrat de presse)"
    })

    # SCÉNARIO C : JANICKI / SEDRON - High Tech
    # Fort si : Grand volume ET Besoin Eau
    score_op = 5
    if vol_boue > 80: score_op += 5
    if ts_boue > 20: score_op += 3 # Préfère la boue sèche
    if cible == "Zéro Rejet Liquide (ZLD)": score_op += 2 # Peut le faire par évaporation totale
    
    recos.append({
        "Tech": "JANICKI / SEDRON (Omni Processor)",
        "Type": "Combustion Vapeur / Incinération",
        "Score": score_op,
        "Avantage": "💧 Production massive d'eau distillée. Standard industriel.",
        "Produit": "Eau Distillée + Élec",
        "Rejet Liquide": "NON (Si évaporation totale)"
    })

    recos.sort(key=lambda x: x["Score"], reverse=True)
    return segment, desc, recos, ms_totale

# --- 3. AFFICHAGE DASHBOARD ---

segment, desc, recos, ms_totale_jour = analyser_scenarios()
best = recos[0]

# BANNIÈRE DE RÉSULTAT
st.header(f"🎯 Diagnostic : {segment}")
st.info(desc)

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Meilleure Option")
    st.success(f"🏆 **{best['Tech']}**")
    st.metric("Score de Pertinence", f"{best['Score']}/15")
    st.write(f"**Pourquoi ?** {best['Avantage']}")
    st.write(f"**Sortie Principale :** {best['Produit']}")
    
    if best['Rejet Liquide'] == "NON (Recyclé interne)":
        st.badge("ZLD - Zéro Rejet Liquide")

with col2:
    st.subheader("Comparatif Stratégique")
    df_reco = pd.DataFrame(recos)
    st.dataframe(df_reco[["Tech", "Avantage", "Produit", "Rejet Liquide"]], hide_index=True)

st.markdown("---")

# SIMULATION ÉCONOMIQUE (Basée sur le choix optimal)
st.subheader(f"📊 Simulation Préliminaire ({best['Tech']})")

c1, c2, c3 = st.columns(3)

# 1. Bilan Matière
c1.metric("Masse Sèche à Traiter", f"{int(ms_totale_jour)} kg/jour")

# 2. Production (Selon la techno)
if "SSSP" in best['Tech']:
    # Modèle Matériaux (15% de cendres -> Pavés)
    nb_paves = (ms_totale_jour * 0.15) * 2 # Ratio approx
    c2.metric("Production Pavés", f"~{int(nb_paves)} unités/jour")
    c3.metric("Revenu Est.", f"{int(nb_paves * 0.5)} $/jour", help="Base 0.5$ le pavé")
    
elif "JANICKI" in best['Tech']:
    # Modèle Eau + Élec
    eau_prod = (vol_boue*1000) * 0.8
    c2.metric("Eau Distillée", f"~{int(eau_prod)} L/jour")
    c3.metric("Revenu Est.", f"{int(eau_prod * 0.01)} $/jour", help="Vente eau uniquement")

else: # ANKUR
    # Modèle Élec
    kwh_prod = (ms_totale_jour * 12 / 3.6) * 0.10 # Rendement global faible
    c2.metric("Électricité Nette", f"~{int(kwh_prod)} kWh/jour")
    c3.metric("Revenu Est.", f"{int(kwh_prod * 0.15)} $/jour")

# SECTION ÉDUCATIVE (Survey Report)
with st.expander("📚 Comprendre la Classification (Source : Technical Survey Report)"):
    st.markdown("""
    * **Petits Volumes (<30m3)** : La technologie dominante est la pyrolyse simplifiée. L'objectif est sanitaire avant d'être énergétique.
    * **Volumes Moyens (30-90m3)** : C'est le domaine des solutions modulaires comme **SSSP**. Elles permettent une flexibilité (ajout de modules si la ville grandit).
    * **Grands Volumes (>90m3)** : On entre dans le domaine de l'infrastructure lourde (Incinération). Rentable uniquement si le flux est constant.
    * **Concept ZLD (Zero Liquid Discharge)** : Crucial pour SSSP. Toute l'eau extraite des boues est traitée et réutilisée dans l'usine (refroidissement, lavage), aucun tuyau ne sort vers la rivière.
    """)
