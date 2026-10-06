# 4. Éco-responsabilité et accessibilité

## 4.1 Sobriété

Le MVP applique quelques mesures de sobriété vérifiables : la régression logistique est entraînée sur CPU, les conversions de collecte et les variables saisonnières sont vectorisées, les mois déjà collectés ne sont plus téléchargés par défaut, et SQLite évite un service de base distinct. Les colonnes d'archive sont conservées pour la traçabilité; elles ne figurent pas dans la matrice de variables du modèle si elles ne sont pas utilisées.

L'application est actuellement exécutée localement. AWS est une option de cible, pas un hébergement déjà en place ni un choix démontré par le PDF EdC-01 fourni. L'étude des fournisseurs, des localisations, des PUE, des certifications et des limites de comparaison est dans [`05-hebergement-responsable.md`](05-hebergement-responsable.md). CodeCarbon 3.3.1 a estimé une exécution locale d'entraînement à **0,0027 gCO₂e**; cette valeur est une estimation du processus CPU/RAM et non une mesure électrique au compteur. Elle est enregistrée dans `models/metrics.json`; toute nouvelle exécution peut varier selon le matériel et l'intensité électrique détectée.

Pour les phases suivantes, AWS pourra être comparé à des fournisseurs comme Scaleway ou OVHcloud, en tenant compte de l'énergie, de la localisation, du coût et des garanties de sécurité.

## 4.2 Accessibilité

La cible déclarée est **RGAA 4.1.2** et **WCAG 2.2 niveau AA**. Ce sont des objectifs de conception, pas une conformité acquise : le MVP n'a pas fait l'objet d'un audit d'accessibilité.

Quelques points à prendre en compte dans l'interface :

- Ne pas transmettre une information uniquement par la couleur; garder des contrastes suffisants.
- Décrire les graphiques et fournir des textes alternatifs lorsque nécessaire.
- Utiliser des libellés, unités et messages d'erreur explicites.
- Permettre la navigation au clavier avec un focus visible et vérifier la lisibilité après agrandissement.
- Prévoir une structure compatible avec les lecteurs d'écran et les principaux navigateurs.

La démo présente le risque avec un libellé et une valeur; cela ne suffit pas à démontrer la conformité. Les contrastes, l'ordre de tabulation, les lecteurs d'écran, les erreurs, le zoom, les graphiques, les mobiles et les navigateurs n'ont pas été audités. Une campagne de tests clavier, lecteur d'écran et vérifications manuelles/automatiques reste à réaliser.

La sécurité est aussi à traiter avant le déploiement : HTTPS, validation des entrées et absence de données personnelles. L'interface doit rester simple et donner un retour clair après une action.
