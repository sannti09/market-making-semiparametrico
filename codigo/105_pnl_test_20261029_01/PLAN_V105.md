# v105: PnL de market making en el test 4–20 sep con los modelos congelados v103 (29 oct; escrito antes de correr; autorizado por Santiago: "quiero ver en el test del 4 al 20")

**Pregunta.** Si cada modelo decide a qué distancia cotizar, ¿cuánto gana o pierde? Es la misma regla para todos los modelos; solo cambia la intensidad λ̂ que predice cada uno.

**Datos.** Carpeta canónica 00_DATOS; test 4–20 sep; los bins de 1 s y las predicciones son las de v104 (sin reajuste). La corrida libre sigue cerrada.

**Regla de cotización (Avellaneda–Stoikov miope, igual para todos):**
- En cada segundo y en cada lado, δ* = argmax_δ λ̂(δ)·δ sobre la rejilla {0,5; 1; 2; 3; 5; 7,5; 10; 15; 20} bps.
- Cotizaciones: ask = ceil(mid·(1+δ*)) en ticks de 0,01 y como mínimo best_bid + 1 tick; bid = floor(mid·(1−δ*)) y como máximo best_ask − 1 tick. Se usa el mid y el BBO del inicio del bin.
- Una orden de 1 unidad (0,01 BTC) por lado y por segundo.
- Límite de inventario: |q| ≤ 10 unidades; al alcanzarlo no se cotiza el lado que lo aumentaría.

**Ejecución (regla conservadora validada en v80/v81 con hftbacktest):** la orden se ejecuta si, dentro de ese segundo, llega un agresor con precio estrictamente más allá del nuestro. Hay como mucho una ejecución por lado y por segundo, y se ejecuta al precio de la orden.

**Referencias sin modelo:** δ fijo = 0,5, 2 y 5 bps.

**Métricas (por día; IC95 bootstrap por días, 2 000 réplicas, semilla 20261029):**
- ejecuciones por día;
- markout por ejecución a 10 s y 60 s (bps; lado·(precio − mid_H)/precio);
- PnL del día valorado a mercado al cierre (efectivo + inventario × último mid), en USDT y en bps por ejecución;
- comisión maker de equilibrio = PnL bruto en bps por ejecución.
- Todo es bruto, sin comisiones; se informa también con la comisión maker estándar de Binance spot (VIP0 0,1 % = 10 bps; con BNB 7,5 bps).

**Lectura esperada (de v81–v89):** el market making pasivo pierde ≈ −1,2 bps por ejecución antes de comisiones. Aquí se mide si una mejor predicción de λ cambia eso o lo reduce. No hay criterio de éxito: es informativo (P2 pausada).
