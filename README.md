# 🚀 Démarrage rapide

```bash
# 1. Environnement
python -m venv .venv
.venv\Scripts\activate          # Windows  (source .venv/bin/activate sous Linux/macOS)
pip install -r dependencies_versions.txt

# 2. Collecte des données SYNOP Météo-France (+ agrégats quotidiens)
python -m src.data_collection --start 2015 --end 2024

# 3. Entraînement + évaluation du modèle
python -m src.train

# 4. API de prédiction (http://127.0.0.1:8000/docs)
uvicorn src.api:app --reload

# 5. Interface de démonstration (http://127.0.0.1:8501)
streamlit run app/streamlit_app.py

# Tests
pytest -q
```

---

## 🧩 Fonctionnalités du MVP

- **Collecte** des données SYNOP essentielles OMM (Licence Ouverte) et stockage **SQLite**.
- **Modèle** de prévision de pluie à J+1 (régression logistique calibrée) :
  saisonnalité + antécédents météorologiques.
- **API REST FastAPI** : risque de pluie en fonction d'une date (`/predict`).
- **Interface Streamlit** accessible : jauge de risque, courbe sur 14 jours, indicateurs qualité.
- **Tests** automatisés (pytest) et **documentation** complète.

### Résultats du modèle (test 2023–2024)

| Indicateur                       | Valeur                     |
| -------------------------------- | -------------------------- |
| ROC-AUC                          | **0,773**                  |
| PR-AUC                           | 0,501 (taux de base 0,243) |
| Brier score                      | 0,156                      |
| F1 / Rappel (seuil optimal 0,22) | 0,575 / **0,751**          |

---

## 🗂️ Structure du dépôt

```
goutte-deau-mvp/
├── config.py                 # Paramètres (station, période, chemins)
├── dependencies_versions.txt
├── src/
│   ├── database.py           # Schéma & accès SQLite (C14)
│   ├── data_collection.py    # Collecte SYNOP → base (C13)
│   ├── features.py           # Feature engineering
│   ├── train.py              # Entraînement & sélection de modèle
│   ├── evaluate.py           # Métriques & indicateurs qualité
│   └── api.py                # API FastAPI (C11)
├── app/
│   └── streamlit_app.py      # Interface de démonstration (C15)
├── tests/test_mvp.py         # Tests pytest
├── scripts/smoke_api.py      # Test de fumée de l'API
└── docs/
    ├── 01-planification.md         # Planning, budget, schéma directeur (C7–C10)
    ├── 02-architecture.md          # Diagrammes architecture & composants (C11, C13)
    ├── 03-documentation-technique.md (C13, C14)
    └── 04-eco-responsabilite-accessibilite.md # Green IT, hébergement responsable & RGAA/WCAG (C12, C15)
```

---

## 📄 Document explicatif du travail effectué

Le projet a été mené dans l'ordre suivant :

1. **Cadrage & planification** — reprise de l'EdC-01 : méthode **Scrum / Jira**,
   équipe-projet, backlog priorisé, WBS, Gantt, schéma directeur, budget
   (**MVP ≈ 147 k€**, 550 k€ annuels), outils collaboratifs.
   → [`docs/01-planification.md`](docs/01-planification.md).
2. **Architecture** — diagrammes d'architecture et de composants (sources
   SYNOP + capteurs IoT cible, notifications multicanal, 3 profils
   utilisateurs), contrat d'API, sécurité/scalabilité.
   → [`docs/02-architecture.md`](docs/02-architecture.md).
3. **Données** — identification de la source pertinente (SYNOP Météo-France),
   collecte idempotente et stockage SQLite (29 181 observations → 3 653 jours).
4. **Modèle** — prévision de pluie à J+1 (saisonnalité + persistance + pression),
   sélection par validation croisée temporelle, calibration des probabilités.
5. **Évaluation** — ROC-AUC, PR-AUC, Brier, matrice de confusion, seuil optimal,
   et pont vers les KPIs cibles RMSE/MAE de l'EdC-01.
6. **API** — FastAPI exposant `/predict`, `/health`, `/model-info` (OpenAPI).
7. **Interface** — démonstration Streamlit accessible avec indicateurs qualité.
8. **Documentation** — technique, éco-responsabilité, accessibilité, tests.

Les choix et limites sont détaillés dans
[`docs/03-documentation-technique.md`](docs/03-documentation-technique.md).

---

## ✅ Correspondance avec les compétences évaluées

| Compétence                                       | Où                                                                    |
| ------------------------------------------------ | --------------------------------------------------------------------- |
| **C7** Organiser le travail de l'équipe-projet   | `docs/01-planification.md`                                            |
| **C8** Outils de travail collaboratif            | `docs/01-planification.md`                                            |
| **C9** Budget prévisionnel                       | `docs/01-planification.md`                                            |
| **C10** Schéma directeur / calendrier            | `docs/01-planification.md`                                            |
| **C11** Architecture fonctionnelle               | `docs/02-architecture.md`, `src/api.py`                               |
| **C12** Éco-conception / hébergement responsable | `docs/04-eco-responsabilite-accessibilite.md`                         |
| **C13** Frameworks, plateformes, IA, IoT         | `src/`, `docs/03-documentation-technique.md`                          |
| **C14** Conception de la base de données         | `src/database.py`, `docs/03-documentation-technique.md`               |
| **C15** Interface accessible                     | `app/streamlit_app.py`, `docs/04-eco-responsabilite-accessibilite.md` |

---

## 📜 Données & licence

Données : **SYNOP essentielles OMM** — Météo-France, **Licence Ouverte / Open
Licence 2.0**. Code du projet : usage pédagogique.
