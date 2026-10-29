"""T5: tabla del test 4–20 sep con modelos v108 (lee resultados_test_v101.json escrito por test_v109 en esta carpeta)."""
import csv, json
from pathlib import Path
R = Path(__file__).resolve().parents[1]; O = json.loads((R / "salida" / "resultados_test_v101.json").read_text()); S = R / "tablas_tesis"
ETQ = {"E3-fkX": "E3 f(δ)·k(X), 44 cov.", "E3": "E3 base (−kδ, 44 cov.)", "E1": "AS base", "E1+h-f": "AS + hora + f(δ)", "E1+S": "AS + 7 señales", "E1+X49": "GLM lineal 49 cov.",
       "E2+h-f": "Hawkes 1 escala + hora + f(δ)", "E2+S": "Hawkes 1 escala + señales", "E2m+h-f": "Hawkes 2 escalas + hora + f(δ)", "E2m+S": "Hawkes 2 escalas + señales"}
cab = ["Modelo"] + [f"{c} ({l})" for l in ("ask", "bid") for c in ("E3 − modelo (ll/bin) [IC95]", "Días E3 gana", "AUC δ=2")]
filas = [["E3 tesis (49 cov., f(δ)·k(X))"] + [x for l in ("ask", "bid") for x in ("—", "—", f"{O[f'auc_E3-fkX+B_{l}']:.3f}")]]
for m, e in ETQ.items():
    filas.append([e] + [x for l in ("ask", "bid") for x in (f"{O[f'{m}_{l}']['dll']:+.3f} [{O[f'{m}_{l}']['ic'][0]:+.3f}; {O[f'{m}_{l}']['ic'][1]:+.3f}]", f"{O[f'{m}_{l}']['dias']}/17", f"{O[f'{m}_{l}']['auc']:.3f}")])
b = O["brechas_E3-fkX+B"]
nota = (f"Test 4–20 sep 2026 (17 días, modelos v108: E3 tesis y E3-fkX con curva reoptimizada, ver NOTA_V108; entrenados 29 jun–3 sep). IC95 bootstrap por días. Criterios preregistrados: {', '.join(k for k, v in O['criterios'].items() if v)} cumplidos. "
        f"Brecha de rebote de E3 tesis: vendedores {b['vend']:+.3f}, compradores {b['comp']:+.3f}.")
md = ["### Test final (4–20 sep): E3 tesis frente a cada modelo (v108)", "", "| " + " | ".join(cab) + " |", "|" + "---|" * len(cab)] + ["| " + " | ".join(f) + " |" for f in filas] + ["", nota]
(S / "T5_test.md").write_text("\n".join(md) + "\n")
with open(S / "T5_test.csv", "w", newline="") as f:
    csv.writer(f).writerows([cab] + filas)
esc = lambda s: s.replace("%", r"\%").replace("δ", r"$\delta$").replace("−", "$-$").replace("·", r"$\cdot$")
tex = [r"\begin{table}[ht]\centering\small", r"\caption{Test final (4--20 sep): E3 tesis frente a cada modelo}", r"\begin{tabular}{l" + "c" * (len(cab) - 1) + "}", r"\toprule",
       " & ".join(esc(c) for c in cab) + r" \\", r"\midrule"] + [" & ".join(esc(x) for x in f) + r" \\" for f in filas] + [r"\bottomrule", r"\end{tabular}", r"\par\footnotesize " + esc(nota), r"\end{table}"]
(S / "T5_test.tex").write_text("\n".join(tex) + "\n")
