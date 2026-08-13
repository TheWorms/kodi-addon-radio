# -*- coding: utf-8 -*-
"""
radio_ui.py — interface plein écran "façon radio.fr" (v1.1.0) + favoris JSON.

Architecture calquée sur les patterns éprouvés du fork SoundCloud :
  - WindowXMLDialog + listes horizontales alimentées par un thread de
    chargement (une garde try/except PAR rangée : une rangée en échec
    n'empêche pas les autres de s'afficher) ;
  - égaliseur pseudo-réactif dans la barre de lecture : Kodi n'expose pas
    l'audio aux addons, les barres sont animées par un thread (setHeight)
    avec une graine dérivée du nom de la station — même approche que le
    visualiseur waveform SoundCloud ;
  - le thread écrit uniquement sur des contrôles ajoutés par addControl
    et s'arrête via un Event + join court avant la fermeture.

Favoris : nouveau format favorites.json (liste de {name,url,logo}).
Migration automatique et unique depuis l'ancien sender.txt
(###NAME###...###URL###...###LOGO###...###) ; l'ancien fichier est
conservé en sender.txt.bak après migration.
"""

import base64
import json
import os
import re
import threading
import time

import requests
import xbmc
import xbmcaddon
import xbmcgui
import xbmcvfs

ADDON = xbmcaddon.Addon()
ADDON_PATH = xbmcvfs.translatePath(ADDON.getAddonInfo("path"))
PROFILE = xbmcvfs.translatePath(ADDON.getAddonInfo("profile"))

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) "
      "Gecko/20100101 Firefox/125.0")
HEADERS = {
    "Referer": "https://www.radio.fr/",
    "User-Agent": UA,
    "Accept-Language": "fr-FR,fr;q=0.9",
}
API = "https://prod.radio-api.net/stations/"

L = ADDON.getLocalizedString


def log(msg, level=xbmc.LOGINFO):
    xbmc.log("plugin.audio.radio(ui): %s" % msg, level)


# Lecture des reglages en TEXTE (getSetting) avec repli sur le defaut :
# getSettingInt/getSettingBool se sont reveles peu fiables sur les
# settings v2 a <options> (mode d'ecoute lu 0 au lieu de 1, pulsation
# ignoree). getSetting renvoie toujours la valeur brute ('true'/'false'
# ou un nombre en texte, '' si jamais ecrite) -- c'est le pattern deja
# eprouve par get_bool_setting() du menu classique.
def s_bool(key, default=True):
    try:
        v = xbmcaddon.Addon().getSetting(key)
    except Exception:
        return default
    if v == "":
        return default
    return v == "true"


def s_str(key, default=""):
    try:
        v = xbmcaddon.Addon().getSetting(key)
        return v if v else default
    except Exception:
        return default


def s_int(key, default=0):
    try:
        v = xbmcaddon.Addon().getSetting(key)
        return int(v) if v != "" else default
    except (ValueError, Exception):
        return default


# ------------------------------------------------------------------ favoris --
FAV_JSON = os.path.join(PROFILE, "favorites.json")
LEGACY_TXT = os.path.join(PROFILE, "sender.txt")


def _ensure_profile():
    if not os.path.isdir(PROFILE):
        try:
            os.makedirs(PROFILE)
        except OSError:
            pass


