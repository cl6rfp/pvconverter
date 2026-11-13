# Versionado del proyecto

Formato: **`0.000.0000`**, siempre con tres bloques, ceros a la izquierda y puntos. Ejemplo: `0.001.0000`.

- **Primer bloque (`0`)**: etapa del producto. Se mantiene en `0` durante toda la beta; la transición a `1.000.0000` indica la primera versión estable y exige una decisión expresa. No se toma por defecto.
- **Segundo bloque (`000`)**: cambios importantes dentro de la beta: arquitectura, organización general, capacidad o comportamiento que merece una revisión significativa. Al incrementarse, el último bloque vuelve a `0000`.
- **Tercer bloque (`0000`)**: cambios menores, correcciones localizadas, documentación puntual y ajustes compatibles.

Así se distinguen **cambios menores**, **cambios grandes dentro de beta** y el **hito importante de pasar a versión estable**. Si fuera necesario diferenciar cambios incompatibles durante beta, se marcarán expresamente en el changelog y se elevará el segundo bloque; no se publicará una versión estable por accidente.

## Reglas de entrega

1. Actualizar `VERSION`, `README.md` (si cambia la versión visible) y `CHANGELOG.md`.
2. Añadir auditoría de la entrega con alcance, ficheros, pruebas ejecutadas, resultados y límites.
3. Conservar fuentes y datos anteriores, salvo limpieza acordada.
4. Entregar un ZIP completo; GitHub es de solo lectura y el usuario decide qué publicar.
5. No atribuir una fecha, prueba, autor o resultado que no pueda comprobarse.

## Versiones diferentes

La versión del **producto** (`0.001.0000`) no cambia la versión del **contenedor de archivos** (`PVF 1.0`). Un ajuste de documentación no obliga a migrar archivos `.pv`.
