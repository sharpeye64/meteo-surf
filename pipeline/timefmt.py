"""Contrat horaire des données publiées (issue #2).

FORMAT : chaque instant publié (forecast.json, data/app/, health.json) s'écrit en ISO 8601 AVEC DÉCALAGE, à l'heure LOCALE
du lieu : « 2026-11-27T10:00+01:00 » à Lacanau, « 2026-11-27T09:00+00:00 » au même instant à Ericeira (Europe/Lisbon).
  - Les 16 premiers caractères restent l'heure locale affichable (le code qui découpe t[11:16] continue de marcher) ;
  - le décalage rend l'instant exact, lisible partout (navigateur, iOS, Android, Python) quel que soit le fuseau de l'appareil ;
  - les dates seules (« 2026-11-27 ») restent des dates locales du lieu.
Fuseaux IANA par lieu : Europe/Paris (France, bouée Gascogne), Europe/Madrid (Espagne), Europe/Lisbon (Portugal continental).
Les instants physiques ne changent jamais : seule leur écriture dépend du lieu.

ORIGINE DES HEURES DANS LE ROBOT (vérifié le 27/11/2026) :
  - Open-Meteo, avec `timezone=Europe/Paris`, écrit ses séries avec UN SEUL décalage, celui du moment de la requête
    (`utc_offset_seconds`) : le 25/10/2026 compte 24 heures, sans heure répétée. Un instant Open-Meteo = heure écrite −
    utc_offset_seconds, exactement. (Avant ce lot, les heures situées après un changement d'heure étaient donc décalées d'1 h.)
  - Mesures des bouées, marées : heure murale de Paris (converties depuis l'UTC par zoneinfo). Pendant l'heure répétée
    d'octobre, une série ordonnée permet de savoir laquelle est la première (pli 0) et la seconde (pli 1) ; une valeur isolée
    ambiguë est écrite avec le premier décalage et comptée dans meta.time.ambiguous (jamais réinterprétée en silence).
Les ANCIENNES données (archive de la branche history) ne sont pas réécrites : heure de Paris sans décalage.
"""
import copy
import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

PARIS, MADRID, LISBON = "Europe/Paris", "Europe/Madrid", "Europe/Lisbon"
NAIVE = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d(:\d\d)?$")
VERSION = 2
_Z = {}


def zone(name):
    if name not in _Z:
        _Z[name] = ZoneInfo(name)
    return _Z[name]


def spot_tz(spot):
    """Fuseau d'un spot d'après sa région (pipeline/spots.json peut le préciser avec « tz »)."""
    if spot.get("tz"):
        return spot["tz"]
    r = spot.get("region", "")
    if r.startswith("Portugal"):
        return LISBON
    if r in ("Espagne Nord", "Galice"):
        return MADRID
    return PARIS


def place_tz(lat, lon):
    """Fuseau d'une bouée d'après sa position : Portugal continental, côte espagnole, sinon France (et Gascogne, au large)."""
    lat, lon = float(lat), float(lon)
    if lat < 41.9 and -10.5 < lon < -6.1:   # frontière nord : le Minho (≈ 41,87° N) ; Cabo Silleiro (42,1° N) est en Espagne
        return LISBON
    if lat < 43.75 and -10.5 < lon < -1.7:
        return MADRID
    return PARIS


