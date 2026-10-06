# Gantt du MVP

Le calendrier est un **cadrage relatif** de dix semaines. La date de démarrage n'étant pas fournie, le 12 octobre 2026 sert uniquement de modèle.

```mermaid
gantt
    title Projet Goutte d'eau — MVP (10 semaines)
    dateFormat YYYY-MM-DD
    axisFormat S%V
    excludes weekends

    section P0 — Cadrage et socle
    S1 Cadrage, backlog, dépôt et critères :p0, 2026-10-12, 1w

    section P1 — Données et qualité
    S2 Source, schéma SQLite et parsing :p1a, after p0, 1w
    S3 Collecte, agrégats et contrôles :p1b, after p1a, 1w

    section P2 — Modèle et services
    S4 EDA, split temporel et baseline :p2a, after p1b, 1w
    S5 Features, entraînement et calibration :p2b, after p2a, 1w
    S6 Validation, seuil et métriques :p2c, after p2b, 1w
    S7 API et contrat de réponse :p2d, after p2c, 1w

    section P3 — Recette et transfert
    S8 Interface et revue d'accessibilité :p3a, after p2d, 1w
    S9 Tests, CI, docs et artefacts :p3b, after p3a, 1w
    S10 Recette, bilan et transfert :p3c, after p3b, 1w
```

Les ressources prévues par sprint sont détaillées dans [`../01-planification.md`](../01-planification.md). Les capteurs IoT, l'hébergement cloud et les fonctions d'industrialisation sont hors de ce Gantt MVP.
