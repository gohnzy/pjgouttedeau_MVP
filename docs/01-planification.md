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

**Scrum avec Jira**, comme prévu dans l'étude de cas 1. Les essais sur les données et le modèle peuvent faire évoluer les priorités; des sprints courts permettent de revoir le travail régulièrement.

- **Sprints de 2 semaines**, cérémonies : planning, daily stand-up (15 min),
  revue de sprint, rétrospective.
- **Backlog priorisé** (cf. §1.4) géré dans **Jira**, découpage en _epics_
  BACK / FRONT.
- **Définition of Done (DoD)** : code revu (pull request), testé, documenté,
  déployé en environnement de recette.
- **Gestion des risques** : revue hebdomadaire du registre des risques (§1.8).

### Équipe-projet et rôles (reprise de l'EdC-01)

L'EdC-01 a dimensionné l'équipe suivante (coûts annuels chargés indiqués au
budget, §1.6). Les ETP ci-dessous correspondent à la **phase MVP**.

L'équipe prévue pour le MVP comprend un chef de projet (0,6 ETP), un ingénieur IoT pour le déploiement, deux Data Scientists, deux développeurs et un UX designer (0,5 ETP). Le RSSI et le DPO interviennent en appui. Les Data Scientists et développeurs construisent la chaîne logicielle; l'ingénieur IoT prépare le pilote toulousain.

> Le MVP mobilise prioritairement les **Data Scientists** et **Développeurs**
> (chaîne données → modèle → API → interface) ; l'**Ingénieur IoT** prépare le
> déploiement des capteurs sur la zone pilote de Toulouse.

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

Le MVP couvre les phases P0 à P3, sur dix semaines : cadrage en S1, données et analyse en S2–S4, modèle/API/interface en S5–S8, puis recette et documentation en S9–S10. L'industrialisation (automatisation, authentification, notifications, cloud et IoT) est prévue en S11–S20. La généralisation à plusieurs zones vient ensuite.

---

## 1.6 Outils de travail collaboratif

Les outils prévus sont Jira pour le backlog, GitHub ou GitLab pour le code et les revues, et leurs outils CI pour lancer les tests. La documentation reste dans le dépôt; Teams ou Mattermost servent aux échanges, et Nextcloud au partage documentaire. La branche `main` est protégée : pas de push direct, revue et CI verte requises.

**Paramétrage clé** : protection de la branche `main` (pas de push direct,
revue obligatoire, CI verte requise), synchronisation Jira ↔ dépôt Git
(références de tickets dans les commits), conventions de commits, droits
d'accès par rôle (principe du moindre privilège).

---

## 1.7 Budget prévisionnel

Le budget reprend celui établi dans l'EdC-01 : un **budget annuel de
fonctionnement de 550 000 €** pour le projet complet, dont un **budget MVP de
147 000 €**.

### Budget annuel du projet complet (rappel EdC-01)

Le budget annuel prévisionnel est de **550 000 €** : 410 000 € pour l'équipe, 95 000 € pour le cloud, les capteurs et les licences, et 45 000 € pour la formation, la communication, la maintenance et l'énergie.

### Budget du MVP (147 000 €)

Le MVP mobilise une partie de l'équipe sur ~3 mois et déploie la zone pilote
(Toulouse, 50 km²).

Le budget MVP est estimé à **147 000 €** : environ 84 000 € de ressources humaines, 50 000 € pour les capteurs, 8 000 € de cloud et 5 000 € de licences et outils.

> **Note MVP pédagogique.** La brique logicielle réalisée dans ce dépôt
> (collecte SYNOP, modèle, API, interface) n'engage **aucun coût réel** :
> données en Licence Ouverte, exécution locale, outils open-source. Les montants
> ci-dessus correspondent au budget _projet_ tel que cadré en EdC-01, pour
> conserver la cohérence budgétaire entre les deux études de cas.

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
