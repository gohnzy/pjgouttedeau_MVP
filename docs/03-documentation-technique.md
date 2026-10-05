# 3. Documentation technique du MVP

> Compétences couvertes : **C13** (frameworks, plateformes, IA, IoT),
> **C14** (conception de la base de données).

---

## 3.1 Vue d'ensemble

Le MVP met en œuvre la chaîne complète *données → modèle → API → interface*
pour estimer le **risque de pluie** à une date donnée, pour la station SYNOP de
**Montpellier-Fréjorgues (07643, Occitanie — arc méditerranéen)**, zone agricole
à fort enjeu inondation (épisodes méditerranéens / cévenols).

| Étape | Module | Technologie |
|---|---|---|
| Collecte | `src/data_collection.py` | `requests`, `pandas`, `truststore` |
| Stockage | `src/database.py` | SQLite |
| Features | `src/features.py` | `pandas`, `numpy` |
| Entraînement | `src/train.py` | `scikit-learn`, `joblib` |
| Évaluation | `src/evaluate.py` | `scikit-learn` |
| API | `src/api.py` | `FastAPI`, `Uvicorn` |
| Interface | `app/streamlit_app.py` | `Streamlit`, `plotly` |

---

## 3.2 Source de données (C13)

- **Jeu de données (MVP)** : *Données SYNOP essentielles OMM* de Météo-France.
- **Licence** : Licence Ouverte / Open Licence 2.0 (réutilisation libre).
- **Format** : un fichier CSV compressé (`.gz`) par mois, séparateur `;`,
  valeurs manquantes codées `mq`, pas de temps **3 heures**.
- **URL** : `.../Txt/Synop/Archive/synop.AAAAMM.csv.gz`.
- **Variables retenues** : température (`t`), point de rosée (`td`), humidité
  (`u`), pression mer (`pmer`), vent (`ff`, `dd`), précipitations (`rr1`, `rr3`,
  `rr24`).

> Les températures SYNOP sont en **Kelvin** (converties en °C) ; les
> précipitations à valeur négative (`-0.1`, « trace ») sont ramenées à 0.

> **Cible (EdC-01).** Les données SYNOP ouvertes servent de *proxy* pour amorcer
> le MVP. La cible est l'ingestion **temps réel** des **capteurs IoT** déployés
> sur la zone pilote (50 km²), avec une granularité au km² et une fraîcheur
> < 5 min — même schéma de données, source enrichie.

---

## 3.3 Modèle de données (C14)

Deux tables SQLite :

### `observations` (mesures brutes 3 h)

| Colonne | Type | Description |
|---|---|---|
| `station_id` | TEXT | Identifiant station (clé primaire 1/2) |
| `obs_time` | TEXT | Horodatage ISO 8601 UTC (clé primaire 2/2) |
| `t, td, u, pmer, ff, dd` | REAL | Variables météorologiques |
| `rr24, rr_best` | REAL | Précipitations (24 h / meilleur cumul court) |

### `daily` (agrégats quotidiens, prêts pour le modèle)

| Colonne | Type | Description |
|---|---|---|
| `station_id`, `obs_date` | TEXT | Clé primaire composite |
| `precip_mm` | REAL | Cumul quotidien de précipitations |
| `t_mean, t_min, t_max` | REAL | Températures du jour |
| `u_mean, pmer_mean, ff_mean` | REAL | Humidité / pression / vent moyens |
| `is_rainy` | INTEGER | **Cible** : 1 si `precip_mm > 1,0 mm` |

**Choix de conception** : séparation *brut / agrégé* (traçabilité + recalcul
idempotent), clés primaires naturelles (idempotence des `UPSERT`), index sur
`obs_date` (requêtes temporelles). La cible `is_rainy` matérialise la règle
métier (seuil de pluie paramétrable).

---

## 3.4 Pipeline de collecte

```
download_month(year, month)  →  filtre station  →  parse variables
        →  upsert_observations()  →  build_daily()  (agrégation + cible)
```

Caractéristiques : **idempotent** (`ON CONFLICT ... DO UPDATE`), **résilient**
(mois manquant ignoré), **compatible proxy d'entreprise** (`truststore` =
magasin de certificats du système). Volume collecté : **2015–2024, 28 605
observations → 3 653 jours**, dont **13,6 % de jours pluvieux** (climat
méditerranéen sec : classe « pluie » minoritaire).

---

## 3.5 Feature engineering (`features.py`)

Le modèle réalise une **prévision à J+1** : il estime la pluie d'une date à
partir de variables **antérieures** uniquement (pas de fuite de données).

| Groupe | Variables | Rôle |
|---|---|---|
| Saisonnalité | `doy_sin/cos`, `doy_sin2/cos2` | Climatologie (cycle annuel, 2 harmoniques) |
| Persistance | `precip_lag1`, `rained_lag1`, `precip_roll3` | Pluie récente (forte autocorrélation) |
| Dynamique | `pmer_lag1`, `pmer_trend` | Baisse de pression → passage pluvieux |
| État | `u_lag1`, `t_mean_lag1` | Humidité / température de la veille |

