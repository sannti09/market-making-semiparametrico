"""Convenciones matemáticas, dependencias de canales y evaluación formal de criterios (v27).

Garantías metodológicas de v27:
1. Clasificación estricta de dependencias por canal:
   - Markov, Baseline_R, Principal_RF: Trades exclusivamente.
   - V1 (volumen), V2 (duración racha), V3 (tiempos inter-llegada): Trades exclusivamente.
   - V4 (spread/OBI), V5 (microprecio): Trades + LOB acreditado continuo.
   - V6 (combinación): Unión dinámica de las dependencias de sus componentes activos.
   - Frente B (distancias, barreras, excursiones, profundidad): LOB acreditado continuo.
2. Advertencia metodológica de exposición de trades:
   - Los trades recibidos válidos permiten estudiar marcas y dirección condicional (Frente A),
     pero NO acreditan exposición temporal continua ni autorizan intensidades absolutas ni Hawkes.
3. Comparación justa sobre soporte común idéntico:
   - Toda métrica relativa candidato vs. baseline debe evaluarse sobre la intersección
     estricta de observaciones donde ambos modelos son elegibles.
4. Denominador estricto de 12 fechas nominales conservado íntegramente.
"""

import math
from typing import List, Dict, Any, Tuple, Optional, Sequence

EPSILON = 1e-12
TICK_SIZE = 0.01  # Tick size de BTCUSDT en Binance
DISTANCIAS_BPS_DEF = [0.5, 1.0, 2.0, 3.0, 5.0, 7.5, 10.0, 15.0, 20.0]
HORIZONTES_SEC_DEF = [1, 5, 30, 60]
HORIZONTES_MS_DEF = [100, 1000, 5000]
CANDIDATOS_L2_DEF = [0.0001, 0.001, 0.01, 0.1, 1.0, 10.0, 100.0]

# Canales canónicos de dependencia
CANAL_TRADES = "trades"
CANAL_TRADES_LOB = "trades_lob"
CANAL_LOB = "lob"
CANAL_UNION = "union"

# Matriz autoritativa de dependencias
DEPENDENCIAS_FAMILIAS: Dict[str, str] = {
    "markov": CANAL_TRADES,
    "Markov": CANAL_TRADES,
    "r": CANAL_TRADES,
    "R": CANAL_TRADES,
    "Baseline_R": CANAL_TRADES,
    "rf": CANAL_TRADES,
    "RF": CANAL_TRADES,
    "Principal_RF": CANAL_TRADES,
    "v1": CANAL_TRADES,
    "V1": CANAL_TRADES,
    "v2": CANAL_TRADES,
    "V2": CANAL_TRADES,
    "v3": CANAL_TRADES,
    "V3": CANAL_TRADES,
    "v4": CANAL_TRADES_LOB,
    "V4": CANAL_TRADES_LOB,
    "v5": CANAL_TRADES_LOB,
    "V5": CANAL_TRADES_LOB,
    "v6": CANAL_UNION,
    "V6": CANAL_UNION,
    "V6_Combinada": CANAL_UNION,
    "frente_b": CANAL_LOB,
    "Frente_B": CANAL_LOB,
}

# Advertencia de exposición continua de trades
EXPOSICION_TRADES_CONTINUA_DEFAULT = "NO_ACREDITADA"
AVISO_METODOLOGICO_EXPOSICION_TRADES = (
    "Trades recibidos válidos permiten estudiar marcas y dirección condicional (Frente A), "
    "pero no acreditan exposición temporal continua ni autorizan estimación de intensidades "
    "absolutas ni procesos de Hawkes."
)

# Catálogo canónico de unidades y metadatos de features
UNIDADES_FEATURES: Dict[str, str] = {
    "s_prev": "signo_{-1,+1}",
    "streak_signed": "signo*ln(conteoracha)",
    "i_20": "ratio_[-1,1]",
    "i_100": "ratio_[-1,1]",
    "v_20": "ln(1+vol_btc)",
    "v_100": "ln(1+vol_btc)",
    "log_dt_streak": "ln(1+ms)",
    "log_dt_last": "ln(1+ms)",
    "log_dt_mean20": "ln(1+ms)",
    "spread_bps": "bps",
    "imbalance_obi": "ratio_[-1,1]",
    "micro_price_diff": "ticks"
}

