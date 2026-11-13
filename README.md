# PV Converter — beta 0.001.0010 (PVF 1.0)

Aplicación de escritorio para importar GenCAD 1.4, construir el modelo PV Core y generar archivos `.pv`. Incluye lector PVF, validación de integridad y exportación de vista geométrica SVG.

**Versión del proyecto:** `0.001.0010` (beta). La versión del contenedor PVF (`1.0`) es independiente.

[Wiki y documentación](docs/README.md) · [Historial de versiones](CHANGELOG.md) · [Auditorías](auditorias/README.md)

## Guía rápida

- **Qué hace:** convierte archivos GenCAD 1.4 a `.pv`, comprueba su integridad y permite exportar SVG de diagnóstico.
- **Cómo empezar:** consulta [Uso de la aplicación](#uso-de-la-aplicación) y [Requisitos para ejecutar desde Python](#requisitos-para-ejecutar-desde-python).
- **Cómo crear el EXE:** consulta [Crear el ejecutable Windows](#crear-el-ejecutable-windows) y la [guía completa de compilación](docs/desarrollo/COMPILAR_WINDOWS.md).
- **Qué está pendiente:** consulta [Estado y límites conocidos](#estado-y-límites-conocidos), [Estado actual](docs/wiki/ESTADO_ACTUAL.md) y [Futuros importadores](docs/wiki/FORMATOS_FUTUROS.md).
- **Registro de desarrollo:** [CHANGELOG](CHANGELOG.md) y [auditorías](auditorias/README.md).


## Contenido

- `pv_converter_gui.py`: interfaz de escritorio Windows (Tkinter, incluido con Python).
- `gencad_parser.py`: importador GenCAD 1.4.
- `build_pv.py`: normalización del modelo y creación de bloques PVF.
- `pvf.py`: contenedor binario, directorio, Zstandard y CRC32.
- `pv_geometry.py`: lector de alto nivel, validación de relaciones y vista SVG.
- `route_audit.py`: diferencias entre primitivas consecutivas de una ruta.
- `connectivity_audit.py`: agrupación geométrica de extremos por ruta y capa, sin suponer continuidad eléctrica.
- `contact_audit.py`: candidatos de contacto entre extremos de pistas y vías, y comprobación de referencias pin-red.
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

**Resumen:** en Windows 10/11 de 64 bits instala Python 3.12 x64, extrae esta distribución, abre la carpeta raíz del proyecto y ejecuta `build_windows.bat`. El script instala las dependencias en `.venv-build`, ejecuta las pruebas y genera el paquete portable. La primera compilación necesita Internet. No basta con copiar el `.exe` aislado: distribuye la carpeta completa o su ZIP.


La distribución portable se compila **en Windows** mediante `build_windows.bat`. Utiliza un entorno aislado `.venv-build`, instala PyInstaller y las dependencias, ejecuta las pruebas unitarias y de arcos, compila y crea un ZIP de la carpeta de distribución. No incluye los archivos CAD o PV de referencia en el ejecutable.

**Guía completa:** [Compilar y verificar en Windows](docs/desarrollo/COMPILAR_WINDOWS.md).

El fichero final será `dist/PV_Converter_0.001.0010_Windows_x64.zip`. El empaquetado no sustituye una prueba manual en Windows: comprueba la interfaz, una conversión real, la validación y la exportación SVG antes de distribuir.

## Pruebas

Ejecuta las pruebas unitarias y sintéticas:

```bat
py -3.12 -m unittest -v test_gencad_parser test_pv_validation test_pvf_security test_route_audit test_connectivity_audit test_contact_audit
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

GitHub Actions tiene configurada esta batería al actualizar `main`. Para generar un informe geométrico de contactos entre extremos:

```bat
py -3.12 connectivity_audit.py "generated/MS-7B79 r1.0.pv" --output auditorias/resultado_local.json
```

El diagnóstico **no demuestra continuidad eléctrica**: excluye contactos interiores, pads, puentes entre capas por vías y cruces de rutas distintas. [Método y límites](docs/validaciones/CONECTIVIDAD.md).

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
`docs/validaciones/ARCFIX_VALIDATION.md` for the reference-board validation counts and diagnostics.


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

## Registro del proyecto y auditorías

La documentación técnica se organiza desde `docs/README.md`. Las notas antiguas se mantienen en su idioma original y las auditorías previas no se reescriben.

- `docs/historia/HISTORIAL.md`: cronología del trabajo **documentado** y entregas posteriores; distingue hechos históricos de nuevas decisiones.
- `docs/wiki/ARQUITECTURA_OBJETIVO.md`: objetivos futuros (visor web, 3D, fotografías, trazado y múltiples importadores) **sin afirmar que estén implementados**.
- `docs/formato/PVF_COMPATIBILIDAD.md`: notas actuales de compatibilidad, seguridad y límites del prototipo PVF 1.0.
- `auditorias/`: informes, resultados reproducibles y pendientes.

### Endurecimiento del lector (2026-11-13)

`read_pvf()` rechaza por defecto archivos de más de 512 MiB, más de 256 bloques,
bloques comprimidos o descomprimidos de más de 128 MiB y sumas de tamaños
descomprimidos declarados superiores a 512 MiB. Son límites preventivos,
no una nueva versión del formato; el escritor y los datos convertidos no cambian.
Para modificar estas políticas consulte `pvf.py`. `verify_source` permanece
por compatibilidad histórica, pero **no** verifica el CAD original: la comparación
de SHA-256 del bloque fuente se realiza en `geometry_report()`.

### Auditoría no destructiva de secuencia de rutas

```bash
python route_audit.py "generated/MS-7B79 r1.0.pv" --output auditorias/rutas_actual.json
```

El informe cuenta saltos entre pares **consecutivos** de primitivas en una ruta,
incluidas transiciones con vías; por ello puede diferir del recuento de
`disconnected_pairs` de `VALD`, que excluye las transiciones con vías.
No determina continuidad eléctrica, ni introduce correcciones o conexiones.

Para generar el informe de contactos pista-vía sobre un PV existente:

```bat
py -3.12 contact_audit.py "generated/MS-7B79 r1.0.pv" --output "auditorias/contactos_locales.json"
```

No se deducen cortes eléctricos a partir de los contactos que faltan. Véase [validación de contactos](docs/validaciones/CONTACTOS_VIAS.md).

### Vista diagnóstica con capas independientes

```sh
python pv_geometry.py "generated/MS-7B79 r1.0.pv" --svg "generated/MS-7B79 r1.0_layers.svg" --html "generated/MS-7B79 r1.0_layers.html" --components
```

Abre el HTML resultante directamente en el navegador. La lista de capas no está limitada a TOP/BOTTOM; consulta [la documentación](docs/validaciones/CAPAS_Y_PREVISUALIZACION.md) para las advertencias sobre el contorno y las capas físicas.

### Navegación de las vistas HTML de diagnóstico

En `generated/MS-7B79 r1.0_artwork.html` y `generated/MS-7B79 r1.0_layers.html`, usa la rueda sobre la placa para ampliar o reducir, mantén el clic derecho para desplazarte y pulsa **Restablecer vista** para volver al encuadre inicial. Los filtros de capa y de tipo de elemento siguen siendo independientes. Consulta [el inventario de serigrafía y elementos mecánicos](docs/validaciones/NAVEGACION_Y_FUENTE.md) antes de interpretar las figuras como contornos físicos.

### Comprobación de las transformaciones

```bash
python component_transform.py "generated/MS-7B79 r1.0.pv" --output auditorias/transformaciones.json
python -m unittest -v test_component_transform
```

Este diagnóstico utiliza la convención del SVG actual; no demuestra la orientación física de la cara inferior. Los registros fuente se conservan sin cambios.

### Comparar GenCAD con el PVF resultante

```bash
python gencad_roundtrip_audit.py "MS-7B79 r1.0.cad" "generated/MS-7B79 r1.0.pv"
```

Comprueba preservación de datos, no la geometría visual de un CAD independiente.

## Ampliación futura de formatos

El importador actual admite **GenCAD 1.4**. Se ha estudiado un conjunto de archivos de Nintendo Switch OLED cuyo `.pcb` corresponde al formato **XZZPCB**; sus acompañantes `.obdata`, `.conf` y `.sqlite3` contienen información auxiliar. **XZZPCB todavía no se puede convertir con esta versión.**

El análisis, el inventario de archivos y las precauciones para una eventual integración están en [Formatos futuros](docs/wiki/FORMATOS_FUTUROS.md) y [la auditoría preliminar XZZPCB](auditorias/2026-11-13_analisis_preliminar_xzzpcb.md). No se han incorporado los archivos originales de esa placa a esta distribución.

El proyecto permanece en fase beta. El visor web profesional, las vistas 2D/3D, la superposición de fotografías y el soporte para placas multicapa son líneas de desarrollo futuras, no funciones incluidas en el ejecutable actual.
