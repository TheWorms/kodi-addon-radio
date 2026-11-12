import json
import os
import sys
import urllib.parse

import requests
import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin

addon = xbmcaddon.Addon()
L = addon.getLocalizedString

addonicon = addon.getAddonInfo('icon')
addonfanart = addon.getAddonInfo('fanart')

script_file = os.path.realpath(__file__)
addondir = os.path.dirname(script_file)

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0"
REF = "https://www.radio.fr/"
headers = {
    'Referer': REF,
    'User-Agent': UA,
    'Accept-Language': 'fr-FR,fr;q=0.9',
}

no_image = "special://home/addons/plugin.audio.radio/no_image.jpg"

API_HOST = "prod.radio-api.net"
DEFAULT_LOCAL = ("https://prod.radio-api.net/stations/local"
                 "?count=25&offset=0")


def api_url_ok(url):
    """Liste blanche : seule l'API officielle est interrogee. Le
    parametre url d'un plugin:// peut etre forge par un favori ou un
    autre addon ; les contournements du type prod.radio-api.net.evil.com
    ou evil.com/@prod.radio-api.net sont refuses (audit v1.2.14)."""
    try:
        parsed = urllib.parse.urlparse(url or "")
    except ValueError:
        return False
    return (parsed.scheme == "https"
            and parsed.netloc.lower() == API_HOST)


def stream_ok(url):
    """La lecture n'accepte que http/https : un favori ou une entree
    d'API altere ne fait plus lire file:// ou un autre schema."""
    try:
        return urllib.parse.urlparse(url or "").scheme in ("http", "https")
    except ValueError:
        return False

def render_stations(stud_list):
    """Rend une liste de stations de l'API radio-api.net.
    Garde PAR station : une entree malformee (sans stream, champ absent)
    est ignoree au lieu de faire echouer la page entiere."""
    for i in stud_list:
        try:
            name = i.get('name') or ''
            image = (i.get('logo300x300') or i.get('logo630x630')
                     or i.get('logo100x100') or no_image)
            streams = i.get('streams') or []
            if not name or not streams or not streams[0].get('url'):
                continue
            url = streams[0]['url']
            city = i.get('city') or ''
            country = i.get('country') or ''
            genres = ', '.join(i.get('genres') or [])
            place = ', '.join(p for p in (city, country) if p)
            desc = (place + '[CR]' if place else '') + genres
            addLink(url, name, image, desc, '', '')
        except Exception as e:
            xbmc.log('plugin.audio.radio: station ignoree (%s)' % e,
                     xbmc.LOGWARNING)


def MENU():
    addDir(L(30000), '-', 2, addonicon, '', L(30000))
    addDir(L(30001), '-', 3, addonicon, '', L(30001))
    addDir(L(30002), '-', 5, addonicon, '', L(30002))

def STATIONS(page, next_mode):
    """LOCAL() et SEARCH() fusionnees : meme rendu (render_stations),
    seule la page suivante differe (mode 2 = liste locale, 4 = recherche)."""
    try:
        # Retour au menu : mode 99 (menu classique reel). L'ancien mode
        # vide faisait planter int(mode) au clic (audit v1.2.14).
        addDir('[B]%s[/B]' % L(30003), '-', 99, addonicon, '', '')
        r = requests.get(page, headers=headers, timeout=5)
        r.raise_for_status()
        json_data = json.loads(r.content.decode())
        stud_list = json_data['playables']
        count = int(json_data['totalCount'])
        render_stations(stud_list)
        # Pagination : l'offset est extrait puis reconstruit via urllib.parse
        # (plus robuste que l'ancienne regex sur l'URL).
        parsed = urllib.parse.urlparse(page)
        query = urllib.parse.parse_qs(parsed.query)
        offset = int(query.get('offset', ['0'])[0]) + 25
        if offset < count:
            query['offset'] = [str(offset)]
            nextpage = urllib.parse.urlunparse(parsed._replace(query=urllib.parse.urlencode(query, doseq=True)))
            addDir('[B]%s[/B] [B]>>>[/B]' % L(30004), nextpage, next_mode, addonicon, '', '')
    except Exception as e:
        xbmc.log('plugin.audio.radio: erreur de chargement des stations (%s) : %s'
                 % (page, e), xbmc.LOGERROR)
        # Dialog().notification : plus de builtin Notification(), casse par
        # un nom de station avec virgules ou parentheses (audit v1.2.14)
        xbmcgui.Dialog().notification(L(30005), L(30006), addonicon, 5000)

