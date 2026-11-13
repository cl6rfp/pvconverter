# Estado del proyecto

**Versión:** 0.001.0010 (beta). **Formato de salida actual:** PVF 1.0.

## Disponible

- Importación GenCAD 1.4 con el archivo CAD de referencia recibido.
- Normalización, creación y lectura de archivos `.pv` con validación de integridad.
- Herramienta Tkinter, exportación SVG y diagnósticos de geometría/rutas.
- Pruebas unitarias, scripts de comprobación y auditorías históricas.
- Auditoría geométrica por extremos de segmentos, separada de la adyacencia del orden fuente.
- Diagnóstico de coincidencias entre extremos de pista y posiciones de vías en capas declaradas por padstack, más comprobación de referencias pin-red.

## Límites abiertos

- Confirmar unidades físicas, espejado de cara inferior y contorno mecánico real.
- Distinguir conectividad eléctrica verdadera de adyacencia geométrica en los informes de rutas.
- Definir un modelo neutral y política de evolución del formato para otros importadores y clientes web.
- Verificación independiente en Windows/Python 3.12 y con muestras adicionales.

## Objetivos posteriores (no implementados)

Visor web 2D interactivo, seguimiento de redes, fotos superpuestas, ayudas para técnicos, vista 3D y aplicaciones para Windows/Linux. Otros formatos de boardview/PCB solo cuando existan ejemplos reales. Véase [arquitectura objetivo](ARQUITECTURA_OBJETIVO.md).

## Próximo trabajo técnico

Revisar contactos interiores de segmentos y reglas de transición de vías; después, validar transformaciones de pines/pads con casos de referencia. Los diagnósticos actuales no establecen conectividad eléctrica.

## Vista por capas (0.001.0003)

La exportación diagnóstica ofrece una página HTML local con visibilidad por capa y tipo de objeto. No sustituye al visor web definitivo. Véase [capas y previsualización](../validaciones/CAPAS_Y_PREVISUALIZACION.md).

## Diagnóstico BOARD (0.001.0004)

La vista HTML permite identificar y aislar grupos de arte. El borde físico de la placa todavía no está verificado. Véase [arte y contorno](../validaciones/ARTWORK_Y_CONTORNO.md).

## Navegación e inventario (0.001.0005)

Las vistas HTML incluyen zoom con rueda y arrastre con botón derecho. El CAD contiene siete taladros `$MECH`; no se ha identificado una capa explícita de serigrafía ni el contorno físico. Véase [navegación e inventario](../validaciones/NAVEGACION_Y_FUENTE.md).

## Cobertura del CAD (0.001.0006)

El importador puede inventariar instrucciones de origen y rechazar conversiones con instrucciones desconocidas mediante `--strict-source`. La muestra actual no contiene instrucciones desconocidas, pero todavía hay semánticas parciales y transformaciones sin verificar. Véase [cobertura GenCAD](../validaciones/COBERTURA_GENCAD.md).

## Transformaciones y encuadre (0.001.0007)

La auditoría de coordenadas de pads es reproducible y el SVG encuadra sus envolventes transformadas. La interpretación de espejo aún necesita una referencia externa. Véase [transformaciones](../validaciones/TRANSFORMACIONES.md).

## Rendimiento del futuro visor

El HTML diagnóstico actual presenta lentitud al navegar. Para el visor definitivo se evaluará WebGL/WebGPU con geometría agrupada y selección por capas, con posibilidad de vistas 2D/3D. La vista 3D no se considera una optimización por sí misma.

## Comparación contra el CAD (0.001.0008)

Se contrasta la conservación de registros de origen, incluido el orden de las rutas, con `gencad_roundtrip_audit.py`. En la muestra de referencia se verificaron 768.221 campos sin diferencias. Quedan pendientes la interpretación visual del espejo y la validación con más placas. Véase [integridad GenCAD](../validaciones/INTEGRIDAD_GENCAD.md).

## Pausa de desarrollo GenCAD y formatos futuros

El importador GenCAD queda en beta funcional para la muestra de referencia, pendiente de validar el ejecutable en Windows y de probar otros archivos de origen. Esta versión incorpora una evaluación documental del formato XZZPCB como posible siguiente importador, sin añadir código de conversión ni soporte operativo para `.pcb`. Véase [formatos futuros](FORMATOS_FUTUROS.md).
