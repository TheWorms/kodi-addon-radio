# -*- coding: utf-8 -*-
"""Lancement de l'interface plein écran : écran de chargement et accueil
de Kodi placé SOUS l'interface.

Module volontairement léger (xbmc et xbmcgui seulement) : il est chargé
avant tout le reste pour que l'écran de chargement s'affiche au plus tôt.

Pourquoi passer par l'accueil : ouvert depuis Extensions, un plugin est
affiché par Kodi dans l'explorateur de fichiers. Si l'interface s'ouvre
par-dessus, sa fermeture rend la main à l'explorateur, qu'on voit un
instant avant le retour à l'accueil. L'entrée plugin remplace donc tout de
suite l'explorateur par l'accueil et lance l'interface par l'entrée script
(RunScript) : à la fermeture, Kodi revient directement à l'accueil.

Ordre impératif : Kodi refuse de changer de fenêtre tant qu'un dialogue
est affiché, et l'écran de chargement en est un. Il ne doit donc JAMAIS
être à l'écran quand on demande l'accueil ni quand l'interface s'ouvre
(0.6.29 / 1.2.19 de test : écran de chargement bloqué, interface jamais
affichée). D'où : accueil d'abord, écran de chargement ensuite, et
fermeture de cet écran AVANT d'ouvrir l'interface.
"""
import time

import xbmc
import xbmcgui

ADDON_ID = 'plugin.audio.radio'
SPLASH_XML = 'script-radio-splash.xml'
SPLASH_RES = '720p'
# Écran de chargement affiché par le service de l'addon quand il tourne
# (il est déjà en mémoire : affichage immédiat), sinon par l'entrée script.
PROP_SPLASH = 'radio.splash'
PROP_ALIVE = PROP_SPLASH + '.alive'
HANDOFF_ARG = 'handoff'
MAIN_XML = 'script-radio-home.xml'

# Fenêtres d'où l'ouverture n'est pas un geste de l'utilisateur dans
# l'explorateur : widget de l'accueil, sélecteur de chemin du skin…
_NOT_USER = ('Window.IsActive(home) | Window.IsActive(filebrowser) | Window.IsActive(selectdialog)'
             ' | Window.IsActive(addoninformation) | Window.IsActive(script-skinshortcuts.xml)'
             ' | Window.IsActive(script-skinshortcuts-menu.xml)')
# Fenêtres de type explorateur, à remplacer par l'accueil avant d'ouvrir.
_EXPLORER = ('Window.IsActive(videos) | Window.IsActive(music) | Window.IsActive(programs)'
             ' | Window.IsActive(addonbrowser) | Window.IsActive(filemanager)')

_local = None


class _Splash(xbmcgui.WindowXMLDialog):
    pass


def user_open():
    """Ouverture par l'utilisateur, interface pas déjà affichée (remplacer
    la fenêtre courante par l'accueil la refermerait)."""
    if xbmc.getCondVisibility('Window.IsVisible(%s)' % MAIN_XML):
        return False
    return not xbmc.getCondVisibility(_NOT_USER)


def _service_alive():
    return xbmcgui.Window(10000).getProperty(PROP_ALIVE) == '1'


def _wait(condition, expected, timeout):
    """Attend que la condition Kodi prenne la valeur voulue."""
    monitor = xbmc.Monitor()
    deadline = time.time() + timeout
    while bool(xbmc.getCondVisibility(condition)) != expected:
        if time.time() >= deadline or monitor.waitForAbort(0.05):
            return False
    return True


def hand_off(handle):
    """Entrée plugin : remplace l'explorateur par l'accueil, puis confie
    l'ouverture à l'entrée script. L'appelant n'a plus rien à faire."""
    import xbmcplugin
    xbmcplugin.endOfDirectory(handle, succeeded=False, cacheToDisc=False)
    xbmc.executebuiltin('ReplaceWindow(home)')
    # L'accueil doit être en place AVANT l'écran de chargement.
    at_home = _wait('Window.IsActive(home)', True, 2.0)
    if at_home and _service_alive():
        xbmcgui.Window(10000).setProperty(PROP_SPLASH, 'show')
    xbmc.executebuiltin('RunScript(%s,%s)' % (ADDON_ID, HANDOFF_ARG))


def go_home(handed_off, timeout=3.0):
    """À appeler AVANT splash_show. Fait en sorte que l'accueil soit la
    fenêtre active, pour que l'interface s'ouvre par-dessus lui.

    handed_off : l'entrée plugin s'en est déjà chargée. Sinon (favori,
    Programmes, menu du skin) on le demande ici si l'explorateur est
    affiché."""
    is_home = 'Window.IsActive(home)'
    if xbmc.getCondVisibility(is_home):
        return True
    if handed_off:
        return _wait(is_home, True, 1.0)
    if not xbmc.getCondVisibility(_EXPLORER):
        return False  # lancé d'ailleurs (lecteur, autre addon) : on n'y touche pas
    xbmc.executebuiltin('ReplaceWindow(home)')
    if not _wait(is_home, True, timeout):
        xbmc.log('[%s] accueil non atteint en %.0f s, ouverture quand même' % (ADDON_ID, timeout),
                 xbmc.LOGWARNING)
        return False
    return True


def splash_show(addon_path):
    """Entrée script, APRÈS go_home : écran de chargement pendant le
    chargement des modules."""
    global _local
    if xbmc.getCondVisibility('Window.IsVisible(%s)' % SPLASH_XML):
        return  # déjà affiché par le service
    if _service_alive():
        xbmcgui.Window(10000).setProperty(PROP_SPLASH, 'show')
        return
    try:
        _local = _Splash(SPLASH_XML, addon_path, 'Default', SPLASH_RES)
        _local.show()
    except Exception as exc:  # l'écran de chargement n'est jamais bloquant
        xbmc.log('[%s] écran de chargement : %s' % (ADDON_ID, exc), xbmc.LOGWARNING)
        _local = None


def splash_hide():
    """À appeler AVANT d'ouvrir l'interface : ferme l'écran de chargement
    et attend qu'il ait vraiment disparu. Sans risque de l'appeler
    plusieurs fois, ou sans écran affiché."""
    global _local
    try:
        if _service_alive():
            xbmcgui.Window(10000).setProperty(PROP_SPLASH, 'hide')
        if _local is not None:
            _local.close()
    except Exception:
        pass
    _local = None
    _wait('Window.IsVisible(%s)' % SPLASH_XML, False, 1.5)
