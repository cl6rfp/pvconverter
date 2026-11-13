# Registro de cambios

Versiones del proyecto, no del archivo PVF. Las entregas anteriores se registran con la información verificable que tenemos; no se asignan versiones retrospectivas sin evidencia.

## [0.001.0010] — 2026-11-13 · Documentación de cierre provisional y formatos futuros

**Tipo:** documentación y mantenimiento del empaquetado; sin cambios en conversión GenCAD ni en PVF 1.0.

- Se mantuvo el README de raíz como presentación general y guía de uso, incorporando acceso directo a la compilación del ejecutable en Windows.
- Se incorporó la auditoría del conjunto XZZPCB/OBDATA/CONF/SQLite como referencia de un posible segundo importador. No se ha implementado ni convertido XZZPCB.
- Se actualizó el índice de wiki, el estado beta, la versión del paquete portable y las instrucciones de Windows.
- La generación y ejecución del `.exe` en un equipo Windows siguen pendientes de comprobación.

## [0.001.0009] — 2026-11-13 · Preparación de distribución Windows

**Tipo:** mejora de empaquetado y documentación; el convertidor, el formato PVF 1.0 y las transformaciones de GenCAD permanecen sin cambios.

- Se sustituyó el script de compilación por un proceso reproducible con Python 3.12 x64 y entorno de compilación `.venv-build` independiente.
- Se fijó la versión de PyInstaller y se añadió `scripts/package_windows.py` para empaquetar el directorio `onedir` sin archivos CAD/PV de referencia.
- El proceso ejecuta la batería unitaria antes de compilar y valida la integridad del ZIP resultante.
- Se documentó el procedimiento de instalación, ejecución, pruebas de aceptación, avisos de SmartScreen y límites de compatibilidad.
- La compilación nativa y el funcionamiento del `.exe` en Windows quedan **pendientes de comprobación** en el equipo de destino.

## [0.001.0008] — 2026-11-13 · Verificación de conservación GenCAD

**Tipo:** validación adicional del convertidor; archivo PVF 1.0 sin cambios.

- Se incorporó `gencad_roundtrip_audit.py` para contrastar el CAD original con los registros convertidos. Comprueba hashes, copia de origen incrustada, cantidades, componentes, posiciones, tokens de huella, taladros, geometría de arte y orden/coordenadas originales de pistas y vías.
- El CAD de referencia supera 768.221 comparaciones de campos sin discrepancias, utilizando el `.pv` generado por el proyecto. Esta verificación demuestra preservación de campos, **no certifica** la interpretación de `MIRRORY`, el borde mecánico ni la dirección real de arcos ambiguos.
- Se añadieron pruebas unitarias y una ejecución de esta auditoría al flujo CI tras convertir el CAD.
- El visor futuro contemplará vistas TOP/BOTTOM independientes, además de la superposición; el espejado visual no altera las coordenadas de origen.
- Detalles en `docs/validaciones/INTEGRIDAD_GENCAD.md` y `auditorias/2026-11-13_entrega_010_integridad.md`.

## [0.001.0007] — 2026-11-13 · Encuadre de pads y auditoría de transformaciones

**Tipo:** corrección de previsualización y validación adicional de GenCAD. PVF 1.0 sin cambios.

- El encuadre SVG incluye ahora la envolvente de los pads después de aplicar rotación de pin, rotación de padstack, espejo y rotación del componente. Antes solo incluía los centros de los pines.
- `component_transform.py` contiene la transformación de referencia utilizada por el diagnóstico y genera un informe de pines, tokens de huella y límites aproximados.
- Cinco pruebas nuevas cubren rotación, traslación, espejo y pads rotados.
- La convención visual aplicada a `MIRRORY` **no está certificada** mediante un visor CAD independiente. No se han alterado las coordenadas almacenadas en PVF ni el parser.
- Se vuelve a convertir el CAD de referencia y se regeneran las vistas HTML/SVG.
- Registro y limitaciones: `docs/validaciones/TRANSFORMACIONES.md` y `auditorias/2026-11-13_entrega_009_transformaciones.md`.

## [0.001.0006] — 2026-11-13 · Comprobación de cobertura GenCAD

**Tipo:** control de calidad del importador, sin cambios en la geometría ni en PVF 1.0.

- Nuevo inventario de instrucciones del CAD por sección, con registros desconocidos, incompletos y parcialmente interpretados.
- `build_pv.py --strict-source` permite detener la conversión ante instrucciones desconocidas o incompletas; el modo habitual sigue igual.
- Se incorporaron seis pruebas unitarias y un informe JSON de la muestra de referencia.
- La auditoría da 0 instrucciones desconocidas, 0 registros cortos y 482 registros parcialmente interpretados. No certifica precisión visual.
- Detalles: `docs/validaciones/COBERTURA_GENCAD.md` y `auditorias/2026-11-13_entrega_008_cobertura_cad.md`.

## [0.001.0005] — 2026-11-13 · Navegación del HTML e inventario de la fuente

**Tipo:** mejora menor de visualización y diagnóstico; PVF 1.0 sin cambios.

- La vista HTML permite zoom con rueda alrededor del puntero y desplazamiento manteniendo el clic derecho; se añadió un botón para restablecer el encuadre.
- Se regeneraron las vistas HTML de capas y arte a partir del PVF de referencia.
- Nuevo `source_features_audit.py`: inventario de grupos de arte, taladros mecánicos, capas y transformaciones. No se atribuye serigrafía ni contorno físico sin respaldo en el CAD.
- Se documentaron las pruebas, los límites de interpretación y las siguientes comprobaciones de espejado.

