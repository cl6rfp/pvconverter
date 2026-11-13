# Entrega 006 · 0.001.0004 · Procedencia de geometría BOARD

## Motivo

En la inspección visual del SVG se observaron recuadros aislados y geometría aparentemente desplazada. Se necesitaba identificar el objeto fuente antes de decidir si existe un error de transformación o si se trata de un dibujo legítimo.

## Cambios

- Nuevo `artwork_audit.py`: inventario geométrico no destructivo de los grupos de `$BOARD`.
- Las salidas SVG incluyen identificador, nombre y título de los grupos `ARTWORK`.
- La vista HTML permite seleccionar un grupo de arte y atenuar los demás.
- Nuevo documento `docs/validaciones/ARTWORK_Y_CONTORNO.md` y pruebas `test_artwork_audit.py`.

## Observaciones sobre MS-7B79 r1.0

- 204 grupos `ARTWORK` en el PV.
- 152 grupos cumplen la comprobación básica de ciclo cerrado compuesto solo por líneas.
- 0 primitivas de tipo `rectangle` en esos grupos. Las figuras rectangulares observadas pueden estar constituidas por líneas.
- No hay justificación suficiente para declarar un contorno mecánico de placa ni borrar arte de la fuente.

Los resultados por grupo están en `2026-11-13_artwork_referencia.json`.

## Alcance

Esta entrega añade trazabilidad y herramientas de inspección: no afirma haber corregido el rectángulo de una captura concreta ni modifica datos fuente. El futuro diagnóstico de transformaciones de componentes tendrá su propia evidencia y pruebas.

## Compatibilidad

El importador GenCAD, el contenedor PVF 1.0 y los datos `.pv` permanecen intactos. La mejora afecta a informes y al SVG/HTML de diagnóstico.

## Verificación ejecutada

- 61 pruebas unitarias seleccionadas: correctas.
- Reconversión de `MS-7B79 r1.0.cad`: correcta; 18 bloques PVF.
- `test_pvf.py`, `test_geometry.py`, `test_arc_direction.py`: correctos.
- El SVG regenerado se analizó con el parser XML sin errores.
- Ejecutado en Linux/Python 3.13. No verificado en Windows ni comparado con un visor CAD independiente.
