# Historial del proyecto — registro acumulativo

Este registro distingue **trabajo previo reconstruido** a partir de los archivos recibidos y **cambios ejecutados en esta entrega**. No se inventan fechas, autorías ni resultados anteriores no demostrados. GitHub es exclusivamente una fuente de consulta; las entregas se realizan mediante ZIP.

## Trabajo anterior a la entrega de 2026-11-13 (fecha exacta no determinada)

Fuentes: `README.md`, `docs/validaciones/GEOMETRY_VALIDATION.md`, `docs/validaciones/ARCFIX_VALIDATION.md`, `docs/validaciones/COMPONENT_OUTLINES.md`, código y pruebas recibidos en el ZIP original.

- Se implementó importación GenCAD 1.4 desde archivos CAD y normalización al modelo interno PV.
- Se creó PVF 1.0 (18 bloques en el convertidor actual), con contenido semántico JSON UTF-8 comprimido mediante Zstandard, metadatos, hashes y CRC.
- Se incorporó interfaz Tkinter para el convertidor, inspección de PV y generación de SVG.
- Se preservaron tokens de transformación de cara inferior; el espejado de previsualización es provisional, no una transformación certificada del origen.
- Se corrigió la interpretación de rectángulos y el sentido SVG de arcos; los criterios y comprobaciones de arcos constan en `docs/validaciones/ARCFIX_VALIDATION.md`.
- Se incorporó diagnóstico no destructivo de integridad y continuidad en `VALD`, con advertencias para geometría incierta.
- Se documentaron limitaciones: unidades físicas no resueltas, contorno mecánico no inequívoco, arcos ambiguos y límites de semántica de capas/vías.
- Se integraron pruebas automatizadas en GitHub Actions (solo lectura desde aquí).

Los documentos originales siguen siendo el registro técnico detallado de esa fase. Las acciones anteriores se reconstruyen de esos documentos y **no son cambios hechos por esta entrega**.

## 2026-11-13 — Auditoría y entrega local 001

- Se incorporaron dos auditorías anteriores a `auditorias/` y un diagnóstico JSON de rutas de la placa incluida.
- Se añadieron límites defensivos al lector `read_pvf` para tamaño de archivo, número de bloques, tamaño por bloque y tamaño total declarado descomprimido.
- Se limitó la salida de la ruta de descompresión mediante CLI `zstd` para impedir acumulación sin límites en memoria; se rechaza salida mayor a lo declarado.
- Se mantuvo sin modificación el formato PVF 1.0 **en disco** y el código de escritura/conversión de geometría.
- Se añadieron siete pruebas del lector defensivo y dos pruebas de diagnóstico de adyacencia.
- Se creó `route_audit.py` como herramienta independiente de solo lectura para clasificar rutas con saltos entre primitivas consecutivas; no comprueba conectividad eléctrica.
- Se actualizó documentación y CI para ejecutar las nuevas pruebas.
- Los comandos y resultados exactos de la entrega se detallan en `auditorias/2026-11-13_entrega_001.md`.

## Reglas para futuras entregas

Cada ZIP deberá conservar: fecha e identificador de entrega, ficheros creados/modificados, motivo, evidencias y comandos de pruebas, resultados, limitaciones, compatibilidad y asuntos pendientes. No modificar GitHub directamente. No se aplicarán reparaciones geométricas inferidas sin justificación verificada.
