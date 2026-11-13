# Auditoría técnica del ZIP pvconverter-main
Fecha: 2026-11-13
Ámbito: copia local recibida del usuario; **ninguna modificación en GitHub**. Se evaluó el convertidor actual, no se diseñó ni implementó un visor.

## Resumen ejecutivo

El convertidor está funcional para la placa de referencia GenCAD/PCAD incluida. La generación del PVF 1.0 y sus pruebas de contenedor y geometría terminan satisfactoriamente. Sin embargo, existen importantes ambigüedades y advertencias de conectividad de rutas en los datos, y la representación no debe tratarse como una reconstrucción eléctrica/mecánica completamente verificada. La arquitectura futura debe prever formatos de entrada intercambiables y una representación neutral apta para web, 3D y superposición de imágenes.

## Evidencia y pruebas ejecutadas

Entorno de prueba: Python 3.13 en Linux (el README y CI indican Python 3.12). Contenido original descomprimido sin alterar archivos fuente.

- `python -m unittest -v test_gencad_parser test_pv_validation`: 27/27 OK.
- `python test_arc_direction.py`: OK.
- `python test_geometry.py "MS-7B79_test.pv"`: OK; fixture histórico de 17 bloques.
- `python build_pv.py "MS-7B79 r1.0.cad" <ruta temporal>`: OK, PVF de 6.047.124 bytes y 18 bloques.
- `python test_pvf.py <PV temporal>`: OK; integridad del contenedor, referencias y hashes.
- `python test_geometry.py <PV temporal>`: OK; generó SVG.
- `python -m unittest discover -v`: no debe tomarse como criterio de fallo del programa; los scripts `test_pvf.py` y `test_geometry.py` interpretan el argumento `discover` como ruta de un PV, por tener comportamiento al importarse. Deben migrarse a `if __name__ == '__main__'` o separarse los tests ejecutables.

## Estadísticas reproducidas

- 2.693 componentes; 11.104 pines; 1.997 redes y rutas.
- 94.146 segmentos; 7.149 vías; 101.295 primitivas de ruta.
- 27.729 arcos (incluyendo artwork); 27.437 arcos de ruta sin dirección explícita.
- La validación de integridad informa `blocking_errors=0`, `warnings=15034`, `informational=97`, `ambiguous=632`; estado `review_required`.
- 7.177 pares de primitivas desconectados según la tolerancia usada (`0.0001` unidades fuente), 574 geometrías de ruta duplicadas, 3 rutas vacías y 7.149 vías sin contexto de capas en el diagnóstico; estos conteos requieren interpretación del formato de origen, no equivalen automáticamente a defectos del convertidor.
- El hash SHA-256 del origen almacenado en el PV coincide según la validación.

## Hallazgos por prioridad

### Alta: contrato de datos e interpretación eléctrica

1. No dar por confirmado el seguimiento de pistas basándose solo en el orden de primitivas: el diagnóstico identifica 7.177 desconexiones y 15.034 advertencias. Validar la semántica de rutas y vías con más archivos reales antes de introducir herramientas de trazado eléctrico.
2. Fijar una especificación del modelo interno PV y campos opcionales: unidades, ejes, cara, capas, redes, incertidumbre/diagnóstico, IDs persistentes y versiones. Mantener los originales sin inventar geometría.
3. El formato actual PVF 1.0 usa bloques de JSON UTF-8 comprimido con Zstandard. Es correcto como prototipo, pero se debe definir compatibilidad y política de versiones antes de un visor público.
4. Limitar explícitamente bloques, tamaños comprimidos/descomprimidos y memoria usada al abrir PVF de terceros. `read_pvf` confía en tamaños del encabezado y la ruta externa `zstd` captura el resultado entero.

### Media: arquitectura, calidad y mantenimiento

5. `read_pvf(path, verify_source=True)` recibe `verify_source` pero no lo usa en su implementación. Definir su comportamiento o retirar el parámetro.
6. `test_geometry.py` y `test_pvf.py` ejecutan código al importarse, por lo que `unittest discover` falla aunque la batería documentada pasa. Convertirlos en pruebas convencionales y mantener validación end-to-end separada.
7. CI está configurado y reproduce la batería documentada en Python 3.12. Esta auditoría se ejecutó en 3.13, por lo que conviene revalidarla también en versión objetivo y Windows.
8. La dependencia `zstandard==0.25.0` está fijada; registrar versión del compilador/ejecutable y añadir pruebas de lectura defensiva/corrupción.
9. La interfaz es Tkinter para Windows. Para el futuro visor web se recomienda reutilizar el modelo/contrato, no intentar transportar la GUI actual al navegador.

### Geometría y funciones futuras

10. Arcos: se preservan candidatos sin imponer sentido cuando la fuente es ambigua. Es una estrategia correcta; cualquier reconstrucción visual debe informar su grado de certeza.
11. Las coordenadas preservan `USER 1000` sin afirmar conversión a mm. No es seguro usar medición física o modelos 3D dimensionales hasta verificar escala.
12. El contorno mecánico no está identificado inequívocamente en `$BOARD`, y `MIRRORY FLIP` se aplica provisionalmente solo a la previsualización. Evitar tomar esas inferencias como geometría mecánica certificada.
13. Para fotos superpuestas, diseñar más adelante un registro de imágenes con transformaciones calibrables, puntos de control y referencia de cara/capa; almacenar imágenes como recursos opcionales, no como sustituto del CAD.
14. Para 3D, diferenciar extrusión/estimación de componentes frente a modelos mecánicos reales. No hay evidencias suficientes en este conjunto para reconstruir alturas y cuerpos reales con precisión.
15. Para varios formatos, una capa de importadores (`GenCAD`, luego otros) debe producir un modelo neutral, validarse y serializarse a PVF. No expandir el parser existente a formatos ajenos.

## Plan recomendado

Fase 1: cerrar auditoría semántica de rutas y escala en archivos fuente reales; categorizar advertencias y decidir cuáles importan al usuario final.

Fase 2: escribir una especificación neutral y versionada del formato PV Core/PVF, más pruebas de compatibilidad y límites de seguridad del lector.

Fase 3: separar importación, normalización, validación y empaquetado sin romper los resultados ya validados.

Fase 4 (futura): visor web 2D con búsqueda de componentes, capas y redes; fotos calibradas y trazado; luego 3D según calidad de los datos; al final empaquetado multiplataforma y nuevos importadores.

## Límites de esta auditoría

No se comprobaron otros CAD reales ni un programa de referencia independiente para comparar los píxeles del render. No se probó el empaquetado Windows ni se realizó fuzzing o pentesting. El éxito de pruebas no demuestra fidelidad total de geometría, semántica eléctrica o ausencia de vulnerabilidades. No se modificó ningún archivo del repositorio; solo se crearon artefactos temporales en el área de auditoría.
