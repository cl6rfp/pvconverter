# PVF 1.0: contrato observado y restricciones del lector

Documento técnico provisional basado en `pvf.py`, no una especificación formal definitiva. El formato de disco **no se ha cambiado** en entrega 001.

- Cabecera `HEADER` little-endian, identificador `PVF\\0`, versión principal 1, integridad CRC32 de cabecera.
- Directorio `DIRENT` con IDs ASCII de 4 caracteres, offsets, tamaños, recuentos, CRC32 del contenido descomprimido, método de compresión y versión de esquema.
- Cada carga actual es JSON UTF-8; normalmente comprimida con Zstandard. No es todavía el modelo binario compacto final.
- Lectura: revisiones de tamaños físicos, directorio, unicidad, solapamiento, compresión, tamaño resultante, CRC y decodificación JSON.
- Límites del lector: 512 MiB por archivo; máximo 256 bloques; 128 MiB por bloque comprimido o descomprimido; máximo 512 MiB de suma declarada descomprimida. Estos son valores de **política de aplicación** configurables en `pvf.py`, no campos nuevos de PVF.
- El SHA-256 del origen CAD puede contrastarse al procesar SRCE/META en `pv_geometry.geometry_report()`. El parámetro histórico `read_pvf(..., verify_source=True)` **no** verifica el origen; queda reservado para compatibilidad de llamadas.

## Pendiente antes del visor externo

- Contrato formal por bloque y por `schema_version`.
- Decisión para bloques opcionales/desconocidos y campos obligatorios.
- Estrategia de migración de versiones, ficheros grandes y carga incremental en navegador.
- Pruebas de robustez/fuzzing, implementación web y comparación entre lectores.
