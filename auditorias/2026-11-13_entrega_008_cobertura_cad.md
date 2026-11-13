# Entrega 008 — cobertura GenCAD

**Versión:** 0.001.0006 (beta)  
**Fecha:** 2026-11-13

## Trabajo realizado

- Se añadió `cad_coverage_audit.py` para inventariar instrucciones por sección y señalar registros desconocidos, parcialmente interpretados y estructuralmente incompletos.
- `build_pv.py` acepta `--strict-source` para impedir la creación de PVF cuando el inventario detecta instrucciones desconocidas o con campos insuficientes. La conversión predeterminada no cambia.
- Se añadieron seis pruebas unitarias y un resultado JSON para la placa de referencia.
- No se alteró ninguna coordenada, capa, primitiva ni transformación. Se conserva PVF 1.0.

## Comprobación local

- Placa `MS-7B79 r1.0.cad`: cero instrucciones desconocidas, cero registros cortos, 482 registros con interpretación parcial.
- Conversión con `--strict-source`: correcta.
- Lectura e integridad del PVF generado: correcta (`test_pvf.py`).
- Validación geométrica y exportación SVG: correctas (`test_geometry.py`).
- `test_cad_coverage_audit.py`: 6 pruebas superadas.

**Alcance:** la comprobación cuenta instrucciones y campos. No certifica la precisión geométrica ni las conexiones eléctricas. La placa sigue sin borde mecánico confirmado y persiste la incertidumbre de transformaciones de cara inferior.

**Próximo trabajo:** análisis de transformaciones de componentes y pads con pruebas sintéticas, seguido de contraste dimensional con datos externos si llegan a estar disponibles.
