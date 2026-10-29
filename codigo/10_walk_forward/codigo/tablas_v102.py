#!/usr/bin/env python3
"""v102: tablas (md, csv, tex) y gráficos (png, pdf) del walk-forward para el proyecto de grado. Solo numpy, json y matplotlib."""
import csv, json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

R = Path(__file__).resolve().parents[1]; RR = R.parent; SAL = R / "salida"; OUT = R / "tablas_tesis"; OUT.mkdir(exist_ok=True)
F = json.loads((SAL / "por_dia_v102.json").read_text()); E = np.load(SAL / "eventos_v102.npy")
NOMS = ["E3-fkX+B", "E3-fkX", "E3", "E1", "E1+h-f", "E1+S", "E1+X49", "E2+h-f", "E2+S", "E2m+h-f", "E2m+S"]
ETQ = {"E3-fkX+B": "E3 tesis (49 cov., f(δ)·k(X))", "E3-fkX": "E3 f(δ)·k(X), 44 cov.", "E3": "E3 base (−kδ, 44 cov.)", "E1": "AS base",
       "E1+h-f": "AS + hora + f(δ)", "E1+S": "AS + 7 señales", "E1+X49": "GLM lineal 49 cov.", "E2+h-f": "Hawkes 1 escala + hora + f(δ)",
       "E2+S": "Hawkes 1 escala + señales", "E2m+h-f": "Hawkes 2 escalas + hora + f(δ)", "E2m+S": "Hawkes 2 escalas + señales"}
REF, LADOS = "E3-fkX+B", ("ask", "bid")
fu = [r for r in F if r["tipo"] == "fuera"]; de = [r for r in F if r["tipo"] == "dentro"]; folds = sorted({r["fold"] for r in fu})
nd = len(fu); IDX = np.random.default_rng(20261029).integers(0, nd, size=(2000, nd)); n = np.array([r["n"] for r in fu], float)

