"""Bilan de l'archive des bouées côtières : combien de mesures, depuis quand, et un premier aperçu de l'écart modèle / mesure.

Usage (dossier history/ récupéré depuis la branche « history ») :
  python -m tools.coast_report [chemin/vers/history]
Quand il y aura assez de jours (≥ 30) et de situations variées (houle longue et courte), ces données serviront à apprendre,
par bouée, comment la hauteur et la période prévues se traduisent en hauteur mesurée près de la côte.
"""
import json
import sys
from pathlib import Path

import numpy as np

from pipeline import history


def main(d):
    d = Path(d)
    cs = history.coast_summary(d)
    print(f"Passages archivés : {cs['runs']}")
    for bid, v in cs["buoys"].items():
        print(f"  bouée {bid} : {v['n']} mesures horaires, du {v['first']} au {v['last']}")
    # Aperçu : écart (prévu − mesuré) à l'heure du passage, selon la période prévue (courte / moyenne / longue)
    obs = {}
    for f in sorted((d / "coast_obs").glob("*.json")) if (d / "coast_obs").exists() else []:
        for bid, rows in json.loads(f.read_text(encoding="utf-8")).items():
            obs.setdefault(bid, {}).update(rows)
    rows = []
    for f in sorted((d / "coast_runs").glob("*.jsonl")) if (d / "coast_runs").exists() else []:
        for line in f.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            for bid, b in r["b"].items():
                for k in range(0, len(b["hs"]), 1):
                    t = _plus(r["t0"], k)
                    o = obs.get(bid, {}).get(t)
                    if o and b["hs"][k] is not None and b["tp"] and b["tp"][k] is not None and k <= 24:
                        rows.append((bid, k, b["hs"][k], b["tp"][k], o["hs"], o.get("tp")))
    if len(rows) < 30:
        print("Pas encore assez de couples prévision/mesure pour un aperçu (il en faut au moins 30).")
        return
    a = np.array([(r[2], r[3], r[4]) for r in rows], dtype=float)
    for name, lo, hi in (("période < 8 s", 0, 8), ("8 à 11 s", 8, 11), ("≥ 11 s", 11, 99)):
        m = (a[:, 1] >= lo) & (a[:, 1] < hi)
        if m.sum() >= 5:
            print(f"  {name} : {int(m.sum())} cas, prévu {a[m, 0].mean():.2f} m, mesuré {a[m, 2].mean():.2f} m, rapport {a[m, 2].mean() / max(a[m, 0].mean(), 0.05):.2f}")


def _plus(t, k):
    from datetime import datetime, timedelta
    return (datetime.strptime(t, "%Y-%m-%dT%H:%M") + timedelta(hours=k)).strftime("%Y-%m-%dT%H:00")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else history.history_dir())
