# Entrega 010 — 0.001.0008

**Fecha:** 2026-11-13

## Objetivo

Comprobar que la conversión de la placa GenCAD de referencia conserva sus registros y no modifica coordenadas por motivos de presentación. Separar las decisiones futuras del visor de las reglas del importador.

## Cambios

- Nuevo `gencad_roundtrip_audit.py` con comprobación de campos fuente → PVF y código de salida distinto de cero ante diferencias.
- Dos pruebas unitarias del auditor: conversión coherente y detección de posición alterada.
- Actualización de CI, wiki y changelog.
- Ninguna transformación nueva en el importador. Ningún cambio al contrato PVF 1.0.

## Resultado de referencia

El informe `2026-11-13_gencad_integridad_fuente.json` recoge 768.221 comprobaciones sin diferencias sobre el `.pv` existente. Conviene volver a generarlo en cada entorno antes de repetir la auditoría; CI lo hace a partir del CAD original.

## Limitaciones

Este ensayo comprueba fidelidad de registros, no correspondencia visual con un programa CAD externo. El usuario mostró una vista de OpenBoardView con TOP y BOTTOM separadas, ejemplo útil para el diseño del futuro visor, pero no una verificación del espejo de esta placa GenCAD. Se mantienen como pendientes la geometría mecánica definitiva, la semántica de espejado y las muestras adicionales.
