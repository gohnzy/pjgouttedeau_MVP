# 3. Documentation technique du MVP

> Ce document résume les données, le modèle et les commandes utiles pour lancer le MVP.

---

## 3.1 Vue d'ensemble

Le MVP estime le risque de pluie pour une date donnée à partir des relevés SYNOP de Toulouse-Blagnac (07630). La chaîne comprend la collecte, le stockage, l'entraînement, l'API et une interface de démonstration.

Les principaux modules sont `src/data_collection.py` pour la collecte, `src/database.py` pour SQLite, `src/features.py` pour les variables, `src/train.py` et `src/evaluate.py` pour le modèle, `src/api.py` pour l'API et `app/streamlit_app.py` pour l'interface.

---

## 3.2 Source de données

- **Source** : données SYNOP essentielles de Météo-France, sous Licence Ouverte 2.0.
- **Format** : fichiers CSV compressés par mois, séparateur `;`, valeurs manquantes notées `mq`, relevés toutes les 3 heures.
- **URL** : `.../Txt/Synop/Archive/synop.AAAAMM.csv.gz`.
- **Variables utilisées** : température, point de rosée, humidité, pression, vent et précipitations (`rr1`, `rr3`, `rr24`).

> Les températures SYNOP sont en Kelvin et sont converties en °C. Les précipitations négatives (`-0.1`, traces) sont ramenées à 0.

Les données SYNOP servent de point de départ. L'ingestion de capteurs IoT sur une zone pilote de 50 km² reste une évolution prévue, avec une maille visée de 1 km² et une mise à jour en moins de 5 minutes.

---

## 3.3 Modèle de données

Deux tables SQLite :

### `observations` (mesures brutes 3 h)

Cette table contient l'identifiant de station et l'heure UTC (clé primaire composée), les variables météo `t`, `td`, `u`, `pmer`, `ff`, `dd`, ainsi que les précipitations `rr24` et `rr_best`.

### `daily` (agrégats quotidiens, prêts pour le modèle)

Cette table utilise la station et la date comme clé. Elle stocke le cumul de pluie, les températures minimale/moyenne/maximale, l'humidité, la pression et le vent moyens. `is_rainy` vaut 1 si `precip_mm` dépasse 1 mm.

La séparation entre mesures brutes et agrégats permet de recalculer les données quotidiennes. Les clés naturelles rendent les nouvelles collectes idempotentes.

---

## 3.4 Pipeline de collecte

```
download_month(year, month)  →  filtre station  →  parse variables
        →  upsert_observations()  →  build_daily()  (agrégation + cible)
```

La collecte peut être relancée sans créer de doublons (`ON CONFLICT ... DO UPDATE`). Un mois indisponible est ignoré. `truststore` permet d'utiliser le magasin de certificats du système. Le jeu utilisé couvre 2015–2024 : 29 181 observations regroupées en 3 653 jours, dont environ 22,5 % de jours pluvieux.

---

## 3.5 Feature engineering (`features.py`)

Le modèle estime la pluie du lendemain à partir des jours précédents. Les variables du jour prédit ne sont donc pas utilisées.

- **Saisonnalité** : cycle annuel (`doy_sin/cos` et deuxième harmonique).
- **Pluie récente** : cumul et présence de pluie la veille, cumul glissant sur trois jours.
- **Pression** : valeur de la veille et tendance.
- **Conditions de la veille** : humidité et température moyenne.

L'API reconstruit les variables depuis la base. Si l'historique manque ou date de plus de 7 jours, elle utilise une estimation saisonnière et les médianes calculées à l'entraînement.

---

## 3.6 Modèle et entraînement

- **Découpage** : entraînement sur 2015–2022 (2 922 jours), test sur 2023–2024 (731 jours).
- **Comparaison** : régression logistique et `HistGradientBoosting`, avec `TimeSeriesSplit` en 5 plis.
- **Résultat** : la régression logistique est retenue (ROC-AUC moyen de 0,752, contre 0,730).
- **Calibration** : sigmoïde avec `CalibratedClassifierCV`.
- **Fichiers produits** : `models/rain_model.joblib` et `models/metrics.json`.

---

## 3.7 Évaluation et indicateurs qualité (test 2023–2024)

Le ROC-AUC vaut **0,773**, la PR-AUC **0,501** (taux de base : 0,243) et le Brier score **0,156**. Au seuil de 0,5, accuracy, précision, rappel et F1 sont respectivement de 0,767, 0,559, 0,186 et 0,280. Au seuil de 0,222, ils sont de 0,729, 0,465, 0,751 et 0,575.

**Matrice de confusion (seuil optimal)** : VN=398, FP=153, FN=44, VP=133.

> **Interprétation.** Au seuil 0,5, le modèle est prudent (peu de fausses
> Le rappel est faible au seuil de 0,5. Un seuil proche de 0,22 détecte environ 75 % des jours pluvieux, mais entraîne davantage de fausses alertes. Ce compromis doit être revu avant tout usage opérationnel.

### Lien avec les KPIs cibles de l'EdC-01

Le MVP traite l'occurrence de pluie, pas encore la quantité. Il ne satisfait donc pas les objectifs de maille, de fraîcheur ou de fiabilité des alertes définis dans le cahier des charges.

- **Quantité de pluie (RMSE/MAE)** : le MVP classe les jours; une régression reste à développer.
- **Maille de 1 km²** : le MVP couvre une station; il faudra ajouter des capteurs et une méthode d'interpolation.
- **Fraîcheur sous 5 min** : les données sont traitées en batch; une ingestion temps réel est nécessaire.
- **Alertes valides à plus de 90 %** : la précision mesurée est de 47 % au seuil retenu; il faudra enrichir les données et réévaluer le seuil.

> Le **Brier score** (0,156) est l'analogue probabiliste du MAE : il mesure déjà
> Le Brier score mesure la qualité des probabilités; il ne remplace pas le RMSE ou le MAE sur les quantités de pluie.

---

## 3.8 Référence de l'API

Base : `http://127.0.0.1:8000` — documentation interactive : `/docs` (OpenAPI).

Les routes principales sont `GET /health` (état du service et plage de données), `GET /model-info` (métriques et métadonnées) et `GET /predict?date=YYYY-MM-DD` (risque pour une date).

Exemple :

```bash
curl "http://127.0.0.1:8000/predict?date=2024-07-14"
```

```json
{
	"date": "2024-07-14",
	"station": "Toulouse-Blagnac",
	"rain_probability": 0.1517,
	"risk_level": "faible",
	"based_on_history": true
}
```

Codes d'erreur : `422` (format de date invalide), `503` (modèle non chargé).

---

## 3.9 Exécution (reproductibilité)

```bash
python -m venv .venv && .venv\Scripts\activate      # Windows
pip install -r dependencies_versions.txt

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
