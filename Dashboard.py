# dashboard_uranium_iran.py
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

# Données actualisées de l'AIEA (février 2026) [citation:1][citation:4][citation:8]
LATEST_IAEA_DATA = {
    "report_date": "2026-02-27",
    "uranium_60_percent": 440.9,  # kg [citation:1]
    "uranium_total": 9247.6,  # kg [citation:5]
    "weapons_potential": 10,  # nombre de bombes potentielles [citation:1][citation:10]
    "facilities": {
        "Isfahan": {
            "name": "Complexe nucléaire d'Ispahan (ENTC)",
            "status": "Actif - Stockage d'uranium hautement enrichi",
            "enrichment_levels": ["20%", "60%"],
            "storage_tunnel": "Complexe souterrain",
            "iaea_access": "Non autorisé depuis juin 2025",
            "last_inspection": "2025-06-10",
            "vehicle_activity": "Élevée - Observations satellite récentes [citation:1]",
            "bombed": "Oui - Frappes israélo-américaines juin 2025",
            "damage": "Limité - Installations souterraines préservées [citation:4]",
            "fourth_facility": "Nouvelle installation non localisée par l'AIEA [citation:1]",
            "coordinates": {"lat": 32.65, "lon": 51.68}
        },
        "Natanz": {
            "name": "Site d'enrichissement de Natanz",
            "status": "Activité observée sans vérification possible [citation:2]",
            "enrichment_levels": ["Jusqu'à 60%"],
            "pilot_plant": "PFEP - Installation pilote",
            "iaea_access": "Non autorisé",
            "last_inspection": "2025-06-09",
            "observations": "Panneaux installés sur cage anti-drone [citation:2]",
            "bombed": "Oui - Sévèrement endommagé [citation:1]",
            "coordinates": {"lat": 33.72, "lon": 51.72}
        },
        "Fordow": {
            "name": "Site de Fordow (souterrain)",
            "status": "Activité observée sans vérification [citation:2]",
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
        "significant_quantity": 42,  # kg à 60% pour une bombe [citation:8]
        "jcpoa_limit": 3.67,  # %
        "breakout_time": 15  # jours estimés
    }
}

# Historique des inspections AIEA
INSPECTION_HISTORY = pd.DataFrame({
    "date": pd.date_range(start="2023-01-01", end="2026-02-01", freq="M"),
    "inspections_conducted": [12, 10, 8, 9, 7, 5, 4, 3, 2, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    "access_level": [100, 95, 90, 85, 80, 75, 70, 60, 50, 40, 30, 20, 10, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5, 5],
    "stock_60pct": [87.5, 95.2, 103.8, 114.5, 126.3, 140.1, 155.2, 170.5, 188.3, 208.1, 230.4, 255.2, 283.7, 315.8, 350.2, 388.5, 408.6, 440.9, 440.9, 440.9, 440.9, 440.9, 440.9, 440.9, 440.9, 440.9, 440.9, 440.9, 440.9, 440.9, 440.9, 440.9, 440.9, 440.9, 440.9, 440.9, 440.9, 440.9],
})

# Négociations internationales
NEGOTIATIONS_DATA = [
    {"date": "2026-02-26", "location": "Genève", "parties": ["États-Unis", "Iran", "Oman"], "outcome": "Aucune percée [citation:4]"},
    {"date": "2026-02-19", "location": "Genève", "parties": ["États-Unis", "Iran", "Oman"], "outcome": "Discussions techniques"},
    {"date": "2026-02-12", "location": "Genève", "parties": ["États-Unis", "Iran", "Oman"], "outcome": "Premier round indirect"},
    {"date": "2026-02-27", "location": "Washington", "parties": ["États-Unis", "Oman"], "outcome": "Rencontre Vance-Busaidi [citation:2]"},
    {"date": "2026-03-02", "location": "Vienne", "parties": ["Iran", "AIEA"], "outcome": "Réunion programmée [citation:2]"},
]

# Déclarations officielles
OFFICIAL_STATEMENTS = [
    {"date": "2026-02-27", "source": "IAEA", "statement": "L'AIEA ne peut vérifier si l'Iran a suspendu toutes les activités d'enrichissement [citation:2]"},
    {"date": "2026-02-27", "source": "Vice-président JD Vance", "statement": "Preuves que l'Iran tente de reconstruire son programme d'armes nucléaires [citation:2]"},
    {"date": "2026-02-27", "source": "Oman FM Badr al Busaidi", "statement": "L'Iran a accepté de diluer son uranium enrichi au niveau le plus bas possible [citation:2]"},
    {"date": "2026-02-25", "source": "Marco Rubio", "statement": "L'Iran n'enrichit pas actuellement mais cherche à pouvoir le faire [citation:2]"},
    {"date": "2026-02-23", "source": "Abbas Araghchi", "statement": "Les armes nucléaires sont inacceptables pour l'Iran [citation:5]"},
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
        bombs_possible = value / 42  # 42 kg à 60% = 1 bombe potentielle [citation:8]
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
            f"**Accès aux sites:** Non autorisé [citation:2]")
    
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
    st.caption("Données AIEA - Mise à jour: 28 février 2026 [citation:1][citation:4]")
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
    l'uranium à 60% [citation:1][citation:2][citation:4].
</div>
""", unsafe_allow_html=True)

# KPIs principaux
st.markdown("### 📊 Indicateurs Clés")

col_kpi1, col_kpi2, col_kpi3, col_kpi4, col_kpi5 = st.columns(5)

with col_kpi1:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-value'>{LATEST_IAEA_DATA['uranium_60_percent']} kg</div>", unsafe_allow_html=True)
    st.markdown("<div class='metric-label'>Uranium enrichi à 60%</div>", unsafe_allow_html=True)
    st.caption("Stock pré-attaque juin 2025 [citation:1]")
    st.markdown("</div>", unsafe_allow_html=True)

with col_kpi2:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-value'>{LATEST_IAEA_DATA['uranium_total']:.0f} kg</div>", unsafe_allow_html=True)
    st.markdown("<div class='metric-label'>Uranium enrichi total</div>", unsafe_allow_html=True)
    st.caption("45x limite JCPOA [citation:5]")
    st.markdown("</div>", unsafe_allow_html=True)

with col_kpi3:
    st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
    st.markdown(f"<div class='metric-value'>{LATEST_IAEA_DATA['weapons_potential']}</div>", unsafe_allow_html=True)
    st.markdown("<div class='metric-label'>Bombes potentielles</div>", unsafe_allow_html=True)
    st.caption("Selon yardstick AIEA [citation:1]")
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

elif menu == "🏭 Sites nucléaires":
    st.markdown("## 🏭 Sites nucléaires iraniens")
    
    # Carte des sites
    st.markdown("### 🗺️ Localisation des sites")
    
    # Préparer les données pour la carte
    sites_data = []
    for site_name, site_info in LATEST_IAEA_DATA["facilities"].items():
        if "coordinates" in site_info:
            threat = "CRITIQUE" if site_info.get("enrichment_levels") and "60%" in str(site_info["enrichment_levels"]) else "MODÉRÉ"
            color = "#DA0000" if threat == "CRITIQUE" else "#FFA500" if threat == "ÉLEVÉ" else "#239F40"
            
            sites_data.append({
                "Site": site_name,
                "lat": site_info["coordinates"]["lat"],
                "lon": site_info["coordinates"]["lon"],
                "statut": site_info["status"],
                "enrichissement": ", ".join(site_info.get("enrichment_levels", ["N/A"])),
                "accès": site_info.get("iaea_access", "Inconnu"),
                "couleur": color,
                "taille": 20 if threat == "CRITIQUE" else 15
            })
    
    df_sites = pd.DataFrame(sites_data)
    
    fig_map = px.scatter_mapbox(
        df_sites,
        lat="lat",
        lon="lon",
        text="Site",
        hover_name="Site",
        hover_data={"statut": True, "enrichissement": True, "accès": True},
        color_discrete_sequence=["#DA0000", "#FFA500", "#239F40"],
        size=[20, 20, 20, 20, 15],
        zoom=5,
        mapbox_style="open-street-map",
        title="Sites nucléaires iraniens"
    )
    
    fig_map.update_layout(height=500)
    st.plotly_chart(fig_map, use_container_width=True)
    
    # Détails des sites
    st.markdown("### 📋 Détails des installations")
    
    col1, col2 = st.columns(2)
    
    for i, (site_name, site_info) in enumerate(LATEST_IAEA_DATA["facilities"].items()):
        with col1 if i % 2 == 0 else col2:
            status_color = get_facility_status_color(site_info.get("iaea_access", ""))
            
            st.markdown(f"""
            <div class='facility-card' style='border-left: 5px solid {status_color};'>
                <h4>{site_info['name']}</h4>
                <p><b>Statut:</b> {site_info['status']}</p>
                <p><b>Niveaux d'enrichissement:</b> {', '.join(site_info.get('enrichment_levels', ['N/A']))}</p>
                <p><b>Accès AIEA:</b> <span style='color: {status_color}; font-weight: bold;'>{site_info.get('iaea_access', 'Inconnu')}</span></p>
                <p><b>Dernière inspection:</b> {site_info.get('last_inspection', 'Inconnue')}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Focus sur Ispahan (site critique)
    st.markdown("### ⚠️ Focus: Complexe d'Ispahan")
    
    isfahan = LATEST_IAEA_DATA["facilities"]["Isfahan"]
    
    st.markdown(f"""
    <div class='critical-box'>
        <h4>Complexe nucléaire d'Ispahan (ENTC) - Point d'attention majeur</h4>
        <p><b>Stockage souterrain:</b> Uranium enrichi jusqu'à 60% stocké dans un complexe de tunnels</p>
        <p><b>Activité observée:</b> {isfahan['vehicle_activity']}</p>
        <p><b>Impact des frappes:</b> {isfahan['damage']}</p>
        <p><b>Nouvelle installation:</b> {isfahan['fourth_facility']}</p>
        <p><b>Enjeu:</b> L'AIEA n'a pas accès à ce site depuis juin 2025 et ne peut vérifier 
        si l'uranium à 60% est toujours présent ou a été déplacé [citation:1][citation:4]</p>
    </div>
    """, unsafe_allow_html=True)

elif menu == "📈 Évolution de l'enrichissement":
    st.markdown("## 📈 Analyse détaillée de l'enrichissement")
    
    col_graph1, col_graph2 = st.columns(2)
    
    with col_graph1:
        st.markdown("### 📊 Stock d'uranium enrichi à 60%")
        
        fig_stock = go.Figure()
        
        # Données historiques
        fig_stock.add_trace(go.Scatter(
            x=INSPECTION_HISTORY['date'],
            y=INSPECTION_HISTORY['stock_60pct'],
            mode='lines+markers',
            name='Stock à 60%',
            line=dict(color='#DA0000', width=3),
            fill='tozeroy'
        ))
        
        # Seuil pour une bombe
        fig_stock.add_hline(y=42, line_dash="dash", line_color="#FFA500",
                           annotation_text="Seuil 1 bombe (42 kg)")
        
        # Seuil pour 10 bombes
        fig_stock.add_hline(y=420, line_dash="dash", line_color="#DA0000",
                           annotation_text="Seuil 10 bombes")
        
        # Marqueur pour les frappes
        fig_stock.add_vline(x=datetime(2025, 6, 15), line_dash="dash", line_color="#666666",
                           annotation_text="Frappes juin 2025")
        
        fig_stock.update_layout(
            xaxis_title="Date",
            yaxis_title="Kilogrammes d'uranium à 60%",
            hovermode='x',
            template='plotly_white',
            height=400
        )
        
        st.plotly_chart(fig_stock, use_container_width=True)
    
    with col_graph2:
        st.markdown("### ⚖️ Comparaison avec les seuils")
        
        current_stock = LATEST_IAEA_DATA["uranium_60_percent"]
        
        fig_gauge = go.Figure()
        
        # Jauge pour visualiser le stock par rapport aux seuils
        fig_gauge.add_trace(go.Indicator(
            mode="gauge+number+delta",
            value=current_stock,
            title={'text': "Stock d'uranium à 60% (kg)"},
            delta={'reference': 420, 'increasing': {'color': "#DA0000"}},
            gauge={
                'axis': {'range': [None, 500], 'tickwidth': 1},
                'bar': {'color': "#DA0000"},
                'steps': [
                    {'range': [0, 42], 'color': '#239F40'},
                    {'range': [42, 420], 'color': '#FFA500'},
                    {'range': [420, 500], 'color': '#DA0000'}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': 42
                }
            }
        ))
        
        fig_gauge.update_layout(height=400)
        st.plotly_chart(fig_gauge, use_container_width=True)
    
    # Graphique des niveaux d'enrichissement
    st.markdown("### 📊 Niveaux d'enrichissement et seuils critiques")
    
    levels = [3.67, 20, 60, 90]
    level_names = ["Limite JCPOA", "Enrichissement modéré", "Niveau actuel", "Qualité militaire"]
    colors = ["#239F40", "#FFA500", "#DA0000", "#8B0000"]
    
    fig_levels = go.Figure()
    
    for i, level in enumerate(levels):
        fig_levels.add_trace(go.Bar(
            x=[level_names[i]],
            y=[level],
            name=level_names[i],
            marker_color=colors[i],
            text=f"{level}%",
            textposition='inside'
        ))
    
    fig_levels.update_layout(
        title="Comparaison des niveaux d'enrichissement",
        xaxis_title="",
        yaxis_title="Pourcentage d'enrichissement",
        yaxis=dict(range=[0, 100]),
        showlegend=False,
        height=400,
        template='plotly_white'
    )
    
    st.plotly_chart(fig_levels, use_container_width=True)
    
    # Calcul des bombes potentielles
    st.markdown("### 💣 Calcul des bombes potentielles")
    
    bombs_60 = current_stock / 42  # 42 kg à 60% pour une bombe après enrichissement
    
    col_bomb1, col_bomb2, col_bomb3 = st.columns(3)
    
    with col_bomb1:
        st.metric("Bombes potentielles (à 60%)", f"{bombs_60:.1f}")
    
    with col_bomb2:
        uranium_90 = current_stock * 60/90  # après enrichissement à 90%
        bombs_90 = uranium_90 / 25  # ~25 kg à 90% pour une bombe
        st.metric("Bombes potentielles (après enrichissement)", f"{bombs_90:.1f}")
    
    with col_bomb3:
        st.metric("Seuil critique atteint", "OUI" if bombs_60 >= 10 else "NON",
                 delta_color="inverse" if bombs_60 >= 10 else "normal")

elif menu == "🌍 Négociations & Diplomatie":
    st.markdown("## 🌍 Négociations internationales")
    
    col_dip1, col_dip2 = st.columns(2)
    
    with col_dip1:
        st.markdown("### 🤝 Derniers rounds de négociations")
        
        df_nego = pd.DataFrame(NEGOTIATIONS_DATA)
        for _, row in df_nego.iterrows():
            outcome_color = "#239F40" if "programmée" in row['outcome'] or "techniques" in row['outcome'] else "#FFA500" if "Aucune" in row['outcome'] else "#666666"
            st.markdown(f"""
            <div style='background-color: #f8f9fa; padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0; border-left: 5px solid {outcome_color};'>
                <b>{row['date']} - {row['location']}</b><br>
                Parties: {', '.join(row['parties'])}<br>
                Résultat: {row['outcome']}
            </div>
            """, unsafe_allow_html=True)
    
    with col_dip2:
        st.markdown("### 📅 Prochaines échéances")
        
        st.markdown("""
        <div style='background-color: #e3f2fd; padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0;'>
            <b>📌 2 mars 2026</b><br>
            Réunion Iran-AIEA à Vienne [citation:2]<br>
            Enjeu: Négociations sur les inspections des sites endommagés
        </div>
        
        <div style='background-color: #e3f2fd; padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0;'>
            <b>📌 2 mars 2026</b><br>
            Conseil des gouverneurs de l'AIEA<br>
            Discussion du rapport confidentiel sur l'Iran
        </div>
        
        <div style='background-color: #fff3cd; padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0;'>
            <b>⚠️ Échéance non définie</b><br>
            Négociations USA-Iran via Oman<br>
            Demande américaine: Démantèlement de l'infrastructure nucléaire [citation:4]
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("### 🗺️ Acteurs et positions")
    
    col_act1, col_act2, col_act3, col_act4 = st.columns(4)
    
    with col_act1:
        st.markdown("""
        <div class='facility-card'>
            <h4>🇮🇷 Iran</h4>
            <p><b>Position:</b> Programme pacifique, droit à l'enrichissement [citation:5]</p>
            <p><b>Ligne rouge:</b> Armes nucléaires "inacceptables"</p>
            <p><b>Concession possible:</b> Dilution du stock [citation:2]</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_act2:
        st.markdown("""
        <div class='facility-card'>
            <h4>🇺🇸 États-Unis</h4>
            <p><b>Position:</b> Démantèlement complet [citation:4]</p>
            <p><b>Preuves:</b> Reconstruction du programme d'armes [citation:2]</p>
            <p><b>Option militaire:</b> Forces massées dans la région</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_act3:
        st.markdown("""
        <div class='facility-card'>
            <h4>🇮🇱 Israël</h4>
            <p><b>Position:</b> Empêcher l'Iran d'avoir l'arme nucléaire</p>
            <p><b>Action:</b> Frappes préventives en juin 2025</p>
            <p><b>Menace:</b> Nouvelles frappes si nécessaire</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col_act4:
        st.markdown("""
        <div class='facility-card'>
            <h4>🇴🇲 Oman</h4>
            <p><b>Rôle:</b> Médiateur principal</p>
            <p><b>Actions:</b> Organisation des pourparlers indirects</p>
            <p><b>Proposition:</b> Dilution de l'uranium [citation:2]</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("### 🔄 Scénarios diplomatiques")
    
    tab_scen1, tab_scen2, tab_scen3 = st.tabs(["Scénario 1: Accord", "Scénario 2: Statu quo", "Scénario 3: Escalade"])
    
    with tab_scen1:
        st.markdown("""
        **Accord diplomatique** (probabilité: 30%)
        
        - Iran accepte de diluer son stock d'uranium à 60% [citation:2]
        - Réintégration des inspecteurs de l'AIEA
        - Levée partielle des sanctions
        - Maintien d'un programme civil limité
        - Délai: 3-6 mois
        
        *Conditions:* Concessions mutuelles, médiation d'Oman efficace
        """)
    
    with tab_scen2:
        st.markdown("""
        **Statu quo prolongé** (probabilité: 45%)
        
        - Maintien du stock d'uranium non vérifié
        - Poursuite des négociations sans percée
        - Activité observée mais non vérifiée sur les sites
        - Tensions régionales persistantes
        - Risque de prolifération
        
        *Conditions:* Aucune des parties ne veut escalader
        """)
    
    with tab_scen3:
        st.markdown("""
        **Escalade militaire** (probabilité: 25%)
        
        - Nouvelles frappes préventives israéliennes ou américaines
        - Destruction des installations restantes
        - Réaction iranienne par ses proxies
        - Conflit régional élargi
        - Programme nucléaire repoussé de plusieurs années
        
        *Déclencheurs:* Preuve de militarisation imminente, échec des négos
        """)

elif menu == "📰 Actualités & Déclarations":
    st.markdown("## 📰 Dernières actualités et déclarations")
    
    col_news1, col_news2 = st.columns([2, 1])
    
    with col_news1:
        st.markdown("### 📢 Déclarations officielles récentes")
        
        for statement in OFFICIAL_STATEMENTS:
            source_color = "#2196f3" if "IAEA" in statement['source'] else "#DA0000" if "Rubio" in statement['source'] or "Vance" in statement['source'] else "#239F40" if "Araghchi" in statement['source'] else "#FFA500"
            st.markdown(f"""
            <div style='background-color: #f8f9fa; padding: 1rem; border-radius: 0.5rem; margin: 0.5rem 0; border-left: 5px solid {source_color};'>
                <b>{statement['date']} - {statement['source']}</b><br>
                {statement['statement']}
            </div>
            """, unsafe_allow_html=True)
    
    with col_news2:
        st.markdown("### 📊 Synthèse médias")
        
        st.markdown("""
        **Titres récents:**
        
        - **Gulf Times:** L'AIEA demande l'accès aux sites d'Ispahan [citation:1]
        - **ISW:** L'AIEA ne peut vérifier la suspension de l'enrichissement [citation:2]
        - **Al Jazeera:** Stock d'uranium hautement enrichi sous terre à Ispahan [citation:4]
        - **Jerusalem Post:** Première confirmation de la localisation de l'uranium à 60% [citation:8]
        
        **Mots-clés trending:**
        - #IranNuclear
        - #IAEA
        - #Isfahan
        - #Breakout
        """)
        
        st.markdown("### 📈 Tension médiatique")
        
        # Graphique simplifié de tension médiatique
        fig_tension = go.Figure()
        
        dates_tension = pd.date_range(start="2025-06-01", end="2026-02-28", freq='W')
        tension_levels = [30, 45, 60, 75, 85, 90, 88, 85, 82, 80, 78, 75, 73, 70, 68, 72, 78, 85, 88, 92, 95, 98, 100, 98, 95, 92, 90, 88, 92, 95, 98, 100, 98, 95, 92, 90, 88, 85, 82, 80]
        
        fig_tension.add_trace(go.Scatter(
            x=dates_tension[:len(tension_levels)],
            y=tension_levels,
            mode='lines',
            fill='tozeroy',
            line=dict(color='#DA0000', width=3)
        ))
        
        fig_tension.update_layout(
            title="Indice de tension médiatique",
            xaxis_title="Date",
            yaxis_title="Indice (0-100)",
            height=300,
            template='plotly_white'
        )
        
        st.plotly_chart(fig_tension, use_container_width=True)

elif menu == "⚖️ Seuils & Scénarios":
    st.markdown("## ⚖️ Analyse des seuils critiques et scénarios")
    
    col_thresh1, col_thresh2 = st.columns(2)
    
    with col_thresh1:
        st.markdown("### 📊 Seuils techniques")
        
        thresholds_df = pd.DataFrame({
            'Seuil': ['Limite JCPOA (2015)', 'Enrichissement modéré', 'Niveau actuel', 'Qualité militaire', 'Quantité significative'],
            'Valeur (%)': ['3.67%', '20%', '60%', '90%', 'N/A'],
            'Quantité (kg)': ['N/A', 'N/A', '440.9 kg', '~25 kg', '42 kg (à 60%)'],
            'Signification': ['Limite accord', 'Usage civil élargi', 'Seuil critique', 'Arme nucléaire', 'Assez pour 1 bombe']
        })
        
        st.dataframe(thresholds_df, use_container_width=True, hide_index=True)
    
    with col_thresh2:
        st.markdown("### ⏱️ Temps de breakout")
        
        breakout_data = pd.DataFrame({
            'Scénario': ['Statu quo', 'Décision de militarisation', 'Avec inspections'],
            'Temps estimé': ['15 jours', '3-6 mois', 'Indétectable'],
            'Probabilité': ['Élevée', 'Moyenne', 'Faible'],
            'Risque': ['⚠️ Critique', '🔴 Élevé', '🟡 Modéré']
        })
        
        st.dataframe(breakout_data, use_container_width=True, hide_index=True)
    
    st.markdown("### 🎯 Scénarios d'évolution")
    
    tab_scen_det1, tab_scen_det2, tab_scen_det3 = st.tabs([
        "Scénario A: Poursuite", "Scénario B: Accord", "Scénario C: Conflit"
    ])
    
    with tab_scen_det1:
        st.markdown("""
        ### Scénario A: Poursuite du programme avec opacity (Probabilité: 40%)
        
        **Contexte:** L'Iran maintient son stock d'uranium à 60% sans le réduire, tout en continuant à refuser l'accès à l'AIEA.
        
        **Évolution:**
        - Activité non vérifiée se poursuit sur les sites [citation:2]
        - Véhicules continuent de circuler autour d'Ispahan [citation:1]
        - Négociations traînent sans résultat concret
        - Tensions régionales persistantes
        
        **Conséquences:**
        - Incertitude totale sur le programme
        - Risque de prolifération non détectée
        - Pression militaire maintenue
        - Sanctions économiques prolongées
        
        **Point de bascule:** Si l'Iran atteint 90% sans être détecté
        """)
    
    with tab_scen_det2:
        st.markdown("""
        ### Scénario B: Accord diplomatique (Probabilité: 35%)
        
        **Contexte:** Succès des négociations Oman-USA-Iran avec concessions mutuelles.
        
        **Termes possibles:**
        - Dilution du stock d'uranium à 60% au niveau le plus bas possible [citation:2]
        - Réintégration complète des inspecteurs de l'AIEA
        - Démantèlement de certaines installations
        - Levée progressive des sanctions
        - Maintien d'un programme civil limité
        
        **Calendrier:**
        - Mars 2026: Réunions techniques à Vienne [citation:2]
        - Avril-Mai 2026: Négociations finales
        - Juin 2026: Mise en œuvre initiale
        
        **Vérification:** Inspections surprises, surveillance satellite, transparence totale
        """)
    
    with tab_scen_det3:
        st.markdown("""
        ### Scénario C: Escalade militaire (Probabilité: 25%)
        
        **Contexte:** Échec des négociations et preuves de militarisation imminente.
        
        **Déclencheurs possibles:**
        - Détection d'enrichissement à 90%
        - Expulsion définitive des inspecteurs
        - Déclaration officielle d'intention militaire
        
        **Actions:**
        - Frappes préventives israéliennes sur les sites souterrains
        - Implication américaine potentielle
        - Réponse iranienne via ses proxies
        - Conflit régional élargi
        
        **Cibles prioritaires:**
        1. Complexe souterrain d'Ispahan [citation:1]
        2. Installation non localisée (4ème site)
        3. Natanz et Fordow
        
        **Conséquences:** Programme repoussé de 3-5 ans mais instabilité régionale majeure
        """)
    
    # Visualisation des seuils
    st.markdown("### 📈 Visualisation des seuils critiques")
    
    fig_thresh = go.Figure()
    
    # Barres des niveaux
    levels_scenario = [3.67, 20, 60, 90]
    level_desc = ["JCPOA", "20%", "60% (actuel)", "90% (militaire)"]
    
    for i, level in enumerate(levels_scenario):
        color = "#239F40" if i == 0 else "#FFA500" if i == 1 else "#DA0000" if i == 2 else "#8B0000"
        fig_thresh.add_trace(go.Bar(
            x=[level_desc[i]],
            y=[level],
            name=level_desc[i],
            marker_color=color,
            text=f"{level}%",
            textposition='inside'
        ))
    
    fig_thresh.update_layout(
        title="Seuils d'enrichissement et position actuelle",
        xaxis_title="",
        yaxis_title="Niveau d'enrichissement (%)",
        yaxis=dict(range=[0, 100]),
        showlegend=False,
        height=400,
        template='plotly_white'
    )
    
    st.plotly_chart(fig_thresh, use_container_width=True)

# Footer
st.markdown("---")
col_footer1, col_footer2, col_footer3 = st.columns(3)

with col_footer1:
    st.markdown("""
    <div class='info-box'>
        <b>📌 Sources principales</b><br>
        • Agence Internationale de l'Énergie Atomique (AIEA)<br>
        • Institute for the Study of War (ISW)<br>
        • Reuters, Associated Press<br>
        • Al Jazeera, Gulf Times
    </div>
    """, unsafe_allow_html=True)

with col_footer2:
    st.markdown("""
    <div class='info-box'>
        <b>📅 Mise à jour</b><br>
        • Dernier rapport AIEA: 27 février 2026 [citation:1]<br>
        • Négociations: 26 février 2026 (Genève)<br>
        • Prochaine réunion: 2 mars 2026 (Vienne)<br>
        • Données en temps réel simulées
    </div>
    """, unsafe_allow_html=True)

with col_footer3:
    st.markdown("""
    <div class='warning-box'>
        <b>⚠️ Avertissement</b><br>
        Les données présentées sont basées sur les rapports publics de l'AIEA et des sources médiatiques.
        La situation évolue rapidement. Consultez les sources officielles pour les dernières informations.
    </div>
    """, unsafe_allow_html=True)

# Message en persan
st.markdown("""
<div style='text-align: center; font-family: Roboto; font-size: 1rem; margin-top: 1rem; direction: rtl;'>
    <p>🇮🇷 داشبورد برنامه هسته‌ای ایران - به‌روزرسانی فوریه ۲۰۲۶</p>
    <p>منابع: آژانس بین‌المللی انرژی اتمی، رسانه‌های بین‌المللی</p>
</div>
""", unsafe_allow_html=True)
