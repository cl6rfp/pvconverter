# Conservación del origen GenCAD

El objetivo de esta comprobación es saber si el convertidor pierde información al generar un PVF. No verifica cómo debe verse una placa en un programa CAD.

## Ejecución

```bash
python build_pv.py "MS-7B79 r1.0.cad" "generated/MS-7B79 r1.0.pv" --strict-source
python gencad_roundtrip_audit.py "MS-7B79 r1.0.cad" "generated/MS-7B79 r1.0.pv" --output auditorias/comparacion_gencad.json
```

La auditoría compara el SHA-256 del fichero de entrada, la copia completa almacenada en `SRCE`, las cantidades de registros y varios campos de origen en `COMP`, `HOLE`, `PRIM`, `SEGS`, `VIAS` y `ARTW`. No convierte unidades ni aplica espejados. Las discrepancias detienen el proceso con un código de error.

La prueba no es independiente del parser: tanto el `.pv` como parte de la comparación usan `gencad_parser.py`. Si ese parser interpretase mal una instrucción, ambos podrían compartir el mismo defecto. El escaneo `cad_coverage_audit.py` ayuda a identificar las instrucciones no reconocidas, pero no resuelve ambigüedades de significado.

## Dos caras y varias capas

El ejemplo de OpenBoardView entregado como referencia visual muestra dos caras de una placa, una junto a la otra. Esa disposición es útil para el visor, pero no determina el sentido físico de `MIRRORY` en GenCAD. El convertidor conserva los tokens y las coordenadas tal como aparecen en la fuente. En el visor deberán distinguirse tres conceptos: capa física, orientación de cámara y transformación local de huella.

La vista web definitiva deberá poder presentar TOP y BOTTOM por separado o juntos y, en archivos multicapa, activar cada capa individualmente. Mantener la orientación del lado BOTTOM como parámetro visual evita alterar los datos originales.

## Lo que falta para certificar el importador

- Contrastar la semántica de rotación, `FLIP` y `MIRRORY` con una especificación o un ejemplo CAD verificado.
- Identificar, si existe, una entidad mecánica que represente con certeza el borde físico de la placa.
- Obtener más muestras GenCAD para cubrir otras variantes de instrucciones, capas y geometría.
- Validar unidades físicas y dirección de arcos cuya fuente no indica explícitamente el recorrido.

Estos puntos no impiden generar un `.pv` válido de la placa de referencia, pero sí impiden declarar fidelidad universal.
