# Cobertura del importador GenCAD

El archivo `cad_coverage_audit.py` recorre las instrucciones originales y distingue tres situaciones: instrucciones desconocidas, registros con menos campos de los necesarios y registros conservados cuya semántica solo se interpreta parcialmente. No modifica el archivo de entrada.

```bash
python cad_coverage_audit.py "MS-7B79 r1.0.cad" --output auditorias/cobertura.json
python build_pv.py "MS-7B79 r1.0.cad" salida.pv --strict-source
```

La segunda orden detiene la conversión si encuentra instrucciones desconocidas o registros estructuralmente incompletos. Sin `--strict-source` se conserva el comportamiento anterior. El análisis no equivale a validar todos los valores numéricos ni a verificar la geometría contra el programa CAD original.

## Resultados de referencia (13/11/2026)

- Instrucciones desconocidas: **0**.
- Registros con menos campos de los previstos: **0**.
- Registros parcialmente interpretados: **482**. Incluyen 408 entradas `PART`, 67 `INSERT` y 7 registros de cabecera/atributos que requieren interpretación contextual. Sus líneas originales siguen dentro de la fuente que se incluye en PVF.

Los resultados completos están en `auditorias/2026-11-13_cobertura_gencad.json`. Las secciones `$ARTWORKS`, `$TESTPINS` y `$POWERPINS` están vacías en esta muestra; eso no demuestra su compatibilidad con futuros archivos que sí las utilicen.

## Pendiente antes de cerrar GenCAD

1. Comparar la geometría de componentes de la cara inferior contra una referencia independiente; no corregir `MIRRORY` ni `FLIP` a ciegas.
2. Verificar unidades reales, origen y dimensiones con una medida externa de la placa.
3. Identificar el contorno físico o documentar expresamente su ausencia.
4. Probar archivos GenCAD distintos de esta placa, especialmente aquellos con instrucciones no presentes en la muestra.
5. Comprobar contactos de pads, arcos y segmentos interiores; las coincidencias de extremos no certifican conectividad.

Hasta completar estas verificaciones, el convertidor GenCAD se considera **funcional en beta**, no cerrado ni universal.
