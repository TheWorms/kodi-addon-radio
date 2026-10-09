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

import radio_ui  # noqa: E402

radio_ui.open_home()
