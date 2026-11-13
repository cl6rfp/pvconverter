# Visión objetivo: convertidor y visor técnico profesional

**Documento de planificación**, no descripción de capacidades implementadas. Confirmado por el usuario el 2026-11-13.

## Separación de responsabilidades

1. **Importadores**: un adaptador por formato fuente. Hoy: GenCAD/PCAD según los archivos disponibles. Más adelante: otros boardview y PCB según muestras reales y documentación legal/técnica.
2. **Modelo intermedio neutral**: componentes, pines, pads, capas, redes, trazados, unidades, transformaciones, metadatos de origen y grados de confianza. Debe conservar hechos observados y marcar incertidumbre.
3. **Validación y serialización**: chequeos de referencias, geometría y procedencia; PVF versionado y compatibilidad entre productos.
4. **Visor web**: inicialmente navegador, con procesamiento local de archivos cuando resulte viable; interfaces adaptables a aplicación de escritorio posterior en Windows/Linux y otros sistemas (por ejemplo, empaquetado web).

## Funciones objetivo, aún no implementadas

- Visor 2D interactivo con capas, redes, mediciones y búsqueda de componentes/pines.
- Seguimiento de pistas y conexiones con diferenciación visible entre **confirmado por fuente**, **inferido** y **desconocido**.
- Fotografías de placa y capas de imágenes con calibración, puntos de control, transparencia y alineación por cara.
- Visualización 3D; diferenciar cuerpos reales con alturas verificadas de extrusiones ilustrativas o estimaciones.
- Herramientas para técnicos: localización, resaltado de señales, correspondencia entre vistas, anotaciones y ayudas de diagnóstico.
- Arquitectura extensible a múltiples formatos, sin integrar toda la lógica en `gencad_parser.py`.

## Condiciones previas

- Verificar escala física y convención de transformaciones, particularmente `MIRRORY FLIP`.
- Definir contrato de geometría y conectividad que no confunda secuencia de primitivas con conexiones eléctricas verdaderas.
- Formalizar versionado de bloques PVF y límites de lectura antes del visor de acceso público.
- Obtener archivos PCB u otros formatos reales del usuario cuando llegue esa fase; por ahora trabajar solo con la muestra aportada.

## Orden de trabajo

Seguridad e integridad del convertidor → investigación de ambigüedades → especificación neutral → visor web 2D → herramientas avanzadas y fotos → 3D → empaquetado de escritorio y expansión de importadores. El orden es provisional y sujeto a resultados comprobados.
