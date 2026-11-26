"""Simulations de pannes pour l'issue #3 : chaque artefact abîmé doit être REFUSÉ par tools/check_site.py,
une simple panne de source doit être tolérée (avertissement). Base : sortie du test hors ligne (sources simulées),
dont on retire les marques de test pour obtenir un site « valide » de référence.
    python simulate.py <dossier de sortie du test> <dépôt>"""
import json, re, shutil, sys, tempfile
from pathlib import Path

src, repo = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(repo))
from tools.check_site import check

base = Path(tempfile.mkdtemp(prefix="houlalah-sim-")) / "base"
shutil.copytree(repo / "web", base)            # sources du site (index.html, brand…) comme dans le workflow
for sub in ("spots", "bouees", "data/app", "og"):
    shutil.rmtree(base / sub, ignore_errors=True)
shutil.copytree(src, base, dirs_exist_ok=True)  # + ce que le robot a généré
# retirer les marques de test → site de référence
for f in base.rglob("*.html"):
    t = f.read_text(encoding="utf-8")
    if 'houlalah-test' in t:
        f.write_text(t.replace('<meta name="robots" content="noindex"><meta name="houlalah-test" content="1">',
                               '<meta name="robots" content="index,follow,max-image-preview:large">'), encoding="utf-8")
for rel in ("data/forecast.json", "data/app/index.json", "health.json"):
    p = base / rel; j = json.loads(p.read_text(encoding="utf-8"))
    (j.get("meta") or j).pop("_test", None); j.pop("_test", None)
    p.write_text(json.dumps(j, ensure_ascii=False), encoding="utf-8")


def case(name, mutate, expect_ok, must=None):
    d = base.parent / re.sub(r"\W+", "_", name)
    shutil.rmtree(d, ignore_errors=True); shutil.copytree(base, d)
    if mutate: mutate(d)
    ok, rep = check(d, max_age_h=None)
    hit = must is None or any(must in e for e in rep["errors"])
    res = "OK" if (ok == expect_ok and hit) else "ÉCHEC DU TEST"
    print(f"[{res}] {name} → {'publié' if ok else 'REFUSÉ'}" + ("" if ok else f" : {rep['errors'][0][:110]}")
          + (f" ({len(rep['warnings'])} avert.)" if rep['warnings'] else ""))
    return res == "OK"


def jset(rel, fn):
    def m(d):
        p = d / rel; j = json.loads(p.read_text(encoding="utf-8")); fn(j); p.write_text(json.dumps(j, ensure_ascii=False), encoding="utf-8")
    return m


def rm(rel):
    return lambda d: (shutil.rmtree(d / rel) if (d / rel).is_dir() else (d / rel).unlink())


def sub(rel, a, b):
    def m(d):
        p = d / rel; t = p.read_text(encoding="utf-8"); assert a in t, (rel, a); p.write_text(t.replace(a, b, 1), encoding="utf-8")
    return m


S = "https://houlalah.fr"
results = [
    case("site de référence (marques de test retirées)", None, True),
    case("panne d'une source (CANDHIS) : tolérée", jset("data/forecast.json", lambda j: j["meta"]["errors"].update(candhis="timeout")), True),
    case("données de test dans forecast.json", jset("data/forecast.json", lambda j: j["meta"].update(_test=True)), False, "test"),
    case("une page de test oubliée", sub("spots/lacanau/index.html", "<head>", '<head><meta name="houlalah-test" content="1">'), False, "test"),
    case("échec des données de l'appli (exception)", jset("data/forecast.json", lambda j: j["meta"]["errors"].update(appdata="KeyError: 'marine'")), False, "appdata"),
    case("échec des pages bouées (exception)", jset("data/forecast.json", lambda j: j["meta"]["errors"].update(seo_bouees="ValueError")), False, "seo_bouees"),
    case("échec SEO complet (exception)", jset("data/forecast.json", lambda j: j["meta"]["errors"].update(seo="OSError")), False, "seo"),
    case("pages bouées absentes", rm("bouees"), False, "pages absentes"),
    case("une page de spot absente", rm("spots/hossegor-la-graviere" if (base / "spots/hossegor-la-graviere").exists() else "spots/lacanau"), False, "pages absentes"),
    case("une fiche spot de l'appli absente", rm("data/app/spots/lacanau.json"), False, "fiche spot"),
    case("une fiche bouée de l'appli absente", lambda d: next((d / "data/app/bouees").glob("*.json")).unlink(), False, "fiche bouée"),
    case("index de l'appli : JSON tronqué", lambda d: (d / "data/app/index.json").write_text('{"v":1,"spo', encoding="utf-8"), False, "JSON invalide"),
    case("forecast.json absent", rm("data/forecast.json"), False, "forecast.json absent"),
    case("un spot manquant dans forecast.json", jset("data/forecast.json", lambda j: j["spots"].pop()), False, "catalogue"),
    case("appli d'une autre génération", jset("data/app/index.json", lambda j: j.update(generated="2020-01-01T00:00")), False, "génération"),
    case("sitemap avec adresse locale", sub("sitemap.xml", f"<loc>{S}/</loc>", f"<loc>{S}/</loc><url><loc>http://localhost:8766/x/</loc></url>"), False, "sitemap"),
    case("sitemap absent", rm("sitemap.xml"), False, "sitemap.xml absent"),
    case("canonique fausse", sub("spots/lacanau/index.html", f'href="{S}/spots/lacanau/"', f'href="{S}/spots/autre/"'), False, "canoniques"),
    case("page en trop (reste d'un ancien spot)", lambda d: ((d / "spots/ancien").mkdir(), (d / "spots/ancien/index.html").write_text("x")), False, "inattendues"),
    case("secret dans health.json", jset("health.json", lambda j: j["errors"].update(x="apikey=abcdefghijklmnop1234")), False, "secret"),
    case("index.html du site absent", rm("index.html"), False, "index.html absent"),
]
# fraîcheur : une génération vieille de 5 h est refusée avec la limite de 3 h
d = base.parent / "vieux"; shutil.rmtree(d, ignore_errors=True); shutil.copytree(base, d)
for rel, key in (("data/forecast.json", "meta"), ("data/app/index.json", None)):
    p = d / rel; j = json.loads(p.read_text(encoding="utf-8")); (j[key] if key else j)["generated"] = "2026-01-01T00:00"; p.write_text(json.dumps(j), encoding="utf-8")
ok, rep = check(d, max_age_h=3)
results.append(not ok and any("généré il y a" in e for e in rep["errors"]))
print(f"[{'OK' if results[-1] else 'ÉCHEC DU TEST'}] génération trop ancienne → {'publié' if ok else 'REFUSÉ'} : {rep['errors'][0][:80]}")
print(f"\n{sum(results)}/{len(results)} scénarios conformes")
sys.exit(0 if all(results) else 1)
