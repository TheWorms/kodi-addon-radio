# -*- coding: utf-8 -*-
"""
cinema.py — vue « cinema » (logo de la station en plein ecran).

Extraite d'addon.py en v1.1.8 pour etre partagee par les deux
interfaces : le menu classique et l'accueil plein ecran.
"""

import base64
import os
import threading
import time

import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

no_image = "special://home/addons/plugin.audio.radio/no_image.jpg"


def _white_px():
    """Texture blanche garantie (meme logique que radio_ui.white_px) :
    le voile de fond et les barres animees de cette vue en dependent ;
    sans elle, la vue est transparente et les barres invisibles."""
    profile = xbmcvfs.translatePath(
        xbmcaddon.Addon().getAddonInfo("profile"))
    try:
        if not os.path.isdir(profile):
            os.makedirs(profile)
        path = os.path.join(profile, "white.png")
        if not os.path.exists(path):
            with open(path, "wb") as f:
                f.write(base64.b64decode(
                    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4"
                    "2mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII="))
        return path
    except OSError:
        return ""


class RadioCinema(xbmcgui.WindowXMLDialog):
    def set_data(self, logo, name, show_bar, stop_on_exit=True):
        self._logo = logo if logo else no_image
        self._name = name if name else ''
        self._show_bar = show_bar
        # Depuis l'interface plein ecran, quitter la vue doit rendre la
        # main a l'accueil SANS arreter la station.
        self._stop_on_exit = stop_on_exit

    def onInit(self):
        try:
            self.setProperty('px', _white_px())
            self.setProperty('logo', self._logo)
            self.setProperty('name', self._name)
            self.setProperty('showbar', '1' if self._show_bar else '0')
        except Exception:
            pass
        threading.Thread(target=self._watch, daemon=True).start()

    def _watch(self):
        player = xbmc.Player()
        monitor = xbmc.Monitor()
        # Laisse le flux démarrer (max 15 s)
        start = time.time()
        while not monitor.abortRequested() and (time.time() - start) < 15:
            if player.isPlaying():
                break
            if monitor.waitForAbort(0.5):
                break
        # Reste affiché tant que la lecture continue
        while not monitor.abortRequested():
            if not player.isPlaying():
                break
            if monitor.waitForAbort(1):
                break
        try:
            self.close()
        except Exception:
            pass

    def onAction(self, action):
        # Retour / menu precedent / stop : on ferme la vue. La lecture n'est
        # arretee que si stop_on_exit (menu classique) ; depuis l'interface
        # plein ecran la radio continue.
        if action.getId() in (9, 10, 13, 92):
            if getattr(self, '_stop_on_exit', True):
                try:
                    xbmc.Player().stop()
                except Exception:
                    pass
            self.close()
