# Análisis preliminar de archivos Switch OLED HEG-CPU-01

Fecha: 2026-11-13  
Estado: **solo lectura; no se ha implementado ningún convertidor PCB**.

## Inventario

| Archivo | Tamaño (bytes) | Contenido confirmado |
| --- | ---: | --- |
| `Switch OLED-HEG-CPU-01 PCB layer.pcb` | 1.610.148 | Formato XZZPCB, identificado mediante la firma de cabecera desofuscada por XOR. |
| `Switch OLED-HEG-CPU-01 PCB layer.obdata` | 27.200 | Archivo de texto `OBDATA_V002`, 1.039 registros de metadatos de componentes y 453 registros de metadatos de redes. |
| `Switch OLED-HEG-CPU-01 PCB layer.conf` | 437 | Ajustes para imagen frontal/trasera, escala, espejado, desplazamiento y transparencia; referencia a un PDF. |
| `Switch OLED-HEG-CPU-01 PCB layer.conf~` | 437 | Copia idéntica, byte a byte, del `.conf`. |
| `Switch OLED-HEG-CPU-01 PCB layer_pcb.sqlite3` | 12.288 | Base SQLite con tabla `annotations` y 2 anotaciones de usuario. |

## Identificación del PCB

Los primeros seis bytes del PCB son `74 76 76 7c 6f 6e`, que no forman una firma ASCII legible. El byte en offset `0x10` es `0x2c`. Al aplicar XOR `0x2c` a esos seis bytes se obtiene `XZZPCB`. Esto coincide con la detección implementada en `XZZPCBFile::verifyFormat` de OpenBoardView.

Fuente de referencia: https://github.com/OpenBoardView/OpenBoardView/blob/master/src/openboardview/FileFormats/XZZPCBFile.cpp

Ese analizador describe bloques de arcos, vías, segmentos, texto, partes/pines, taladros y capas; no todos los bloques están interpretados exhaustivamente por OpenBoardView. Esto **no confirma todavía** cuáles de ellos están presentes en este archivo ni su integridad tras descifrarlo.

## Datos auxiliares y límites

- `.obdata` contiene metadatos de componentes (por ejemplo tipo/encapsulado) y mediciones o notas de redes; no sustituye al `.pcb` como fuente de geometría.
- `.conf` apunta al archivo `Switch OLED-HEG-CPU-01 PCB layer.pdf`, que **no forma parte de los archivos recibidos**. Sus transformaciones de superposición deben preservarse como metadatos separados; no deberían aplicarse automáticamente a las coordenadas de placa.
- `.conf~` parece una copia de respaldo idéntica; basta preservar el archivo original y señalar esta duplicidad en el inventario.
- SQLite incluye anotaciones sobre `N65106` con referencias de pin/red y notas. Debe preservarse el texto original y su vínculo con los identificadores de origen.
- Los 1.039 componentes y 453 redes del `.obdata` son registros de anotación, **no** el inventario completo demostrado del tablero. No inferir totales del `.pcb` a partir de ellos.

## Viabilidad y trabajo requerido

**Viabilidad: favorable, con complejidad media-alta.** XZZPCB es un formato conocido y hay código de lectura disponible como referencia. Sin embargo, para una conversión fiel se requiere:

1. Un lector XZZPCB autónomo con identificación robusta, manejo del cifrado y límites de recursos.
2. Decodificar e inventariar todos los bloques del archivo real, incluyendo los desconocidos, sin descartarlos.
3. Mapear geometría, capas, componentes, pines y redes a un modelo PV común, conservando referencias y valores originales.
4. Asociar metadatos `.obdata`, ajustes `.conf`, y anotaciones SQLite sin confundirlos con datos CAD nativos.
5. Mantener dentro del `.pv` una copia íntegra de las fuentes o bloques originales para garantizar preservación incluso si algún campo aún no se interpreta.
6. Verificar el resultado con OpenBoardView y pruebas independientes, sin suponer que un modelo 3D, pistas completas o un borde mecánico exacto están siempre disponibles.

No se ha realizado conversión, desofuscación completa, descifrado ni modificación de ninguno de los archivos proporcionados.

## Decisión

No incorporar todavía XZZPCB al convertidor GenCAD congelado. Cuando se autorice esta fase, implementar un importador independiente y mantener el formato PVF versionado y compatible.
