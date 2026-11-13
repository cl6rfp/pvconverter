# Formatos e importadores futuros

**Estado:** planificación. La beta `0.001.0010` únicamente importa GenCAD 1.4; ninguna parte de este documento implica que XZZPCB ya funcione.

## XZZPCB — Nintendo Switch OLED HEG-CPU-01

El primer conjunto examinado consta de un `.pcb` XZZPCB como archivo principal y cuatro auxiliares: `.obdata` (metadatos de componentes/redes), `.conf` (ajustes de imágenes), `.conf~` (respaldo idéntico) y una base `.sqlite3` (anotaciones). El archivo PDF mencionado en la configuración no se recibió.

**Viabilidad preliminar:** favorable; complejidad media-alta. El código de OpenBoardView ofrece un punto de referencia, pero todavía no se han decodificado todos los bloques del archivo ni validado su geometría.

## Criterio de incorporación

1. Implementar cada formato mediante un importador independiente, sin alterar el comportamiento probado de GenCAD.
2. Inventariar todos los bloques y preservar la fuente y los datos auxiliares, incluso cuando no se interpreten por completo.
3. Diferenciar geometría nativa de anotaciones y configuración de superposición.
4. Conservar nombres y orden de capas y sus significados sin asumir que todas las placas son de dos caras o dos capas eléctricas.
5. Verificar coordenadas, componentes, pads, vías y redes con muestras adicionales y, cuando sea posible, herramientas independientes.
6. Versionar de forma explícita cualquier ampliación del contenedor `.pv` y mantener lectura compatible cuando corresponda.

No se ha realizado implementación ni conversión XZZPCB. Antes de comenzar habrá que contar con autorización específica y acordar los casos de prueba.

[Inventario y análisis de los archivos recibidos](../../auditorias/2026-11-13_analisis_preliminar_xzzpcb.md).
