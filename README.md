# TOGO DATA LAB — Analyse des Services Publics

Ce repository contient un mini-projet de bout en bout (EDA → nettoyage → KPI → dashboard → restitution) visant à analyser l’accès et la performance des services publics au Togo.

## Objectifs

- **Mesurer la performance** opérationnelle (délais, rejets, activité).
- **Évaluer la couverture territoriale** (communes desservies vs communes totales).
- **Fournir un support décisionnel** via un dashboard Streamlit et des livrables de restitution.

## Livrables

- **Notebooks d’EDA** et d’analyse:

  - `notebooks/01_eda.ipynb`
  - `notebooks/03_analyse_kpi.ipynb`
- **Nettoyage / préparation des données**:

  - `notebooks/02_nettoyage_preparation.ipynb`
  - sorties CSV dans `data/cleaned_data/`
- **Dashboard (Streamlit)**:

  - `Dashboard/app.py`
- **Tableau des KPI (Markdown/Excel)**:

  - disponible dans le `notebooks/03_analyse_kpi.ipynb`
- **Présentation PowerPoint**:

  - `rapport/Présentation powerpoint.pptx`
- **Rapport de synthèse (3 à 5 pages)**:

  - `rapport/synthese.md`)

## Données

Le projet s’appuie sur des fichiers CSV.

- **Données nettoyées** (utilisées par le dashboard): `data/cleaned_data/*.csv`
- **Données brutes**: `data/raw/` (ignoré par Git via `.gitignore`)

Fichiers clés (nettoyés):

- `data/cleaned_data/demandes_service_public_nettoye.csv`
- `data/cleaned_data/centres_service_nettoye.csv`
- `data/cleaned_data/logs_activite_nettoye.csv`
- `data/cleaned_data/details_communes_nettoye.csv`

## KPI (définition synthétique)

Les KPI calculés dans le dashboard ncluent notamment:

- **Total des demandes**: somme de `nombre_demandes`.
- **Délai moyen pondéré**: moyenne de `delai_traitement_jours` pondérée par `nombre_demandes`.
- **Taux de rejet pondéré**: moyenne de `taux_rejet` pondérée par `nombre_demandes`.
- **Couverture territoriale (%)**: communes desservies / communes totales × 100.
  - Calcul robuste: exclusion des valeurs non informatives (ex: `"autres"`), calcul par région puis agrégation.
- **Taux d’occupation (%)**: volume traité / capacité théorique × 100.
  - Capacité théorique: somme des capacités journalières des centres × nombre de jours observés.

## Reproductibilité

### 1) Nettoyage / préparation

Ouvrir et exécuter le notebook:

- `notebooks/02_nettoyage_preparation.ipynb`

Sorties attendues:

- fichiers `*_nettoye.csv` mis à jour dans `data/cleaned_data/`

### 2) Lancer le dashboard

Depuis la racine du projet:

```bash
streamlit run Dashboard/app.py
```

Si vous utilisez un environnement virtuel, installez d’abord les dépendances (voir section suivante).

## Installation

### Prérequis

- Python 3.9+ recommandé
- `pip`

### Dépendances

Le projet peut être exécuté avec les dépendances nécessaires au dashboard.

Si un fichier `Dashboard/requirements.txt` n’est pas présent, vous pouvez installer au minimum:

```bash
pip install streamlit pandas numpy plotly
```