FAMILIAS_INFO: Dict[str, Dict[str, Any]] = {
    "Markov": {
        "key": "feat_r",
        "names": ["s_prev"],
        "requiere_lob": False,
        "canal_dependencia": CANAL_TRADES,
        "n_unpenalized": 2
    },
    "R": {
        "key": "feat_r",
        "names": ["s_prev", "streak_signed"],
        "requiere_lob": False,
        "canal_dependencia": CANAL_TRADES,
        "n_unpenalized": 3
    },
    "RF": {
        "key": "feat_rf",
        "names": ["s_prev", "streak_signed", "i_20", "i_100"],
        "requiere_lob": False,
        "canal_dependencia": CANAL_TRADES,
        "n_unpenalized": 3
    },
    "V1": {
        "key": "feat_v1",
        "names": ["s_prev", "streak_signed", "i_20", "i_100", "v_20", "v_100"],
        "requiere_lob": False,
        "canal_dependencia": CANAL_TRADES,
        "n_unpenalized": 3,
        "extra_names": ["v_20", "v_100"]
    },
    "V2": {
        "key": "feat_v2",
        "names": ["s_prev", "streak_signed", "i_20", "i_100", "log_dt_streak"],
        "requiere_lob": False,
        "canal_dependencia": CANAL_TRADES,
        "n_unpenalized": 3,
        "extra_names": ["log_dt_streak"]
    },
    "V3": {
        "key": "feat_v3",
        "names": ["s_prev", "streak_signed", "i_20", "i_100", "log_dt_last", "log_dt_mean20"],
        "requiere_lob": False,
        "canal_dependencia": CANAL_TRADES,
        "n_unpenalized": 3,
        "extra_names": ["log_dt_last", "log_dt_mean20"]
    },
    "V4": {
        "key": "feat_v4",
        "names": ["s_prev", "streak_signed", "i_20", "i_100", "spread_bps", "imbalance_obi"],
        "requiere_lob": True,
        "canal_dependencia": CANAL_TRADES_LOB,
        "n_unpenalized": 3,
        "extra_names": ["spread_bps", "imbalance_obi"]
    },
    "V5": {
        "key": "feat_v5",
        "names": ["s_prev", "streak_signed", "i_20", "i_100", "micro_price_diff"],
        "requiere_lob": True,
        "canal_dependencia": CANAL_TRADES_LOB,
        "n_unpenalized": 3,
        "extra_names": ["micro_price_diff"]
    }
}


def determinar_dependencia_v6(familias_componentes: Sequence[str]) -> Tuple[str, bool]:
    """Determina la dependencia canónica de V6 a partir de la unión de sus componentes activos.
    
    Devuelve (canal_dependencia, requiere_lob).
    Si algún componente requiere LOB (V4 o V5), V6 requiere LOB.
    Si todos son trades (ej. V1 y V2), V6 requiere únicamente Trades.
    """
    for fam in familias_componentes:
        dep = DEPENDENCIAS_FAMILIAS.get(fam, CANAL_TRADES_LOB)
        if dep == CANAL_TRADES_LOB:
            return CANAL_TRADES_LOB, True
    return CANAL_TRADES, False


def clip_prob(p: float) -> float:
    """Acota probabilidad p en [EPSILON, 1 - EPSILON] de forma simétrica."""
    if p < EPSILON:
        return EPSILON
    if p > 1.0 - EPSILON:
        return 1.0 - EPSILON
    return p


def sigmoide(z: float) -> float:
    """Función sigmoide con protección contra desbordamiento en extremos."""
    if z < -35.0:
        return EPSILON
    if z > 35.0:
        return 1.0 - EPSILON
    return 1.0 / (1.0 + math.exp(-z))


# Alias de sigmoide
sigmoid = sigmoide


def calcular_log_loss(y_true: List[int], p_pred: List[float]) -> float:
    """Calcula la pérdida logarítmica binaria media (Log-Loss)."""
    if not y_true or not p_pred or len(y_true) != len(p_pred):
        raise ValueError("Longitudes inválidas o listas vacías en calcular_log_loss")
    n = len(y_true)
    loss = 0.0
    for y, p in zip(y_true, p_pred):
        p_c = clip_prob(p)
        if y == 1:
            loss -= math.log(p_c)
        else:
            loss -= math.log(1.0 - p_c)
    return loss / float(n)


# Alias de calcular_log_loss
log_loss = calcular_log_loss


def calcular_brier_score(y_true: List[int], p_pred: List[float]) -> float:
    """Calcula el Brier Score cuadrático medio."""
    if not y_true or not p_pred or len(y_true) != len(p_pred):
        raise ValueError("Longitudes inválidas o listas vacías en calcular_brier_score")
    n = len(y_true)
    return sum((p - y) ** 2 for y, p in zip(y_true, p_pred)) / float(n)


# Alias de calcular_brier_score
brier_score = calcular_brier_score


