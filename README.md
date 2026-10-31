# Market Making with Statistical Learning: semiparametric order-arrival intensities in BTC/USDT

Undergraduate thesis, Data Science, Pontificia Universidad Javeriana (2026). Author: Santiago Rueda. Advisor: Vladimir Moreno.

The thesis document is in Spanish (`documento/`). This repository contains it together with the code, sealed protocols and results of the final phase of the work. The earlier exploratory phase is summarised in appendices B and C of the document.

## The question

A market maker quotes a buy and a sell price around the mid and earns the spread when aggressive orders hit them. The classical models assume how often that happens:
- Avellaneda–Stoikov (E1): a constant intensity that decays exponentially with distance;
- Hawkes (E2): self-exciting order flow.

The thesis proposes **E3**, a semiparametric intensity:

**log λ(t, δ) = g(X_t) + h(t) + m(X_t)·f(δ)**

- g: gradient boosting on 49 market covariates (order flow, book, volatility, sweeps);
- h: hour-of-day effect;
- f: a free monotone curve in the distance δ;
- m: a state modulation of that curve.

It then asks two separate questions:
1. **Prediction:** does E3 estimate the arrival of aggressive orders better than AS and Hawkes?
2. **Economics:** does that better estimate produce value under an optimal quoting policy (HJB)?

## Main results

