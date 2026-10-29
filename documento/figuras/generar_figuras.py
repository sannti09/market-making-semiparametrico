#!/usr/bin/env python3
"""Figuras del documento final (notación del texto: E3 tesis = f(δ)·m(X) con 49 covariables).
Lee solo salidas ya guardadas de v102, v104, v105 y v106; no recalcula modelos. Uso: python generar_figuras.py <carpeta senales_condicionales_20261025_01>"""
import csv, json, sys
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

RR = Path(sys.argv[1]); OUT = Path(__file__).resolve().parent
AZUL, NARANJA, TINTA, TINTA2, REJILLA = "#2a78d6", "#eb6834", "#0b0b0b", "#52514e", "#e4e3df"
plt.rcParams.update({"font.size": 9, "axes.edgecolor": TINTA2, "axes.labelcolor": TINTA, "xtick.color": TINTA2, "ytick.color": TINTA2,
                     "axes.spines.top": False, "axes.spines.right": False, "font.family": "DejaVu Sans"})
# orden y etiquetas comunes (de mejor a peor en el walk-forward)
ORDEN = ["E3-fkX+B", "E3-fkX", "E3", "E1+X49", "E2m+S", "E2m+h-f", "E2+S", "E1+S", "E2+h-f", "E1+h-f", "E1"]
ETQ = {"E3-fkX+B": "E3 tesis", "E3-fkX": "E3-fkX (44 cov.)", "E3": "E3 base (−kδ)", "E1+X49": "GLM lineal (49 cov.)", "E2m+S": "Hawkes 2 esc. + S",
       "E2m+h-f": "Hawkes 2 esc. + h + f", "E2+S": "Hawkes 1 esc. + S", "E1+S": "AS + S", "E2+h-f": "Hawkes 1 esc. + h + f", "E1+h-f": "AS + h + f", "E1": "AS base"}
CSV2NOM = {"E3 tesis (49 cov., f(δ)·k(X))": "E3-fkX+B", "E3 f(δ)·k(X), 44 cov.": "E3-fkX", "E3 base (−kδ, 44 cov.)": "E3", "AS base": "E1",
           "AS + hora + f(δ)": "E1+h-f", "AS + 7 señales": "E1+S", "GLM lineal 49 cov.": "E1+X49", "Hawkes 1 escala + hora + f(δ)": "E2+h-f",
           "Hawkes 1 escala + señales": "E2+S", "Hawkes 2 escalas + hora + f(δ)": "E2m+h-f", "Hawkes 2 escalas + señales": "E2m+S"}
TT = RR / "102_walk_forward_20261029_01" / "tablas_tesis"
def leer(n): return {CSV2NOM[r["Modelo"]]: r for r in csv.DictReader(open(TT / n, encoding="utf-8"))}
def guardar(fig, n):
    fig.savefig(OUT / f"{n}.pdf", bbox_inches="tight"); fig.savefig(OUT / f"{n}.png", dpi=200, bbox_inches="tight"); plt.close(fig)

def barras_parte(parte, titulo, n):
    fig, ax = plt.subplots(figsize=(6.2, 3.9)); y = np.arange(len(ORDEN)); h = 0.38
    for k, (lado, c) in enumerate((("ask", AZUL), ("bid", NARANJA))):
        v = [parte[m][lado] for m in ORDEN]
        ax.barh(y + (k - 0.5) * (h + 0.02), v, height=h, color=c, label=lado, edgecolor="white", linewidth=0.6)
    ax.set_yticks(y, [ETQ[m] for m in ORDEN]); ax.invert_yaxis(); ax.set_xlim(0, 105); ax.axvline(100, color=TINTA2, lw=0.8, ls=":")
    ax.set_xlabel("Parte de la mejora de E3 tesis sobre AS base (%)"); ax.grid(axis="x", color=REJILLA, lw=0.6); ax.set_axisbelow(True)
    ax.set_title(titulo, loc="left", color=TINTA, fontsize=10); ax.legend(frameon=False, loc="lower right"); guardar(fig, n)

# F1: parte de la mejora, walk-forward
T1 = leer("T1_walkforward_resumen.csv")
pf = lambda s: float(s.replace("%", "").strip())
barras_parte({m: {"ask": pf(T1[m]["Parte de la mejora (ask)"]), "bid": pf(T1[m]["Parte de la mejora (bid)"])} for m in ORDEN},
             "Walk-forward: 34 días fuera de muestra (1 ago.–3 sep.)", "F1_parte_mejora_wf")

# F2: ventaja de E3 tesis por ventana (Δll por intervalo)
T2 = leer("T2_walkforward_por_ventana.csv"); vent = ["1–7 ago", "8–14 ago", "15–21 ago", "22–28 ago", "29 ago–3 sep"]
SEL = ["E1+h-f", "E1+S", "E2m+h-f", "E2m+S", "E1+X49", "E3"]; COL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#6250d6"]
fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.2), sharey=True)
for ax, lado in zip(axs, ("ask", "bid")):
    for m, c in zip(SEL, COL):
        ax.plot(range(5), [float(T2[m][f"{lado} {v}"]) for v in vent], color=c, lw=2, marker="o", ms=4.5, label=ETQ[m])
    ax.axhline(0, color=TINTA2, lw=0.8); ax.set_xticks(range(5), [v.replace(" ", "\n", 1) for v in vent]); ax.set_title(f"lado {lado}", loc="left", fontsize=10)
    ax.grid(axis="y", color=REJILLA, lw=0.6); ax.set_axisbelow(True)
