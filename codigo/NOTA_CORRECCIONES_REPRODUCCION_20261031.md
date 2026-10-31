# Correcciones de reproducción — 31 de octubre de 2026

Revisión de código sobre la base `f2ffcdb`. No modifica los modelos congelados, los protocolos sellados ni las cifras publicadas.

## Cambios

- El walk-forward solo reutiliza ventanas con JSON y eventos legibles y coherentes con sus fechas. Reconstruye los checkpoints incompletos o corruptos y vuelve a escribir ambos agregados, incluso si todas las ventanas ya estaban guardadas. Las escrituras publican archivos completos mediante reemplazo atómico.
- La caché de bins comprueba que la rejilla solicitada coincide con la almacenada. Si cambia o el archivo está incompleto, se reconstruye sin truncar el archivo anterior durante la escritura.
- El generador y los encabezados de las tablas de v115 llaman a R1 escenario de sensibilidad, en lugar de cota del PnL real. Los valores de las tablas no cambian.

## Verificación

- Seis pruebas de caché, sin datos de mercado: reutilización de rejilla equivalente, cambio con igual longitud, archivo truncado, conteos incompatibles, fallo de escritura y distancias no finitas.
- Once escenarios de reanudación contrastados con una corrida sintética completa, incluyendo una ventana sin eventos. Se comprueba que solo se recalculen ventanas inválidas y que los dos agregados finales coincidan con la corrida completa.
- Seis pruebas numéricas HJB existentes, sin cambios en el solver.
- Reproducción económica del 4 de septiembre con modelos y tablas congelados y cachés de bins/covariables nuevas: las 47 combinaciones coinciden exactamente en ejecuciones, PnL, nocional, suma de markout a 10 s e inventario medio. Usa eventos y paquete previamente generados y datos canónicos locales; no es una reestimación completa desde mensajes crudos.

Las pruebas no reentrenan los modelos finales ni repiten todo el walk-forward. La comprobación diaria se ejecutó con scikit-learn 1.9.0 disponible localmente; los modelos guardados indican 1.9.1 y el repositorio conserva las versiones originales fijadas en requirements.txt.

Comandos desde la raíz:

```bash
python -m unittest discover -s codigo/03_cargador_datos/codigo -p 'test_cache_v98.py' -v
python codigo/10_walk_forward/codigo/test_reanudacion_v102.py
python -m unittest discover -s codigo/08_hjb_exponencial -p 'test_hjb.py' -v
```
