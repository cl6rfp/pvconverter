# Entrega 009 — 0.001.0007

Fecha: 2026-11-13

## Cambios

- Nuevo módulo `component_transform.py` para cálculo y diagnóstico sin alterar el archivo fuente.
- `pv_geometry.py` incluye las envolventes transformadas de los pads al calcular el encuadre.
- Añadidas cinco pruebas unitarias en `test_component_transform.py`.
- Reconversión y regeneración de las vistas `layers` y `artwork`.

## Comprobación

- 74 pruebas unitarias: correctas.
- Conversión de `MS-7B79 r1.0.cad` con `--strict-source`: correcta.
- Pruebas de arcos, integridad PVF y geometría sobre la nueva conversión: correctas.
- SVG generado y página HTML de diagnóstico: correctos en generación; interacción manual no comprobada aquí.
- Informe de transformaciones: 2.693 componentes y 11.104 pines evaluados; 0 coordenadas no finitas y 0 pines sin geometría de pad; 243 tokens FLIP y 243 MIRRORY. Aparecen 4.900 tokens numéricos `0` asociados a la huella, conservados pero no interpretados semánticamente.

## Límites

Estos resultados no certifican el espejo físico, la serigrafía, el borde mecánico ni el seguimiento eléctrico. La modificación SVG afecta al encuadre, no a las posiciones originales de pads o componentes.

La lentitud del HTML queda anotada como deuda técnica del visor, no del formato PVF.
