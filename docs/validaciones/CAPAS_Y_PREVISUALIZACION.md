# Capas y vista de diagnóstico

El SVG es una vista técnica, no un archivo de fabricación ni un sustituto del CAD original.

## Capas de la placa de referencia

La cabecera de `MS-7B79 r1.0.cad` declara cuatro capas de enrutamiento (`Number of Routing Layers: 4`). El bloque `LAYR` del PV incluye `TOP`, `INNER_1`, `INNER_2` y `BOTTOM`, además de máscaras y pasta. Las pistas incluidas en el bloque `SEGS` solo hacen referencia a `TOP` (53.669 segmentos) y `BOTTOM` (40.477 segmentos). Por tanto, no puede afirmarse a partir de este archivo que la placa física sea de dos capas ni que contenga cobre interno recuperable.

El archivo PV mantiene la lista de capas declaradas y la asignación de las geometrías. No se colapsan las internas en TOP o BOTTOM. Si un futuro archivo aporta más capas, podrán mantenerse sus nombres sin un límite fijo en el filtro del exportador.

## Archivos de vista

```sh
python pv_geometry.py "generated/MS-7B79 r1.0.pv" --svg "generated/MS-7B79 r1.0_layers.svg" --html "generated/MS-7B79 r1.0_layers.html" --components
```

La página HTML funciona localmente en un navegador moderno. Permite ocultar cada capa con geometría por separado y también los conjuntos de pistas, arte gráfico, componentes, etiquetas, vías y taladros. No cambia el `.pv` ni su geometría; el SVG conserva grupos `data-layer` y `data-kind` para facilitar la inspección.

Se han reforzado los colores y el grosor del arte gráfico. Las vías permanecen en un grupo independiente; no se asignan a una capa única sin evaluar su padstack. Estas mejoras de contraste no corrigen errores de posición o rotación.

## Borde de placa

El CAD de referencia no proporciona un borde mecánico explícito y verificado en los datos convertidos. Por eso **no** dibujamos una silueta física basada en una caja o envolvente de las pistas: sería engañosa. Reconstruir el borde requiere identificar su geometría en el archivo fuente o incorporar una referencia fiable.

## Pendiente

- Identificar si hay un perfil recuperable en secciones GenCAD aún no interpretadas.
- Mostrar el orden de apilado físico solo cuando sea conocido; el orden de una tabla no demuestra el espesor ni las conexiones.
- Revisar el posicionamiento de componentes y el espejado frente a evidencia geométrica, sin desplazar objetos a ojo.
- Integrar la gestión de capas en el futuro visor web, con control de orden, transparencia y modo de capas aisladas.
