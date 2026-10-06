# 1. Planification du projet — Projet Goutte d'eau

> Le document présente le cadrage, l'organisation et le calendrier du projet. Il reprend les choix de l'étude de cas 1 et précise ce qui est couvert par le MVP.

---

## 1.1 Contexte et cadrage

Le projet vise à mieux anticiper la pluie pour les agriculteurs, les collectivités et les services de secours. La cible à terme s'appuie sur des capteurs IoT et des prévisions plus fines. Le MVP teste d'abord la chaîne de traitement sur les données ouvertes d'une station météo à Toulouse.

Le produit vise des prévisions à 24 h, à l'échelle du km², avec des alertes pour les agriculteurs, les collectivités et les SDIS. Le MVP démontre la chaîne collecte, stockage, modèle, API et interface sur les données de la station Toulouse-Blagnac.

Le commanditaire est la Direction de la prévision de France Météo; le sponsor, la Direction de la transformation digitale. Les autres parties prenantes sont les agriculteurs, les SDIS, les collectivités, les chambres d'agriculture, l'équipe technique, la DSI, le RSSI, la direction financière et le DPO.

### Objectifs produit (SMART, repris de l'EdC-01)

1. Prévoir les précipitations à 24 h et suivre l'erreur avec RMSE et MAE.
2. Viser une maille de 1 km² et des mises à jour toutes les 15 minutes.
3. Mettre à jour les prévisions en moins de 5 minutes après réception des mesures.
4. Atteindre plus de 90 % d'alertes valides et 80 % de satisfaction auprès de 50 agriculteurs testeurs.

### Objectifs techniques du MVP

Le MVP ne vise pas encore ces performances produit. Il vérifie que la chaîne fonctionne, de la collecte à l'interface, sur une classification pluie/sec.