axs[0].set_ylabel("E3 tesis − modelo (log-verosimilitud por intervalo)")
fig.legend(*axs[0].get_legend_handles_labels(), loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.12)); fig.tight_layout(); guardar(fig, "F2_ventaja_por_ventana")

# F3: brecha del rebote tras barridos (walk-forward), mapa divergente azul–gris–rojo
T4 = leer("T4_rebote.csv"); cel = ["Vendedor, 1 h al alza", "Vendedor, 1 h a la baja", "Comprador, 1 h al alza", "Comprador, 1 h a la baja"]
M = np.array([[float(T4[m][c]) for c in cel] for m in ORDEN])
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
cmap = LinearSegmentedColormap.from_list("div", ["#2a78d6", "#f0efec", "#d03b2f"])
fig, ax = plt.subplots(figsize=(6.0, 4.4)); im = ax.imshow(M, cmap=cmap, norm=TwoSlopeNorm(0, -1.2, 1.2), aspect="auto")
for i in range(M.shape[0]):
    for j in range(M.shape[1]):
        ax.text(j, i, f"{M[i, j]:+.2f}", ha="center", va="center", fontsize=8, color="white" if abs(M[i, j]) > 0.8 else TINTA)
ax.set_xticks(range(4), ["Barrido vendedor\n1 h al alza", "Barrido vendedor\n1 h a la baja", "Barrido comprador\n1 h al alza", "Barrido comprador\n1 h a la baja"], fontsize=8)
ax.set_yticks(range(len(ORDEN)), [ETQ[m] for m in ORDEN]); ax.tick_params(length=0)
for s in ax.spines.values(): s.set_visible(False)
cb = fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02); cb.set_label("brecha O/E del lado contrario (0 = calibrado)", fontsize=8); cb.outline.set_visible(False)
guardar(fig, "F3_rebote")

# F4: parte de la mejora en el test (4–20 sep), respecto de AS base
O = json.loads((RR / "104_test_final_20261029_01" / "salida" / "resultados_test_v101.json").read_text())
parte_t = {m: {l: (100.0 if m == "E3-fkX+B" else 0.0 if m == "E1" else 100 * (1 - O[f"{m}_{l}"]["dll"] / O[f"E1_{l}"]["dll"])) for l in ("ask", "bid")} for m in ORDEN}
barras_parte(parte_t, "Test: 17 días (4–20 sep.), modelos congelados", "F4_parte_mejora_test")

# F5: PnL por ejecución en el test (v110: ajuste corregido; HJB con curva interpolada), IC95 por días, y ejecuciones por día
R10 = json.loads((RR / "110_hjb_exacta_20261029_01" / "salida" / "resumen_v110.json").read_text())
MIO = {f["politica"]: f for f in R10["miope"]}; POLS = {(f["modelo"], f["politica"]): f for f in R10["politicas"]}
MS = ["E3-fkX+B", "E3", "E1+X49", "E2m+S", "E2m+h-f", "E1+h-f", "E1"]; POL = [("Miope", AZUL), ("HJB exacta", NARANJA), ("GLFT", "#1baf7a")]
fig, axs = plt.subplots(1, 2, figsize=(7.4, 3.6), sharey=True, gridspec_kw={"width_ratios": [1.3, 1]}); y = np.arange(len(MS))
for k, (pol, c) in enumerate(POL):
    fs = [MIO[m] if pol == "Miope" else POLS[(m, pol)] for m in MS]
    v = np.array([f["bps"] for f in fs]); e = [f["ejec_dia"] for f in fs]; yy = y + (k - 1) * 0.26
    axs[0].errorbar(v[:, 0], yy, xerr=[v[:, 0] - v[:, 1], v[:, 2] - v[:, 0]], fmt="o", ms=5, color=c, lw=1.4, capsize=0, label=pol.replace(" exacta", ""))
    axs[1].barh(yy, e, height=0.24, color=c, edgecolor="white", linewidth=0.6)
axs[0].axvline(0, color=TINTA2, lw=0.8); axs[0].set_xlim(-1.9, 0.15); axs[0].set_xlabel("PnL bruto por ejecución (bps), IC95 por días")
axs[1].set_xlabel("Ejecuciones por día"); axs[0].set_yticks(y, [ETQ[m] for m in MS]); axs[0].invert_yaxis()
for a in axs: a.grid(axis="x", color=REJILLA, lw=0.6); a.set_axisbelow(True)
fig.legend(*axs[0].get_legend_handles_labels(), loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.14), title="Política"); fig.tight_layout(); guardar(fig, "F5_pnl_test")
print("ok")
