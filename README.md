# PV Converter – PVF 1.0 (prototipo funcional)

Aplicación de escritorio para importar GenCAD 1.4, construir el modelo PV Core y generar archivos `.pv`. Incluye lector PVF, validación de integridad y exportación de vista geométrica SVG.

## Contenido

- `pv_converter_gui.py`: interfaz de escritorio Windows (Tkinter, incluido con Python).
- `gencad_parser.py`: importador GenCAD 1.4.
- `build_pv.py`: normalización del modelo y creación de bloques PVF.
- `pvf.py`: contenedor binario, directorio, Zstandard y CRC32.
- `pv_geometry.py`: lector de alto nivel, validación de relaciones y vista SVG.
- `test_pvf.py`: integridad del contenedor y recuentos del modelo.
- `test_geometry.py`: comprobaciones geométricas y generación de SVG.
- `test_arc_direction.py`: pruebas sintéticas de sentido de arco, incluido el recorrido inverso.
- `MS-7B79 r1.0.cad`: CAD de referencia usado para las pruebas.
- `MS-7B79_test.pv`: archivo PV de prueba generado.

## Requisitos para ejecutar desde Python

Windows 10/11, Python 3.12 de 64 bits y Zstandard:

```bat
py -3.12 -m pip install -r requirements.txt
py -3.12 pv_converter_gui.py
```

La aplicación también puede iniciarse con `C:\PV_Converter\.venv\Scripts\python.exe pv_converter_gui.py` si ese entorno tiene instalado `zstandard`.

## Crear el ejecutable Windows

Ejecuta `build_windows.bat`. PyInstaller generará `dist\PV_Converter\PV_Converter.exe`. Se distribuye la carpeta completa `PV_Converter`, no solo el EXE, porque contiene las bibliotecas necesarias.

## Pruebas

Ejecuta las pruebas unitarias y sintéticas:

```bat
py -3.12 -m unittest -v test_gencad_parser test_pv_validation
py -3.12 test_arc_direction.py
```

El archivo `MS-7B79_test.pv` es un fixture histórico anterior al bloque `VALD`;
se utiliza para comprobar la geometría, no para las comprobaciones PVF actuales:

```bat
py -3.12 test_geometry.py "MS-7B79_test.pv"
```

Para validar el contenedor y la conversión actual, genera un PV nuevo desde el CAD
de referencia y ejecuta las dos comprobaciones sobre ese archivo:

```bat
py -3.12 build_pv.py "MS-7B79 r1.0.cad" "generated/MS-7B79 r1.0_ci.pv"
py -3.12 test_pvf.py "generated/MS-7B79 r1.0_ci.pv"
py -3.12 test_geometry.py "generated/MS-7B79 r1.0_ci.pv"
```

GitHub Actions ejecuta automáticamente esta batería al actualizar `main`.

## Uso de la aplicación

1. **Importar CAD y convertir a PV**: selecciona el CAD y dónde guardar el `.pv`.
2. **Abrir archivo PV y validar**: comprueba la lectura, los bloques y las relaciones de rutas.
3. **Exportar vista geométrica SVG**: permite visualizar todas las capas o una capa concreta; el SVG se abre en el navegador.

## Estado y límites conocidos

- Las conversiones actuales generan 18 bloques PVF, incluido `VALD` para diagnósticos de integridad. Las cargas semánticas siguen serializadas como JSON UTF-8 comprimido con Zstandard dentro de un contenedor binario; todavía no es la codificación compacta definitiva.
- La auditoría numérica bloquea valores no finitos en componentes, pines, padstacks, geometrías de pads y ARTWORK; exige dimensiones positivas en círculos/rectángulos y permite perforación cero en padstacks sin taladro.
- Las coordenadas conservan las unidades fuente `USER 1000`; no se convierten a milímetros porque la escala física no está demostrada.
- Los tokens `MIRRORY FLIP` se conservan sin aplicar una transformación geométrica no verificada.
- Los registros GenCAD no contienen un token explícito que indique el sentido de los arcos. El exportador SVG evalúa el sentido de recorrido de la ruta en ambas orientaciones (inicio→final y final→inicio) y utiliza la continuidad tangencial de los segmentos vecinos cuando existe evidencia suficiente. La selección es solo para visualización y no modifica los datos del archivo `.pv`. Los casos ambiguos se identifican y usan un arco menor como alternativa diagnóstica.
- El perímetro mecánico de la placa no se declara automáticamente porque `$BOARD` contiene grupos ARTWORK sin identificar inequívocamente el contorno exterior.
- Esta herramienta es el **PV Converter**. El **PV Viewer** para clientes será otro programa independiente y no se incluye en este paquete.

## Geometry preview update

The SVG exporter reconstructs component footprints by following the PV references:
component -> shape pins -> padstack -> pad geometry. It renders copper pad outlines/fills,
drill apertures, pin numbers and component references, and includes footprint pin positions
in the SVG bounds. The source `MIRRORY FLIP` token is used for a provisional display-side
reflection only; the original tokens remain preserved in PV. Mechanical board outline is
not fabricated from artwork: the current GenCAD input does not explicitly identify which
artwork groups form the true board perimeter, so all source artwork remains displayed as-is.

For the reference board, the preview was rendered with 2,693 component footprints.
PV integrity and geometry tests passed.

## Rectangular pad geometry correction

The SVG renderer treats GenCAD `RECTANGLE x y width height` coordinates as the rectangle
origin plus dimensions, rather than treating x/y as its center. This removes the erroneous
half-width/half-height offset that displaced rectangular footprint pads. Both artwork
rectangles and pad rectangles use the same convention. The source coordinates in PVF are
unchanged.

## Arc direction correction (ARCFIX3)

The route-arc resolver evaluates both stored endpoint orientations and both possible arc
sweeps. It uses tangent continuity with adjacent route lines to infer the display direction,
including routes that traverse an arc from its stored end to its stored start. If continuity
does not provide enough evidence, the preview uses a clearly reported minor-arc fallback.
The PV source data remains unchanged.

The included synthetic tests cover forward and reverse route traversal. See
`ARCFIX_VALIDATION.md` for the reference-board validation counts and diagnostics.


## SVG arc sweep correction (ARCFIX4)

The SVG preview reflects the board's Y axis with `scale(1,-1)`. SVG's native
sweep flag therefore has to be inverted when mapping the GenCAD arc direction:
positive GenCAD counter-clockwise sweeps use SVG `sweep=1`, and clockwise
sweeps use `sweep=0`. The previous mapping selected the opposite side of the
chord and could make otherwise correctly resolved curves appear reversed.
This is a display-only correction; source PV coordinates and arc records are
not modified. The synthetic arc-direction test now checks the actual sweep-flag
mapping as well as forward and reverse route traversal.

## GenCAD -> PV integrity diagnostics

The PV validation block includes source-preserving integrity diagnostics for route
primitive ordering and references, adjacent endpoint continuity, via transitions,
layer changes, arc/line transitions, duplicate route geometry, and numeric geometry
prerequisites. Findings are categorized as blocking errors, warnings, informational
items, or ambiguous source data. Route gaps and uncertain via/layer/transform meaning
are reported without automatically connecting, moving, or otherwise repairing records.
Endpoint comparisons use a default tolerance of `0.0001` source coordinate units.
The diagnostic issue list is capped at 20 examples; category counts and route totals
remain available in the `VALD` block and PV validation report.