def guardar(nombre, cab, filas, titulo, nota=""):
    with open(OUT / f"{nombre}.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(cab); w.writerows(filas)
    md = [f"### {titulo}", "", "| " + " | ".join(cab) + " |", "|" + "---|" * len(cab)] + ["| " + " | ".join(map(str, x)) + " |" for x in filas]
    (OUT / f"{nombre}.md").write_text("\n".join(md + ([f"", nota] if nota else [])) + "\n")
    esc = lambda s: str(s).replace("%", "\\%").replace("_", "\\_").replace("δ", "$\\delta$").replace("−", "$-$").replace("≥", "$\\geq$").replace("·", "$\\cdot$")
    tex = ["\\begin{table}[htbp]", "\\centering", "\\small", f"\\caption{{{esc(titulo)}}}", f"\\label{{tab:{nombre}}}",
           "\\begin{tabular}{l" + "r" * (len(cab) - 1) + "}", "\\toprule", " & ".join(esc(c) for c in cab) + " \\\\", "\\midrule"]
    tex += [" & ".join(esc(c) for c in x) + " \\\\" for x in filas] + ["\\bottomrule", "\\end{tabular}"]
    if nota:
        tex += [f"\\par\\smallskip\\footnotesize {esc(nota)}"]
    (OUT / f"{nombre}.tex").write_text("\n".join(tex + ["\\end{table}"]) + "\n")

# --- verificación: la ventana 1 debe reproducir v98 / v100b en 1–7 ago
v98 = {r["fecha"]: r for r in json.loads((RR / "03_cargador_datos" / "salida" / "por_dia_v98.json").read_text())}
v100 = {r["fecha"]: r for r in json.loads((RR / "07_modelos_as_hawkes" / "por_dia_v100.json").read_text())}
rep = []
for r in [x for x in fu if x["fold"] == 1]:
    for m, ref in (("E3-fkX+B", v98), ("E3", v98), ("E3-fkX", v98), ("E2m+S", v100), ("E1+X49", v100), ("E1+S", v100)):
        for l in LADOS:
            rep.append(abs(r[f"ll_{m}_{l}"] - ref[r["fecha"]][f"ll_{m}_{l}"]) / abs(ref[r["fecha"]][f"ll_{m}_{l}"]))
verif = f"Ventana 1 frente a v98/v100b (1–7 ago): diferencia relativa máxima {max(rep):.1e}"

# --- T1: resumen global fuera de muestra
res, filas = {}, []
for m in NOMS:
    fila = [ETQ[m]]
    for l in LADOS:
        tot = sum(r[f"ll_{REF}_{l}"] - r[f"ll_E1_{l}"] for r in fu); parte = sum(r[f"ll_{m}_{l}"] - r[f"ll_E1_{l}"] for r in fu) / tot
        dif = np.array([r[f"ll_{REF}_{l}"] - r[f"ll_{m}_{l}"] for r in fu]); bs = dif[IDX].sum(1) / n[IDX].sum(1); lo, hi = np.percentile(bs, [2.5, 97.5])
        auc = float(np.mean([r[f"auc_{m}_{l}"] for r in fu])); pf = []
        for k in folds:
            rk = [r for r in fu if r["fold"] == k]; pf.append(sum(r[f"ll_{REF}_{l}"] - r[f"ll_{m}_{l}"] for r in rk) / sum(r["n"] for r in rk))
        res[(m, l)] = {"parte": parte, "dll": dif.sum() / n.sum(), "lo": lo, "hi": hi, "dias": int((dif > 0).sum()), "auc": auc, "por_fold": pf}
        fila += [f"{100 * parte:.1f} %", "—" if m == REF else f"{dif.sum() / n.sum():+.3f} [{lo:+.3f}; {hi:+.3f}]", "—" if m == REF else f"{int((dif > 0).sum())}/{nd}", f"{auc:.3f}"]
    filas.append(fila)
cab = ["Modelo"] + [f"{c} ({l})" for l in LADOS for c in ("Parte de la mejora", "E3 − modelo (ll/bin) [IC95]", "Días E3 gana", "AUC δ=2")]
guardar("T1_walkforward_resumen", cab, filas, "Walk-forward (5 ventanas semanales, 34 días fuera de muestra, 1 ago–3 sep): comparación de modelos",
        "Parte de la mejora = (ll del modelo − ll de AS base) / (ll de E3 tesis − ll de AS base). IC95 bootstrap por días. " + verif)

# --- T2: E3 − modelo por ventana
filas = []
for m in NOMS[1:]:
    filas.append([ETQ[m]] + [f"{res[(m, l)]['por_fold'][k - 1]:+.3f}" for l in LADOS for k in folds])
fini = ["1–7 ago", "8–14 ago", "15–21 ago", "22–28 ago", "29 ago–3 sep"]
guardar("T2_walkforward_por_ventana", ["Modelo"] + [f"{l} {fini[k - 1]}" for l in LADOS for k in folds], filas,
        "Ventaja de E3 tesis sobre cada modelo por ventana (Δll por bin; positivo = gana E3)")

# --- T3: sobreajuste (dentro vs fuera de muestra, ventaja de E3 sobre el GLM lineal y sobre AS base)
filas, ratios = [], []
for k in folds:
    fila = [f"Ventana {k} ({fini[k - 1]})"]
    for l in LADOS:
        for rival in ("E1+X49", "E1"):
            dd = [r for r in de if r["fold"] == k]; ff = [r for r in fu if r["fold"] == k]
            vin = sum(r[f"ll_{REF}_{l}"] - r[f"ll_{rival}_{l}"] for r in dd) / sum(r["n"] for r in dd)
            vout = sum(r[f"ll_{REF}_{l}"] - r[f"ll_{rival}_{l}"] for r in ff) / sum(r["n"] for r in ff)
            fila += [f"{vin:+.3f}", f"{vout:+.3f}", f"{vout / vin:.2f}"]
            if rival == "E1+X49":
                ratios.append(vout / vin)
    filas.append(fila)
guardar("T3_sobreajuste", ["Ventana"] + [f"{l} vs {rv}: {c}" for l in LADOS for rv in ("GLM 49", "AS base") for c in ("dentro", "fuera", "cociente")], filas,
        "Diagnóstico de sobreajuste: ventaja de E3 tesis dentro de muestra (última semana ajustada) y fuera de muestra (semana siguiente)",
        "Cociente = fuera / dentro. Se marca sobreajuste si el cociente frente al GLM es < 0,5 en 3 o más ventanas.")

# --- T4: rebote (4 celdas) fuera de muestra
s, sube, nan = E[:, 1], E[:, 4] > 0, np.isnan(E[:, 4])
cel = {"Vendedor, 1 h al alza": (s < 0) & sube, "Vendedor, 1 h a la baja": (s < 0) & ~sube & ~nan, "Comprador, 1 h al alza": (s > 0) & sube, "Comprador, 1 h a la baja": (s > 0) & ~sube & ~nan}
filas, brech = [], {}
for k, m in enumerate(NOMS):
    la, lb = np.exp(E[:, 5 + 2 * k]), np.exp(E[:, 6 + 2 * k])
    ba = sum(r["O_ask"] for r in fu) / sum(r[f"E_{m}_ask"] for r in fu); bb = sum(r["O_bid"] for r in fu) / sum(r[f"E_{m}_bid"] for r in fu)
    b = [float((E[mm, 2].sum() / la[mm].sum() - ba) if c.startswith("Vend") else (E[mm, 3].sum() / lb[mm].sum() - bb)) for c, mm in cel.items()]
    brech[m] = b; filas.append([ETQ[m]] + [f"{x:+.3f}" for x in b])
guardar("T4_rebote", ["Modelo"] + list(cel), filas, "Rebote tras barridos (brecha = O/E del lado contrario − O/E base, δ = 2 bps; fuera de muestra)",
        "Positivo: llegan más agresores del lado contrario de los que el modelo espera; 0 = acierta como en momentos normales.")

# --- veredicto de los criterios del plan
c1 = all(x > 0 for m in NOMS[1:] for l in LADOS for x in res[(m, l)]["por_fold"])
c2 = all(res[(m, l)]["lo"] > 0 for m in NOMS[1:] for l in LADOS)
c3 = sum(min(ratios[2 * j:2 * j + 2]) < 0.5 for j in range(len(ratios) // 2)) >= 3  # plan: ventanas (no ventana×lado); una ventana cuenta si algún lado < 0,5
ver = {"C1_estabilidad_5_ventanas": c1, "C2_global_IC>0": c2, "C3_sobreajuste_marcado": c3, "verificacion": verif}
(OUT / "veredicto_v102.json").write_text(json.dumps(ver, indent=1, ensure_ascii=False))

# --- gráficos
plt.rcParams.update({"font.size": 9, "figure.dpi": 150})
orden = sorted(NOMS, key=lambda m: res[(m, "ask")]["parte"])
fig, ax = plt.subplots(figsize=(7, 4.2)); y = np.arange(len(orden))
for j, (l, c) in enumerate((("ask", "#4C72B0"), ("bid", "#DD8452"))):
    ax.barh(y + (j - 0.5) * 0.38, [100 * res[(m, l)]["parte"] for m in orden], 0.38, label=l, color=c)
ax.set_yticks(y); ax.set_yticklabels([ETQ[m] for m in orden]); ax.set_xlabel("Parte de la mejora de E3 tesis sobre AS base (%)"); ax.axvline(100, color="k", lw=0.6, ls="--"); ax.legend()
ax.set_title("Walk-forward, 34 días fuera de muestra"); fig.tight_layout()
for ext in ("png", "pdf"): fig.savefig(OUT / f"G1_parte_mejora.{ext}")
fig, axs = plt.subplots(1, 2, figsize=(9, 3.6), sharey=True)
for ax, l in zip(axs, LADOS):
    for m in ("E1+h-f", "E1+S", "E1+X49", "E2m+h-f", "E2m+S", "E3"):
        ax.plot(folds, res[(m, l)]["por_fold"], marker="o", label=ETQ[m])
    ax.axhline(0, color="k", lw=0.6); ax.set_xticks(folds); ax.set_xticklabels(fini, rotation=30, ha="right"); ax.set_title(l)
axs[0].set_ylabel("E3 tesis − modelo (ll por bin)"); axs[1].legend(fontsize=7); fig.tight_layout()
for ext in ("png", "pdf"): fig.savefig(OUT / f"G2_ventaja_por_ventana.{ext}")
fig, ax = plt.subplots(figsize=(7, 4)); xs = np.arange(len(NOMS))
for j, (l, c) in enumerate((("ask", "#4C72B0"), ("bid", "#DD8452"))):
    ax.bar(xs + (j - 0.5) * 0.4, [res[(m, l)]["auc"] for m in NOMS], 0.4, label=l, color=c)
ax.set_xticks(xs); ax.set_xticklabels([ETQ[m] for m in NOMS], rotation=40, ha="right", fontsize=7); ax.set_ylim(0.45, 0.86); ax.set_ylabel("AUC (cruce a 2 bps)"); ax.legend(); fig.tight_layout()
for ext in ("png", "pdf"): fig.savefig(OUT / f"G3_auc.{ext}")
fig, ax = plt.subplots(figsize=(6, 4.5)); M_ = np.array([brech[m] for m in NOMS]); im = ax.imshow(M_, cmap="RdBu_r", vmin=-1, vmax=1)
ax.set_xticks(range(4)); ax.set_xticklabels(list(cel), rotation=25, ha="right", fontsize=7); ax.set_yticks(range(len(NOMS))); ax.set_yticklabels([ETQ[m] for m in NOMS], fontsize=7)
for i in range(len(NOMS)):
    for j in range(4): ax.text(j, i, f"{M_[i, j]:+.2f}", ha="center", va="center", fontsize=6)
fig.colorbar(im, label="brecha del rebote"); ax.set_title("Rebote tras barridos (0 = bien calibrado)"); fig.tight_layout()
for ext in ("png", "pdf"): fig.savefig(OUT / f"G4_rebote.{ext}")
print(json.dumps(ver, ensure_ascii=False, indent=1)); print((OUT / "T1_walkforward_resumen.md").read_text())