def load_favorites():
    """Liste de dicts {name,url,logo}. Migre sender.txt une seule fois."""
    _ensure_profile()
    if os.path.exists(FAV_JSON):
        try:
            with open(FAV_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except (ValueError, OSError):
            return []
    # migration depuis l'ancien format texte
    favs = []
    if os.path.exists(LEGACY_TXT):
        try:
            raw = open(LEGACY_TXT, "r", encoding="utf-8",
                       errors="ignore").read()
            for name, url, logo in re.compile(
                    r"###NAME###(.+?)###URL###(.+?)###LOGO###(.+?)###"
            ).findall(raw):
                favs.append({"name": name, "url": url, "logo": logo})
            save_favorites(favs)
            os.replace(LEGACY_TXT, LEGACY_TXT + ".bak")
            log("Favoris migres sender.txt -> favorites.json (%d)" % len(favs))
        except OSError as e:
            log("Migration favoris impossible: %s" % e, xbmc.LOGWARNING)
    else:
        save_favorites(favs)
    return favs


def save_favorites(favs):
    _ensure_profile()
    tmp = FAV_JSON + ".tmp"
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(favs, f, ensure_ascii=False)
        os.replace(tmp, FAV_JSON)
    except OSError as e:
        log("save_favorites: %s" % e, xbmc.LOGWARNING)


def is_favorite(url):
    return any(f.get("url") == url for f in load_favorites())


def add_favorite(name, url, logo):
    favs = load_favorites()
    if not any(f.get("url") == url for f in favs):
        favs.append({"name": name, "url": url, "logo": logo or ""})
        save_favorites(favs)
        return True
    return False


def remove_favorite(url):
    favs = load_favorites()
    kept = [f for f in favs if f.get("url") != url]
    if len(kept) != len(favs):
        save_favorites(kept)
        return True
    return False


# ---------------------------------------------------------------------- API --
def fetch_stations(url):
    """Retourne (liste playables, totalCount). Garde par appel."""
    r = requests.get(url, headers=HEADERS, timeout=5)
    data = json.loads(r.content.decode())
    return data.get("playables") or [], int(data.get("totalCount") or 0)


def station_fields(i):
    """Extrait (name, stream, logo, sous-titre) d'une entrée API,
    None si inutilisable — garde PAR station."""
    name = i.get("name") or ""
    streams = i.get("streams") or []
    if not name or not streams or not streams[0].get("url"):
        return None
    logo = (i.get("logo300x300") or i.get("logo630x630")
            or i.get("logo100x100") or "")
    city = i.get("city") or ""
    country = i.get("country") or ""
    place = ", ".join(p for p in (city, country) if p)
    genres = ", ".join((i.get("genres") or [])[:2])
    return name, streams[0]["url"], logo, (place or genres)


# Genres proposés par le bouton Genres. L'API n'expose pas de route de
# listing publique stable : chaque genre interroge la recherche, qui
# matche aussi le champ genre des stations.
GENRES = ["Jazz", "Rock", "Pop", "Électro", "Rap", "Classique", "Chill",
          "Oldies", "Métal", "Reggae", "Country", "Info", "Sport", "Enfants"]

# Nombre de stations chargees par rangee (defilement horizontal).
STATIONS_PER_ROW = 16


BG_FILES = {1: "bg1.jpg", 2: "bg2.jpg", 3: "bg3.jpg", 4: "bg4.jpg"}


def background_path():
    """Chemin de l'image de fond choisie dans les reglages, '' si fond uni
    ou fichier absent. Utilise aussi par le menu classique (fanart)."""
    bg = BG_FILES.get(s_int("ui.background", 0))
    if not bg:
        return ""
    path = os.path.join(ADDON_PATH, "resources", "skins", "Default",
                        "media", bg)
    return path if os.path.exists(path) else ""


def nowbar_mode():
    """0 = logo plein ecran (vue cinema), 1 = barre en bas. Exclusif."""
    return 1 if s_int("ui.nowplaying", 1) == 1 else 0


def genre_setting():
    """Genre de la rangee d'accueil, choisi dans une liste (0 = aucune)."""
    idx = s_int("ui.genre_row", 1)
    if 1 <= idx <= len(GENRES):
        return GENRES[idx - 1]
    return ""

def white_px():
    """Chemin d'une texture blanche TOUJOURS disponible.

    Le white.png du dossier media peut manquer (mise a jour partielle,
    zip sans binaires) : dans ce cas toutes les textures de l'interface
    -- dont le fond opaque -- ne rendent rien et le skin transparait
    derriere. On genere donc notre propre 1x1 dans le profil et on
    l'utilise pour TOUS les aplats (fond, voiles, barres, boutons)."""
    _ensure_profile()
    path = os.path.join(PROFILE, "white.png")
    if not os.path.exists(path):
        try:
            with open(path, "wb") as f:
                f.write(base64.b64decode(
                    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4"
                    "2mP8/x8AAwMCAO+ip1sAAAAASUVORK5CYII="))
        except OSError:
            shipped = os.path.join(ADDON_PATH, "resources", "skins",
                                   "Default", "media", "white.png")
            return shipped if os.path.exists(shipped) else ""
    return path


# ------------------------------------------------------------- égaliseur ----
class _EqUpdater(threading.Thread):
    """Anime les barres (setHeight) tant que la lecture tourne.
    Pseudo-réactif : graine par station, trois zones (basses/médiums/aigus)
    aux cadences différentes. Arrêt par Event, jamais d'accès après stop."""
    TICK = 0.09

    def __init__(self, bars, base_y, max_h):
        super().__init__(daemon=True)
        self._bars = bars
        self._base_y = base_y
        self._max_h = max_h
        self._stop = threading.Event()
        self._t = 0.0
        self._seed = 1

    def set_station(self, name):
        h = 0
        for c in (name or "x"):
            h = (h * 31 + ord(c)) & 0x7FFFFFFF
        self._seed = h or 1

    def stop(self):
        self._stop.set()

    def run(self):
        import math
        player = xbmc.Player()
        n = len(self._bars)
        while not self._stop.is_set():
            try:
                playing = player.isPlaying()
            except Exception:
                playing = False
            self._t += self.TICK
            for idx, bar in enumerate(self._bars):
                if self._stop.is_set():
                    return
                try:
                    if not playing:
                        h = 2
                    else:
                        zone = 0.6 if idx < n // 3 else (
                            1.6 if idx < 2 * n // 3 else 2.6)
                        phase = ((self._seed >> (idx % 24)) & 0xFF) / 40.0
                        amp = 0.35 + (((self._seed >> (idx % 16)) & 0x3F) / 63.0) * 0.6
                        v = abs(math.sin(self._t * zone + phase)) * amp
                        h = max(2, int(self._max_h * v))
                    bar.setHeight(h)
                    bar.setPosition(bar.getX(), self._base_y - h)
                except Exception:
                    return  # contrôle disparu (fenêtre fermée) -> sortie propre
            if self._stop.wait(self.TICK):
                return


# ------------------------------------------------------------- la fenêtre ---
ROW_LIST_IDS = (210, 220, 230)
BTN_SEARCH, BTN_SETTINGS = 110, 112
BTN_STOP = 310
# Fermeture : large filet d'ids selon les telecommandes/claviers --
# PARENT_DIR(9), PREVIOUS_MENU(10), NAV_BACK(92), STOP(13),
# BACKSPACE(110 clavier), MENU(117 gere a part), plus les codes remote
# generiques renvoyes par certaines box (216, 247, 275).
ACTION_CLOSE = (9, 10, 92, 13, 216, 247, 275)
ACTION_CONTEXT = (117,)

EQ_BARS = 40
EQ_X0, EQ_W, EQ_GAP = 560, 8, 5
EQ_BASE_Y, EQ_MAX_H = 710, 54


class RadioHome(xbmcgui.WindowXML):
    """Fenetre PLEINE (pas un dialogue).

    Un WindowXMLDialog est dessine PAR-DESSUS la fenetre du skin : il n'a
    pas de fond propre, le fanart de l'addon et les widgets du skin
    restent visibles derriere, et la pile de fenetres complique la
    fermeture. Un WindowXML remplace la fenetre courante : fond opaque
    natif (<backgroundcolor>), retour gere par Kodi, aucune transparence.
    """


    def _apply_background(self):
        # ui.solid : texture d'aplat garantie, utilisee par TOUS les
        # controles du XML (fond, voiles, boutons, tuiles). Ne depend
        # plus d'un fichier media qui pourrait manquer.
        solid = white_px()
        self.setProperty("ui.solid", solid)
        self.setProperty("ui.nowbar", "1" if nowbar_mode() == 1 else "0")
        path = background_path()
        if path:
            self.setProperty("ui.bg", path)
            self.setProperty("ui.bgmode", "photo")
            log("fond photo: %s" % path)
        else:
            if s_int("ui.background", 0):
                log("fond photo introuvable -> uni", xbmc.LOGWARNING)
                xbmcgui.Dialog().notification(
                    "Radio", L(30135), xbmcgui.NOTIFICATION_WARNING, 6000)
            self.setProperty("ui.bg", solid)
            self.setProperty("ui.bgmode", "solid")

    def onInit(self):
        log("RadioHome onInit — addon v%s"
            % xbmcaddon.Addon().getAddonInfo("version"))
        self._mode = "home"
        self._cinema = None
        self._apply_background()
        self._eq = None
        self._eq_bars = []
        self._playing_url = ""
        self.setProperty("np.playing", "0")
        self.setProperty("np.name", "")
        self.setProperty("np.logo", "")
        if s_bool("eq.enabled", True) and nowbar_mode() == 1:
            self._build_eq()
        threading.Thread(target=self._load_home, daemon=True).start()

    # ---------- construction ----------
    def _build_eq(self):
        px = white_px()
        if not px:
            return
        for i in range(EQ_BARS):
            bar = xbmcgui.ControlImage(
                EQ_X0 + i * (EQ_W + EQ_GAP), EQ_BASE_Y - 2, EQ_W, 2,
                px, colorDiffuse="FFFFB454")
            self._eq_bars.append(bar)
        try:
            self.addControls(self._eq_bars)
        except Exception as e:
            log("addControls eq: %s" % e, xbmc.LOGWARNING)
            self._eq_bars = []
            return
        self._eq = _EqUpdater(self._eq_bars, EQ_BASE_Y, EQ_MAX_H)
        self._eq.start()

    def _rows_spec_home(self):
        per_row = STATIONS_PER_ROW
        rows = [
            (L(30002), "favorites", ""),
            (L(30000), "api", API + "local?count=%d&offset=0" % per_row),
        ]
        genre = genre_setting()
        if genre:
            rows.append((genre, "api",
                         API + "search?query=%s&count=%d&offset=0"
                         % (requests.utils.quote(genre), per_row)))
        else:
            # Pas de rangee genre -> on tente les "top". L'endpoint varie
            # selon l'API : candidats essayes dans l'ordre, rangee masquee
            # si aucun ne repond.
            rows.append((L(30120), "api_multi", [
                API + "top?count=%d&offset=0" % per_row,
                API + "list-by-system-name?systemName=STATIONS_TOP"
                      "&count=%d&offset=0" % per_row,
            ]))
        return rows[:3]

    def _load_home(self):
        self._mode = "home"
        self._fill_rows(self._rows_spec_home())

    def _fill_rows(self, spec):
        for idx, list_id in enumerate(ROW_LIST_IDS):
            title, kind, url = spec[idx] if idx < len(spec) else ("", "", "")
            self.setProperty("row%d.title" % idx, title)
            self.setProperty("row%d.count" % idx, "")
            try:
                ctrl = self.getControl(list_id)
                ctrl.reset()
                if not kind:
                    continue
                if kind == "favorites":
                    items, total = self._favorite_items()
                elif kind == "api_multi":
                    items, total = [], 0
                    for candidate in url:
                        try:
                            items, total = self._api_items(candidate)
                        except Exception:
                            items, total = [], 0
                        if items:
                            break
                    if not items:
                        # aucun candidat ne repond : on masque la rangee
                        self.setProperty("row%d.title" % idx, "")
                        continue
                else:
                    items, total = self._api_items(url)
                if items:
                    ctrl.addItems(items)
                self.setProperty("row%d.count" % idx,
                                 "%d stations" % total if total else "")
            except Exception as e:
                # garde PAR rangée : les autres rangées s'affichent
                log("rangée %r en échec: %s" % (title, e), xbmc.LOGWARNING)

    def _favorite_items(self):
        favs = load_favorites()
        items = []
        for f in favs:
            li = xbmcgui.ListItem(f.get("name") or "")
            li.setLabel2("★")
            li.setArt({"thumb": f.get("logo") or ""})
            li.setProperty("stream", f.get("url") or "")
            li.setProperty("logo", f.get("logo") or "")
            items.append(li)
        return items, len(favs)

    def _api_items(self, url):
        playables, total = fetch_stations(url)
        items = []
        for i in playables:
            fields = station_fields(i)
            if not fields:
                continue
            name, stream, logo, sub = fields
            li = xbmcgui.ListItem(name)
            li.setLabel2(sub)
            li.setArt({"thumb": logo})
            li.setProperty("stream", stream)
            li.setProperty("logo", logo)
            items.append(li)
        return items, total

    # ---------- interactions ----------
    def onClick(self, control_id):
        if control_id in ROW_LIST_IDS:
            try:
                item = self.getControl(control_id).getSelectedItem()
            except Exception:
                item = None
            if item:
                self._play(item.getLabel(),
                           item.getProperty("stream"),
                           item.getProperty("logo"))
            return
        if control_id == BTN_SEARCH:
            self._do_search()
        elif control_id == BTN_SETTINGS:
            xbmcaddon.Addon().openSettings()
            # openSettings est bloquant : au retour, on applique
            # immediatement les nouveaux reglages (fond, mode de lecture,
            # rangee de genre) sans avoir a ressortir de l'addon.
            self._refresh_settings()
        elif control_id == BTN_STOP:
            self._stop_playback()

    def onAction(self, action):
        aid = action.getId()
        log("onAction id=%d focus=%d mode=%s"
            % (aid, self.getFocusId(), self._mode), xbmc.LOGDEBUG)
        if aid in ACTION_CONTEXT:
            self._toggle_favorite_focused()
            return
        if aid in ACTION_CLOSE:
            if self._mode != "home":
                # retour depuis une vue genre/recherche -> accueil
                threading.Thread(target=self._load_home, daemon=True).start()
                return
            self._quit()
            return
        super().onAction(action)

    def _refresh_settings(self):
        self._apply_background()
        # l'egaliseur suit le mode d'affichage choisi
        if nowbar_mode() == 1 and s_bool("eq.enabled", True):
            if not self._eq:
                self._build_eq()
        elif self._eq:
            self._eq.stop()
            self._eq = None
        if self._mode == "home":
            threading.Thread(target=self._load_home, daemon=True).start()
        # Exclusivite appliquee IMMEDIATEMENT, meme en cours de lecture :
        # - passage en mode barre -> fermer la vue plein ecran si ouverte ;
        # - passage en mode logo pendant l'ecoute -> l'ouvrir sur-le-champ.
        try:
            playing = xbmc.Player().isPlaying()
        except Exception:
            playing = False
        if nowbar_mode() == 1 and self._cinema is not None:
            try:
                self._cinema.close()
            except Exception:
                pass
        elif nowbar_mode() == 0 and playing and self._cinema is None:
            self._open_cinema(self.getProperty("np.logo"),
                              self.getProperty("np.name"))

    def _quit(self):
        """Sortie unique et sure : arrete le thread eq puis ferme."""
        try:
            self._teardown()
        except Exception:
            pass
        self.close()

    def _toggle_favorite_focused(self):
        fid = self.getFocusId()
        if fid not in ROW_LIST_IDS:
            return
        try:
            item = self.getControl(fid).getSelectedItem()
        except Exception:
            return
        if not item:
            return
        name = item.getLabel()
        url = item.getProperty("stream")
        logo = item.getProperty("logo")
        if not url:
            return
        if is_favorite(url):
            remove_favorite(url)
            xbmcgui.Dialog().notification("Radio", L(30008), time=3000)
        else:
            add_favorite(name, url, logo)
            xbmcgui.Dialog().notification("Radio", L(30009), time=3000)
        if self._mode == "home":
            # rafraîchir la rangée favoris
            spec = self._rows_spec_home()
            try:
                ctrl = self.getControl(ROW_LIST_IDS[0])
                ctrl.reset()
                items, total = self._favorite_items()
                if items:
                    ctrl.addItems(items)
                self.setProperty("row0.count",
                                 "%d stations" % total if total else "")
            except Exception:
                pass

    def _do_search(self):
        kb = xbmc.Keyboard("", L(30010))
        kb.doModal()
        if not kb.isConfirmed():
            return
        query = kb.getText().strip()
        if not query:
            return
        per_row = STATIONS_PER_ROW
        base = API + "search?query=%s" % requests.utils.quote(query)
        self._mode = "search"
        # La rangee 0 (Mes stations) est CONSERVEE : les favoris restent
        # accessibles pendant une recherche ou une exploration par genre.
        spec = [
            (L(30002), "favorites", ""),
            (u"%s « %s »" % (L(30121), query), "api",
             base + "&count=%d&offset=0" % per_row),
            (L(30122), "api", base + "&count=%d&offset=%d" % (per_row, per_row)),
        ]
        threading.Thread(target=self._fill_rows, args=(spec,),
                         daemon=True).start()

    # ---------- lecture ----------
    def _play(self, name, stream, logo):
        if not stream:
            return
        li = xbmcgui.ListItem(name)
        li.setArt({"thumb": logo, "icon": logo})
        tag = li.getMusicInfoTag()
        tag.setTitle(name)
        xbmc.Player().play(stream, li)
        self._playing_url = stream
        self.setProperty("np.name", name)
        self.setProperty("np.logo", logo or "")
        self.setProperty("np.playing", "1")
        if self._eq:
            self._eq.set_station(name)
        # Mode "logo plein ecran" : on ouvre la vue cinema A LA PLACE de la
        # barre du bas (les deux modes sont exclusifs). Quitter la vue ne
        # coupe PAS la radio : on revient a l'accueil, la lecture continue.
        mode = nowbar_mode()
        log("lecture %r — mode ecoute=%s (0=logo plein ecran, 1=barre)"
            % (name, mode))
        if mode == 0:
            self._open_cinema(logo, name)

    def _open_cinema(self, logo, name):
        try:
            from cinema import RadioCinema
            log("ouverture vue plein ecran (pulsation=%s)"
                % s_bool("cinema.pulsebar", True))
            w = RadioCinema("script-radio-cinema.xml", ADDON_PATH,
                            "Default", "720p")
            w.set_data(logo, name, s_bool("cinema.pulsebar", True),
                       stop_on_exit=False)
            self._cinema = w
            w.doModal()
            self._cinema = None
            del w
        except Exception as e:
            log("vue cinema indisponible: %s" % e, xbmc.LOGERROR)
            xbmcgui.Dialog().notification("Radio", str(e),
                                          xbmcgui.NOTIFICATION_WARNING, 5000)

    def _stop_playback(self):
        try:
            xbmc.Player().stop()
        except Exception:
            pass
        self._playing_url = ""
        self.setProperty("np.playing", "0")
        self.setProperty("np.name", "")
        self.setProperty("np.logo", "")

    def _teardown(self):
        if self._eq:
            self._eq.stop()
            if self._eq.is_alive():
                try:
                    self._eq.join(1.0)
                except RuntimeError:
                    pass
            self._eq = None


GUARD_PROP = "radio.ui.open"
CLOSED_PROP = "radio.ui.closed_at"
REOPEN_GRACE = 3.0   # secondes


def open_home():
    home = xbmcgui.Window(10000)

    # Garde 1 : interface deja ouverte -> ne pas empiler une 2e fenetre.
    if home.getProperty(GUARD_PROP) == "1":
        log("UI deja ouverte, relance ignoree")
        return

    # Garde 2 (anti-boucle) : apres une fermeture, le retour a l'accueil
    # peut faire relancer l'addon par un widget ou le container. Toute
    # relance dans les secondes qui suivent une fermeture est ignoree.
    try:
        closed_at = float(home.getProperty(CLOSED_PROP) or 0)
    except ValueError:
        closed_at = 0
    if closed_at and (time.time() - closed_at) < REOPEN_GRACE:
        log("relance %.1fs apres fermeture -> ignoree (anti-boucle)"
            % (time.time() - closed_at))
        return

    home.setProperty(GUARD_PROP, "1")
    try:
        win = RadioHome("script-radio-home.xml", ADDON_PATH, "Default", "720p")
        win.doModal()
        del win
    finally:
        home.clearProperty(GUARD_PROP)
        # La garde est posee AVANT le changement de fenetre : si l'accueil
        # (ou un widget) relance l'addon dans la foulee, la relance est
        # ignoree -> pas de boucle.
        home.setProperty(CLOSED_PROP, "%f" % time.time())
        # A la fermeture, Kodi revient a la fenetre d'ou l'addon a ete
        # invoque : la page (vide) du plugin dans Musique. On renvoie donc
        # explicitement a l'accueil.
        if xbmc.getCondVisibility("Window.IsActive(MyMusicNav.xml)"):
            xbmc.executebuiltin("ReplaceWindow(home)")
