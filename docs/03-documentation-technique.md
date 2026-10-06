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
- **Variables conservées en brut** : température, point de rosée, humidité, pression, vent et précipitations (`rr1`, `rr3`, `rr24`) pour la traçabilité et le recalcul des agrégats. Le modèle n'utilise qu'un sous-ensemble explicite décrit en §3.5.

> Les températures SYNOP sont en Kelvin et sont converties en °C. Les précipitations négatives (`-0.1`, traces) sont ramenées à 0.

Les données SYNOP servent de point de départ. L'ingestion de capteurs IoT sur une zone pilote de 50 km² reste une évolution prévue, avec une maille visée de 1 km² et une mise à jour en moins de 5 minutes.

---

## 3.3 Modèle de données

Deux tables SQLite :

### `observations` (mesures brutes 3 h)

Cette table contient l'identifiant de station et l'heure UTC (clé primaire composée), les variables météo `t`, `td`, `u`, `pmer`, `ff`, `dd`, ainsi que les précipitations `rr24` et `rr_best`.

### `daily` (agrégats quotidiens, prêts pour le modèle)

Cette table utilise la station et la date comme clé. Elle stocke le cumul de pluie, les températures minimale/moyenne/maximale, l'humidité, la pression et le vent moyens, ainsi que `n_observations` et `n_precip_reports` pour décrire la couverture quotidienne. `is_rainy` n'est calculé que si les huit rapports pluie attendus sont présents et que `precip_mm` dépasse le seuil de 1 mm; un jour sous-couvert conserve son cumul partiel à titre d'information, mais sa cible reste inconnue (`NULL`).

La séparation entre mesures brutes et agrégats permet de recalculer les données quotidiennes. Les clés naturelles rendent les nouvelles collectes idempotentes; les mois déjà présents sont désormais ignorés au téléchargement, sauf option `--refresh`.

Le jeu d'entraînement est la matrice de variables produite par `build_feature_frame` et sa cible `is_rainy`, pas l'ensemble des colonnes de stockage. Les champs `td`, `dd`, `rr24`, `t_min`, `t_max` et `ff_mean` sont conservés dans les tables source/agrégat pour la traçabilité ou des évolutions, mais ne sont pas des entrées du modèle actuel.

---

## 3.4 Pipeline de collecte

```
download_month(year, month)  →  filtre station  →  parse variables
        →  upsert_observations()  →  build_daily()  (agrégation + cible)
```

La collecte peut être relancée sans créer de doublons (`ON CONFLICT ... DO UPDATE`) et saute les mois déjà stockés; `--refresh` force leur nouvelle lecture. Un mois indisponible est ignoré. `truststore` est une dépendance facultative de l'environnement proxy Windows, pas une dépendance générale requise par le projet. La base locale couvre 2015–2024 : 29 181 observations regroupées en 3 653 jours; après exclusion des 90 jours sous-couverts, 806 des 3 563 jours étiquetés sont classés pluvieux (22,6 %).

Le contrôle sur la base locale retrouve **90 jours avec moins de huit rapports pluie** et **29 jours avec moins de huit observations SYNOP au total**. Les 90 cibles sous-couvertes restent `NULL` et ne sont ni des jours secs ni des jours pluvieux. Les lignes qui suivent immédiatement une journée sous-couverte sont aussi exclues du modèle tant que leurs retards pluie ne sont pas complets. Le seuil de huit rapports est un indicateur de couverture fondé sur la cadence SYNOP de trois heures, pas une garantie que le cumul reconstitué correspond à un pluviomètre quotidien de référence; les sommes de `rr1`/`rr3` restent des estimations.

---

## 3.5 Feature engineering (`features.py`)

Le modèle estime la pluie du lendemain à partir des jours précédents. Les variables du jour prédit ne sont donc pas utilisées.

- **Saisonnalité** : cycle annuel (`doy_sin/cos` et deuxième harmonique).
- **Pluie récente** : cumul et présence de pluie la veille, cumul glissant sur trois jours.
- **Pression** : valeur de la veille et tendance.
- **Conditions de la veille** : humidité et température moyenne.

L'API reconstruit les variables depuis la base. Les antécédents observés ne sont utilisés que si le dernier jour de données est exactement la veille de la date cible; sinon, elle utilise une estimation saisonnière et les médianes calculées à l'entraînement. Une date future distante n'est donc pas présentée comme un J+1 fondé sur des relevés vieux de plusieurs jours.

---

## 3.6 Modèle et entraînement

