# Procedencia del dibujo BOARD y contorno de placa

El bloque `$BOARD` del GenCAD de referencia contiene 204 grupos `ARTWORK`. No hay instrucciones `RECTANGLE` en esos grupos: las figuras rectangulares visibles en la vista son cadenas de líneas.

El diagnóstico `artwork_audit.py` guarda para cada grupo su identificador, capa, nombre, tipos de primitiva y caja de coordenadas. También comprueba si las líneas forman un único ciclo cerrado. La comprobación no determina si ese ciclo representa la periferia física de la placa: 152 de los grupos de referencia forman ciclos cerrados y la mayoría pueden representar otras entidades.

```sh
python artwork_audit.py "generated/MS-7B79 r1.0.pv" --output auditorias/2026-11-13_artwork_referencia.json
python pv_geometry.py "generated/MS-7B79 r1.0.pv" --svg "generated/MS-7B79 r1.0_artwork.svg" --html "generated/MS-7B79 r1.0_artwork.html" --components
```

La vista HTML incorpora **Arte individual**. Al seleccionar un grupo, atenúa los demás grupos de dibujo y mantiene visibles las pistas y los componentes. Los elementos contienen `data-artwork` y un título con el nombre y la capa de origen; las coordenadas no se han cambiado. Los controles generales de capa y tipo siguen funcionando.

Para investigar una figura sospechosa, seleccionar el grupo que la dibuja, consultar su ID en `auditorias/2026-11-13_artwork_referencia.json` y buscar el nombre `ARTWORK artworkNN` en la sección `$BOARD` del `.cad`. El origen puede quedar demostrado incluso sin un visor CAD de terceros.

## Limitaciones y próximos pasos

- Una cadena cerrada no acredita un borde mecánico ni permite decidir si el elemento debe ocultarse.
- No se ha identificado todavía un contorno físico completo con procedencia verificada.
- Este análisis no corrige rotaciones, espejado, arcos ni desplazamientos aparentes de componentes.
- El diagnóstico de arcos mantiene su tratamiento conservador cuando la dirección de barrido no consta explícitamente.

No se ha cambiado el contenido del `.pv` ni su versión PVF 1.0.
