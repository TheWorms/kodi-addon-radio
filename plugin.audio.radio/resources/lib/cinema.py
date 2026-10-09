# -*- coding: utf-8 -*-
# Copyright (C) 2026 TheWorms. Vue cinema derivee du module « Radio » de
# Publish3r (GPL v2) -- voir LICENSE.txt pour la licence et les credits
# d'origine.
"""
cinema.py — vue « cinema » (logo de la station en plein ecran).

Extraite d'addon.py en v1.1.8 pour etre partagee par les deux
interfaces : le menu classique et l'accueil plein ecran.
"""

import threading
import time

import xbmc
import xbmcgui

import radio_ui

no_image = "special://home/addons/plugin.audio.radio/no_image.jpg"


def log(msg, level=xbmc.LOGDEBUG):
    xbmc.log("plugin.audio.radio(cinema): %s" % msg, level)


class RadioCinema(xbmcgui.WindowXMLDialog):
    def set_data(self, logo, name, show_bar, stop_on_exit=True):
        self._logo = logo if logo else no_image
        self._name = name if name else ''
        self._show_bar = show_bar
        # Depuis l'interface plein ecran, quitter la vue doit rendre la
        # main a l'accueil SANS arreter la station.
        self._stop_on_exit = stop_on_exit
        # Event d'arret du thread de surveillance : pose a la fermeture de
        # la fenetre, il evite le thread orphelin qui survit a la vue (un
        # par station ecoutee, audit v1.2.14).
        self._stop = threading.Event()

    def onInit(self):
        # white.png valide ET present : la vue reutilise la reparation
        # atomique de radio_ui, plus de copie locale qui ne testait que
        # l'existence du fichier (audit v1.2.14).
        try:
            self.setProperty('px', radio_ui.white_px())
            self.setProperty('logo', self._logo)
            self.setProperty('name', self._name)
            self.setProperty('showbar', '1' if self._show_bar else '0')
        except Exception as e:
            log("onInit : %s" % e, xbmc.LOGERROR)
        threading.Thread(target=self._watch, daemon=True).start()

    def _watch(self):
        player = xbmc.Player()
        monitor = xbmc.Monitor()
        ev = getattr(self, '_stop', None)
        # Laisse le flux demarrer (max 15 s)
        start = time.time()
        while not monitor.abortRequested() and (time.time() - start) < 15:
            if (ev is not None and ev.is_set()) or player.isPlaying():
                break
            if monitor.waitForAbort(0.5):
                return
        # Reste affiche tant que la lecture continue ; l'Event pose a la
        # fermeture fait sortir SANS re-appeler close() sur une vue deja
        # fermee (audit v1.2.14).
        while not monitor.abortRequested():
            if ev is not None and ev.is_set():
                return
            if not player.isPlaying():
                break
            if monitor.waitForAbort(1):
                return
        try:
            self.close()
        except Exception as e:
            log("close : %s" % e, xbmc.LOGDEBUG)

    def _shutdown(self, stop_playback):
        ev = getattr(self, '_stop', None)
        if ev is not None:
            ev.set()
        if stop_playback:
            try:
                xbmc.Player().stop()
            except Exception as e:
                log("stop : %s" % e, xbmc.LOGDEBUG)
        self.close()

    def onAction(self, action):
        aid = action.getId()
        if aid == 13:
            # STOP coupe TOUJOURS la radio, meme depuis l'accueil plein
            # ecran (comportement annonce par le changelog v1.2.13).
            self._shutdown(stop_playback=True)
        elif aid in (9, 10, 92):
            # Retour / menu precedent : ferme la vue ; la lecture n'est
            # arretee que si stop_on_exit (menu classique) -- depuis
            # l'interface plein ecran la radio continue.
            self._shutdown(stop_playback=getattr(self, '_stop_on_exit', True))