- **Découpage** : données antérieures à 2023 pour le développement, test final sur 2023–2024. Après exclusion des jours sous-couverts et de leurs retards incomplets, il reste **2 742 lignes d'entraînement** et **629 lignes de test**. L'année 2022 est réservée à la sélection du seuil; la validation croisée de sélection du modèle est limitée aux années antérieures.
- **Comparaison** : régression logistique et `HistGradientBoosting`, avec `TimeSeriesSplit` en 5 plis sur la portion d'ajustement.
- **Résultat** : la régression logistique est retenue (ROC-AUC moyen CV de 0,7411, contre 0,7203).
- **Calibration** : sigmoïde avec `CalibratedClassifierCV`.
- **Baselines** : probabilité constante égale au taux de pluie d'entraînement, et persistance « pluie la veille »; leurs Brier sur test sont respectivement 0,1882 et 0,2957.
- **Empreinte d'entraînement** : CodeCarbon 3.3.1 estime cette exécution locale à **0,0027 gCO₂e**. Valeur issue d'un modèle logiciel CPU/RAM et d'une intensité électrique détectée, pas d'un compteur électrique; le résultat dépend de la machine et de son environnement.
- **Fichiers produits** : `models/rain_model.joblib` et `models/metrics.json`.

---

## 3.7 Évaluation et indicateurs qualité (test 2023–2024)

Le ROC-AUC vaut **0,7664**, la PR-AUC **0,5043** (taux de base : 0,2496) et le Brier score **0,1601**. Le seuil **0,2124** est maximisé sur la validation chronologique de 2022 puis gelé avant le test. Sur le test, au seuil de 0,5, accuracy, précision, rappel et F1 valent 0,7583, 0,5490, 0,1783 et 0,2692. Au seuil fixé par validation, ces valeurs sont 0,6963, 0,4366, 0,7452 et 0,5506.

**Matrice de confusion au seuil fixé par validation** : VN=321, FP=151, FN=40, VP=117.

Au seuil de 0,5, le rappel est faible (0,1783). Le seuil choisi sur validation détecte 74,5 % des jours pluvieux du test, mais seulement 43,7 % des alertes émises sont correctes. L'indicateur ne satisfait donc pas l'objectif produit de plus de 90 % d'alertes valides.

| Indicateur qualité        | Objectif                                 | Résultat test                                          | Statut                    |
| ------------------------- | ---------------------------------------- | ------------------------------------------------------ | ------------------------- |
| ROC-AUC                   | ≥ 0,75 (objectif technique MVP)          | 0,7664                                                 | Atteint                   |
| Brier                     | Inférieur à la baseline taux de base     | 0,1601 contre 0,1882                                   | Atteint                   |
| PR-AUC                    | Suivi informatif; taux de base 0,2496    | 0,5043                                                 | Mesuré, cible non définie |
| Précision des alertes     | > 90 % (objectif EdC-01)                 | 43,7 % au seuil de validation                          | Non atteint               |
| Satisfaction utilisateurs | ≥ 80 % auprès de 50 testeurs (EdC-01)    | Non mesurée; panel non constitué                       | Non mesuré                |
| RMSE / MAE du cumul       | À définir pour une prévision de quantité | Non calculables pour le classifieur actuel             | Hors périmètre MVP        |
| Fraîcheur des prévisions  | Calcul < 5 min après réception (EdC-01)  | Chaîne batch historique; cible temps réel non déployée | Non démontré              |

### Lien avec les KPIs cibles de l'EdC-01

Le MVP traite l'occurrence de pluie, pas encore la quantité. Il ne satisfait donc pas les objectifs de maille, de fraîcheur ou de fiabilité des alertes définis dans le cahier des charges.

- **Quantité de pluie (RMSE/MAE)** : le MVP classe les jours; une régression reste à développer.
- **Maille de 1 km²** : le MVP couvre une station; il faudra ajouter des capteurs et une méthode d'interpolation.
- **Fraîcheur sous 5 min** : les données sont traitées en batch; une ingestion temps réel est nécessaire.
- **Alertes valides à plus de 90 %** : la précision mesurée est de 47 % au seuil retenu; il faudra enrichir les données et réévaluer le seuil.

Le Brier score mesure la qualité des probabilités d'occurrence. Il ne remplace pas le RMSE ou le MAE sur les quantités de pluie.

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
	"region": "Occitanie",
	"rain_probability": 0.1517,
	"risk_level": "faible",
	"threshold_mm": 1.0,
	"alert_probability_threshold": 0.2124,
	"based_on_history": true,
	"note": "Prévision fondée sur les antécédents météorologiques observés."
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
