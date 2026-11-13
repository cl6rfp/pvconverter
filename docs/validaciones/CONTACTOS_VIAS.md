# Candidatos de contacto entre pistas y vías

## Alcance

`contact_audit.py` inspecciona el modelo PVF sin editarlo. Por cada ruta (`ROUT`) construye un índice espacial de extremos de segmentos (`SEGS`) y busca vías (`VIAS`) cuya posición coincida dentro de la tolerancia. Solo considera capas enumeradas en el padstack (`PSTK`) de esa vía.

Las vías se revisan dentro de su propia ruta. El programa **no** une redes diferentes, ni supone que dos capas estén conectadas internamente porque figuren en un padstack. La coincidencia se llama *candidato geométrico*: no prueba conectividad eléctrica.

Se comprueba además que los `pin_id` de las conexiones declaradas en `NETS` existan en `PINS`, y que las rutas hagan referencia a una red conocida. Son comprobaciones de referencias, independientes de las coordenadas.

## Uso

```sh
python contact_audit.py "generated/MS-7B79 r1.0.pv" --tolerance 0.0001 --top 20 --output auditorias/contactos_locales.json
```

La tolerancia está expresada en unidades del archivo origen, cuya conversión a unidades físicas continúa sin confirmar. `--top` limita los ejemplos conservados en el informe, no los totales. El reporte JSON no modifica los bloques PVF.

## Lo que falta comprobar

- Contactos en mitad de una pista, ramificaciones en T y cruces geométricos.
- Semántica del tramo conductor de una vía, metalización y alcance real entre capas.
- Contornos de cobre de pads; relación entre capa, giro y espejado de componentes.
- Contactos entre rutas distintas que pertenezcan a la misma red.

Un extremo de pista que no coincide con una vía no se considera un circuito abierto. Los pines de los componentes aparecen en el modelo con coordenadas locales; aún no se hace una comparación física pista-pad porque el espejado inferior y algunas transformaciones siguen bajo investigación.

## Datos de referencia

El informe `auditorias/2026-11-13_contactos_vias.json` procede del PV de referencia y se reprodujo tras convertir de nuevo el CAD original: 7.149 vías examinadas, 5.148 con candidatos de extremo, 2.001 sin coincidencia de extremo y 2.704 con candidatos en más de una capa. Los 10.595 enlaces pin-red registrados son referencias existentes en el modelo, no uniones geométricas verificadas.
