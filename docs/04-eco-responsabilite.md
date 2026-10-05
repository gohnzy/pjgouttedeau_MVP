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

## 4.4 Hébergement : optimiser le choix AWS (EdC-01)

Le cahier des charges (EdC-01) a retenu **AWS** comme fournisseur cloud, pour
son écosystème IoT (AWS IoT Core), sa scalabilité et son stockage. L'enjeu
d'éco-conception est donc d'**exploiter AWS de façon responsable**, puis de
garder ouverte l'option d'un hébergeur souverain plus sobre.

### Rendre le déploiement AWS responsable

| Levier | Mise en œuvre sur AWS |
|---|---|
| **Région bas-carbone** | Déployer dans une région à électricité décarbonée (ex. `eu-west-3` Paris, `eu-north-1` Suède) ; AWS vise 100 % d'énergies renouvelables. |
| **Processeurs efficients** | Instances **Graviton** (ARM) : meilleur rendement performance/watt que x86. |
| **Serverless & autoscaling** | Lambda / Fargate pour ne consommer qu'à l'usage ; pas de serveur allumé en continu. |
| **Extinction hors production** | Arrêt programmé des environnements de recette la nuit/week-end (*instance scheduler*). |
| **Stockage par paliers** | S3 Intelligent-Tiering / Glacier pour les archives ; cycle de vie des données. |
| **Mesure** | *AWS Customer Carbon Footprint Tool* pour suivre les émissions. |
| **Right-sizing** | Dimensionnement au plus juste (Compute Optimizer), pas de surprovisionnement. |

### Alternative souveraine (recommandation de veille)

Critères de choix d'un hébergeur éco-responsable :

| Critère | Description |
|---|---|
| **PUE** (Power Usage Effectiveness) | Efficacité énergétique du datacenter (cible < 1,3). |
| **Mix énergétique** | Part d'énergies renouvelables / bas-carbone. |
| **Réutilisation de chaleur** | Récupération de la chaleur fatale. |
| **WUE** (Water Usage Effectiveness) | Consommation d'eau du refroidissement. |
| **Souveraineté & localisation** | Hébergement en France/UE (RGPD, réseau court). |
| **Engagements & labels** | *Climate Neutral Data Centre Pact*, ISO 14001, *Code of Conduct* européen. |

| Hébergeur | Atouts éco | Remarque |
|---|---|---|
| **Scaleway** (Free/Iliad) | Datacenter DC5 à *free cooling* adiabatique (sans clim), PUE ~1,15 | Souverain, France |
| **OVHcloud** | Refroidissement liquide (watercooling), réutilisation, serveurs conçus en interne | Souverain, France |
| **Infomaniak** | 100 % énergies renouvelables, neutralité carbone, réutilisation de chaleur | Souverain, Suisse |

> **Recommandation.** Conserver **AWS** (choix EdC-01) en appliquant les leviers
> ci-dessus (région décarbonée, Graviton, serverless, extinction programmée).
> Pour un **service public** soumis à des exigences de souveraineté et
> d'exemplarité environnementale, **réévaluer en P4** une bascule partielle vers
> un hébergeur souverain à faible PUE (Scaleway, OVHcloud) — notamment pour les
> données et traitements sensibles. Déploiement en **conteneurs** pour
> dimensionner au plus juste.

---

## 4.5 Indicateurs d'éco-responsabilité à suivre

- Énergie estimée de l'entraînement (kWh) et émissions (gCO₂e) — via CodeCarbon.
- Empreinte par requête d'inférence.
- Taux d'utilisation des ressources (éviter le surdimensionnement).
- PUE/mix énergétique de l'hébergeur retenu.
- Volume de données stockées et transférées.
