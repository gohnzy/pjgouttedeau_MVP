# 4. Éco-responsabilité et hébergement responsable

> Compétence couverte : **C12** (architectures numériques optimisant les
> ressources, réduisant la consommation d'énergie, favorisant des technologies
> respectueuses de l'environnement).

---

## 4.1 Enjeux

Le numérique représente environ **3 à 4 % des émissions mondiales de gaz à
effet de serre**, en croissance rapide. Un projet d'IA doit donc maîtriser son
empreinte, d'autant plus pour un service public (France Météo) à vocation
d'exemplarité. La démarche s'appuie sur le **Référentiel Général d'Écoconception
de Services Numériques (RGESN)** et les principes du **Green IT / Green AI**.

---

## 4.2 Bonnes pratiques appliquées dans le MVP

| Domaine | Bonne pratique | Mise en œuvre dans le projet |
|---|---|---|
| **Sobriété des données** | Ne collecter que l'utile | Une station, variables sélectionnées, agrégation quotidienne. |
| **Sobriété du modèle** | Privilégier un modèle simple et frugal | Régression logistique (entraînement en secondes, CPU seul, pas de GPU). |
| **Frugalité de calcul** | Éviter le sur-entraînement coûteux | Nombre d'itérations borné, pas de recherche d'hyperparamètres massive. |
| **Réutilisation** | Mutualiser les ressources | Modèle chargé une fois, API *stateless* partagée. |
| **Stockage mesuré** | Base légère, formats compressés | SQLite, téléchargements `.gz`, données regénérables non versionnées. |
| **Efficacité réseau** | Limiter les transferts | Collecte incrémentale/idempotente, cache applicatif (`st.cache_data`). |
| **Code efficient** | Vectorisation | `pandas`/`numpy` plutôt que des boucles. |
| **Fin de vie** | Nettoyage | Artefacts et données temporaires regénérables et purgés (`.gitignore`). |

---

## 4.3 Green AI — spécificités IA

- **« Le bon modèle, pas le plus gros »** : un modèle linéaire calibré atteint
  ici un ROC-AUC de 0,77, rendant inutile un modèle profond énergivore.
- **Mesure de l'empreinte** : outils recommandés — `CodeCarbon`,
  `Scaphandre`, calculateur **Boavizta** — pour estimer kWh et gCO₂e de
  l'entraînement et de l'inférence, et en faire un **indicateur de pilotage**.
- **Ré-entraînement raisonné** : fréquence pilotée par la dérive réelle des
  métriques, pas systématique.
- **Inférence sobre** : réponse calculée à la demande, pas de pré-calcul massif.

---

## 4.4 Étude des hébergements responsables

Critères de choix d'un hébergeur éco-responsable :

| Critère | Description |
|---|---|
| **PUE** (Power Usage Effectiveness) | Efficacité énergétique du datacenter (cible < 1,3). |
| **Mix énergétique** | Part d'énergies renouvelables / bas-carbone. |
| **Réutilisation de chaleur** | Récupération de la chaleur fatale. |
| **WUE** (Water Usage Effectiveness) | Consommation d'eau du refroidissement. |
| **Souveraineté & localisation** | Hébergement en France/UE (RGPD, réseau court). |
| **Engagements & labels** | *Climate Neutral Data Centre Pact*, ISO 14001, *Code of Conduct* européen. |

### Comparatif synthétique (hébergeurs adaptés)

| Hébergeur | Atouts éco | Remarque |
|---|---|---|
| **Scaleway** (Free/Iliad) | Datacenter DC5 à *free cooling* par adiabatique (sans clim), PUE ~1,15 | Souverain, France |
| **OVHcloud** | Refroidissement liquide (watercooling), réutilisation, serveurs conçus en interne | Souverain, France |
| **Infomaniak** | 100 % énergies renouvelables, neutralité carbone, réutilisation de chaleur | Souverain, Suisse |
| Clever Cloud | PaaS, mise à l'échelle fine (sobriété), France | Souverain |

> **Recommandation MVP** : un hébergeur **souverain** (Scaleway, OVHcloud ou
> Infomaniak) avec datacenter à faible PUE et énergie bas-carbone, aligné sur
> les exigences d'un établissement public. Déploiement en **conteneurs** pour
> dimensionner au plus juste (pas de VM surdimensionnée) et **extinction des
> environnements hors production** la nuit/week-end.

---

## 4.5 Indicateurs d'éco-responsabilité à suivre

- Énergie estimée de l'entraînement (kWh) et émissions (gCO₂e) — via CodeCarbon.
- Empreinte par requête d'inférence.
- Taux d'utilisation des ressources (éviter le surdimensionnement).
- PUE/mix énergétique de l'hébergeur retenu.
- Volume de données stockées et transférées.
