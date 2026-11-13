# Entrega 007 · Navegación e inventario de la fuente

**Versión:** 0.001.0005  
**Base:** 0.001.0004  
**Alcance:** interfaz HTML diagnóstica e inventario de GenCAD, sin cambios en PVF.

## Cambios

- Zoom con rueda centrado en el puntero. Desplazamiento manteniendo botón derecho, captura del puntero y cancelación del menú contextual sobre el SVG.
- Botón para restablecer el encuadre, indicador de zoom y límites para evitar escalas extremas.
- `source_features_audit.py` inventaría trazos de `$BOARD`, capas, `$MECH` y transformaciones de los componentes. No etiqueta arte como serigrafía sin datos que lo justifiquen.
- Nuevos controles y pruebas; HTML regenerado a partir del mismo PVF de referencia.

## Pruebas

- 63 pruebas unitarias seleccionadas: correctas. `test_geometry.py` y `test_pvf.py` son scripts con argumento posicional y se ejecutan por separado, no mediante descubrimiento automático.
- Validación estática de los controles en el HTML regenerado y análisis de la fuente GenCAD.
- Interacción real con Edge/Chrome pendiente de verificar manualmente; no se considera validada en un navegador.

## Resultados del inventario

- 204 grupos `ARTWORK` de `$BOARD`: 143 TOP, 61 BOTTOM, 1174 líneas y 114 arcos.
- `$ARTWORKS` vacío, sin nombres de capa explícitos `SILK`/`LEGEND`: serigrafía **no identificada explícitamente**.
- Siete taladros mecánicos en `$MECH`; sin contorno de placa clasificado como tal.
- 2.693 componentes: 2.450 TOP y 243 BOTTOM, estos últimos con `FLIP`/`MIRRORY`.

## Archivos relevantes

`pv_geometry.py`, `source_features_audit.py`, `test_layer_preview.py`, `test_source_features_audit.py`, `generated/MS-7B79 r1.0_artwork.html`, `generated/MS-7B79 r1.0_layers.html`, `docs/validaciones/NAVEGACION_Y_FUENTE.md`, `auditorias/2026-11-13_inventario_serigrafia_mecanica.json`.

**Sin cambios en la geometría convertida ni en GitHub.**
