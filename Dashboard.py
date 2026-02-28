# dashboard_uranium_iran.py (corrigé)
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time
import json
import warnings
import requests
from io import BytesIO
warnings.filterwarnings('ignore')

# Configuration de la page
st.set_page_config(
    page_title="Dashboard Nucléaire Iranien - Enrichissement d'Uranium",
    page_icon="☢️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS personnalisé
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;700&display=swap');
    
    .main-header {
        font-size: 2.5rem;
        color: #DA0000;
        text-align: center;
        margin-bottom: 1rem;
        font-family: 'Roboto', sans-serif;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
        background: linear-gradient(135deg, #239F40 0%, #FFFFFF 50%, #DA0000 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .persian-header {
        font-family: 'Roboto', sans-serif;
        font-size: 1.5rem;
        direction: rtl;
        text-align: center;
        color: #333;
        margin-bottom: 1rem;
    }
    
    .metric-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1.5rem;
        border-radius: 1rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        border-left: 5px solid #DA0000;
        transition: transform 0.3s;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.15);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: bold;
        color: #DA0000;
    }
    
    .metric-label {
        font-size: 1rem;
        color: #666;
        margin-top: 0.5rem;
    }
    
    .critical-badge {
        background-color: #DA0000;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        font-weight: bold;
        display: inline-block;
        margin: 0.2rem;
        animation: pulse 2s infinite;
    }
    
    .warning-badge {
        background-color: #FFA500;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        font-weight: bold;
        display: inline-block;
        margin: 0.2rem;
    }
    
    .safe-badge {
        background-color: #239F40;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        font-weight: bold;
        display: inline-block;
        margin: 0.2rem;
    }
    
    .iaea-badge {
        background-color: #2196f3;
        color: white;
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        font-weight: bold;
        display: inline-block;
        margin: 0.2rem;
    }
    
    .info-box {
        background-color: #e3f2fd;
        border-left: 4px solid #2196f3;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    
    .warning-box {
        background-color: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    
    .critical-box {
        background-color: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.8; }
        100% { opacity: 1; }
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #f8f9fa;
        border-radius: 4px 4px 0 0;
        padding: 10px 20px;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #DA0000 !important;
        color: white !important;
    }
    
    .uranium-positive {
        color: #DA0000;
        font-weight: bold;
    }
    
    .uranium-negative {
        color: #239F40;
        font-weight: bold;
    }
    
    .facility-card {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialisation des variables de session
if 'selected_facility' not in st.session_state:
    st.session_state.selected_facility = "Isfahan"

if 'show_weapons_grade' not in st.session_state:
    st.session_state.show_weapons_grade = True

if 'comparison_mode' not in st.session_state:
    st.session_state.comparison_mode = False

# Données actualisées de l'AIEA (février 2026) 
LATEST_IAEA_DATA = {
    "report_date": "2026-02-27",
    "uranium_60_percent": 440.9,  # kg 
    "uranium_total": 9247.6,  # kg 
    "weapons_potential": 10,  # nombre de bombes potentielles 
    "facilities": {
        "Isfahan": {
            "name": "Complexe nucléaire d'Ispahan (ENTC)",
            "status": "Actif - Stockage d'uranium hautement enrichi",
            "enrichment_levels": ["20%", "60%"],
            "storage_tunnel": "Complexe souterrain",
            "iaea_access": "Non autorisé depuis juin 2025",
            "last_inspection": "2025-06-10",
            "vehicle_activity": "Élevée - Observations satellite récentes ",
            "bombed": "Oui - Frappes israélo-américaines juin 2025",
            "damage": "Limité - Installations souterraines préservées ",
            "fourth_facility": "Nouvelle installation non localisée par l'AIEA ",
            "coordinates": {"lat": 32.65, "lon": 51.68}
        },
        "Natanz": {
            "name": "Site d'enrichissement de Natanz",
            "status": "Activité observée sans vérification possible ",
            "enrichment_levels": ["Jusqu'à 60%"],
            "pilot_plant": "PFEP - Installation pilote",
            "iaea_access": "Non autorisé",
            "last_inspection": "2025-06-09",
            "observations": "Panneaux installés sur cage anti-drone ",
            "bombed": "Oui - Sévèrement endommagé ",
            "coordinates": {"lat": 33.72, "lon": 51.72}
        },
        "Fordow": {
            "name": "Site de Fordow (souterrain)",
            "status": "Activité observée sans vérification ",
            "enrichment_levels": ["Jusqu'à 60%"],
            "facility_type": "Installation souterraine fortifiée",
            "iaea_access": "Non autorisé",
            "last_inspection": "2025-06-08",
            "bombed": "Oui",
            "coordinates": {"lat": 34.88, "lon": 50.99}
        },
        "Arak": {
            "name": "Réacteur à eau lourde d'Arak",
            "status": "Fonctionnement limité",
            "enrichment_levels": ["Non enrichi"],
            "reactor_type": "IR-40 (reconfiguré)",
            "iaea_access": "Partiel",
            "last_inspection": "2025-12-15",
            "bombed": "Non directement",
            "coordinates": {"lat": 34.37, "lon": 49.24}
        },
        "Bushehr": {
            "name": "Centrale nucléaire de Bushehr",
            "status": "Opérationnel - Production électrique",
            "enrichment_levels": ["Non enrichi"],
            "reactor_type": "VVER-1000",
            "iaea_access": "Autorisé",
            "last_inspection": "2026-01-20",
            "bombed": "Non",
            "coordinates": {"lat": 28.83, "lon": 50.89}
        }
    },
    "timeline_events": [
        {"date": "2015-07-14", "event": "Signature du JCPOA", "type": "accord"},
        {"date": "2018-05-08", "event": "Retrait des États-Unis du JCPOA", "type": "crise"},
        {"date": "2019-07-01", "event": "Dépassement du seuil d'enrichissement 3.67%", "type": "escalade"},
        {"date": "2021-04-01", "event": "Début enrichissement à 60%", "type": "escalade"},
        {"date": "2023-09-01", "event": "Stock dépasse 4,500 kg d'uranium enrichi", "type": "seuil"},
        {"date": "2025-06-01", "event": "Iran déclare 4ème installation à Ispahan", "type": "nouvelle"},
        {"date": "2025-06-15", "event": "Frappes israéliennes sur sites nucléaires", "type": "attaque"},
        {"date": "2025-06-20", "event": "États-Unis rejoignent les frappes - Guerre de 12 jours", "type": "attaque"},
        {"date": "2025-06-25", "event": "Fin des frappes - Destruction partielle des sites", "type": "attaque"},
        {"date": "2025-07-01", "event": "Iran suspend coopération avec AIEA", "type": "crise"},
        {"date": "2026-02-27", "event": "Rapport AIEA - 440.9 kg à 60% non vérifiables", "type": "rapport"}
    ],
    "enrichment_history": [
        {"date": "2015-07-01", "level": 3.67, "stock": 0},
        {"date": "2018-05-01", "level": 3.67, "stock": 0},
        {"date": "2019-07-01", "level": 4.5, "stock": 200},
        {"date": "2020-01-01", "level": 4.5, "stock": 500},
        {"date": "2021-01-01", "level": 20, "stock": 1000},
        {"date": "2021-04-01", "level": 60, "stock": 1200},
        {"date": "2022-01-01", "level": 60, "stock": 2000},
        {"date": "2023-01-01", "level": 60, "stock": 3500},
        {"date": "2024-01-01", "level": 60, "stock": 5000},
        {"date": "2025-01-01", "level": 60, "stock": 7500},
        {"date": "2025-06-01", "level": 60, "stock": 9247.6},
        {"date": "2026-02-01", "level": 60, "stock": 9247.6}
    ],
    "thresholds": {
        "weapons_grade": 90,  # %
        "significant_quantity": 42,  # kg à 60% pour une bombe 
        "jcpoa_limit": 3.67,  # %
        "breakout_time": 15  # jours estimés
    }
}

# Correction: Calcul du nombre de mois entre 2023-01-01 et 2026-02-01
date_range = pd.date_range(start="2023-01-01", end="2026-02-01", freq="M")
n_months = len(date_range)  # Devrait être 38 mois

# Historique des inspections AIEA - CORRIGÉ avec longueurs égales
INSPECTION_HISTORY = pd.DataFrame({
    "date": date_range,
    "inspections_conducted": [12, 10, 8, 9, 7, 5, 4, 3, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0][:n_months],
    "access_level": [100, 95, 90, 85, 80, 75, 70, 60, 50, 40, 30, 20, 10, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5][:n_months],
    "stock_60pct": [87.5, 95.2, 103.8, 114.5, 126.3, 140.1, 155.2, 170.5, 188.3, 208.1, 230.4, 255.2, 283.7, 315.8, 350.2, 388.5, 408.6, 440.9, 440.9, 440.9, 440.9, 440.9, 440.9, 440.9, 440.9, 440.9, 440.9, 440.9, 440.9, 440.9, 440.9, 440.9, 440.9, 440.9, 440.9, 440.9, 440.9, 440.9][:n_months],
})

# Négociations internationales
NEGOTIATIONS_DATA = [
    {"date": "2026-02-26", "location": "Genève", "parties": ["États-Unis", "Iran", "Oman"], "outcome": "Aucune percée "},
    {"date": "2026-02-19", "location": "Genève", "parties": ["États-Unis", "Iran", "Oman"], "outcome": "Discussions techniques"},
    {"date": "2026-02-12", "location": "Genève", "parties": ["États-Unis", "Iran", "Oman"], "outcome": "Premier round indirect"},
    {"date": "2026-02-27", "location": "Washington", "parties": ["États-Unis", "Oman"], "outcome": "Rencontre Vance-Busaidi "},
    {"date": "2026-03-02", "location": "Vienne", "parties": ["Iran", "AIEA"], "outcome": "Réunion programmée "},
]

# Déclarations officielles
OFFICIAL_STATEMENTS = [
    {"date": "2026-02-27", "source": "IAEA", "statement": "L'AIEA ne peut vérifier si l'Iran a suspendu toutes les activités d'enrichissement "},
    {"date": "2026-02-27", "source": "Vice-président JD Vance", "statement": "Preuves que l'Iran tente de reconstruire son programme d'armes nucléaires "},
    {"date": "2026-02-27", "source": "Oman FM Badr al Busaidi", "statement": "L'Iran a accepté de diluer son uranium enrichi au niveau le plus bas possible "},
    {"date": "2026-02-25", "source": "Marco Rubio", "statement": "L'Iran n'enrichit pas actuellement mais cherche à pouvoir le faire "},
    {"date": "2026-02-23", "source": "Abbas Araghchi", "statement": "Les armes nucléaires sont inacceptables pour l'Iran "},
]

# Fonctions utilitaires
def format_uranium_kg(value, include_bombs=True):
    """Formate une quantité d'uranium en kg avec équivalent bombes"""
    if value is None or value == 0:
        return "N/A"
    
    if value >= 1000:
        result = f"{value/1000:.2f} tonnes"
    else:
        result = f"{value:.1f} kg"
    
    if include_bombs and value > 0:
        bombs = value / LATEST_IAEA_DATA["thresholds"]["significant_quantity"]
        bombs_possible = value / 42  # 42 kg à 60% = 1 bombe potentielle 
        result += f" (≈ {bombs_possible:.1f} bombes potentielles)"
    
    return result

def get_threat_level(percentage):
    """Détermine le niveau de menace basé sur le pourcentage d'enrichissement"""
    if percentage >= 90:
        return "CRITIQUE", "🔴"
    elif percentage >= 60:
        return "ÉLEVÉ", "🟠"
    elif percentage >= 20:
        return "MODÉRÉ", "🟡"
    else:
        return "FAIBLE", "🟢"

def get_facility_status_color(status):
    """Retourne une couleur basée sur le statut d'accès"""
    if "non autorisé" in status.lower() or "Non" in status:
        return "#DA0000"
    elif "partiel" in status.lower():
        return "#FFA500"
    else:
        return "#239F40"

# Sidebar
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/c/ca/Flag_of_Iran.svg", width=100)
    st.markdown("<h2 style='text-align: center;'>☢️ Dashboard Nucléaire</h2>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Menu principal
    menu = st.radio(
        "Navigation",
        ["📊 Tableau de bord principal",
         "🏭 Sites nucléaires",
         "📈 Évolution de l'enrichissement",
         "🌍 Négociations & Diplomatie",
         "📰 Actualités & Déclarations",
         "⚖️ Seuils & Scénarios"]
    )
    
    st.markdown("---")
    
    # Dernier rapport AIEA
    st.markdown("### 📋 Dernier rapport AIEA")
    st.info(f"**Date:** {LATEST_IAEA_DATA['report_date']}\n\n"
            f"**Uranium 60%:** {LATEST_IAEA_DATA['uranium_60_percent']} kg\n\n"
            f"**Bombes potentielles:** {LATEST_IAEA_DATA['weapons_potential']}\n\n"
            f"**Accès aux sites:** Non autorisé ")
    
    st.markdown("---")
    
    # Options d'affichage
    st.markdown("### ⚙️ Options")
    st.session_state.show_weapons_grade = st.checkbox(
        "Afficher seuil militaire (90%)",
        value=st.session_state.show_weapons_grade
    )
    
    # Sélection du site
    facilities_list = list(LATEST_IAEA_DATA["facilities"].keys())
    selected_facility = st.selectbox(
        "Site nucléaire à surveiller",
        options=facilities_list,
        index=0
    )
    st.session_state.selected_facility = selected_facility
    
    st.markdown("---")
    st.caption("Données AIEA - Mise à jour: 28 février 2026 ")
    st.caption("Sources: IAEA, ISW, Al Jazeera, Reuters")

# Main content
st.markdown("<h1 class='main-header'>☢️ Programme d'Enrichissement d'Uranium de l'Iran</h1>", unsafe_allow_html=True)
st.markdown("<p class='persian-header'>برنامه غنی‌سازی اورانیوم ایران</p>", unsafe_allow_html=True)

# Badges contextuels
col_badges1, col_badges2, col_badges3, col_badges4, col_badges5 = st.columns(5)
with col_badges1:
    threat_level, threat_icon = get_threat_level(60)
    st.markdown(f"<span class='critical-badge'>{threat_icon} Niveau: {threat_level}</span>", unsafe_allow_html=True)
with col_badges2:
    st.markdown("<span class='warning-badge'>⚠️ 60% Enrichissement</span>", unsafe_allow_html=True)
with col_badges3:
    st.markdown("<span class='iaea-badge'>📋 AIEA: Accès limité</span>", unsafe_allow_html=True)
with col_badges4:
    st.markdown("<span class='critical-badge'>💣 10 bombes potentielles</span>", unsafe_allow_html=True)
with col_badges5:
    st.markdown("<span class='warning-badge'>🕒 Breakout: 15 jours</span>", unsafe_allow_html=True)

# Alerte critique
st.markdown("""
<div class='critical-box'>
    <b>🚨 ALERTE CRITIQUE - FÉVRIER 2026</b><br>
    L'AIEA ne peut pas vérifier la localisation, la taille ou la composition du stock d'uranium enrichi iranien.
    Des activités régulières de véhicules sont observées autour du complexe souterrain d'Ispahan où était stocké 
    l'uranium à 60% .
</div>
""", unsafe_allow_html=True)

# KPIs principaux
st.markdown("### 📊 Indicateurs Clés")

col_kpi1, col_kpi2, col_kpi3, col_kpi4, col_kpi5 = st.columns(5)

with col_kpi1:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-value'>{LATEST_IAEA_DATA['uranium_60_percent']} kg</div>", unsafe_allow_html=True)
    st.markdown("<div class='metric-label'>Uranium enrichi à 60%</div>", unsafe_allow_html=True)
    st.caption("Stock pré-attaque juin 2025 ")
    st.markdown("</div>", unsafe_allow_html=True)

with col_kpi2:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-value'>{LATEST_IAEA_DATA['uranium_total']:.0f} kg</div>", unsafe_allow_html=True)
    st.markdown("<div class='metric-label'>Uranium enrichi total</div>", unsafe_allow_html=True)
    st.caption("45x limite JCPOA ")
    st.markdown("</div>", unsafe_allow_html=True)

with col_kpi3:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-value'>{LATEST_IAEA_DATA['weapons_potential']}</div>", unsafe_allow_html=True)
    st.markdown("<div class='metric-label'>Bombes potentielles</div>", unsafe_allow_html=True)
    st.caption("Selon yardstick AIEA ")
    st.markdown("</div>", unsafe_allow_html=True)

with col_kpi4:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-value'>{LATEST_IAEA_DATA['thresholds']['breakout_time']} jours</div>", unsafe_allow_html=True)
    st.markdown("<div class='metric-label'>Temps de breakout</div>", unsafe_allow_html=True)
    st.caption("Estimation pour arme")
    st.markdown("</div>", unsafe_allow_html=True)

with col_kpi5:
    days_since_last = (datetime.now() - datetime(2025, 6, 10)).days
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-value'>{days_since_last} jours</div>", unsafe_allow_html=True)
    st.markdown("<div class='metric-label'>Sans inspection AIEA</div>", unsafe_allow_html=True)
    st.caption("Dernier accès: 10 juin 2025")
    st.markdown("</div>", unsafe_allow_html=True)

# Menu principal
if menu == "📊 Tableau de bord principal":
    st.markdown("## 📈 Évolution du programme nucléaire iranien")
    
    # Graphique d'évolution de l'enrichissement
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=("Évolution du stock d'uranium enrichi", 
                        "Niveaux d'enrichissement",
                        "Accès AIEA aux sites",
                        "Inspections réalisées"),
        specs=[[{"secondary_y": True}, {"type": "domain"}],
               [{"type": "scatter"}, {"type": "bar"}]]
    )
    
    # Graphique 1: Évolution du stock
    df_hist = pd.DataFrame(LATEST_IAEA_DATA["enrichment_history"])
    df_hist['date'] = pd.to_datetime(df_hist['date'])
    
    fig.add_trace(
        go.Scatter(x=df_hist['date'], y=df_hist['stock'],
                  name="Stock total (kg)", line=dict(color='#DA0000', width=3),
                  fill='tozeroy'),
        row=1, col=1
    )
    
    fig.add_trace(
        go.Scatter(x=df_hist['date'], y=df_hist['level'],
                  name="Niveau enrichissement (%)", line=dict(color='#FFA500', width=2, dash='dash'),
                  yaxis="y2"),
        row=1, col=1, secondary_y=True
    )
    
    # Seuils
    if st.session_state.show_weapons_grade:
        fig.add_hline(y=90, line_dash="dash", line_color="#DA0000",
                     annotation_text="Seuil militaire (90%)", row=1, col=1)
    
    fig.add_hline(y=60, line_dash="dash", line_color="#FFA500",
                 annotation_text="Niveau actuel (60%)", row=1, col=1)
    fig.add_hline(y=3.67, line_dash="dash", line_color="#239F40",
                 annotation_text="Limite JCPOA", row=1, col=1)
    
    # Graphique 2: Niveaux d'enrichissement (camembert)
    enrichment_data = pd.DataFrame({
        'Niveau': ['3.67% (JCPOA)', '20%', '60%', '90% (militaire)'],
        'Statut': ['Dépassé', 'Atteint', 'Atteint', 'Non atteint']
    })
    
    fig.add_trace(
        go.Pie(labels=enrichment_data['Niveau'], values=[1, 1, 1, 0],
               marker=dict(colors=['#239F40', '#FFA500', '#DA0000', '#666666']),
               textinfo='label'),
        row=1, col=2
    )
    
    # Graphique 3: Accès AIEA
    fig.add_trace(
        go.Scatter(x=INSPECTION_HISTORY['date'], y=INSPECTION_HISTORY['access_level'],
                  name="Niveau d'accès (%)", line=dict(color='#2196f3', width=3),
                  fill='tozeroy'),
        row=2, col=1
    )
    
    # Marqueur pour les frappes
    fig.add_vline(x=datetime(2025, 6, 15), line_dash="dash", line_color="#DA0000",
                 annotation_text="Frappes israélo-américaines", row=2, col=1)
    
    # Graphique 4: Inspections
    fig.add_trace(
        go.Bar(x=INSPECTION_HISTORY['date'].iloc[-24:], 
               y=INSPECTION_HISTORY['inspections_conducted'].iloc[-24:],
               name="Inspections mensuelles", marker_color='#2196f3'),
        row=2, col=2
    )
    
    fig.update_layout(height=800, showlegend=True, template='plotly_white',
                     title_text="Analyse chronologique du programme nucléaire iranien")
    fig.update_xaxes(title_text="Date", row=1, col=1)
    fig.update_xaxes(title_text="Date", row=2, col=1)
    fig.update_yaxes(title_text="Stock (kg)", row=1, col=1)
    fig.update_yaxes(title_text="Niveau d'enrichissement (%)", secondary_y=True, row=1, col=1)
    fig.update_yaxes(title_text="Niveau d'accès (%)", row=2, col=1)
    fig.update_yaxes(title_text="Nombre d'inspections", row=2, col=2)
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Timeline des événements
    st.markdown("### 📅 Chronologie des événements clés")
    
    df_timeline = pd.DataFrame(LATEST_IAEA_DATA["timeline_events"])
    df_timeline['date'] = pd.to_datetime(df_timeline['date'])
    df_timeline = df_timeline.sort_values('date')
    
    # Créer une timeline visuelle
    fig_timeline = go.Figure()
    
    colors = {'accord': '#239F40', 'crise': '#FFA500', 'escalade': '#DA0000', 
              'attaque': '#DA0000', 'seuil': '#FFA500', 'nouvelle': '#2196f3', 'rapport': '#2196f3'}
    
    for i, row in df_timeline.iterrows():
        fig_timeline.add_trace(go.Scatter(
            x=[row['date']], y=[1],
            mode='markers+text',
            marker=dict(size=15, color=colors.get(row['type'], '#666666')),
            text=row['event'],
            textposition="top center",
            name=row['event'],
            showlegend=False
        ))
    
    fig_timeline.update_layout(
        title="Chronologie des événements (2015-2026)",
        xaxis_title="Date",
        yaxis=dict(showticklabels=False, showgrid=False),
        height=200,
        hovermode='x',
        template='plotly_white'
    )
    
    st.plotly_chart(fig_timeline, use_container_width=True)

# La suite du code reste identique...
# (Pour économiser de l'espace, je ne répète pas tout le code, mais le reste est inchangé)

# Note: La suite du code (sections "🏭 Sites nucléaires", "📈 Évolution de l'enrichissement", etc.)
# reste identique à votre script original. Seule la définition de INSPECTION_HISTORY a été corrigée.

st.markdown("---")
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.8rem;'>
    ✅ Version corrigée - Toutes les listes ont maintenant la même longueur
</div>
""", unsafe_allow_html=True)
