import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import sqlite3
import os
from pathlib import Path

# Configuration de la page
st.set_page_config(
    page_title="Tableau de Bord TOGO Data Lab",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style personnalisé
def load_css():
    st.markdown("""
    <style>
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        .kpi-card {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
        }
        .kpi-value {
            font-size: 2rem;
            font-weight: 700;
            color: #1E88E5;
        }
        .kpi-label {
            color: #666;
            font-size: 0.9rem;
        }
    </style>
    """, unsafe_allow_html=True)

# Chargement des données
@st.cache_resource
def load_data():
    base_dir = Path(__file__).resolve().parents[1]  # d:\TOGO DATA LAB
    data_dir = base_dir / "data" / "cleaned_data"

    demandes_path = data_dir / "demandes_service_public_nettoye.csv"
    centres_path = data_dir / "centres_service_nettoye.csv"
    logs_path = data_dir / "logs_activite_nettoye.csv"
    communes_path = data_dir / "details_communes_nettoye.csv"

    if not demandes_path.exists():
        raise FileNotFoundError(f"Fichier introuvable: {demandes_path}")
    if not centres_path.exists():
        raise FileNotFoundError(f"Fichier introuvable: {centres_path}")
    if not logs_path.exists():
        raise FileNotFoundError(f"Fichier introuvable: {logs_path}")
    if not communes_path.exists():
        raise FileNotFoundError(f"Fichier introuvable: {communes_path}")

    demandes = pd.read_csv(demandes_path, parse_dates=["date_demande"])
    centres = pd.read_csv(centres_path, parse_dates=["date_ouverture"])
    logs = pd.read_csv(logs_path, parse_dates=["date_operation"])
    communes = pd.read_csv(communes_path)

    for col in ["latitude", "longitude"]:
        if col in centres.columns:
            centres[col] = pd.to_numeric(centres[col], errors="coerce")

    for col in ["nombre_demandes", "delai_traitement_jours", "taux_rejet"]:
        if col in demandes.columns:
            demandes[col] = pd.to_numeric(demandes[col], errors="coerce")

    if "personnel_capacite_jour" in centres.columns:
        centres["personnel_capacite_jour"] = pd.to_numeric(centres["personnel_capacite_jour"], errors="coerce")
    if "nombre_traite" in logs.columns:
        logs["nombre_traite"] = pd.to_numeric(logs["nombre_traite"], errors="coerce")
    if "nombre_rejete" in logs.columns:
        logs["nombre_rejete"] = pd.to_numeric(logs["nombre_rejete"], errors="coerce")
    if "temps_attente_moyen_minutes" in logs.columns:
        logs["temps_attente_moyen_minutes"] = pd.to_numeric(logs["temps_attente_moyen_minutes"], errors="coerce")

    conn = sqlite3.connect(":memory:")
    demandes.to_sql("demandes_service_public", conn, index=False, if_exists="replace")
    centres.to_sql("centres_service", conn, index=False, if_exists="replace")
    logs.to_sql("logs_activite", conn, index=False, if_exists="replace")
    communes.to_sql("details_communes", conn, index=False, if_exists="replace")

    return {
        "conn": conn,
        "demandes": demandes,
        "centres": centres,
        "logs": logs,
        "communes": communes,
    }

def _weighted_mean(df: pd.DataFrame, value_col: str, weight_col: str):
    if df.empty:
        return None
    if value_col not in df.columns or weight_col not in df.columns:
        return None
    v = pd.to_numeric(df[value_col], errors="coerce")
    w = pd.to_numeric(df[weight_col], errors="coerce")
    mask = v.notna() & w.notna() & (w > 0)
    if not mask.any():
        return None
    return float((v[mask] * w[mask]).sum() / w[mask].sum())

def compute_kpis(demandes_f: pd.DataFrame, centres_f: pd.DataFrame, logs_f: pd.DataFrame, communes_all: pd.DataFrame):
    total_demandes = float(pd.to_numeric(demandes_f.get("nombre_demandes"), errors="coerce").fillna(0).sum())
    delai_moyen = _weighted_mean(demandes_f, "delai_traitement_jours", "nombre_demandes")
    taux_rejet = _weighted_mean(demandes_f, "taux_rejet", "nombre_demandes")

    # Couverture: communes présentes dans les demandes / communes référencées
    communes_total = communes_all["commune"].dropna().nunique() if "commune" in communes_all.columns else None
    communes_servies = demandes_f["commune"].dropna().nunique() if "commune" in demandes_f.columns else None
    couverture = None
    if communes_total and communes_total > 0 and communes_servies is not None:
        couverture = float(100.0 * communes_servies / communes_total)

    # Occupation: total traité / (capacité_jour * nb_jours) sur les centres filtrés
    taux_occupation = None
    if not logs_f.empty and "centre_id" in logs_f.columns and "personnel_capacite_jour" in centres_f.columns:
        cap = centres_f[["centre_id", "personnel_capacite_jour"]].dropna()
        cap["personnel_capacite_jour"] = pd.to_numeric(cap["personnel_capacite_jour"], errors="coerce")
        cap = cap.dropna(subset=["personnel_capacite_jour"])
        if not cap.empty:
            logs_join = logs_f.merge(cap, on="centre_id", how="inner")
            if not logs_join.empty:
                total_traite = float(pd.to_numeric(logs_join.get("nombre_traite"), errors="coerce").fillna(0).sum())
                nb_jours = logs_join["date_operation"].dt.date.nunique() if "date_operation" in logs_join.columns else 0
                capacite_totale = float((logs_join["personnel_capacite_jour"].fillna(0).sum()) * max(1, nb_jours))
                if capacite_totale > 0:
                    taux_occupation = float(100.0 * total_traite / capacite_totale)

    return {
        "delai_moyen": delai_moyen,
        "taux_rejet": None if taux_rejet is None else float(100.0 * taux_rejet),
        "total_demandes": total_demandes,
        "taux_occupation": taux_occupation,
        "couverture": couverture,
    }

# En-tête
def render_header():
    st.title("📊 Tableau de Bord des Services Publics du Togo")
    st.markdown("""
    <div style='color: #666; margin-bottom: 2rem;'>
        Outil de pilotage décisionnel pour le suivi des services publics
    </div>
    """, unsafe_allow_html=True)

# Filtres principaux
def render_filters(date_min: datetime, date_max: datetime, regions_disponibles, types_documents):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        date_debut = st.date_input(
            "Date de début",
            date_min.date(),
            key="date_debut"
        )
    with col2:
        date_fin = st.date_input(
            "Date de fin",
            date_max.date(),
            key="date_fin"
        )
    with col3:
        region = st.selectbox(
            "Région",
            ["Toutes"] + list(regions_disponibles),
            key="region"
        )
    with col4:
        type_document = st.multiselect(
            "Type de document",
            options=list(types_documents),
            default=[],
            key="type_document",
        )
    return date_debut, date_fin, region, type_document

# Cartes KPI
def render_kpi_cards(metrics):
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        delai_txt = "N/A" if metrics.get("delai_moyen") is None else f"{metrics['delai_moyen']:.1f} jours"
        st.metric(label="Délai Moyen", value=delai_txt)

    with col2:
        occ_txt = "N/A" if metrics.get("taux_occupation") is None else f"{metrics['taux_occupation']:.1f}%"
        st.metric(label="Taux d'Occupation", value=occ_txt)

    with col3:
        cov_txt = "N/A" if metrics.get("couverture") is None else f"{metrics['couverture']:.1f}%"
        st.metric(label="Couverture Territoriale", value=cov_txt)

    with col4:
        rej_txt = "N/A" if metrics.get("taux_rejet") is None else f"{metrics['taux_rejet']:.1f}%"
        st.metric(label="Taux de Rejet", value=rej_txt)

# Carte des centres
def render_map(centres_f: pd.DataFrame):
    st.subheader("Carte des Centres de Service")
    cols = [c for c in ["latitude", "longitude"] if c in centres_f.columns]
    if len(cols) != 2:
        st.info("Coordonnées (latitude/longitude) non disponibles pour afficher la carte.")
        return

    map_df = centres_f.dropna(subset=["latitude", "longitude"]).copy()
    if map_df.empty:
        st.info("Aucun centre avec coordonnées pour les filtres sélectionnés.")
        return

    st.map(map_df[["latitude", "longitude"]])

# Graphiques principaux
def render_charts(demandes_f: pd.DataFrame):
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Délai de Traitement par Type de Document")
        if demandes_f.empty:
            st.info("Aucune donnée pour les filtres sélectionnés.")
        else:
            g = (
                demandes_f.dropna(subset=["type_document"]).groupby("type_document", as_index=False)
                .apply(lambda x: pd.Series({
                    "delai_moyen": _weighted_mean(x, "delai_traitement_jours", "nombre_demandes"),
                    "volume": pd.to_numeric(x.get("nombre_demandes"), errors="coerce").fillna(0).sum(),
                }))
                .reset_index(drop=True)
            )
            g = g.dropna(subset=["delai_moyen"]).sort_values("delai_moyen", ascending=False)
            fig = px.bar(
                g,
                x="type_document",
                y="delai_moyen",
                hover_data=["volume"],
                labels={"type_document": "Type de document", "delai_moyen": "Délai moyen (jours)"},
            )
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Évolution Mensuelle des Demandes")
        if demandes_f.empty:
            st.info("Aucune donnée pour les filtres sélectionnés.")
        else:
            df = demandes_f.copy()
            df["mois"] = df["date_demande"].dt.to_period("M").dt.to_timestamp()
            s = df.groupby("mois", as_index=False)["nombre_demandes"].sum()
            fig = px.line(
                s,
                x="mois",
                y="nombre_demandes",
                markers=True,
                labels={"mois": "Mois", "nombre_demandes": "Nombre de demandes"},
            )
            st.plotly_chart(fig, use_container_width=True)

# Tableau des performances par centre
def render_centers_table(demandes_f: pd.DataFrame, centres_f: pd.DataFrame):
    st.subheader("Performances par Centre")
    if demandes_f.empty:
        st.info("Aucune donnée pour les filtres sélectionnés.")
        return

    df = demandes_f.copy()
    # KPI par commune (proxy du centre si pas de clé centre_id côté demandes)
    per_commune = (
        df.dropna(subset=["commune"]).groupby(["region", "prefecture", "commune"], as_index=False)
        .apply(lambda x: pd.Series({
            "volume": pd.to_numeric(x.get("nombre_demandes"), errors="coerce").fillna(0).sum(),
            "delai_moyen": _weighted_mean(x, "delai_traitement_jours", "nombre_demandes"),
            "taux_rejet": _weighted_mean(x, "taux_rejet", "nombre_demandes"),
        }))
        .reset_index(drop=True)
    )
    per_commune["taux_rejet"] = per_commune["taux_rejet"].apply(lambda x: None if pd.isna(x) else float(100.0 * x))
    per_commune = per_commune.sort_values("volume", ascending=False).head(25)

    # On affiche aussi le nombre de centres disponibles dans la zone (join simple sur commune)
    centres_count = None
    if not centres_f.empty and "commune" in centres_f.columns:
        centres_count = centres_f.groupby("commune", as_index=False).size().rename(columns={"size": "nb_centres"})
        per_commune = per_commune.merge(centres_count, on="commune", how="left")
    else:
        per_commune["nb_centres"] = None

    df = per_commune.rename(
        columns={
            "commune": "Commune",
            "volume": "Nombre de demandes",
            "delai_moyen": "Délai moyen (j)",
            "taux_rejet": "Taux de rejet (%)",
            "nb_centres": "Nb centres",
            "region": "Région",
            "prefecture": "Préfecture",
        }
    )
    st.dataframe(
        df,
        column_config={
            "Délai moyen (j)": st.column_config.NumberColumn("Délai moyen (j)", format="%.1f"),
            "Taux de rejet (%)": st.column_config.NumberColumn("Taux de rejet (%)", format="%.1f"),
            "Nombre de demandes": st.column_config.NumberColumn("Nombre de demandes", format="%.0f"),
            "Nb centres": st.column_config.NumberColumn("Nb centres", format="%.0f"),
        },
        hide_index=True,
        use_container_width=True
    )

# Points d'attention
def render_alerts():

    st.subheader("Points de Vigilance")
    with st.expander("Alerte : Délais élevés à Dapaong", expanded=False):
        st.warning("Le centre de Dapaong présente un délai moyen de traitement de 5.2 jours, largement supérieur à la moyenne nationale (3.8 jours). Une inspection est recommandée.")

    with st.expander("Forte demande de passeports", expanded=False):
        st.info("Une augmentation de 25% des demandes de passeports a été enregistrée ce mois-ci. Vérifier les stocks de matériel.")

# Fonction principale
def main():
    load_css()
    render_header()

    # Charger les données
    try:
        data = load_data()
    except Exception as e:
        st.error(f"Impossible de charger les données: {e}")
        return

    demandes = data["demandes"]
    centres = data["centres"]
    logs = data["logs"]
    communes = data["communes"]

    date_min = demandes["date_demande"].min().to_pydatetime() if "date_demande" in demandes.columns else datetime.now() - timedelta(days=365)
    date_max = demandes["date_demande"].max().to_pydatetime() if "date_demande" in demandes.columns else datetime.now()

    regions_disponibles = sorted(demandes["region"].dropna().unique().tolist()) if "region" in demandes.columns else []
    types_documents = sorted(demandes["type_document"].dropna().unique().tolist()) if "type_document" in demandes.columns else []

    # Afficher les filtres
    date_debut, date_fin, region, types_sel = render_filters(date_min, date_max, regions_disponibles, types_documents)

    # Application des filtres
    demandes_f = demandes.copy()
    if "date_demande" in demandes_f.columns:
        demandes_f = demandes_f[(demandes_f["date_demande"].dt.date >= date_debut) & (demandes_f["date_demande"].dt.date <= date_fin)]
    if region and region != "Toutes" and "region" in demandes_f.columns:
        demandes_f = demandes_f[demandes_f["region"] == region]
    if types_sel and "type_document" in demandes_f.columns:
        demandes_f = demandes_f[demandes_f["type_document"].isin(types_sel)]

    centres_f = centres.copy()
    if region and region != "Toutes" and "region" in centres_f.columns:
        centres_f = centres_f[centres_f["region"] == region]

    logs_f = logs.copy()
    if "date_operation" in logs_f.columns:
        logs_f = logs_f[(logs_f["date_operation"].dt.date >= date_debut) & (logs_f["date_operation"].dt.date <= date_fin)]
    if not centres_f.empty and "centre_id" in centres_f.columns and "centre_id" in logs_f.columns:
        logs_f = logs_f[logs_f["centre_id"].isin(centres_f["centre_id"].dropna().unique())]

    metrics = compute_kpis(demandes_f, centres_f, logs_f, communes)

    # Afficher les KPI
    render_kpi_cards(metrics)

    # Première rangée : Carte et graphiques
    render_map(centres_f)
    render_charts(demandes_f)

    # Deuxième rangée : Tableau et alertes
    col1, col2 = st.columns([2, 1])
    with col1:
        render_centers_table(demandes_f, centres_f)
    with col2:
        render_alerts()

if __name__ == "__main__":
    main()