
# Rapport de synthèse — Analyse des Services Publics au Togo

## 1. Contexte et objectifs

Ce rapport présente une synthèse orientée décision à partir des données disponibles sur les demandes de services publics, l’activité des centres et la couverture territoriale.

Objectifs :

- **Mesurer la performance** de service (délais, rejets, activité).
- **Évaluer l’accès / la couverture territoriale** (communes desservies vs communes totales).
- **Identifier des écarts** (régions/communes/centres) et prioriser des actions.
- **Outiller la décision** via un tableau de bord interactif.

## 2. Données et périmètre

### 2.1 Sources de données

Les analyses s’appuient sur les fichiers nettoyés suivants :

- Demandes : `data/cleaned_data/demandes_service_public_nettoye.csv`
- Centres : `data/cleaned_data/centres_service_nettoye.csv`
- Logs d’activité : `data/cleaned_data/logs_activite_nettoye.csv`
- Référentiel des communes : `data/cleaned_data/details_communes_nettoye.csv`

### 2.2 Périmètre analytique

- L’analyse couvre le périmètre temporel et géographique représenté dans les fichiers.
- Les agrégations utilisent principalement : `region`, `prefecture`, `commune`, ainsi que les dates de demande et d’opération.

## 3. Démarche analytique

### 3.1 Analyse exploratoire (EDA)

- Revue du schéma (colonnes, types), distributions et granularité.
- Contrôles de cohérence (doublons, valeurs inattendues, dates invalides).
- Identification des dimensions clés : volumétrie, géographie, performance et tendance temporelle.

### 3.2 Nettoyage / préparation

Principaux traitements :

- Harmonisation des formats (dates, numériques).
- Normalisation des libellés géographiques (région/commune).
- **Protection des identifiants** (`*_id`) pour éviter des transformations destructrices.

Résultat : génération des fichiers `*_nettoye.csv` dans `data/cleaned_data/`.

### 3.3 KPI et dashboard

- Définition des KPI pour le pilotage opérationnel et territorial.
- Implémentation et visualisation dans le dashboard Streamlit : `Dashboard/app.py`.

## 4. KPI clés et interprétation

Les champs entre accolades `{{...}}` sont à renseigner à partir des valeurs finales du dashboard.

### 4.1 Total des demandes

- **Total des demandes** : `{{TOTAL_DEMANDES}}`

Interprétation :

- Sert à dimensionner la charge globale et à suivre l’évolution par période, région et type de document.

### 4.2 Délai moyen de traitement (pondéré)

- **Délai moyen** : `{{DELAI_MOYEN_JOURS}}` jours

Règle (résumé) : moyenne de `delai_traitement_jours` pondérée par `nombre_demandes`.

Interprétation :

- Indicateur central de qualité de service.
- Un délai élevé peut indiquer : sous-capacité, goulots administratifs, ruptures de stock, ou une complexité documentaire.

### 4.3 Taux de rejet (pondéré)

- **Taux de rejet** : `{{TAUX_REJET_PCT}}` %

Règle (résumé) : moyenne de `taux_rejet` pondérée par `nombre_demandes`.

Interprétation :

- Un taux de rejet élevé peut traduire : dossiers incomplets, mauvaise orientation, manque d’information usager, ou contrôles hétérogènes.

### 4.4 Couverture territoriale

- **Couverture territoriale** : `{{COUVERTURE_PCT}}` %

Règle (résumé) :

- **Couverture (%) = communes desservies / communes totales × 100**
- Les valeurs non informatives (ex: `"autres"`) sont exclues.
- Calcul par région puis agrégation pour limiter les biais.

Interprétation :

- Mesure l’accès réel des citoyens aux services sur le territoire.
- Une couverture faible aide à cibler : nouvelles implantations, guichets mobiles, digitalisation.

### 4.5 Taux d’occupation (capacité vs activité)

- **Taux d’occupation** : `{{TAUX_OCCUPATION_PCT}}` %

Règle (résumé) :

- **Occupation (%) = volume traité / capacité théorique × 100**
- Capacité théorique : somme des capacités journalières (`personnel_capacite_jour`) × nombre de jours observés.

Interprétation :

- **> 100%** : surcharge probable (risque d’allongement des délais).
- **80–100%** : utilisation élevée (zone de vigilance).
- **< 60%** : marge de capacité (optimisation possible avant ajout de ressources).

## 5. Principaux enseignements (insights)

À confirmer et illustrer à partir des vues du dashboard (carte, tendances, comparatifs régionaux) :

1. **Disparités territoriales** : couverture et performance non homogènes entre régions.
2. **Documents à forte demande** : certains types de documents concentrent la volumétrie et pilotent la charge.
3. **Performance variable** : écarts notables entre communes/centres sur délais et rejets.
4. **Tendances temporelles** : pics mensuels possibles nécessitant une gestion proactive des ressources.

## 6. Recommandations opérationnelles

### 6.1 Renforcer la couverture territoriale

- Prioriser les zones sous-desservies via :
  - extension du réseau de centres,
  - guichets mobiles,
  - partenariats locaux,
  - digitalisation des démarches les plus fréquentes.

### 6.2 Réduire les délais

- Identifier les goulots par document/région/centre et :
  - ajuster l’allocation d’effectifs,
  - standardiser les procédures,
  - suivre les délais sur une base hebdomadaire,
  - mettre en place un pilotage par objectifs (SLA internes).

### 6.3 Réduire les rejets

- Agir en amont :
  - checklists usager par document,
  - pré-contrôle des pièces,
  - formation ciblée des agents,
  - communication des motifs de rejet et des corrections attendues.

### 6.4 Optimiser la capacité (occupation)

- Si occupation faible :
  - optimiser la répartition des ressources, élargir certains services, renforcer l’orientation usager.
- Si occupation élevée :
  - plan de renfort (effectifs/horaires), réduction des tâches non essentielles, meilleure planification logistique.

## 7. Limites et perspectives

### 7.1 Limites

- Qualité des libellés géographiques : impact direct sur le calcul de couverture.
- Capacité théorique : `personnel_capacite_jour` peut être une approximation (absences, pannes, variations quotidiennes non capturées).
- Données potentiellement hétérogènes selon les sources (pratiques de saisie).

### 7.2 Perspectives

- Ajouter un suivi plus fin (jour/semaine) et des alertes automatiques.
- Introduire des KPI d’équité territoriale (écarts inter-régions, indice de dispersion).
- Croiser avec données de contexte (population, distances, réseau routier) pour expliquer les disparités.
- Mettre en place une actualisation automatisée des données.

## 8. Références (projet)

- Dashboard : `Dashboard/app.py`
- Notebooks : `notebooks/`