def MYSTATIONS():
    # v1.1.0 : favoris partages avec la nouvelle interface (favorites.json,
    # migration automatique de l'ancien sender.txt)
    for f in _rui.load_favorites():
        addMy(f.get('url', ''), f.get('name', ''), f.get('logo', ''),
              '', '', '')

def ADDSTATION(url, name, image):
    _rui.add_favorite(name, url, image)
    xbmcgui.Dialog().notification(name, L(30009), addonicon, 5000)

def DELSTATION(url):
    _rui.remove_favorite(url)
    xbmc.executebuiltin("Container.Refresh")

def addLink(link, name, image, desc, urlType, fanart):
    liz = xbmcgui.ListItem(name)
    url = sys.argv[0] + "?url=" + urllib.parse.quote_plus(link) + "&mode=1&name=" + urllib.parse.quote_plus(name) + "&description=" + urllib.parse.quote_plus(desc) + "&iconimage=" + urllib.parse.quote_plus(image)
    add = sys.argv[0] + "?url=" + urllib.parse.quote_plus(link) + "&mode=6&name=" + urllib.parse.quote_plus(name) + "&image=" + urllib.parse.quote_plus(image)
    tag = liz.getMusicInfoTag()
    tag.setTitle(name)
    tag.setComment(desc)
    liz.setArt({'icon': image, 'thumb': image, 'poster': image, 'fanart': addonfanart})
    contextMenuItems = []
    contextMenuItems.append((L(30007), f'RunPlugin(plugin://plugin.audio.radio/{add})'))
    liz.addContextMenuItems(contextMenuItems, replaceItems=True)
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=liz)

def addMy(link, name, image, desc, urlType, fanart):
    liz = xbmcgui.ListItem(name)
    url = sys.argv[0] + "?url=" + urllib.parse.quote_plus(link) + "&mode=1&name=" + urllib.parse.quote_plus(name) + "&description=" + urllib.parse.quote_plus(desc) + "&iconimage=" + urllib.parse.quote_plus(image)
    rem = sys.argv[0] + "?url=" + urllib.parse.quote_plus(link) + "&mode=7"
    tag = liz.getMusicInfoTag()
    tag.setTitle(name)
    tag.setComment(desc)
    liz.setArt({'icon': image, 'thumb': image, 'poster': image, 'fanart': addonfanart})
    contextMenuItems = []
    contextMenuItems.append((L(30008), f'RunPlugin(plugin://plugin.audio.radio/{rem})'))
    liz.addContextMenuItems(contextMenuItems, replaceItems=True)
    xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=liz)

def addDir(name, url, mode, iconimage, fanart, description):
    u = sys.argv[0] + "?url=" + urllib.parse.quote_plus(url) + "&mode=" + str(mode) + "&name=" + urllib.parse.quote_plus(name) + "&iconimage=" + urllib.parse.quote_plus(iconimage) + "&fanart=" + urllib.parse.quote_plus(fanart) + "&description=" + urllib.parse.quote_plus(description)
    liz = xbmcgui.ListItem(name)
    tag = liz.getMusicInfoTag()
    tag.setTitle(name)
    tag.setComment(description)
    liz.setArt({'icon': iconimage, 'thumb': iconimage, 'fanart': addonfanart})
    ok = xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=u, listitem=liz, isFolder=True)
    return ok

def get_bool_setting(key, fallback=True):
    try:
        return addon.getSettingBool(key)
    except Exception:
        v = addon.getSetting(key)
        if v == '':
            return fallback
        return v == 'true'

# La vue cinema vit desormais dans resources/lib/cinema.py (partagee
# avec l'interface plein ecran).
sys.path.append(os.path.join(addondir, 'resources', 'lib'))
from cinema import RadioCinema  # noqa: E402
import radio_ui as _rui  # noqa: E402

# Fond du menu classique : l'image choisie dans Configuration remplace le
# fanart historique (radio.de) ; repli sur le fanart de l'addon.
addonfanart = _rui.background_path() or addonfanart


def get_params():
    params = {}
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        cleanedparams = paramstring.replace('?', '')
        if cleanedparams.endswith('/'):
            cleanedparams = cleanedparams[:-1]
        for pair in cleanedparams.split('&'):
            if '=' in pair:
                key, value = pair.split('=', 1)
                params[key] = value
    return params

params = get_params()
url = urllib.parse.unquote_plus(params['url']) if 'url' in params else None
name = urllib.parse.unquote_plus(params['name']) if 'name' in params else None
try:
    mode = int(params['mode']) if 'mode' in params else None
