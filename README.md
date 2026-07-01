**Français** · [English](readme.en.md)

# Radio — interface française

<!-- version:auto -->
**Version : 1.0.7**
<!-- /version:auto -->

Module Kodi pour écouter des **flux radio en streaming**, avec une interface **en français**.

Le module s'**inspire du service [radio.de](https://www.radio.de)** et s'appuie sur son API
publique `prod.radio-api.net`. L'interface est portée sur le système de localisation standard
de Kodi (gettext / fichiers `.po`) et propose une vue « cinéma » pendant la lecture.

## Installation

**Recommandé — dépôt TheWorms** (mises à jour automatiques).

Télécharge le dépôt en cliquant **[ICI](https://raw.githubusercontent.com/TheWorms/kodi-repo/main/zips/repository.theworms/repository.theworms.zip)**, puis dans Kodi :

1. **Add-ons** → **Installer depuis un fichier zip** → sélectionne le zip téléchargé
   *(si Kodi bloque, active **Sources inconnues** dans Système → Add-ons)*
2. **Installer depuis un dépôt** → **TheWorms Repository** → choisis l'addon
3. Les mises à jour seront ensuite automatiques

**Installation manuelle (alternative) :** télécharge le zip de l'addon depuis la page [Releases](../../releases), puis **Add-ons** → **Installer depuis un fichier zip**.

## Crédits

- **Code d'origine :** [Publish3r](https://github.com/Publish3r) — le module dont ce projet est dérivé.
- **Source d'origine :** <https://github.com/Publish3r/repository.kodi.matrix>
- **Adaptation française, corrections, vue cinéma :** [TheWorms](https://github.com/TheWorms).
- **Inspiration :** le service radio.de.

Ce projet est dérivé d'un module sous licence GPL v2 ; le crédit à l'auteur d'origine et la
licence sont conservés conformément à cette licence.

## Fonctionnalités

- **Stations de votre région** — stations populaires localisées (privilégie la France).
- **Rechercher une station** — recherche par nom.
- **Mes stations** — favoris, avec ajout/retrait via le menu contextuel.
- **Vue cinéma** — pendant la lecture, logo de la station en plein écran avec une barre
  d'égaliseur animée (activable/désactivable dans les réglages).

## Installation manuelle

Le module est aussi disponible dans la liste des addons du dépôt. Il dépend de
`script.module.requests` (généralement déjà présent sur CoreELEC / LibreELEC).

## Structure du dépôt

```
plugin.audio.radio/            le module Kodi installable
├── addon.py
├── addon.xml
├── changelog.txt
├── LICENSE.txt
└── resources/
    ├── settings.xml           réglages (vue cinéma, barre)
    ├── language/              traductions gettext (fr_FR, en_GB, de_DE)
    └── skins/Default/         fenêtre plein écran de la vue cinéma
```

## Localisation

Pour modifier ou compléter les traductions, éditer les fichiers :

```
plugin.audio.radio/resources/language/resource.language.fr_fr/strings.po
plugin.audio.radio/resources/language/resource.language.en_gb/strings.po
plugin.audio.radio/resources/language/resource.language.de_de/strings.po
```

## Licence

GPL v2 — voir [`plugin.audio.radio/LICENSE.txt`](plugin.audio.radio/LICENSE.txt),
identique à la licence du module d'origine.