| | Result | Folder |
|---|---|---|
| Walk-forward (34 days) | E3 beats all 10 benchmarks in all 5 windows, on both sides | [`10_`](codigo/10_walk_forward/) |
| Pre-registered test (4–20 Sep; not strictly blind, [see below](#the-test-period-had-been-consulted-before)) | All 4 criteria met; AUC 0.813; E3 beats the best Hawkes on 17 of 17 days | [`17_`](codigo/17_test_predictivo/) |
| Simulation (21 Sep–26 Oct, 36 new days) | Still the best predictor (AUC 0.848 / 0.842); the rebound criterion fails after buyer sweeps | [`19_`](codigo/19_simulacion/) |
| Economic value | With the strict-cross execution rule, every model and policy loses about 1.1–1.3 bps per fill before fees; E3 does not win on PnL | [`18_`](codigo/18_hjb_curva_interpolada/), [`19_`](codigo/19_simulacion/) |
| Queue robustness | Same result with an approximate FIFO queue. Under optimistic execution at the touch, the HJB policy with E3 earns a small gross profit in the simulation (+0.15 bps per fill), far below the fees evaluated (7.5–10 bps) | [`21_`](codigo/21_ejecucion_con_cola/) |
| Why | Adverse selection: whatever is captured by quoting farther is lost when the price keeps moving, mostly within the first second | [`20_`](codigo/20_seleccion_adversa/) |

**In short:** a clear predictive contribution and an economic result that is negative after the fees evaluated, both supported.

### The test period had been consulted before

The 4–20 Sep test is pre-registered but not blind in the strict sense:
- an earlier version of E3 had already been evaluated on those dates, inside the first blind test of the development phase (26 Aug–15 Sep);
- a pause policy was run on it before a hold order, without its results being read;
- the final specifications were evaluated on it more than once: the corrected curve fit (`15_`–`17_`) repeated the evaluation after a code review. The repeat matched the original to three decimals.

No parameter or hyperparameter was estimated on the test, and no version was chosen for its test performance. What the test confirms is the final specifications, which had never been evaluated there. The 21 Sep–26 Oct simulation is the period never seen by any version.

In the [thesis PDF](documento/main.pdf): §6.2 *Partición y protocolo* (methodology) and §9.3 *Limitaciones*, item *Exposición previa del test*; the earlier blind tests are in Appendix B.

## How well each model predicts

All 11 models predict the same thing: how many aggressive orders will reach each of 9 distances from the mid in the next second. They are fitted on the same data (29 Jun–3 Sep) and evaluated on days they never saw.

| Model | What it uses | AUC, test (4–20 Sep) | AUC, simulation (21 Sep–26 Oct) | Share of E3's gain, test / simulation |
|---|---|---|---|---|
| **E3-fkX+B (thesis)** | **Gradient boosting on 49 covariates + hour + f(δ) + m(X)** | **0.813** | **0.845** | **100 % / 100 %** |
| E3-fkX | Same, without sweep covariates (44) | 0.813 | 0.845 | 99 % / 100 % |
| E3 base | Gradient boosting + exponential −kδ | 0.811 | 0.845 | 95 % / 94 % |
| E1+X49 | Linear Poisson GLM with the same 49 covariates | 0.800 | 0.838 | 91 % / 90 % |
| E2m+S | Hawkes, two time scales, + 7 signals | 0.763 | 0.784 | 74 % / 70 % |
| E2m+h-f | Hawkes, two time scales, + hour + f(δ) | 0.748 | 0.764 | 61 % / 60 % |
| E2+S | Hawkes, one time scale, + 7 signals | 0.718 | 0.745 | 45 % / 43 % |
| E1+S | Avellaneda–Stoikov + 7 signals | 0.715 | 0.741 | 43 % / 41 % |
| E2+h-f | Hawkes, one time scale, + hour + f(δ) | 0.627 | 0.654 | 12 % / 16 % |
| E1+h-f | Avellaneda–Stoikov + hour + f(δ) | 0.613 | 0.642 | 10 % / 14 % |
| E1 | Avellaneda–Stoikov (constant intensity) | 0.500 | 0.500 | 0 % / 0 % |

How to read the table:
- **AUC** is computed at δ = 2 bps, averaged over the ask and bid sides. It measures how well the model ranks the seconds in which an order arrives above those in which none does: 0.5 is chance, 1 is perfect.
- **Share of E3's gain** is how much of E3's log-likelihood improvement over plain Avellaneda–Stoikov each model recovers.
- **Takeaways:**
  - E3 beats every Avellaneda–Stoikov and Hawkes variant on every test day (17/17) and every simulation day (36/36). It beats the linear GLM on 16 of 17 test days and 32–35 of 36 simulation days.
  - A linear model with the same covariates gets about 90 % of the way, so most of the gain comes from the covariates. The flexible fit adds the rest.
  - The best Hawkes model reaches about 70–74 %.
  - Prediction did not degrade on the 36 new days: the AUC rose from 0.813 to 0.845.

Details: [`10_`](codigo/10_walk_forward/) (walk-forward), [`17_`](codigo/17_test_predictivo/) (test), [`19_`](codigo/19_simulacion/) (simulation).

## Model names

| Name | Model |
|---|---|
| **E3-fkX+B** | **The thesis model** (49 covariates, curve f(δ), modulation m(X)) |
| E3-fkX, E3 | E3 without sweep covariates (44); E3 base with −kδ |
| E1 | Avellaneda–Stoikov |
| E1+h-f, E1+S, E1+X49 | AS + hour + f(δ); + 7 signals; Poisson GLM with E3's 49 covariates |
| E2+h-f, E2+S | Hawkes, one scale, + hour + f(δ); + signals |
| E2m+h-f, E2m+S | Hawkes, two scales, + hour + f(δ); + signals |

## Structure

```
documento/                      Thesis in LaTeX (main.tex, capitulos/, figuras/) and PDF (Spanish)
captura_datos/                  Data capture on the server: Python scripts, systemd services and shell commands
codigo/
  00_datos_canonicos/           Catalogue of the 120 days (SHA-256 per file); the data are not included
  01_nucleo_e3/                 Data layer, conventions and base E3 model (g + h − kδ)
  02_conteos_respuesta/         Counts of aggressor events reaching each distance (the response)
  03_cargador_datos/            Loader of the canonical layer with a date guard
  04_covariables_barrido/       Sweep and trend covariates; eventos_barridos/ detects the sweeps
  05_curva_distancia/           Monotone curve f(δ) and modulation m(X) (original version)
  06_modulacion_estado/         k(X) variant from the development phase
  07_modelos_as_hawkes/         Avellaneda–Stoikov and Hawkes with one and two scales
  08_hjb_exponencial/           HJB solver with exponential intensity and its tests
  09_protocolo_test/            Test pre-registration and shared functions (GLM, signals, evaluation)
  10_walk_forward/              Five-window walk-forward (11 models)
  11_modelos_finales/           Fit of the final models (29 Jun–3 Sep)
  12_test_predictivo_ajuste_original/
  13_pnl_miope_ajuste_original/
  14_pnl_hjb_aproximada_ajuste_original/
  15_verificacion_gradiente/    Gradient and convergence check of the E3 curve
  16_curva_e3_corregida/        Corrected E3 curve; final models used in the thesis (modelos_finales_v108.pkl)
  17_test_predictivo/           Predictive test with the corrected fit
  18_hjb_curva_interpolada/     HJB with the interpolated distance curve: checks and economic test
  19_simulacion/                Simulation 21 Sep–26 Oct with frozen models and policies
  20_seleccion_adversa/         Decomposition of the loss per fill
  21_ejecucion_con_cola/        Economic evaluation re-run with an approximate queue and optimistic at-touch execution
```

Each numbered folder has an English `README.md` with its purpose and results. It also contains:
- its protocol (`PLAN_*.md` or `ENMIENDA_*.md`, sealed with a `.sha256`; each script checks on start-up that the protocol has not changed);
- its code;
- its run note (`NOTA_*.md`) and summarised outputs.

Protocols and notes are in Spanish, as they were sealed.

**Data partition:**

| Period | Dates | Use |
|---|---|---|
| Training | 29 Jun–3 Sep | Walk-forward validation inside it: 1 Aug–3 Sep |
| Test | 4–20 Sep | Pre-registered; consulted before ([details](#the-test-period-had-been-consulted-before)) |
| Simulation | 21 Sep–26 Oct | Run once with everything frozen |

## Correspondence with the document

| Document | Folder |
|---|---|
| Ch. 6, methodology: response, models and evaluation | `02_`, `05_`, `07_`, `09_` |
| Ch. 7, data: capture and canonical layer | `captura_datos/`, `00_datos_canonicos/`, `03_cargador_datos/` |
| §8.1, final E3 specification | `01_` to `06_` |
| §8.2, walk-forward | `10_walk_forward/` |
| §8.3–8.4, predictive test and post-sweep calibration | `17_test_predictivo/` (identical to `12_` to three decimals) |
| §8.5, HJB policy | `08_hjb_exponencial/`, `18_hjb_curva_interpolada/` |
| §8.6, economic value in the test | `18_hjb_curva_interpolada/` (earlier versions: `13_`, `14_`) |
| §8.7, simulation | `19_simulacion/` |
| §8.8, origin of the loss and queue robustness | `20_seleccion_adversa/`, `21_ejecucion_con_cola/` |
| Appendix A, covariates | `01_nucleo_e3/`, `04_covariables_barrido/` |
| Gradient and convergence check | `15_`, `16_` |

## Data

The data are not in Git. They cover BTC/USDT on Binance Spot, 29 Jun–26 Oct 2026, about 38 GB (35 GB order book, 3 GB trades):
- the order book reconstructed every 100 ms;
- 337 million trades.

| | Records | Compressed | Uncompressed |
|---|---|---|---|
| Server, everything captured (29 Jun–19 Oct, measured) | — | 85 GB | — |
| Binance, primary only (120 days) | ≈ 440 M messages | ≈ 21 GB | ≈ 214 GB |
| Binance, primary + backup (120 days) | ≈ 880 M messages | ≈ 42 GB | ≈ 430 GB |
| Canonical layer: book every 100 ms | 104 M rows × 202 columns | 35 GB | — |
| Canonical layer: trades | 337 M | 3 GB | — |

The server inventory of 19 Oct records 85 GB compressed since 29 Jun (113 days):
- 64 GB of order books;
- 19 GB of trades;
- 2 GB of official Binance files.

It includes a parallel Coinbase (BTC/USD) capture, used only in the exploratory phase. The Binance BTC/USDT part (primary + backup) is about 40 GB over those 113 days. That agrees with two complete raw days kept locally (27–28 Jul), which extrapolate to ≈ 42 GB compressed and ≈ 430 GB uncompressed over 120 days.

Each capture received about 862,800 depth messages per day out of 864,000 possible (99.9 %). Primary and backup differ by a few hundred messages a day: the gaps the backup exists to fill.

This section summarises how the data were obtained and how to use them.

### 1. Capture on the server

The data were captured live on a dedicated Linux server:
- two parallel captures (primary and backup) per stream;
- each capture runs as a systemd service;
- files rotate every 12 hours.

The Python scripts, the systemd units and the install and operation commands are in [`captura_datos/`](captura_datos/README.md):

```bash
# order book: wss://data-stream.binance.vision/ws/btcusdt@depth@100ms (+ REST snapshots /api/v3/depth)
python captura_datos/python/live_lob_capture.py --exchange binance --symbol BTCUSDT --rotate-hours 12 --root /opt/lob_system

# trades: wss://data-stream.binance.vision/ws/btcusdt@trade
python captura_datos/python/live_trade_capture.py --exchange binance --storage-stream binance_trades --symbol BTCUSDT \
  --binance-stream trade --rotate-hours 12 --root /opt/lob_system
```

The book is rebuilt following Binance's official procedure:
- a REST snapshot, then the diffs in `U/u` sequence order;
- uncovered gaps are marked invalid and never interpolated.

The reconstruction and feature-layer code is in the project's public repository, [Market-Making-with-Statistical-Learning](https://github.com/sannti09/Market-Making-with-Statistical-Learning) (`src/reconstruction/`, `src/trades/`, `src/features/`).

### 2. Official trades (Binance Vision)

Trades are checked and completed with the official daily file, which ships with its checksum:

```bash
D=2026-09-04
URL=https://data.binance.vision/data/spot/daily/trades/BTCUSDT/BTCUSDT-trades-$D.zip
curl -sO "$URL" && curl -sO "$URL.CHECKSUM"
shasum -a 256 -c "BTCUSDT-trades-$D.zip.CHECKSUM"
```

On the server this download ran every day at 04:00 UTC (systemd timer). For a date range use the command below; it verifies every file against its checksum.

```bash
python captura_datos/python/download_binance_vision_trades.py --root /path --symbol BTCUSDT \
  --start-date YYYY-MM-DD --end-date YYYY-MM-DD
```

### 3. Use in this repository

Place the canonical layer inside `codigo/00_datos_canonicos/`, one file per day:

```
codigo/00_datos_canonicos/
  market_features_100ms/binance_market_features_100ms_BTCUSDT_YYYY-MM-DD.parquet   # 864,000 rows, 202 columns
  trades_event/binance_trades_events_BTCUSDT_YYYY-MM-DD.parquet                     # one row per trade
  CATALOGO.json
```

If the data live on another disk, symbolic links are enough:

```bash
cd codigo/00_datos_canonicos
ln -s /path/data/market_features_100ms market_features_100ms
ln -s /path/data/trades_event trades_event
```

Check the integrity of the 240 files against the catalogue:

```bash
cd codigo/00_datos_canonicos
python - <<'EOF'
import json, hashlib
from pathlib import Path
cat = json.load(open("CATALOGO.json"))["dias"]; bad = 0
for d, layers in cat.items():
    for layer, info in layers.items():
        name = (f"binance_market_features_100ms_BTCUSDT_{d}.parquet" if layer == "market_features_100ms"
                else f"binance_trades_events_BTCUSDT_{d}.parquet")
        h = hashlib.sha256(Path(layer, name).read_bytes()).hexdigest()
        bad += h != info["sha256"]
print("files that do not match:", bad)
EOF
```

Reading one day: the files are large, so read only the columns you need with PyArrow or DuckDB instead of concatenating everything into one DataFrame.

```bash
python - <<'EOF'
import pyarrow.parquet as pq
d = "2026-09-04"
book = pq.read_table(f"codigo/00_datos_canonicos/market_features_100ms/binance_market_features_100ms_BTCUSDT_{d}.parquet",
                     columns=["ts_ms", "state_valid", "best_bid", "best_ask", "mid"])
trades = pq.read_table(f"codigo/00_datos_canonicos/trades_event/binance_trades_events_BTCUSDT_{d}.parquet",
                       columns=["event_time_us", "price", "qty", "aggressor_buy"])
print(book.num_rows, trades.num_rows)
EOF
```

In the layer:
- the book at time `t` is the state known at `t`;
- `past_*` variables exclude the current interval;
- rows with `state_valid = False` (resynchronisations) must be dropped, never interpolated.

## Regenerated files

These files are not included because of their size; the code itself produces them:

| File | How it is generated |
|---|---|
| `codigo/04_covariables_barrido/eventos_barridos/salida/eventos_v92.pkl` | `eventos_barridos/codigo/eventos_v92.py` |
| `codigo/07_modelos_as_hawkes/paquete/dias/` | `07_modelos_as_hawkes/exportar_paquete.py` (events for the Hawkes fit) |
| `codigo/10_walk_forward/salida/eventos_v102.npy` | `10_walk_forward/codigo/wf_v102.py` (post-sweep events with each model's prediction); **required** by `tablas_v102.py` for table T4 |
| `codigo/18_hjb_curva_interpolada/salida/tablas_v110.pkl` | `18_hjb_curva_interpolada/codigo/verif_v110.py` |
| `salida/cache/` caches | created automatically |

## Execution order

1. `04_.../eventos_barridos/codigo/eventos_v92.py` and `07_.../exportar_paquete.py`: inputs.
2. `10_walk_forward/codigo/wf_v102.py`, then `tablas_v102.py`. The first writes `salida/eventos_v102.npy`, which the second needs; it can be resumed (see [`10_`](codigo/10_walk_forward/README.md)).
3. `11_modelos_finales/codigo/entrenar_v103.py`, then `16_curva_e3_corregida/codigo/actualizar_curva_v108.py`.
4. `17_test_predictivo/codigo/test_v109.py`.
5. `18_hjb_curva_interpolada/codigo/verif_v110.py`, then `econ_v110.py`.
6. `19_simulacion/codigo/sim_v111.py`.
7. `20_seleccion_adversa/codigo/sa_v112.py`.
8. `21_ejecucion_con_cola/codigo/cola_v115.py test`, then `cola_v115.py sim`.

**Reproducibility check:** from this structure, with caches built from scratch, the code exactly reproduces one test day (4 Sep). Prediction, fills and PnL all match with zero difference.

File names keep the version number they were run with (for example `wf_v102.py`), because the sealed protocols and notes refer to them.

## Environment

Python 3.14; versions in `requirements.txt`.

## License

- **Code** (`codigo/`, `captura_datos/`): [MIT License](LICENSE).
- **Thesis document** (`documento/`): [CC BY 4.0](documento/LICENSE.md). It can be shared and adapted with credit to the author.
- The market data are not included; they come from Binance's public streams and Binance Vision files, subject to Binance's terms.