except ValueError:
    # mode vide ou non numerique (favori forge, appel manuel) : traite
    # comme absent, aucun plantage (audit v1.2.14)
    mode = None
iconimage = urllib.parse.unquote_plus(params['iconimage']) if 'iconimage' in params else None
fanart = urllib.parse.unquote_plus(params['fanart']) if 'fanart' in params else None
description = urllib.parse.unquote_plus(params['description']) if 'description' in params else None

xbmc.log("plugin.audio.radio: mode=%s url=%s name=%s"
         % (mode, url, name), xbmc.LOGDEBUG)

if mode == None or url == None or len(url) < 1:
    if get_bool_setting('ui.fullscreen', True):
        # Nouvelle interface plein écran (v1.1.0). endOfDirectory d'abord :
        # l'invocation plugin rend la main a Kodi, puis la fenetre modale
        # s'affiche (meme mecanique que la vue cinema du mode 1).
        xbmcplugin.endOfDirectory(int(sys.argv[1]), succeeded=False,
                                  cacheToDisc=False)
        # NE PAS appeler ReplaceWindow ici : executebuiltin est asynchrone,
        # le changement de fenetre arrivait PENDANT l'ouverture de
        # l'interface et la refermait aussitot -> boucle ouverture/retour.
        # Depuis la v1.1.4 l'interface est un WindowXML : elle remplace
        # elle-meme la fenetre courante, aucun menage prealable requis.
        try:
            _rui.open_home()
        except Exception as e:
            xbmc.log('plugin.audio.radio: UI error, fallback menu (%s)' % e,
                     xbmc.LOGERROR)
            xbmc.executebuiltin(
                'ActivateWindow(Music,plugin://plugin.audio.radio/?mode=99)')
    else:
        MENU()
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
elif mode == 99:
    # menu classique force (repli de la nouvelle interface)
    MENU()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
elif mode == 1:
    if not stream_ok(url):
        xbmc.log('plugin.audio.radio: flux refuse (schema non http/https) : %s'
                 % url, xbmc.LOGWARNING)
        xbmcplugin.endOfDirectory(int(sys.argv[1]), succeeded=False,
                                  cacheToDisc=False)
    else:
        listitem = xbmcgui.ListItem(name)
        listitem.setArt({'icon': iconimage, 'thumb': iconimage})
        # windowed : ne pas basculer Kodi en plein ecran au demarrage du son
        # (fenetre de visualisation, reglage musicfiles.selectaction). La vue
        # logo de la station est l'affichage d'ecoute par defaut (v1.2.13).
        xbmc.Player().play(url, listitem, True)
        if get_bool_setting('cinema.enabled', True):
            try:
                w = RadioCinema('script-radio-cinema.xml', addondir, 'Default', '720p')
                w.set_data(iconimage, name, get_bool_setting('cinema.pulsebar', True))
                w.doModal()
                del w
            except Exception as e:
                xbmc.log('plugin.audio.radio cinema error: %s' % str(e), xbmc.LOGERROR)
elif mode == 2:
    if not api_url_ok(url):
        url = DEFAULT_LOCAL
    STATIONS(url, 2)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
elif mode == 3:
    kb = xbmc.Keyboard('default', 'heading', False)
    kb.setDefault('')
    kb.setHeading(L(30010))
    kb.setHiddenInput(False)
    kb.doModal()
    if (kb.isConfirmed()):
        try:
            search = kb.getText()
            search = ('https://prod.radio-api.net/stations/search?query='
                      + urllib.parse.quote_plus(search) + '&count=25&offset=0')
            STATIONS(search, 4)
        except Exception as e:
            xbmc.log('plugin.audio.radio: recherche echouee (%s)' % e,
                     xbmc.LOGERROR)
    else:
        MENU()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
elif mode == 4:
    if api_url_ok(url):
        STATIONS(url, 4)
        xbmcplugin.endOfDirectory(int(sys.argv[1]))
    else:
        xbmc.log('plugin.audio.radio: URL refusee (hors API) : %s' % url,
                 xbmc.LOGWARNING)
        xbmcplugin.endOfDirectory(int(sys.argv[1]), succeeded=False,
                                  cacheToDisc=False)
elif mode == 5:
    MYSTATIONS()
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
elif mode == 6:
    image = params.get('image')
    image = urllib.parse.unquote_plus(image) if image else ""
    if "special://" in image or image == "":
        image = addonicon  # icone locale : pas de dependance a un hebergeur externe
    ADDSTATION(url, name, image)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
elif mode == 7:
    DELSTATION(url)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))
