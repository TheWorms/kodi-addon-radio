# -*- coding: utf-8 -*-
"""Entree plugin (Musique > Extensions, plugin://plugin.audio.radio).

Ouverte par l'utilisateur depuis l'explorateur, l'interface plein ecran est
confiee a l'entree script (script.py) et l'explorateur est remplace par
l'accueil de Kodi : a la fermeture, Kodi revient droit a l'accueil sans
repasser par l'explorateur (voir resources/lib/launcher.py). Ce fichier
reste leger pour que cela se fasse au plus vite.

Tout le reste (lecture d'une station, menu classique, widgets) est dans
plugin_main.py, l'ancien addon.py, inchange.
"""
import os
import sys

import xbmc
import xbmcaddon

handed_off = False
if len(sys.argv) < 3 or sys.argv[2] in ('', '?'):
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                        'resources', 'lib'))
        import launcher
        if xbmcaddon.Addon().getSetting('ui.fullscreen') != 'false' and launcher.user_open():
            launcher.hand_off(int(sys.argv[1]))
            handed_off = True
    except Exception as exc:  # en cas de souci, ouverture comme avant
        xbmc.log('plugin.audio.radio: passage direct (%s)' % exc, xbmc.LOGWARNING)

if not handed_off:
    import plugin_main  # noqa: F401,E402