1. Livrer un **MVP fonctionnel** (pipeline données + modèle + API + interface de démonstration).
2. Atteindre un **ROC-AUC ≥ 0,75** sur la prédiction « jour pluvieux / sec » (indicateur technique d'étape).
3. **100 % des données** issues de sources ouvertes et traçables (SYNOP Météo-France, Licence Ouverte), en attendant le déploiement des capteurs IoT.

---

## 1.2 Méthode de gestion de projet retenue (C7)

**Scrum avec des sprints hebdomadaires** est retenu pour ce cadrage de dix semaines. L'EdC-01 compare plusieurs méthodes et retient Scrum, mais ne précise ni Jira ni la durée des sprints. Le dépôt GitHub est l'outil effectivement disponible pour le code et les revues; aucun tableau Jira n'est fourni comme preuve.

- **Sprints de 1 semaine**, avec planification, point d'avancement, revue et rétrospective.
- **Backlog priorisé** (cf. §1.4), structuré par lots BACK / FRONT et conservé dans la documentation du dépôt.
- **Définition of Done (DoD)** : code revu (pull request), testé, documenté,
  déployé en environnement de recette.
- **Gestion des risques** : revue hebdomadaire du registre des risques (§1.8).

### Équipe-projet et rôles

L'EdC-01 énumère chef de projet, ingénieur IoT, data scientists, UX designer et développeurs, sans effectifs, ETP ni coûts. Le MVP logiciel présenté ici mobilise un chef de projet, un data scientist, un développeur données, un développeur API/interface, un UX designer, un profil QA/DevOps et un appui RSSI/DPO selon le tableau de budget. L'ingénierie IoT et l'achat de capteurs sont hors du MVP logiciel et relèvent de la phase ultérieure.

---

## 1.3 WBS — Découpage en lots (Work Breakdown Structure)

```
Projet Goutte d'eau
├── 1. Cadrage & gouvernance
│   ├── 1.1 Note de cadrage, objectifs SMART
│   ├── 1.2 Registre des parties prenantes & des risques
│   └── 1.3 Mise en place des outils collaboratifs (Jira, dépôt Git)
├── 2. Données (C13, C14)
│   ├── 2.1 Sources : SYNOP Météo-France (MVP) + capteurs IoT terrain (cible)
│   ├── 2.2 Pipeline de collecte & d'ingestion (batch MVP → temps réel)
│   └── 2.3 Modèle de données & base SQLite (MVP) / PostgreSQL + PostGIS (cible)
├── 3. Modélisation IA
│   ├── 3.1 Analyse exploratoire (EDA)
│   ├── 3.2 Feature engineering
│   ├── 3.3 Entraînement & sélection de modèle
│   └── 3.4 Évaluation & indicateurs qualité (ROC-AUC puis RMSE/MAE)
├── 4. Architecture & services (C11)
│   ├── 4.1 Diagramme d'architecture & de composants
│   ├── 4.2 API de prédiction (FastAPI)
│   ├── 4.3 Authentification des utilisateurs
│   ├── 4.4 Service de notifications multicanal (SMS, mail, push)
│   └── 4.5 Sécurité & scalabilité
├── 5. Interface utilisateur (C15)
│   ├── 5.1 Maquette & accessibilité (RGAA/WCAG)
│   ├── 5.2 Dashboard (MVP) et interface de démonstration (Streamlit)
│   └── 5.3 Historique / statistiques, carte interactive (lots ultérieurs)
├── 6. Éco-responsabilité (C12)
│   ├── 6.1 Bonnes pratiques Green IT / Green AI
│   └── 6.2 Optimisation de l'hébergement (cloud AWS, cf. EdC-01)
└── 7. Industrialisation
    ├── 7.1 CI/CD, tests, qualité
    ├── 7.2 Déploiement & supervision
    └── 7.3 Documentation & transfert
```

---

## 1.4 Backlog produit (repris de l'EdC-01)

Le MVP couvre les lots prioritaires suivants :

- **Réalisés** : collecte SYNOP (7 j), modèle pluie/sec (20 j), interface Streamlit (10 j) et API REST (7 j).
- **À faire ensuite** : automatisation (7 j), authentification (3 j), notifications (5 j), historique et exports (3 j), application mobile (7 j), carte interactive (5 j).

> Le MVP se concentre sur le **chemin critique de valeur** : recueil des données
> (1), algorithme de prévision (2), exposition par API (7) et visualisation (5).

---

## 1.5 Schéma directeur & calendrier

Le MVP dure **10 semaines** (10 sprints hebdomadaires). Les phases P0 à P3 désignent : P0 cadrage et socle (S1), P1 données et qualité (S2–S3), P2 modèle et services (S4–S7), P3 recette et transfert (S8–S10). Le Gantt, les durées, les contenus et les ressources figurent dans [`diagrams/planning-gantt.md`](diagrams/planning-gantt.md). Les lots d'industrialisation, cloud et IoT sont une suite possible, pas le calendrier ni le budget de ce MVP.

| Sprint | Phase | Durée     | Contenu et résultat attendu                                     | Ressources principales                    |
| ------ | ----- | --------- | --------------------------------------------------------------- | ----------------------------------------- |
| S1     | P0    | 1 semaine | Cadrage, backlog, risques, dépôt et critères d'acceptation      | Chef de projet, développeur API, RSSI/DPO |
| S2     | P1    | 1 semaine | Source SYNOP, schéma SQLite, tests de parsing                   | Data scientist, développeur données       |
| S3     | P1    | 1 semaine | Collecte incrémentale, agrégats, contrôle des données           | Data scientist, développeur données       |
| S4     | P2    | 1 semaine | Analyse exploratoire, protocole de découpage temporel, baseline | Data scientist                            |
| S5     | P2    | 1 semaine | Variables, entraînement comparatif et calibration               | Data scientist, développeur données       |
| S6     | P2    | 1 semaine | Validation, choix du seuil, métriques et artefacts              | Data scientist, QA/DevOps                 |
| S7     | P2    | 1 semaine | API typée, prédiction unitaire et groupée                       | Développeur API/interface, data scientist |
| S8     | P3    | 1 semaine | Interface de démonstration et revue d'accessibilité             | Développeur API/interface, UX designer    |
| S9     | P3    | 1 semaine | Tests, CI, documentation, export des données et diagrammes      | QA/DevOps, développeurs, chef de projet   |
| S10    | P3    | 1 semaine | Recette, indicateurs, bilan, présentation et transfert          | Équipe MVP, chef de projet                |

---

## 1.6 Outils de travail collaboratif

Le dépôt GitHub héberge le code et la documentation. Le workflow du dépôt exécute les tests avec GitHub Actions. Aucun espace Jira, Teams, Mattermost ou Nextcloud n'est fourni dans les éléments vérifiables; ces outils ne sont donc pas présentés comme paramétrés. La protection de `main` est une configuration à activer dans les réglages du dépôt, pas une preuve présente dans le code.

Pour matérialiser C8, les tickets doivent être créés dans GitHub Projects (ou l'outil réellement retenu), liés aux PR et accompagnés d'une capture du tableau. Cette preuve d'usage reste à fournir manuellement.

---

## 1.7 Budget prévisionnel

Le budget du MVP est dérivé des 10 semaines de planning ci-dessus. Les TJM sont des hypothèses de chiffrage, pas des tarifs présents dans l'EdC-01 ni des dépenses réellement engagées.

| Rôle                          | ETP moyen sur 10 semaines | Jours-personnes | TJM HT |      Coût HT |
| ----------------------------- | ------------------------: | --------------: | -----: | -----------: |
| Chef de projet                |                       0,2 |              10 |  600 € |      6 000 € |
| Data scientist                |                       0,8 |              40 |  600 € |     24 000 € |
| Développeur données           |                       0,8 |              40 |  550 € |     22 000 € |
| Développeur API/interface     |                       0,6 |              30 |  550 € |     16 500 € |
| UX designer                   |                       0,2 |              10 |  500 € |      5 000 € |
| QA / DevOps                   |                       0,3 |              15 |  500 € |      7 500 € |
| Appui RSSI / DPO              |                       0,1 |               5 |  600 € |      3 000 € |
| **Total ressources humaines** |                   **3,0** |         **150** |        | **84 000 €** |

| Poste complémentaire MVP | Hypothèse                                                              | Coût budgété |
| ------------------------ | ---------------------------------------------------------------------- | -----------: |
| Cloud                    | Exécution locale du MVP; aucun hébergement cloud déployé               |          0 € |
| Licences                 | Dépendances open source; pas de licence commerciale identifiée         |          0 € |
| Capteurs IoT             | Non achetés ni déployés dans le MVP; lot post-MVP à chiffrer sur devis |          0 € |
| **Total MVP estimatif**  | **84 k€ RH + coûts directs réellement retenus**                        | **84 000 €** |

Les montants de **147 k€**, **550 k€ annuels**, **50 k€ de capteurs**, **8 k€ de cloud** et **5 k€ de licences** figurant dans une version antérieure d'EdC-02 ne sont pas justifiés par le PDF EdC-01 fourni : ce dernier présente des catégories de dépenses, des rôles, un backlog et une rubrique Gantt, sans ces montants ni tarifs. Ils sont donc retirés et ne sont pas attribués à EdC-01. Les coûts de déploiement cloud et IoT resteront à chiffrer après choix du dimensionnement et obtention de devis.

---

## 1.8 Registre des risques

- **Données SYNOP incomplètes** : nettoyer, imputer et contrôler les relevés.
- **Peu de jours pluvieux (~22 %)** : suivre le rappel et la PR-AUC, puis ajuster le seuil.
- **Retard IoT** : continuer avec les données ouvertes jusqu'au déploiement.
- **Dérive climatique** : surveiller les résultats et réentraîner le modèle si nécessaire.
- **Dépendance à Météo-France** : conserver une copie locale des données.
- **Dette technique du MVP** : prévoir une reprise avant l'industrialisation.

---

## 1.9 Indicateurs de pilotage

- **Avancement** : vélocité des sprints, burndown chart (Jira).
- **Qualité produit (cible EdC-01)** : RMSE/MAE (quantité de pluie), taux
  d'alertes valides (> 90 %), satisfaction panel (≥ 80 %), fraîcheur (< 5 min).
- **Qualité produit (MVP, étape)** : ROC-AUC, PR-AUC, Brier score
  (cf. `docs/03-documentation-technique.md`).
- **Qualité logicielle** : couverture de tests, taux de PR revues, temps de build CI.
- **Éco-responsabilité** : estimation de l'empreinte (kWh / gCO₂e) du pipeline.
