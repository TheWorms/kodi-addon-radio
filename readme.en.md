[Français](README.md) · **English**

# Radio

Kodi add-on to listen to **radio streams**, with a localized interface.

It is **inspired by the [radio.de](https://www.radio.de) service** and relies on its
public API `prod.radio-api.net`. The interface uses Kodi's standard localization system
(gettext / `.po` files) and offers a "cinema" view during playback.

## Installation

**Recommended — TheWorms repository** (automatic updates).

Download the repository by clicking **[HERE](https://raw.githubusercontent.com/TheWorms/kodi-repo/main/zips/repository.theworms/repository.theworms.zip)**, then in Kodi:

1. **Add-ons** → **Install from zip file** → select the downloaded zip
   *(if Kodi blocks it, enable **Unknown sources** under Settings → Add-ons)*
2. **Install from repository** → **TheWorms Repository** → pick the add-on
3. Updates will then be automatic

**Manual install (alternative):** download the add-on zip from the [Releases](../../releases) page, then **Add-ons** → **Install from zip file**.

## Credits

- **Original code:** [Publish3r](https://github.com/Publish3r) — the add-on this project is derived from.
- **Original source:** <https://github.com/Publish3r/repository.kodi.matrix>
- **French adaptation, fixes, cinema view:** [TheWorms](https://github.com/TheWorms).
- **Inspiration:** the radio.de service.

This project is derived from a GPL v2 add-on; credit to the original author and the
license are preserved in accordance with that license.

## Features

- **Stations from your region** — localized popular stations.
- **Search a station** — search by name.
- **My stations** — favorites, add/remove via the context menu.
- **Cinema view** — during playback, full-screen station logo with an animated
  equalizer bar (toggle in settings).

## Manual installation

The add-on is also available in the repository's add-on list. It depends on
`script.module.requests` (usually already present on CoreELEC / LibreELEC).

## Localization

Translations live in:

```
plugin.audio.radio/resources/language/resource.language.fr_fr/strings.po
plugin.audio.radio/resources/language/resource.language.en_gb/strings.po
plugin.audio.radio/resources/language/resource.language.de_de/strings.po
```

## License

GPL v2 — see [`plugin.audio.radio/LICENSE.txt`](plugin.audio.radio/LICENSE.txt),
identical to the original add-on's license.