def relative_improvement(loss_cand: float, loss_base: float) -> float:
    """Mejora porcentual relativa: ((loss_base - loss_cand) / loss_base) * 100.
    
    Valor positivo indica reducción de error (mejora del candidato).
    """
    if math.isnan(loss_base) or loss_base <= 0.0 or math.isnan(loss_cand):
        return float('nan')
    return ((loss_base - loss_cand) / loss_base) * 100.0


def evaluar_comparacion_muestras_comunes(
    y_comun: List[int],
    p_cand: List[float],
    p_base: List[float]
) -> Dict[str, Any]:
    """Evalúa estrictamente las métricas de un candidato vs. un baseline sobre la misma muestra común."""
    if not y_comun or len(y_comun) != len(p_cand) or len(y_comun) != len(p_base):
        raise ValueError("Discrepancia en longitudes de vectores de soporte común")
    ll_cand = calcular_log_loss(y_comun, p_cand)
    ll_base = calcular_log_loss(y_comun, p_base)
    br_cand = calcular_brier_score(y_comun, p_cand)
    br_base = calcular_brier_score(y_comun, p_base)
    mejora_ll = (ll_base - ll_cand) / ll_base if ll_base > 0 else float('nan')
    return {
        "n_muestras_comunes": len(y_comun),
        "log_loss_candidato": ll_cand,
        "log_loss_baseline": ll_base,
        "brier_candidato": br_cand,
        "brier_baseline": br_base,
        "mejora_relativa_log_loss": mejora_ll,
        "mejora_pct_log_loss": mejora_ll * 100.0 if not math.isnan(mejora_ll) else float('nan'),
        "gana_log_loss": mejora_ll > 0.0,
        "gana_brier": br_cand < br_base
    }


def evaluar_criterio_exploratorio_por_fechas(
    fechas_resultados: List[Dict[str, Any]],
    candidato: str = "principal_rf",
    baseline: str = "baseline_r",
    n_fechas_planificadas: Optional[int] = None
) -> Dict[str, Any]:
    """Evalúa formalmente los 4 criterios del mandato sobre fechas completas:
    
    1. Media relativa de Log-Loss >= 1.0% (positivo es reducción de error).
    2. Fracción de victorias de Log-Loss >= 80% sobre el total planificado.
    3. Peor fecha relativa >= -2.0%.
    4. Fracción de victorias de Brier >= 80% sobre el total planificado.
    
    Garantía metodológica:
    El denominador de victorias incluye todas las fechas planificadas. Si una fecha
    está ausente, vacía o con error/observación incompleta, se contabiliza como no-victoria.
    """
    n_plan = n_fechas_planificadas if n_fechas_planificadas is not None else len(fechas_resultados)
    if n_plan == 0:
        return {
            "cumple_criterio_integral": False,
            "cumple_criterio_global": False,
            "motivo": "sin_fechas_planificadas",
            "n_fechas_planificadas": 0,
            "n_fechas_validas": 0,
            "media_mejora_relativa_ll": float('nan'),
            "fraccion_victorias_ll": 0.0,
            "peor_fecha_relativa_ll": float('nan'),
            "fraccion_victorias_brier": 0.0,
        }

    mejoras_ll: List[float] = []
    victorias_ll = 0
    victorias_brier = 0
    n_validas = 0

    cand_lower = candidato.lower()
    base_lower = baseline.lower()

    for f_info in fechas_resultados:
        # Si la fecha viene marcada explícitamente como no válida
        if f_info.get("valida") is False:
            continue

        # Si viene comparación directa por par (ej. f_info["comparaciones_pares"]["V4_vs_R"])
        comps_pares = f_info.get("comparaciones_pares", {})
        clave_par = f"{candidato}_vs_{baseline}"
        clave_par_alt = f"{cand_lower}_vs_{base_lower}"
        
        comp_directa = comps_pares.get(clave_par) or comps_pares.get(clave_par_alt)
        if comp_directa and isinstance(comp_directa, dict):
            # Exigir estrictamente comparación válida y soporte común comprobado
            if comp_directa.get("valida") is True and comp_directa.get("soporte_comun_valido", True) is not False:
                n_muestras_c = comp_directa.get("n_muestras_comunes", comp_directa.get("n_muestras", 0))
                if n_muestras_c > 0:
                    mejora_rel = comp_directa.get("mejora_relativa_log_loss")
                    br_cand = comp_directa.get("brier_candidato")
                    br_base = comp_directa.get("brier_baseline")
                    if mejora_rel is not None and not math.isnan(mejora_rel) and br_cand is not None and br_base is not None:
                        n_validas += 1
                        mejoras_ll.append(mejora_rel)
                        if mejora_rel > 0.0:
                            victorias_ll += 1
                        if br_cand < br_base:
                            victorias_brier += 1
            # PAR PROCESADO: par no válido o sin soporte común verificado se descarta;
            # Queda estrictamente PROHIBIDO el fallback a métricas individuales.
            continue

        # Si el par NO existe en comparaciones_pares:
        # Por mandato estricto de Codex: par ausente o sin validación de soporte común
        # NO puede recurrir a métricas individuales de LL bajo ninguna circunstancia.
        continue

    if n_validas == 0:
        return {
            "cumple_criterio_integral": False,
            "cumple_criterio_global": False,
            "motivo": "sin_fechas_validas_comparables",
            "n_fechas_planificadas": n_plan,
            "n_fechas_validas": 0,
            "media_mejora_relativa_ll": float('nan'),
            "fraccion_victorias_ll": 0.0,
            "peor_fecha_relativa_ll": float('nan'),
            "fraccion_victorias_brier": 0.0,
        }

    # Denominador estricto sobre fechas planificadas (prohibido eliminar fechas inválidas del denominador)
    media_mejora_ll = sum(mejoras_ll) / float(n_plan)
    peor_fecha_ll = min(mejoras_ll)
    frac_victorias_ll = victorias_ll / float(n_plan)
    frac_victorias_brier = victorias_brier / float(n_plan)

    cond_cobertura_completa = (n_validas == n_plan)
    cond_media = media_mejora_ll >= 0.01       # >= 1.0%
    cond_consistencia = frac_victorias_ll >= 0.80  # >= 80%
    cond_peor_fecha = peor_fecha_ll >= -0.02   # >= -2.0%
    cond_brier = frac_victorias_brier >= 0.80  # >= 80%

    cumple = cond_cobertura_completa and cond_media and cond_consistencia and cond_peor_fecha and cond_brier

    return {
        "n_fechas": n_plan,
        "n_fechas_planificadas": n_plan,
        "n_fechas_validas": n_validas,
        "cobertura_fechas_completa": cond_cobertura_completa,
        "media_mejora_relativa_ll": media_mejora_ll,
        "media_mejora_log_loss_pct": media_mejora_ll * 100.0,
        "fraccion_victorias_ll": frac_victorias_ll,
        "ratio_victorias_log_loss": frac_victorias_ll,
        "peor_fecha_relativa_ll": peor_fecha_ll,
        "peor_fecha_mejora_pct": peor_fecha_ll * 100.0,
        "fraccion_victorias_brier": frac_victorias_brier,
        "ratio_victorias_brier": frac_victorias_brier,
        "condicion_cobertura_completa": cond_cobertura_completa,
        "condicion_media_ge_1pct": cond_media,
        "condicion_fechas_ge_80pct": cond_consistencia,
        "condicion_peor_fecha_ge_m2pct": cond_peor_fecha,
        "condicion_brier_ge_80pct": cond_brier,
        "cumple_criterio_integral": cumple,
        "cumple_criterio_global": cumple,
        "incertidumbre_descriptiva": incertidumbre_descriptiva_por_fechas(mejoras_ll, victorias_ll)
    }


