# Entrega 004 — contactos pista-vía

**Versión:** 0.001.0002 (beta)  
**Fecha:** 2026-11-13  
**Origen:** copia local de la entrega 003; repositorio remoto sin modificar.

## Cambios

- `contact_audit.py`: herramienta de inspección no destructiva.
- `test_contact_audit.py`: ocho casos de prueba, incluidos filtros por capa, coincidencia exacta y tolerancia, geometría interior excluida, referencias inválidas y no mutación.
- Actualizados `VERSION`, `README.md`, `CHANGELOG.md`, índice de wiki, estado del proyecto y CI.
- Creada la especificación de alcance en `docs/validaciones/CONTACTOS_VIAS.md`.
- Guardado `2026-11-13_contactos_vias.json` con los resultados completos del conjunto de referencia.

## Pruebas y resultados

- 54 pruebas unitarias: **OK**.
- Pruebas sintéticas de dirección de arcos: **OK**.
- Prueba geométrica con fixture histórico: **OK**.
- Conversión de `MS-7B79 r1.0.cad` a un nuevo PVF, seguida de pruebas PVF y geométricas: **OK**.
- Repetición del análisis sobre el archivo recién convertido: totales **idénticos** al PV preexistente en `generated/`.

| Métrica | Resultado |
| --- | ---: |
| Rutas inspeccionadas | 1.997 |
| Vías inspeccionadas | 7.149 |
| Vías con contacto candidato en extremos | 5.148 |
| Vías sin contacto candidato en extremos | 2.001 |
| Vías con candidatos en más de una capa | 2.704 |
| Coincidencias de segmento/capa | 9.074 |
| Enlaces pin-red declarados | 10.595 |

Estas métricas no describen averías de la placa. No se cambian los datos de origen ni se reconstruyen conexiones eléctricas.

## Pendiente

Validación de contactos interiores, transiciones entre capas y transformaciones de pads/pines. Repetir la batería en Windows con Python 3.12.
