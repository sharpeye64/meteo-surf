"""Panne réelle de bout en bout : le test hors ligne est rejoué avec appdata.generate et bouees.generate qui lèvent une
exception. On vérifie que build.py enregistre ces erreurs dans forecast.json et health.json et que le contrôle refuse
le site pour ces motifs (en plus des marques de test).   python e2e_panne.py <dépôt>"""
import json, os, runpy, sys
repo = sys.argv[1]
os.chdir(repo); sys.path.insert(0, repo)
import tempfile
out = tempfile.mkdtemp(prefix="houlalah-e2e-")
os.environ["METEO_OUT_DIR"] = out; os.environ["METEO_TEST"] = "1"
_mk = tempfile.mkdtemp; tempfile.mkdtemp = lambda *a, **k: out if k.get("prefix") == "houlalah-test-" else _mk(*a, **k)
from pipeline import appdata, bouees, config
def boom(*a, **k): raise RuntimeError("panne simulée")
appdata.generate = boom; bouees.generate = boom
try:
    runpy.run_module("tests.test_offline", run_name="__main__")
except BaseException as e:   # le test échoue ensuite (fiches absentes) : attendu, seule la sortie du build compte
    print("test interrompu comme prévu :", type(e).__name__, str(e)[:80])
fc = json.load(open(os.path.join(out, "data", "forecast.json"), encoding="utf-8"))
hj = json.load(open(os.path.join(out, "health.json"), encoding="utf-8"))
print("forecast.json errors :", sorted(fc["meta"]["errors"]))
print("health.json errors   :", sorted(hj["errors"]))
from tools.check_site import check
ok, rep = check(out, max_age_h=None)
for e in rep["errors"]: print("  ❌", e[:120])
good = (not ok and "appdata" in fc["meta"]["errors"] and "seo_bouees" in fc["meta"]["errors"]
        and any("robot : appdata" in e for e in rep["errors"]) and any("robot : seo_bouees" in e for e in rep["errors"]))
print("RÉSULTAT :", "OK, panne détectée et publication refusée" if good else "ÉCHEC")
