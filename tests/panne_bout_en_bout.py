"""Panne réelle de bout en bout (issue #3), sans réseau ni publication.   python -m tests.panne_bout_en_bout

Le test hors ligne est rejoué avec :
  - appdata.generate et bouees.generate qui lèvent une exception (échec de génération) ;
  - candhis.fetch_all qui lève une exception contenant une FAUSSE clé, une adresse avec identifiants et paramètres, un en-tête.
On vérifie que build.py enregistre les erreurs de génération, qu'aucune de ces fausses valeurs n'apparaît dans les fichiers
produits, et que le contrôle de publication refuse le site pour ces motifs. Code de sortie 1 si une vérification échoue.
"""
import json
import os
import runpy
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
FAKE_KEY = "FAUSSECLE-0123456789abcdef"          # jamais une vraie clé
FAKE_TOKEN = "jetonbidon9876543210ZYXWVU"
os.environ["METEOFRANCE_APIKEY"] = FAKE_KEY
out = tempfile.mkdtemp(prefix="houlalah-e2e-")
os.environ["METEO_OUT_DIR"] = out
os.environ["METEO_TEST"] = "1"
_mk = tempfile.mkdtemp
tempfile.mkdtemp = lambda *a, **k: out if k.get("prefix") == "houlalah-test-" else _mk(*a, **k)   # le test prendra ce dossier

from pipeline import appdata, bouees, candhis  # noqa: E402  (après les variables d'environnement)


def boom(*a, **k):
    raise RuntimeError("panne simulée")


def leak(*a, **k):
    raise RuntimeError(f"GET https://robot:motdepasse@api.exemple.test/v2/bouees?apikey={FAKE_KEY}&format=json "
                       f"Authorization: Bearer {FAKE_TOKEN} key={FAKE_KEY}")


appdata.generate = boom
bouees.generate = boom
candhis.fetch_all = leak
try:
    runpy.run_module("tests.test_offline", run_name="__main__")
except BaseException as e:   # le test s'arrête ensuite (fiches absentes) : attendu, seule la sortie du robot compte
    print("test hors ligne interrompu comme prévu :", type(e).__name__)
tempfile.mkdtemp = _mk

fails = []
root = Path(out)
fc = json.loads((root / "data" / "forecast.json").read_text(encoding="utf-8"))
hj = json.loads((root / "health.json").read_text(encoding="utf-8"))
print("forecast.json errors :", sorted(fc["meta"]["errors"]))
print("health.json errors   :", sorted(hj["errors"]))
print("message public CANDHIS :", fc["meta"]["errors"].get("candhis"))
for k in ("appdata", "seo_bouees", "candhis"):
    if k not in fc["meta"]["errors"] or k not in hj["errors"]:
        fails.append(f"erreur {k} non enregistrée")
for f in root.rglob("*"):
    if f.is_file() and f.suffix in (".json", ".html", ".xml", ".txt"):
        t = f.read_text(encoding="utf-8", errors="replace")
        for bad in (FAKE_KEY, FAKE_TOKEN, "motdepasse", "format=json"):
            if bad in t:
                fails.append(f"fuite de « {bad[:12]}… » dans {f.relative_to(root)}")
from tools.check_site import check  # noqa: E402
ok, rep = check(root, max_age_h=None)
for e in rep["errors"]:
    print("  ❌", e[:120])
if ok:
    fails.append("le contrôle a accepté le site")
for k in ("robot : appdata", "robot : seo_bouees"):
    if not any(k in e for e in rep["errors"]):
        fails.append(f"motif « {k} » absent du refus")
# le contrôle repère aussi la valeur exacte d'un secret s'il se glisse dans une page
(root / "spots" / "lacanau" / "index.html").write_text(f"<p>{FAKE_KEY}</p>", encoding="utf-8")
ok2, rep2 = check(root, max_age_h=None)
if not any("secret possible" in e for e in rep2["errors"]):
    fails.append("valeur exacte d'un secret non détectée dans une page")
print("RÉSULTAT :", "OK — erreurs enregistrées, aucune fuite, publication refusée" if not fails else "ÉCHEC : " + " ; ".join(fails))
sys.exit(1 if fails else 0)
