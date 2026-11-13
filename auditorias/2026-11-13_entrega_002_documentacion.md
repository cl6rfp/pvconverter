# Entrega 002 — Wiki y versiones beta

**Fecha:** 2026-11-13  
**Versión del proyecto:** `0.001.0000`  
**Alcance:** organización documental únicamente, sobre la copia de la entrega 001.

## Cambios

- Se trasladaron las tres validaciones antiguas de la raíz a `docs/validaciones/`, sin editar su contenido.
- Se agrupó la documentación anterior en `docs/wiki/`, `docs/formato/` y `docs/historia/`.
- Se añadieron `docs/README.md`, guías de versionado y mantenimiento, estado actual, `CHANGELOG.md` y `VERSION`.
- Se corrigieron enlaces actuales en README e historial.
- Se mantuvieron los archivos de auditorías anteriores sin modificación. Sus rutas antiguas siguen describiendo el repositorio que se auditó entonces.

## Compatibilidad

Sin modificaciones en `.py`, `.cad`, `.pv`, SVG, dependencias o CI. PVF sigue siendo 1.0. El cambio de ubicación de Markdown podría afectar enlaces externos directos hacia la raíz; el índice nuevo indica su ubicación actual.

## Validación

Consultar los resultados de ejecución anotados al cerrar esta entrega. No atribuir resultados a plataformas distintas del entorno real de comprobación.

## Pendiente

- Continuar el análisis técnico de conectividad en una entrega posterior.
- Contrastar el historial previo con referencias adicionales si se aportan.

## Comprobaciones ejecutadas en esta entrega

Entorno: Linux, Python 3.13.

```bash
python -m unittest -q test_gencad_parser test_pv_validation test_pvf_security test_route_audit
python -m compileall -q pvf.py pv_geometry.py build_pv.py route_audit.py pv_converter_gui.py
```

Resultado: **36 pruebas unitarias correctas**, compilación de los módulos indicados correcta. Comprobación automatizada de rutas relativas Markdown en README, wiki, changelog y el índice de auditorías: **0 enlaces rotos**. No se repitieron en esta entrega la conversión integral del CAD ni las pruebas con interfaz Windows; figuran en la auditoría de la entrega 001.
