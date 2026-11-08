"""Ajuste les constantes harmoniques d'un port à partir d'un fichier de mesures REFMAR.

1. Télécharge les hauteurs d'eau du marégraphe sur https://data.shom.fr (rubrique REFMAR),
   idéalement 1 an de données « validées horaires » (licence ouverte Etalab).
2. Dépose le fichier dans tides/raw/ (txt ou csv).
3. Lance :  python -m tools.fit_tides tides/raw/socoa.txt socoa
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import utide

ROOT = Path(__file__).resolve().parent.parent


def read_refmar(path):
    rows = []
    for line in Path(path).read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line[0] in "#%" or not line[0].isdigit():
            continue
        for sep in (";", "\t", ",", " "):
            parts = [p for p in line.split(sep) if p]
            if len(parts) >= 2:
                break
        try:
            txt = parts[0] if ":" in parts[0] else parts[0] + " " + parts[1]
            iso = len(txt) > 4 and txt[:4].isdigit() and txt[4] in "-/"  # AAAA-MM-JJ : jamais jour/mois inversés
            t = pd.to_datetime(txt.replace("/", "-") if iso else txt, dayfirst=not iso)
            v = float((parts[1] if ":" in parts[0] else parts[2]).replace(",", "."))
            rows.append((t, v))
        except (ValueError, IndexError):
            continue
    if not rows:
        raise SystemExit("Aucune mesure lisible dans le fichier.")
    s = pd.Series([v for _, v in rows], index=pd.DatetimeIndex([t for t, _ in rows])).sort_index()
    s = s[~s.index.duplicated()]
    # Pas de moyenne par tranche (elle décalerait les heures) : on garde les mesures instantanées.
    # REFMAR est en UTC par défaut. Données très denses : une mesure toutes les 10 min suffit.
    step = s.index.to_series().diff().median()
    if step < pd.Timedelta("10min"):
        s = s[s.index.minute % 10 == 0]
    s = s.dropna()
    # Retire les pics aberrants (écart > 5 écarts-types à la moyenne glissante).
    roll = s.rolling(25, center=True, min_periods=5).median()
    s = s[(s - roll).abs() < 5 * s.std()]
    return s


def to_json(obj):
    if isinstance(obj, dict):
        return {k: to_json(v) for k, v in obj.items()}
    if isinstance(obj, np.ndarray):
        return [to_json(x) for x in obj.tolist()]
    if isinstance(obj, (np.floating, np.integer)):
        return obj.item()
    if isinstance(obj, (list, tuple)):
        return [to_json(x) for x in obj]
    return obj


def main(path, port, lat=43.4):
    s = read_refmar(path)
    days = (s.index[-1] - s.index[0]).days
    if days < 30:
        raise SystemExit(f"Seulement {days} jours de mesures : il en faut au moins 30, idéalement 365.")
    coef = utide.solve(s.index.values, s.values, lat=lat, method="ols", conf_int="none", verbose=False)
    keep = {k: coef[k] for k in ("name", "A", "g", "mean", "slope", "aux") if k in coef}
    keep["aux"] = {k: v for k, v in dict(coef["aux"]).items() if k in ("frq", "lind", "reftime", "lat", "opt")}
    keep["aux"]["opt"] = {k: v for k, v in dict(coef["aux"]["opt"]).items()
                          if k in ("twodim", "nodsatlint", "nodsatnone", "gwchlint", "gwchnone", "prefilt", "notrend", "nodiagn")}
    resid = s.values - utide.reconstruct(s.index.values, coef, verbose=False).h
    meta = {"port": port, "start": str(s.index[0]), "end": str(s.index[-1]), "days": days,
            "constituents": len(coef["name"]), "rms_cm": round(float(np.sqrt(np.nanmean(resid ** 2)) * 100), 1),
            "source": "Mesures REFMAR © Shom, Licence Ouverte. Calcul harmonique indépendant (UTide)."}
    out = ROOT / "tides" / "constants" / f"{port}.json"
    out.write_text(json.dumps({"meta": meta, "coef": to_json(keep)}, ensure_ascii=False))
    print(f"OK : {out.name} · {days} jours · {meta['constituents']} ondes · écart résiduel {meta['rms_cm']} cm")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        raise SystemExit("Usage : python -m tools.fit_tides <fichier> <port> [latitude]")
    main(sys.argv[1], sys.argv[2], float(sys.argv[3]) if len(sys.argv) > 3 else 43.4)
