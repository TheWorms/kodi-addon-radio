# -*- coding: utf-8 -*-
"""Entree « Programme » : lancement direct de l'interface (v1.2.10).

L'addon reste un plugin (entree Musique/Extensions, barre d'adresse
plugin://...) mais expose desormais aussi une entree script. Lancee via
RunScript(plugin.audio.radio) — favori ou element de menu du skin — ou
depuis la section Programmes, cette entree ouvre l'accueil DIRECTEMENT :
pas de passage par l'explorateur de fichiers, que Kodi active
systematiquement pour un plugin (RunAddon/Extensions).

L'interface elle-meme (garde anti-doublon, anti-boucle, retour a l'accueil)
est geree par radio_ui.open_home(), partagee avec l'entree plugin.
"""
import os
import sys

ADDON_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(ADDON_DIR, "resources", "lib"))

import launcher  # noqa: E402

# L'accueil de Kodi sous l'interface (a la fermeture, pas d'explorateur),
# PUIS l'ecran de chargement : dans l'autre ordre, il bloque le changement
# de fenetre (v1.2.19).
launcher.go_home(launcher.HANDOFF_ARG in sys.argv[1:])
launcher.splash_show(ADDON_DIR)
try:
    import radio_ui  # noqa: E402

    launcher.splash_hide()  # avant d'ouvrir : sinon Kodi refuse d'afficher l'interface
    radio_ui.open_home()
finally:
    launcher.splash_hide()
