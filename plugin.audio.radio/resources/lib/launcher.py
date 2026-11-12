# -*- coding: utf-8 -*-
"""Lancement de l'interface plein écran : écran de chargement, et accueil
de Kodi placé SOUS l'interface.

Module volontairement léger (xbmc et xbmcgui seulement) : il est chargé
avant tout le reste pour que l'écran de chargement s'affiche au plus tôt.

L'écran de chargement est une FENÊTRE, pas un dialogue. Kodi refuse tout
changement de fenêtre tant qu'un dialogue est affiché : il fallait donc le
fermer avant d'ouvrir l'interface, et l'accueil réapparaissait une
demi-seconde entre les deux. Une fenêtre, elle, est remplacée directement
par l'interface, sans rien montrer d'autre. Une fois l'interface affichée,
la fenêtre de chargement est détruite : Kodi la retire alors de son
historique, et la fermeture de l'interface ramène droit à l'accueil.

Pourquoi passer par l'accueil : lancé comme plugin (Extensions, ou
raccourci ActivateWindow), l'addon est affiché par Kodi dans l'explorateur
de fichiers AVANT que la moindre ligne de l'addon ne s'exécute. Si
l'interface s'ouvrait par-dessus, sa fermeture rendrait la main à
l'explorateur. L'entrée plugin le remplace donc par l'accueil puis confie
l'ouverture à l'entrée script (RunScript). Lancé directement par
RunScript(<id de l'addon>) (raccourci du menu d'accueil, favori),
l'explorateur n'est jamais ouvert.
"""
import threading
import time

import xbmc
import xbmcgui

ADDON_ID = 'plugin.audio.radio'
SPLASH_XML = 'script-radio-splash.xml'
SPLASH_RES = '720p'
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
_SPLASH_VISIBLE = 'Window.IsVisible(%s)' % SPLASH_XML

_splash = None
_lock = threading.Lock()


class _Splash(xbmcgui.WindowXML):
    def onAction(self, action):
        pass  # Retour ne ferme pas l'écran de chargement : l'interface arrive


def user_open():
    """Ouverture par l'utilisateur, interface pas déjà affichée (remplacer
    la fenêtre courante par l'accueil la refermerait)."""
    if xbmc.getCondVisibility('Window.IsVisible(%s)' % MAIN_XML):
        return False
    return not xbmc.getCondVisibility(_NOT_USER)


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
    _wait('Window.IsActive(home)', True, 2.0)
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


def _take():
    global _splash
    with _lock:
        win, _splash = _splash, None
    return win


def _release():
    """Fil de fond : dès que l'interface a pris la place de l'écran de
    chargement, celui-ci est détruit. Kodi le retire de son historique des
    fenêtres ; sans cela, la fermeture de l'interface le réafficherait."""
    _wait(_SPLASH_VISIBLE, False, 60.0)
    xbmc.Monitor().waitForAbort(0.2)  # laisse Kodi finir d'installer l'interface
    win = _take()
    del win  # plus aucune référence : Kodi détruit la fenêtre


def splash_show(addon_path):
    """Entrée script, APRÈS go_home : écran de chargement pendant le
    chargement des modules. Reste affiché jusqu'à ce que l'interface le
    remplace (ou jusqu'à splash_hide)."""
    global _splash
    try:
        win = _Splash(SPLASH_XML, addon_path, 'Default', SPLASH_RES)
        win.show()
        with _lock:
            _splash = win
        threading.Thread(target=_release, name='%s-splash' % ADDON_ID, daemon=True).start()
    except Exception as exc:  # l'écran de chargement n'est jamais bloquant
        xbmc.log('[%s] écran de chargement : %s' % (ADDON_ID, exc), xbmc.LOGWARNING)


def splash_hide():
    """À appeler en fin de script. Si l'interface ne s'est pas ouverte
    (erreur, relance ignorée), l'écran de chargement est encore là : on le
    ferme, Kodi revient à la fenêtre précédente. Sans effet sinon."""
    win = _take()
    if win is None:
        return
    try:
        if xbmc.getCondVisibility(_SPLASH_VISIBLE):
            win.close()
    except Exception:
        pass
    del win
