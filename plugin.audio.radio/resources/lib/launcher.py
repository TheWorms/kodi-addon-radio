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


def hand_off(handle):
    """Entrée plugin : confie l'ouverture à l'entrée script et remplace
    l'explorateur par l'accueil. L'appelant n'a plus rien à faire."""
    import xbmcplugin
    if _service_alive():
        xbmcgui.Window(10000).setProperty(PROP_SPLASH, 'show')
    xbmc.executebuiltin('RunScript(%s,%s)' % (ADDON_ID, HANDOFF_ARG))
    xbmcplugin.endOfDirectory(handle, succeeded=False, cacheToDisc=False)
    xbmc.executebuiltin('ReplaceWindow(home)')


def splash_show(addon_path):
    """Entrée script : écran de chargement (show() et non doModal() : un
    dialogue modal empêcherait Kodi de changer de fenêtre dessous)."""
    global _local
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
    """Sans risque de l'appeler plusieurs fois, ou sans écran affiché."""
    global _local
    try:
        if _service_alive():
            xbmcgui.Window(10000).setProperty(PROP_SPLASH, 'hide')
        if _local is not None:
            _local.close()
    except Exception:
        pass
    _local = None


def go_home(handed_off, timeout=3.0):
    """Attend que l'accueil soit la fenêtre active, pour que l'interface
    s'ouvre par-dessus lui. Retourne True si c'est le cas.

    handed_off : l'entrée plugin a déjà demandé le remplacement, il suffit
    d'attendre qu'il soit fait (ouvrir l'interface avant la refermerait).
    Sinon (favori, Programmes, menu du skin) on le demande ici si
    l'explorateur est affiché."""
    is_home = 'Window.IsActive(home)'
    if xbmc.getCondVisibility(is_home):
        return True
    if not handed_off:
        if not xbmc.getCondVisibility(_EXPLORER):
            return False  # lancé d'ailleurs (lecteur, autre addon) : on n'y touche pas
        xbmc.executebuiltin('ReplaceWindow(home)')
    monitor = xbmc.Monitor()
    deadline = time.time() + timeout
    while time.time() < deadline:
        if monitor.waitForAbort(0.05):
            return False
        if xbmc.getCondVisibility(is_home):
            return True
    xbmc.log('[%s] accueil non atteint en %.0f s, ouverture quand même' % (ADDON_ID, timeout),
             xbmc.LOGWARNING)
    return False