## [0.001.0004] — 2026-11-13 · Trazabilidad de arte y contornos

**Tipo:** mejora menor de diagnóstico; sin cambios en PVF 1.0.

- Se añadió `artwork_audit.py` para inventariar los grupos `$BOARD`, sus coordenadas y cadenas cerradas.
- Cada grupo `ARTWORK` conserva su identidad en el SVG; la vista HTML permite aislarlo visualmente.
- Se incorporaron cuatro pruebas unitarias y los registros en `docs/validaciones/ARTWORK_Y_CONTORNO.md` y `auditorias/2026-11-13_entrega_006_artwork.md`.
- No se declara un contorno físico ni se suprimen elementos de procedencia incierta.

## [0.001.0003] — 2026-11-13 · Vista de capas y contraste

**Tipo:** mejora menor de presentación y diagnóstico; PVF 1.0 sin cambios.

- El SVG agrupa por capa las pistas y el arte gráfico, además de etiquetar los elementos por tipo.
- Nueva exportación HTML autónoma con controles de visibilidad para capas y elementos técnicos.
- Mejor contraste en pistas y arte gráfico; las coordenadas del archivo original permanecen intactas.
- `geometry_report()` diferencia las capas declaradas de las que contienen segmentos de ruta.
- Se conserva la ausencia de contorno mecánico verificado: no se fabrica un borde mediante una envolvente aproximada.
- Tres pruebas unitarias y documentación en `docs/validaciones/CAPAS_Y_PREVISUALIZACION.md`.

**Comprobación:** pruebas automatizadas y lectura de la nueva vista SVG como XML. No se ha validado visualmente contra una aplicación CAD original.

## [0.001.0002] — 2026-11-13 · Candidatos de contacto pista-vía

**Tipo:** ampliación menor compatible; sin cambios de formato ni de geometría.

- Nuevo `contact_audit.py`: busca extremos de pista cercanos a vías de la misma ruta, respetando las capas presentes en su padstack. El resultado es un conjunto de candidatos, no un grafo eléctrico.
- Comprobación independiente de referencias `NETS` → `PINS` y `ROUT` → `NETS`; sin aplicar transformaciones físicas todavía no verificadas.
- Ocho pruebas sintéticas adicionales; la batería total pasa 54 pruebas.
- Informe reproducible de la placa de referencia y documentación de límites en `docs/validaciones/CONTACTOS_VIAS.md` y `auditorias/2026-11-13_entrega_004_contactos.md`.

**Compatibilidad:** PVF 1.0 sin cambios. Los datos fuente y el convertidor permanecen intactos.

## [0.001.0001] — 2026-11-13 · Diagnóstico de extremos de rutas

**Tipo:** ampliación menor de herramientas de análisis; sin cambios en el formato PVF.

- Se añadió `connectivity_audit.py` para agrupar segmentos que comparten extremos dentro de una misma ruta y capa, incluso cuando aparecen separados en el orden fuente.
- El nuevo informe identifica referencias inválidas, geometría incompleta y grupos geométricos aislados. No modifica coordenadas ni interpreta estos grupos como fallos eléctricos.
- Se incorporaron diez pruebas sintéticas y la nueva batería al flujo de validación.
- Se documentaron método, casos excluidos y resultados sobre la placa de referencia en `docs/validaciones/CONECTIVIDAD.md` y `auditorias/2026-11-13_entrega_003_conectividad.md`.

**Compatibilidad:** archivos `.pv` existentes y PVF 1.0 sin cambios. El diagnóstico es una herramienta externa opcional.

## [0.001.0000] — 2026-11-13 · Wiki y versionado beta

**Tipo:** cambio significativo de organización, sin modificaciones funcionales.

### Cambios
- Se reorganizaron los documentos Markdown en `docs/`, separando arquitectura, formato, validaciones, historial y desarrollo.
- Se creó el índice navegable de la wiki y una guía para mantenerla.
- Se estableció el esquema de versiones `0.000.0000`, con archivo `VERSION`.
- Se incorporó este registro de cambios y un informe específico en `auditorias/`.
- Se actualizaron los enlaces internos del README y el historial.

### Compatibilidad y comprobación
- Sin cambios en el convertidor, el lector, las pruebas o el formato PVF 1.0.
- La versión de aplicación y la versión de formato PVF son independientes.
- Los informes antiguos se conservan sin alterar; las referencias a rutas originales dentro de ellos son históricas.

## Antes del versionado actual — 2026-11-13 · Entrega local 001

- Protección adicional frente a archivos PVF de tamaño excesivo.
- Herramienta no destructiva para diagnóstico de adyacencia de rutas.
- Pruebas adicionales y primer registro acumulativo de auditorías y decisiones.
- Detalle y resultados: [`auditorias/2026-11-13_entrega_001.md`](auditorias/2026-11-13_entrega_001.md).

## Historial anterior (fecha exacta no determinada)

Los hitos del prototipo y las correcciones geométricas previas están recogidos en [`docs/historia/HISTORIAL.md`](docs/historia/HISTORIAL.md) y en las validaciones originales. No se han inventado números de versión para ellos.
