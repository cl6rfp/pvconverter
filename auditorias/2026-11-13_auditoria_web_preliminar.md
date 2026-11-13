# Auditoría técnica preliminar — PV Converter
Fecha: 2026-11-13
Origen (solo lectura): https://github.com/cl6rfp/pvconverter
Rama observada: main

## Alcance y limitación
Revisión estática de documentación y código visible mediante GitHub web. La descarga/clonación del repositorio en el entorno de pruebas falló por resolución DNS. No se ejecutaron pruebas ni se reprodujo la conversión de la placa. Esto NO es una certificación de comportamiento, seguridad ni exactitud geométrica. No se modificó ningún archivo del proyecto ni se escribió en GitHub.

## Arquitectura observada
- `gencad_parser.py`: lectura GenCAD 1.4.
- `build_pv.py`: construcción de modelo normalizado y validaciones.
- `pvf.py`: contenedor PVF 1.0, directorio, bloques JSON UTF-8 comprimidos con Zstandard y CRC32.
- `pv_geometry.py`: lectura geométrica y exportación SVG.
- `pv_converter_gui.py`: interfaz Tkinter.
- `pvf_inspect.py`: inspección.
- Pruebas: `test_gencad_parser.py`, `test_pv_validation.py`, `test_pvf.py`, `test_geometry.py`, `test_arc_direction.py`.
- `requirements.txt`: zstandard==0.25.0.

## Hallazgos
### A1 — Alta — Descompresión sin límites de aplicación independientes
El archivo PVF declara el tamaño sin comprimir (`usize`) que se utiliza como `max_output_size` en el camino Python. No se observa en `read_pvf` un techo definido por la aplicación para `usize`, número de bloques o total descomprimido; la alternativa CLI `zstd` captura toda la salida. Añadir límites y probar archivos manipulados antes de abrir ficheros de terceros. No se ha demostrado explotación.
Fuente: https://github.com/cl6rfp/pvconverter/blob/main/pvf.py

### A2 — Media — Parámetro `verify_source` sin uso visible
`read_pvf(path, verify_source=True)` declara un argumento que no se consulta en el cuerpo de la función, según la versión visible. Documentar/eliminar el parámetro o implementar la semántica prometida tras determinar su intención. Distinguir CRC de bloques de verificación contra CAD original.
Fuente: https://github.com/cl6rfp/pvconverter/blob/main/pvf.py

### A3 — Alta — Formato semántico aún provisional
PVF 1.0 encapsula JSON comprimido, no el diseño compacto definitivo. Antes del PV Viewer de cliente conviene publicar una especificación de bloques, referencias, orden, schema_version, reglas para bloques opcionales/desconocidos y política de compatibilidad.
Fuentes: README.md, pvf.py.

### A4 — Alta — Geometría parcialmente ambigua por origen
Escala USER 1000, MIRRORY FLIP, arcos y verdadero borde mecánico tienen incertidumbres documentadas; no inferir transformaciones ni contornos como hechos. La documentación informa 1.962 arcos de ruta con fallback visual ambiguo y 243 componentes BOTTOM con tokens de transformación.
Fuentes: GEOMETRY_VALIDATION.md, ARCFIX_VALIDATION.md, COMPONENT_OUTLINES.md.

### A5 — Media — Cobertura y portabilidad pendientes de verificación
Hay casos sintéticos, pruebas unitarias y fixture GenCAD real, además de documentación de CI. Falta ejecutar el conjunto en un checkout completo, revisar workflow y medir en Windows 10/11 + Python 3.12 + ejecutable PyInstaller. Una única placa de referencia no demuestra compatibilidad universal con GenCAD 1.4.
Fuente: README.md, archivos test_*.py.

### A6 — Media — Conservación de la procedencia
Verificar que el campo fuente SHA-256 se usa consistentemente, distinguir hash de bytes CAD incorporados del hash de un archivo externo y documentar cuándo se comprueba; la función de lectura baja no necesariamente garantiza esa semántica.
Fuente: pvf.py, README.md.

## Aspectos positivos observados
- Separación razonable entre importador, normalizador, contenedor, geometría y GUI.
- CRC de cabecera y bloques; comprobaciones estructurales de directorio y solapamientos.
- Escritura mediante archivo temporal y reemplazo atómico al completar.
- Preservación del orden de primitivas y registros originales frente a datos dudosos.
- Documentación de las decisiones geométricas y pruebas sintéticas de dirección de arcos.
- Dependencia Zstandard fijada en requirements.

## Secuencia propuesta
1. Obtener ZIP del repositorio tal como está ahora, o checkout local completo.
2. Registrar SHA-256 y snapshot, comprobar imports y sintaxis, ejecutar unittest y scripts integrales; comparar resultados con los markdown.
3. Probar lector PVF con archivos corruptos, truncados, contadores extremos y payloads desproporcionados; registrar memoria y tiempo.
4. Comparar CAD→PV→SVG y resultados de la placa base; incluir nuevos CAD independientes si existen.
5. Definir y congelar contrato PVF para el viewer: esquema, versionado y tratamiento explícito de ambigüedades.
6. Emitir auditoría final con evidencias, severidad, reproducciones, cambios propuestos separados y ninguna edición automática.

## Fuentes consultadas
https://github.com/cl6rfp/pvconverter
https://github.com/cl6rfp/pvconverter/blob/main/README.md
https://github.com/cl6rfp/pvconverter/blob/main/GEOMETRY_VALIDATION.md
https://github.com/cl6rfp/pvconverter/blob/main/ARCFIX_VALIDATION.md
https://github.com/cl6rfp/pvconverter/blob/main/COMPONENT_OUTLINES.md
https://github.com/cl6rfp/pvconverter/blob/main/pvf.py
https://github.com/cl6rfp/pvconverter/blob/main/gencad_parser.py
https://github.com/cl6rfp/pvconverter/blob/main/build_pv.py
https://github.com/cl6rfp/pvconverter/blob/main/pv_geometry.py
