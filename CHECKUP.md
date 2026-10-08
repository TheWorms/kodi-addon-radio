# 🔍 Check-up — kodi-addon-radio (`plugin.audio.radio`)

> Audit du dépôt **TheWorms/kodi-addon-radio** réalisé le 2026-10-08 par Vibe (Mistral AI) à la demande de Thib.
> 1er passage : version publiée **v1.0.7** · Réconciliation : branche de travail **v1.2.3** (interface plein écran) — le solde est intégré dans la **v1.2.4**.

---

## Réconciliation des 16 points de l'audit (v1.0.7 → v1.2.4)

| # | Point | Gravité (audit) | État |
|---|-------|--------|------|
| 1 | Recherche non encodée (accents, `&`, `#`) | 🔴 | ✅ corrigé v1.1.x — `quote_plus` (menu) / `requests.utils.quote` (UI plein écran) |
| 2 | Récursion infinie si `sender.txt` incréable | 🔴 | ✅ corrigé v1.1.0 — favoris JSON, `_ensure_profile()`, plus d'appel récursif |
| 3 | `streams[0]['url']` sans garde → liste entière vide | 🔴 | ✅ corrigé v1.1.x — `render_stations()` / `station_fields()`, garde PAR station |
| 4 | Suppression favoris par sous-chaîne | 🟡 | ✅ corrigé v1.1.0 — `remove_favorite()`, comparaison exacte d'URL |
| 5 | Pagination recherche par regex fragile | 🟡 | ✅ **v1.2.4** — offset extrait/reconstruit via `urllib.parse` |
| 6 | Code mort : `setView()` / réglage `auto-view` inexistant | 🟢 | ✅ **v1.2.4** — supprimé |
| 7 | Duplication morte dans `SEARCH()` | 🟢 | ✅ corrigé v1.1.x — `render_stations()` extrait |
| 8 | Image de repli hotlinkée (i.postimg.cc) | 🟡 | ✅ corrigé v1.1.x — icône locale |
| 9 | `except:` nus généralisés | 🟡 | ✅ **v1.2.4** — `addon.py` aligné sur `radio_ui.py`/`cinema.py` (`Exception` + `xbmc.log`) |
| 10 | API non officielle `prod.radio-api.net` (UA navigateur) | 🟡 | ⚠️ assumée — non corrigeable côté addon ; risque de changement/blocage unilatéral à documenter |
| 11 | Flux potentiellement en `http://` | 🟢 | ⚠️ imposé par l'API — non corrigeable côté addon |
| 12 | Imports sur une ligne + modules inutilisés | 🟢 | ✅ **v1.2.4** — imports PEP 8 (`html`, `urllib.request/error`, `threading`, `time`, `re` retirés) |
| 13 | `LOCAL()` / `SEARCH()` dupliquées à ~90 % | 🟡 | ✅ **v1.2.4** — fusionnées en `STATIONS()` (rendu déjà partagé via `render_stations`) |
| 14 | `print()` de debug | 🟢 | ✅ corrigé v1.1.x — `xbmc.log(..., LOGDEBUG)` |
| 15 | `get_params()` liste **ou** dict | 🟢 | ✅ **v1.2.4** — retourne toujours un dict |
| 16 | No-ops (`ok = True`, `url = url`, constantes mortes) | 🟢 | ✅ **v1.2.4** — supprimés |

**Bilan : 14 points corrigés** (9 par le WIP v1.1–v1.2.3 de Thib, 5 par la v1.2.4), **2 assumés** (#10, #11 — dépendance à une API externe non officielle).

---

## Revue de la nouvelle interface (v1.1.0 → v1.2.3)

**Points forts constatés** — le nouveau code (`resources/lib/radio_ui.py`, `cinema.py`) est de bonne qualité :

- garde PAR rangée / PAR station : une rangée en échec ne masque pas les autres ;
- égaliseur animé propre : thread daemon + `Event` + `join` court dans `_teardown()`, sortie immédiate si un contrôle disparaît ;
- texture blanche garantie (`white_px()`) : repli générée dans le profil si `white.png` manque — l'interface ne devient jamais transparente ;
- garde-fous d'ouverture : `GUARD_PROP` anti-empilement + délai anti-boucle au retour accueil (`CLOSED_PROP`) ;
- favoris JSON avec migration unique de `sender.txt` (`.bak` conservé) et écriture atomique (`tmp` + `os.replace`) ;
- timeouts réseau 5 s partout ; aucun secret ; aucun `eval`/`exec`.

**Notes mineures (informatives, sans action immédiate)** :

- `radio_ui.s_int()` : `except (ValueError, Exception)` — attraper `Exception` suffit (la clause `ValueError` est redondante). Sans risque.
- Les deux `sys.path.append` répétés dans `MYSTATIONS`/`ADDSTATION`/`DELSTATION` étaient superflus (déjà faits au niveau du module) — nettoyés en v1.2.4.

---

## Verdict

Structure saine, zéro secret, aucune régression de sécurité. L'audit v1.0.7 est **soldé** en v1.2.4. Restent hors périmètre addon : la dépendance à l'API non officielle (à documenter : risque de cassage unilatéral) et les flux `http://` imposés par l'API.

Pistes futures (non bloquantes) : `kodi-addon-checker`/`flake8` dans le circuit de release ; mode secours si l'API `prod.radio-api.net` change de format.