À l'inférence, l'API reconstruit ces variables depuis la base. Si l'historique
antérieur est trop ancien (> 7 jours) ou absent, le modèle bascule sur une
**estimation climatologique** (saisonnalité seule + médianes d'entraînement).

---

## 3.6 Modèle et entraînement

- **Split temporel** : entraînement 2015–2022 (2 922 jours), test 2023–2024
  (731 jours) → évaluation de la généralisation dans le temps.
- **Sélection** : validation croisée temporelle (`TimeSeriesSplit`, 5 plis) sur
  le ROC-AUC, entre **régression logistique** (équilibrée) et
  **HistGradientBoosting**.
- **Modèle retenu** : régression logistique (CV ROC-AUC 0,758 vs 0,708).
- **Calibration** : `CalibratedClassifierCV` (sigmoïde) → probabilités fiables.
- **Artefacts** : `models/rain_model.joblib`, `models/metrics.json`.

---

## 3.7 Évaluation et indicateurs qualité (test 2023–2024)

| Indicateur | Seuil 0,5 | Seuil optimal (0,158) | Lecture |
|---|---:|---:|---|
| **ROC-AUC** | **0,743** | 0,743 | Bon pouvoir discriminant (cible ≥ 0,75 quasi atteinte) |
| PR-AUC | 0,331 | 0,331 | vs taux de base 0,129 → nette valeur ajoutée (×2,5) |
| Brier score | 0,101 | 0,101 | Probabilités bien calibrées (bas = mieux) |
| Accuracy | 0,868 | 0,739 | |
| Précision | 0,417 | 0,284 | |
| Rappel | 0,053 | **0,670** | Le seuil optimal privilégie la détection des pluies |
| F1 | 0,094 | **0,399** | |

**Matrice de confusion (seuil optimal)** : VN=475, FP=159, FN=31, VP=63.

> **Interprétation.** Le climat méditerranéen de Montpellier rend la pluie
> **rare** (13 % des jours) : au seuil 0,5, le modèle ne déclenche presque
> jamais l'alerte (rappel 5 %). Pour un usage agricole et de prévention des
> inondations, le **seuil optimal (indice de Youden ≈ 0,16)** est préférable :
> il détecte **67 % des jours pluvieux**, au prix de plus de fausses alertes —
> compromis adapté à la décision d'irrigation/récolte et à la vigilance
> inondation.

### Lien avec les KPIs cibles de l'EdC-01

Le cahier des charges (EdC-01) fixe des cibles produit en **RMSE / MAE**
(quantité de pluie), **taux d'alertes valides > 90 %**, **granularité km²** et
**fraîcheur < 5 min**. Le MVP constitue la **première brique** : il valide la
**prévision d'occurrence** (classification pluie/sec), mesurée par ROC-AUC /
PR-AUC / Brier. La trajectoire vers les cibles EdC-01 :

| Cible EdC-01 | Statut MVP | Prochaine étape |
|---|---|---|
| RMSE / MAE (quantité de pluie, mm) | Occurrence validée (classification) | Ajouter un modèle de **régression** de la lame d'eau |
| Granularité km² | 1 station (ponctuel) | Densifier via **capteurs IoT** + interpolation spatiale |
| Fraîcheur < 5 min | Batch (archive) | Ingestion **temps réel** + ordonnancement |
| Alertes valides > 90 % | Rappel 67 % / précision 28 % | Enrichir les features (radar, modèles numériques), ré-étalonner le seuil |

> Le **Brier score** (0,101) est l'analogue probabiliste du MAE : il mesure déjà
> la qualité de calibration des probabilités, préfigurant le suivi RMSE/MAE sur
> la quantité de pluie.

---

## 3.8 Référence de l'API

Base : `http://127.0.0.1:8000` — documentation interactive : `/docs` (OpenAPI).

| Méthode | Route | Paramètre | Réponse |
|---|---|---|---|
| GET | `/health` | — | état du service + plage de données |
| GET | `/model-info` | — | métriques et métadonnées du modèle |
| GET | `/predict` | `date=YYYY-MM-DD` | risque de pluie |

Exemple :

```bash
curl "http://127.0.0.1:8000/predict?date=2024-07-14"
```

```json
{
  "date": "2024-07-14",
  "station": "Montpellier-Frejorgues",
  "rain_probability": 0.0494,
  "risk_level": "faible",
  "based_on_history": true
}
```

Codes d'erreur : `422` (format de date invalide), `503` (modèle non chargé).

---

## 3.9 Exécution (reproductibilité)

```bash
python -m venv .venv && .venv\Scripts\activate      # Windows
pip install -r requirements.txt

python -m src.data_collection --start 2015 --end 2024   # collecte + agrégats
python -m src.train                                      # entraînement
uvicorn src.api:app --reload                             # API (port 8000)
streamlit run app/streamlit_app.py                       # interface (port 8501)
pytest -q                                                # tests
```

---

## 3.10 Limites et perspectives

- **Portée** : une seule station (MVP). Généralisation multi-régions en P4.
- **Horizon** : prévision à J+1 ; au-delà, repli climatologique.
- **Enrichissements** : variables synoptiques (radar, modèles numériques),
  **capteurs IoT temps réel**, modèles de séries temporelles / apprentissage
  profond, prise en compte explicite de la non-stationnarité climatique
  (ré-entraînement périodique).
- **Industrialisation** : PostgreSQL, conteneurisation, CI/CD, supervision
  (cf. `docs/02-architecture.md`).
