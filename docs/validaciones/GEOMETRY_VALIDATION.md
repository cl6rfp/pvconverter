# MS-7B79 – validación geométrica del prototipo

Fuente única analizada: `MS-7B79 r1.0.cad` (GenCAD 1.4). No se utilizó el JSON intermedio.

## Resultados comprobados

- 2.693 componentes, 112 shapes, 11.104 pines instanciados.
- 347 pads, 228 padstacks, 1.997 redes y 10.595 nodos.
- 66.709 líneas + 27.437 arcos + 7.149 vías.
- 101.295 primitivas de ruta en total.
- 1.174 líneas y 114 arcos en 204 grupos de artwork de `$BOARD`.
- 7 agujeros mecánicos.
- 353 definiciones de TRACK; los 24 identificadores utilizados por las rutas tienen definición. No hay referencias de TRACK ausentes.
- Las 243 instancias de componente de cara BOTTOM llevan los tokens de transformación `MIRRORY FLIP`; ahora se conservan explícitamente en `COMP`.
- 97 padstacks contienen dos entradas `INNER` (194 entradas en total). Se asignan IDs internos `INNER_1` y `INNER_2` por orden de aparición, manteniendo `source_layer: INNER` y el orden original.
- Se preserva el orden intercalado de LINE/ARC/VIA de cada ROUTE en los bloques `PRIM` y `ROUT`.
- Se conservan los extremos y centros de los 27.729 arcos presentes en rutas, pads y artwork. También se guardan ambos candidatos de barrido y el error de radios.
- El error máximo entre radios de inicio y fin medido en arcos de ruta y artwork es aproximadamente 0,00192 unidades fuente.
- 2.297 arcos (2.205 de rutas y 92 de artwork) tienen extremos diametralmente opuestos: el archivo no permite escoger inequívocamente entre los dos barridos semicirculares usando solo esos tres puntos.
- 3 ROUTE están vacíos; se conservan como rutas sin primitivas.
- 509 pines instanciados no aparecen en `$SIGNALS`; se conservan sin asignación de red.

## Límites que siguen abiertos

- `UNITS USER 1000` se conserva literalmente. La unidad física no se convierte a mm porque no se ha demostrado su escala solo con este archivo.
- Los tokens `MIRRORY FLIP` se conservan literalmente. La regla geométrica exacta de aplicación todavía no se da por cerrada.
- La dirección de barrido de los arcos no se inventa. Se guardan ambos candidatos.
- `$BOARD` contiene grupos `ARTWORK`, pero no identifica inequívocamente cuál es el perímetro mecánico de la PCB. No se declara ningún grupo como contorno exterior sin evidencia.
- Las cuatro capas de cobre se representan como TOP, INNER_1, INNER_2 y BOTTOM a partir de la declaración de cuatro capas y del orden repetido de INNER en padstacks. Los nombres originales se conservan.

## Resultado de la prueba del archivo PV

`test_pvf.py` valida recuentos, CRC/lectura de bloques, SHA-256 de la fuente embebida, orden de primitivas, referencias TRACK, capas internas, tokens de transformación y geometría de arcos.

Resultado local: `ALL TESTS PASSED`.

El contenido semántico de los bloques sigue serializado como JSON UTF-8 antes de compresión Zstandard. Este prototipo valida el modelo y el contenedor; todavía no es el formato binario compacto definitivo ni un visor geométrico terminado.

## Segunda fase: lector y vista geométrica

Se añadió `pv_geometry.py`, que vuelve a leer el contenedor, comprueba las referencias de las primitivas de cada ruta y verifica el SHA-256 de la fuente embebida. También genera una vista SVG diagnóstica por capas. La prueba `test_geometry.py` genera un SVG y comprueba sus dimensiones mínimas.

La dirección de barrido no está especificada en el origen para los 27.729 arcos. Para dibujar la vista previa se selecciona provisionalmente el candidato CCW; esto es exclusivamente una decisión de representación visual, no una corrección del dato ni una afirmación sobre la geometría definitiva. Hay 2.475 arcos semicirculares contando rutas, pads y artwork; el subconjunto de rutas y artwork puede diferir del recuento histórico al incluir los pads.

La interfaz inicial `pv_converter_gui.py` permite convertir CAD a PV, abrir y validar PV, y exportar una vista SVG. Usa Tkinter para evitar una dependencia GUI externa. `build_windows.bat` prepara un ejecutable Windows mediante PyInstaller.
