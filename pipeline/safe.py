"""Messages publics sans secret (issue #3).

Les erreurs des sources finissent dans des fichiers PUBLICS (forecast.json, health.json) et dans les journaux du robot.
Une exception peut contenir une adresse d'API complète, un en-tête ou une clé : tout passe par ici avant d'être écrit.
  - redact(msg)        : journaux. Masque les valeurs des secrets connus, les paramètres et en-têtes sensibles, les identifiants dans les adresses.
  - public_error(msg)  : fichiers publics. Comme redact, et en plus retire tout ce qui suit « ? » dans les adresses, puis coupe.
"""
import os
import re

# variables d'environnement dont la VALEUR ne doit jamais apparaître (on masque la valeur exacte, où qu'elle soit)
SECRET_ENV = ("METEOFRANCE_APIKEY", "CANDHIS_TOKEN", "COPERNICUS_PASSWORD", "GITHUB_TOKEN")
MASK = "***"

_KV = re.compile(r"(?i)\b(api[_-]?key|apikey|access[_-]?token|token|key|secret|password|passwd|pwd|auth)\b(\s*[=:]\s*|\"?\s*:\s*\"?)([^\s&\"',;}]+)")
_AUTH = re.compile(r"(?i)\b(authorization|x-api-key|apikey)(\s*[:=]\s*)(bearer\s+|basic\s+)?[^\s,;'\"}]+")
_BEARER = re.compile(r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{8,}")
_USERINFO = re.compile(r"(?i)\b(https?|ftp)://[^/\s:@]+:[^/\s@]+@")
_QUERY = re.compile(r"(?i)\b((?:https?|ftp)://[^\s?#'\"]+)\?[^\s'\"]*")


def secret_values():
    return [v for v in (os.environ.get(k) for k in SECRET_ENV) if v and len(v) >= 6]


def redact(msg):
    s = str(msg)
    for v in secret_values():
        s = s.replace(v, MASK)
    s = _USERINFO.sub(lambda m: f"{m.group(1)}://{MASK}@", s)
    s = _AUTH.sub(lambda m: f"{m.group(1)}{m.group(2)}{MASK}", s)
    s = _BEARER.sub(f"Bearer {MASK}", s)
    s = _KV.sub(lambda m: f"{m.group(1)}{m.group(2)}{MASK}", s)
    return s


def public_error(msg, limit=300):
    """Message d'erreur publiable : secrets masqués, adresses sans paramètres, longueur bornée."""
    return _QUERY.sub(lambda m: m.group(1) + "?…", redact(msg))[:limit]


class RedactingStream:
    """Enveloppe de sys.stdout / sys.stderr : tout ce que le robot affiche passe par redact()."""

    def __init__(self, stream):
        self._s = stream

    def write(self, s):
        return self._s.write(redact(s))

    def __getattr__(self, name):
        return getattr(self._s, name)
