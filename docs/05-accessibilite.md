# 5. Accessibilité de l'interface

> Compétence couverte : **C15** (interfaces utilisateurs accessibles, notamment
> pour les personnes en situation de handicap — sécurité, ergonomie,
> navigabilité, compatibilité écrans/navigateurs).

Ce document pose les **règles d'accessibilité** à respecter pour la réalisation
d'une interface complète dans une phase ultérieure, et décrit ce qui est déjà
appliqué dans l'interface de démonstration (Streamlit).

---

## 5.1 Cadre de référence

- **RGAA** (Référentiel Général d'Amélioration de l'Accessibilité) — obligation
  légale en France pour le secteur public (loi de 2005, article 47).
- **WCAG 2.1** (niveau **AA** visé) — standard international, 4 principes :
  **Perceptible, Utilisable, Compréhensible, Robuste (POUR)**.

> **Diversité des usages (personas EdC-01).** L'interface doit rester accessible
> aux **trois profils** du cahier des charges, dans des contextes variés :
> *Teddy* (agriculteur, en extérieur, forte luminosité, usage mobile),
> *Chantale* (SDIS, décision rapide sous stress → lisibilité et hiérarchie
> claires) et *Frédérick* (urbaniste, consultation d'historiques). Les
> **alertes multicanal** (SMS, mail, notification push) doivent elles aussi être
> accessibles : texte clair, pas d'information portée par la seule couleur,
> contenu compréhensible hors application.

---

## 5.2 Règles à respecter (par principe POUR)

### Perceptible
- **Contrastes** : ratio ≥ **4,5:1** (texte normal), ≥ 3:1 (texte large / éléments graphiques).
- **L'information ne repose jamais sur la seule couleur** : associer texte, icône et valeur (ex. niveau de risque = libellé + icône + pourcentage).
- **Alternatives textuelles** : `alt` pour les images, description textuelle des graphiques (jauge, courbe).
- **Contenu redimensionnable** jusqu'à 200 % sans perte d'information.

### Utilisable
- **Navigation complète au clavier** (tabulation logique, pas de piège clavier).
- **Focus visible** sur tous les éléments interactifs.
- **Cibles tactiles** suffisamment grandes (≥ 24×24 px).
- Pas de contenu clignotant susceptible de provoquer des crises (seuil des 3 flashs/s).

### Compréhensible
- **Langue de la page déclarée** (`lang="fr"`).
- **Libellés explicites** et messages d'erreur clairs (ex. « Format de date invalide (attendu AAAA-MM-JJ) »).
- **Cohérence** de la navigation et des composants.
- Unités et formats explicités (pourcentage, mm, date).

### Robuste
- **HTML sémantique** et attributs **ARIA** pertinents (rôles, labels).
- **Compatibilité** multi-navigateurs (Chrome, Firefox, Edge, Safari) et lecteurs d'écran (NVDA, JAWS, VoiceOver).
- Code **valide** (W3C).

---

## 5.3 Application dans l'interface de démonstration

| Règle | Mise en œuvre (Streamlit) |
|---|---|
| Information non portée par la seule couleur | Niveau de risque = **texte + icône + valeur %** (jauge). |
| Contrastes | Palette à contraste élevé (verts/oranges foncés sur fond clair). |
| Libellés explicites | « Choisissez une date », bouton « Estimer le risque », bulles d'aide. |
| Messages d'erreur clairs | Erreur API et format de date explicités. |
| Structure sémantique | Titres hiérarchisés (`h1`/`h2`), sections, `page_title`. |
| Unités explicites | Probabilité en %, seuil en mm, dates ISO. |
| Navigation clavier | Composants Streamlit natifs focusables au clavier. |

> Streamlit facilite une base accessible mais **ne garantit pas** le niveau AA :
> une interface de production devra être auditée (grille RGAA, tests lecteurs
> d'écran) et, si nécessaire, développée en front dédié (React + composants
> accessibles type Radix/MUI, ou **DSFR** — Système de Design de l'État).

---

## 5.4 Sécurité & ergonomie côté interface

- **Sécurité** : communications **HTTPS**, validation des entrées côté API,
  aucune donnée personnelle manipulée (RGPD *by design*), messages d'erreur
  non divulgants.
- **Ergonomie** : parcours minimal (1 date → 1 résultat), feedback immédiat
  (jauge + libellé), indicateurs qualité accessibles en détail repliable.
- **Navigabilité** : structure claire, actions principales mises en avant,
  cohérence visuelle.

---

## 5.5 Plan de vérification (phase ultérieure)

1. Audit **RGAA** (échantillon de pages, grille des 106 critères).
2. Tests **lecteurs d'écran** (NVDA/VoiceOver) et **navigation clavier seule**.
3. Vérification automatique (axe-core, Lighthouse, Wave) + tests manuels.
4. Tests multi-navigateurs et multi-résolutions (responsive).
5. **Déclaration d'accessibilité** et schéma pluriannuel de mise en conformité.
