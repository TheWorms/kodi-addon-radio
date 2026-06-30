# Radio.de light — interface française

Module Kodi pour écouter les flux radio de [radio.de](https://www.radio.de) (API `prod.radio-api.net`),
avec une interface **en français**.

Ce dépôt est un **fork** du module original **« Radio.de light » de Publish3r**, dont l'interface
était écrite en allemand en dur dans le code. Le fork porte l'interface sur le système de
localisation standard de Kodi (gettext / fichiers `.po`), corrige plusieurs bugs et nettoie l'affichage.

## Crédits

- **Auteur original :** [Publish3r](https://github.com/Publish3r) — module « Radio.de light ».
- **Source d'origine :** <https://github.com/Publish3r/repository.kodi.matrix/tree/main/plugin.audio.radio_de_light>
- **Adaptation française, corrections et nettoyage :** [TheWorms](https://github.com/TheWorms).

Tous les mérites du module d'origine reviennent à Publish3r. Ce dépôt se limite à le traduire
et à le corriger, dans le respect de la licence GPL v2.

## Ce que ce fork apporte

- Interface localisée via gettext (`.po`) : **français** (`fr_FR`), anglais (`en_GB`) et allemand d'origine (`de_DE`).
- Correction d'un plantage à l'ajout d'un favori (paramètre `image` perdu quand le logo contenait `?version=`).
- Correction des stations injouables dont le nom contient des caractères spéciaux (ex. « Radio 50/50 ») : encodage URL de tous les paramètres.
- Correction du clavier de recherche (appel `getText()` invalide) et de la pagination de recherche.
- Suppression de toutes les couleurs dans les textes (le gras est conservé).
- En-tête `Accept-Language: fr-FR` pour privilégier les stations françaises dans « Stations de votre région ».

## Fonctionnalités

- **Stations de votre région** — stations populaires localisées (privilégie la France).
- **Rechercher une station** — recherche par nom.
- **Mes stations** — favoris, avec ajout/retrait via le menu contextuel.

## Installation

1. Télécharger le fichier `plugin.audio.radio_de_light-<version>.zip` depuis la
   page [Releases](../../releases) de ce dépôt.
2. Dans Kodi : **Modules → Installer depuis un fichier zip** → sélectionner le zip.

> Le module dépend de `script.module.requests` (généralement déjà présent sur CoreELEC / LibreELEC).

## Structure du dépôt

```
plugin.audio.radio_de_light/   le module Kodi installable
├── addon.py
├── addon.xml
├── changelog.txt
├── LICENSE.txt
└── resources/language/        traductions gettext (fr_FR, en_GB, de_DE)
```

## Localisation

Pour modifier ou compléter les traductions, éditer les fichiers :

```
plugin.audio.radio_de_light/resources/language/resource.language.fr_fr/strings.po
plugin.audio.radio_de_light/resources/language/resource.language.en_gb/strings.po
plugin.audio.radio_de_light/resources/language/resource.language.de_de/strings.po
```

## Licence

GPL v2 — voir [`plugin.audio.radio_de_light/LICENSE.txt`](plugin.audio.radio_de_light/LICENSE.txt),
identique à la licence du module d'origine.
