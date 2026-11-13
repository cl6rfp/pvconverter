# Entrega 003 — Contactos de extremos

**Fecha:** 2026-11-13  
**Versión:** beta `0.001.0001`  
**Base:** entrega 002 (`0.001.0000`)

## Contexto

El informe anterior detectaba saltos entre elementos consecutivos de una ruta. Dado que el orden fuente puede intercalar ramificaciones y vías, ese recuento no bastaba para diferenciar cambios de tramo de contactos geométricos.

## Cambios

- `connectivity_audit.py`: agrupación por contactos de extremos, con tolerancia y separación estricta por capa y ruta; salida JSON y CLI.
- `test_connectivity_audit.py`: diez pruebas para ramificaciones fuera de orden, tolerancia, cruce interior, separación entre capas, vía no interpretada, entrada inválida, rangos y ausencia de modificaciones de origen.
- `docs/validaciones/CONECTIVIDAD.md`: método, límites de interpretación y ejecución.
- `auditorias/2026-11-13_contactos_extremos.json`: resultado sobre el archivo de prueba recibido.
- `README.md`, `docs/README.md`, `docs/wiki/ESTADO_ACTUAL.md`, `CHANGELOG.md`, `VERSION` y flujo CI: instrucciones, estado y registro de la entrega.

El contenedor PVF, el importador GenCAD y la serialización no se modificaron.

## Resultado en la placa de referencia

Archivo analizado: `generated/MS-7B79 r1.0.pv`, procedente del ZIP de la entrega 002. Tolerancia `0.0001` en unidades fuente.

| Medida | Valor |
|---|---:|
| Rutas examinadas | 1.997 |
| Segmentos LINE/ARC examinados | 94.146 |
| Uniones de grupos por extremos coincidentes | 86.614 |
| Grupos geométricos resultantes | 7.532 |
| Rutas con más de un grupo de segmentos | 1.263 |
| Vías presentes y no usadas como puentes | 7.149 |

Un grupo es una componente geométrica limitada a **extremos, una ruta y una capa**. Es normal que varios grupos de un mismo registro terminen conectándose mediante vías, contactos a mitad de segmento o pads. Por eso no se interpreta el número 1.263 como rutas abiertas. Tampoco son equivalentes estas medidas a los saltos del informe de adyacencia previo.

Tres rutas del origen contienen cero primitivas y un inicio cero; se aceptan como vacías, sin atribuirles datos corruptos.

## Pruebas realizadas

En Linux con Python 3.13:

- `python -m unittest -v test_gencad_parser test_pv_validation test_pvf_security test_route_audit test_connectivity_audit`: **46 pruebas, OK**.
- `python test_arc_direction.py`: **OK**, también la prueba de extremos de arco.
- `python test_pvf.py "generated/MS-7B79 r1.0.pv"`: **OK**, integridad y referencias.
- `python test_geometry.py "generated/MS-7B79 r1.0.pv"`: **OK**, con generación del SVG.
- `python -m compileall -q .`: **OK**.
- Ejecución de `connectivity_audit.py` sobre la placa real: **OK**.

Estas pruebas no equivalen a validación cruzada en Windows ni demuestran el estado físico de ninguna red.

## Pendientes

1. Distinguir conexiones sobre extremos de otras en el interior de un segmento, sin modificar el original.
2. Resolver alcance de vía y padstack con base en la especificación y casos de prueba, antes de permitir saltos de capa.
3. Analizar la relación entre `NETS` (asignación lógica) y contacto de cobre, conservando su procedencia.
4. Repetir pruebas en Windows/Python 3.12 y con otros CAD cuando se disponga de ellos.