def incertidumbre_descriptiva_por_fechas(mejoras_ll: Sequence[float], victorias_ll: int) -> Dict[str, Any]:
    """Incertidumbre por fecha (unidad de dependencia), solo descriptiva (v32).

    No modifica el criterio congelado. Prueba de signo unilateral H0: P(victoria)=0.5 con fechas
    como unidades independientes; p_minimo_alcanzable = 0.5**n muestra la resolución máxima
    (con n=3 nunca baja de 0.125). Las fechas comparten régimen y no son independientes en sentido
    estricto, por lo que el p-valor es optimista.
    """
    n = len(mejoras_ll)
    if n == 0:
        return {"n_fechas_validas": 0, "p_signo_unilateral": float('nan'),
                "p_minimo_alcanzable": float('nan'), "mejoras_relativas_ll_por_fecha": []}
    p_signo = sum(math.comb(n, k) for k in range(victorias_ll, n + 1)) / float(2 ** n)
    media = sum(mejoras_ll) / float(n)
    if n > 1:
        var = sum((m - media) ** 2 for m in mejoras_ll) / float(n - 1)
        ee = math.sqrt(var / n)
    else:
        ee = float('nan')
    return {
        "n_fechas_validas": n,
        "mejoras_relativas_ll_por_fecha": list(mejoras_ll),
        "media_fechas_validas": media,
        "error_estandar_entre_fechas": ee,
        "p_signo_unilateral": p_signo,
        "p_minimo_alcanzable": 0.5 ** n,
        "aviso": "descriptivo; no altera cumple_criterio_integral; fechas no estrictamente independientes",
    }


# Alias de evaluar_criterio_exploratorio_por_fechas
evaluar_criterio_exploratorio = evaluar_criterio_exploratorio_por_fechas
