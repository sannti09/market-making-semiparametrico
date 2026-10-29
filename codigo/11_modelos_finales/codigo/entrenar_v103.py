#!/usr/bin/env python3
"""v103: entrena y guarda los 11 modelos con 29 jun–3 sep (misma función que el walk-forward)."""
import hashlib, json, pickle, sys, time
from pathlib import Path
R = Path(__file__).resolve().parents[1]; RR = R.parent
sys.path.insert(0, str(RR / "10_walk_forward" / "codigo"))
import wf_v102 as W  # noqa: E402
t0 = time.time(); MOD, deltas, cols = W.ajustar("2026-09-03")
p = R / "modelos" / "modelos_finales_v103.pkl"; pickle.dump({"MOD": MOD, "deltas": deltas, "cols": cols, "modelos": W.NOMS}, open(p, "wb"))
man = {"hora": time.strftime("%Y-%m-%d %H:%M:%S %z"), "ventana_ajuste": "2026-06-29..2026-09-03", "modelos": W.NOMS,
       "pkl_sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "segundos": round(time.time() - t0),
       "hawkes_2_escalas": {"betas": MOD["H2"]["betas"].tolist(), "rho": MOD["H2"]["rho"]}, "hawkes_1_escala": {"betas": MOD["H1"]["betas"].tolist(), "rho": MOD["H1"]["rho"]}}
(R / "modelos" / "MANIFIESTO_v103.json").write_text(json.dumps(man, indent=1)); print("GUARDADO", json.dumps(man), flush=True)
