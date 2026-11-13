# Entrega 005 — Capas y visibilidad

Versión: `0.001.0003` · Fuente: entrega 004 (`0.001.0002`).

## Cambios

- `pv_geometry.py`: grupos por capa de origen y por tipo, colores de mayor contraste y exportación HTML autónoma.
- `test_layer_preview.py`: tres pruebas para capas, escape de atributos y controles.
- Documentación: `CHANGELOG.md`, `VERSION`, wiki y validación de capas.

## Observaciones

La cabecera de GenCAD declara 4 capas de enrutamiento; el bloque de pistas en la muestra contiene únicamente TOP y BOTTOM. No se altera la topología ni la geometría para resolver esta discrepancia. No se ha identificado un borde de placa mecánico verificable.

## Limitaciones

La vista HTML es diagnóstica y puede ser pesada debido a la cantidad de elementos SVG. La inspección visual frente al CAD original no está disponible. No se infiere espesor ni conectividad de las capas internas.
