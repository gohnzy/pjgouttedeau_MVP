# 4. Éco-responsabilité et accessibilité

## 4.1 Sobriété

Le MVP reprend plusieurs principes du Green IT : limiter les données stockées et éviter les calculs inutiles. Il utilise une régression logistique entraînée sur CPU, des traitements vectorisés, une collecte incrémentale et une base SQLite. Le modèle entraîné est réutilisé; aucun GPU ni réentraînement régulier n'est nécessaire à ce stade.

L'application est actuellement exécutée localement. AWS est une option pour la suite, pas un hébergement déjà en place. Avant ce déploiement, il faudra ajuster les ressources, choisir une région au mix électrique adapté, arrêter les environnements hors production et définir une durée de conservation des données. L'empreinte de l'entraînement et des prédictions pourrait être suivie avec CodeCarbon.

Pour les phases suivantes, AWS pourra être comparé à des fournisseurs comme Scaleway ou OVHcloud, en tenant compte de l'énergie, de la localisation, du coût et des garanties de sécurité.

## 4.2 Accessibilité

La cible est le RGAA et le niveau AA des WCAG 2.1. Le MVP n'a pas encore fait l'objet d'un audit de conformité.

Quelques points à prendre en compte dans l'interface :

- Ne pas transmettre une information uniquement par la couleur; garder des contrastes suffisants.
- Décrire les graphiques et fournir des textes alternatifs lorsque nécessaire.
- Utiliser des libellés, unités et messages d'erreur explicites.
- Permettre la navigation au clavier avec un focus visible et vérifier la lisibilité après agrandissement.
- Prévoir une structure compatible avec les lecteurs d'écran et les principaux navigateurs.

La démo Streamlit présente le risque avec un libellé, une icône et une valeur. Cela ne suffit pas à démontrer la conformité. Avant une mise en production, il faudra tester au clavier et avec des lecteurs d'écran, compléter par des vérifications automatiques et manuelles, puis essayer l'interface sur mobile et plusieurs navigateurs.

La sécurité est aussi à traiter avant le déploiement : HTTPS, validation des entrées et absence de données personnelles. L'interface doit rester simple et donner un retour clair après une action.