def fmt(dt, tz):
    """Instant (aware) → « AAAA-MM-JJTHH:MM±HH:MM » à l'heure locale de tz."""
    d = dt.astimezone(zone(tz))
    off = d.utcoffset()
    m = int(off.total_seconds() // 60)
    sign = "+" if m >= 0 else "-"
    m = abs(m)
    return d.strftime("%Y-%m-%dT%H:%M") + f"{sign}{m // 60:02d}:{m % 60:02d}"


def from_fixed(s, offset_s):
    """Heure Open-Meteo (décalage unique de la réponse) → instant exact."""
    return (datetime.strptime(s[:16], "%Y-%m-%dT%H:%M") - timedelta(seconds=int(offset_s))).replace(tzinfo=timezone.utc)


def parse(s, tz=PARIS, fold=0):
    """Chaîne publiée → instant. Avec décalage : exact. Sans décalage (ancien format) : heure murale de tz, explicitement."""
    if not NAIVE.match(s):
        return datetime.fromisoformat(s)
    return datetime.strptime(s[:16], "%Y-%m-%dT%H:%M").replace(tzinfo=zone(tz), fold=fold)


def ambiguous(s, tz=PARIS):
    """Heure murale qui existe deux fois (nuit du passage à l'heure d'hiver)."""
    n = datetime.strptime(s[:16], "%Y-%m-%dT%H:%M")
    z = zone(tz)
    return n.replace(tzinfo=z, fold=0).utcoffset() != n.replace(tzinfo=z, fold=1).utcoffset()


def wall_seq(values, tz=PARIS, stats=None):
    """Série ORDONNÉE d'heures murales → instants. Heure répétée : la première occurrence prend le pli 0, la suivante le pli 1
    (déduit de l'ordre, pas deviné). Heure inexistante (passage à l'heure d'été) : décalage d'avant le changement, comptée."""
    out, prev = [], None
    for s in values:
        if s is None:
            out.append(None)
            continue
        a = parse(s, tz, 0)
        if ambiguous(s, tz):
            b = parse(s, tz, 1)
            a = b if prev is not None and a.astimezone(timezone.utc) < prev else a
        n = datetime.strptime(s[:16], "%Y-%m-%dT%H:%M")
        if stats is not None and a.astimezone(timezone.utc).astimezone(zone(tz)).replace(tzinfo=None) != n:
            stats["nonexistent"] = stats.get("nonexistent", 0) + 1
        prev = a.astimezone(timezone.utc)
        out.append(a)
    return out


def hour_key(x):
    """Clé d'heure ABSOLUE (UTC, « AAAA-MM-JJTHH ») pour rapprocher deux séries écrites dans des fuseaux différents.
    Chaîne avec ou sans décalage (sans = heure de Paris) ; datetime naïf = heure de Paris ; datetime avec fuseau = exact."""
    if isinstance(x, str):
        d = parse(x)
    elif x.tzinfo is None:
        d = x.replace(tzinfo=zone(PARIS))
    else:
        d = x
    return d.astimezone(timezone.utc).strftime("%Y-%m-%dT%H")


TZ_LABEL = {PARIS: "heure de Paris", MADRID: "heure d'Espagne", LISBON: "heure du Portugal"}


def tz_label(tz):
    return TZ_LABEL.get(tz or PARIS, "heure locale")


def now(tz=PARIS):
    return datetime.now(zone(tz))


def age_h(s, ref=None, tz=PARIS):
    """Âge en heures d'un instant publié (avec ou sans décalage), par rapport à ref (instant ; maintenant par défaut)."""
    ref = ref or datetime.now(timezone.utc)
    if ref.tzinfo is None:
        ref = ref.replace(tzinfo=zone(PARIS))
    return (ref - parse(s, tz)).total_seconds() / 3600


def _conv_list(vals, tz, stats):
    """Liste d'heures murales de Paris → liste au fuseau tz (série ordonnée)."""
    return [None if a is None else fmt(a, tz) for a in wall_seq(vals, PARIS, stats)]


def _conv_one(s, tz, stats):
    if not s or not NAIVE.match(s):
        return s
    if ambiguous(s):
        stats["ambiguous"] = stats.get("ambiguous", 0) + 1
    return fmt(parse(s), tz)


def _buoy(b, tz, model_off, stats):
    b["tz"] = tz
    raw = {}
    if b.get("obs"):
        ts = _conv_list([o.get("t") for o in b["obs"]], tz, stats)
        for o, t in zip(b["obs"], ts):
            raw[o.get("t")] = t          # heure murale d'origine → instant (pli déduit de l'ordre de la série)
            o["t"] = t
    L = b.get("latest") or {}
    if L.get("time") and NAIVE.match(L["time"]):
        # dernière mesure : si elle figure dans la série, on reprend son instant (pli connu) ; sinon valeur isolée
        L["time"] = raw.get(L["time"]) or _conv_one(L["time"], tz, stats)
    if b.get("model") and model_off is not None:
        for m in b["model"]:
            if m.get("t") and NAIVE.match(m["t"]):
                m["t"] = fmt(from_fixed(m["t"], model_off), tz)


def _trim_to_local_midnight(sp):
    """Hors de Paris (Lisbonne : 1 h de moins), la série commence à 23 h la veille : on retire ces premières heures pour
    qu'elle commence à minuit, heure locale. Toutes les séries horaires du spot sont coupées de la même façon."""
    t = (sp.get("marine") or {}).get("time") or []
    k = next((i for i, x in enumerate(t[:6]) if x[11:13] == "00"), 0)
    if not k:
        return
    n = len(t)
    for block in ("marine", "wind", "wave_models", "wind_models"):
        b = sp.get(block) or {}
        for key, v in list(b.items()):
            if isinstance(v, list) and len(v) == n:
                b[key] = v[k:]


def localize(payload, spots_cfg, om_offset_s, sun_offset_s=None):
    """Copie de forecast.json au contrat horaire v2. Les calculs du robot restent faits avant, sur ses heures internes."""
    p = copy.deepcopy(payload)
    stats = {}
    meta = p["meta"]
    # heure de génération : instant EXACT si le robot l'a fourni (sinon l'heure de Paris écrite serait ambiguë la nuit du
    # passage à l'heure d'hiver : revue de la PR #17)
    gen_utc = p.pop("_generated_utc", None)
    naive_gen = meta.get("generated")
    if gen_utc:
        meta["generated"] = fmt(datetime.fromisoformat(gen_utc), PARIS)
    for k in ("generated", "forecast_fetched"):
        if meta.get(k):
            meta[k] = _conv_one(meta[k], PARIS, stats)
    cfg = {s["name"]: s for s in spots_cfg}
    for sp in p.get("spots") or []:
        tz = spot_tz(cfg.get(sp["name"], {}))
        sp["tz"] = tz
        for block in ("marine", "wind"):
            if sp.get(block) and sp[block].get("time"):
                sp[block]["time"] = [fmt(from_fixed(t, om_offset_s), tz) for t in sp[block]["time"]]
        _trim_to_local_midnight(sp)
        d = sp.get("daily") or {}
        for k in ("sunrise", "sunset"):
            if d.get(k):
                d[k] = [None if x is None else fmt(from_fixed(x, sun_offset_s if sun_offset_s is not None else om_offset_s), tz) for x in d[k]]
        if sp.get("tide") and sp["tide"].get("extremes"):
            ts = _conv_list([e["t"] for e in sp["tide"]["extremes"]], tz, stats)
            for e, t in zip(sp["tide"]["extremes"], ts):
                e["t"] = t
    model_offs = payload.get("_model_offsets") or {}
    off = lambda k: model_offs.get(k) if model_offs.get(k) is not None else om_offset_s
    if p.get("gascogne"):
        _buoy(p["gascogne"], PARIS, off("gascogne"), stats)
    for kind in ("coast", "offshore"):
        for b in p.get(kind) or []:
            _buoy(b, place_tz(b["lat"], b["lon"]), off(str(b.get("id"))), stats)
    for bid, st in (p.get("buoy_stats") or {}).items():
        for k in ("hs_max_t", "hmax_max_t"):
            if st.get(k):
                st[k] = _conv_one(st[k], PARIS, stats)
    td = (meta.get("api") or {}).get("today") or {}
    if td.get("last"):
        td["last"] = meta["generated"] if td["last"] == naive_gen else _conv_one(td["last"], PARIS, stats)
    p.pop("_model_offsets", None)
    meta["time"] = {"version": VERSION, "format": "ISO 8601 avec décalage, heure locale du lieu (fuseau IANA dans « tz »)",
                    "ambiguous": stats.get("ambiguous", 0), "nonexistent": stats.get("nonexistent", 0)}
    return p


def naive_strings(obj, path="", out=None):
    """Toutes les heures SANS décalage d'une structure (pour les tests : il ne doit plus y en avoir dans les données publiées)."""
    out = [] if out is None else out
    if isinstance(obj, dict):
        for k, v in obj.items():
            naive_strings(v, f"{path}.{k}", out)
    elif isinstance(obj, list):
        for i, v in enumerate(obj[:400]):
            naive_strings(v, f"{path}[{i}]", out)
    elif isinstance(obj, str) and NAIVE.match(obj):
        out.append(path)
    return out
