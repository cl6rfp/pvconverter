# Análisis de contactos geométricos

## Motivo

El informe de adyacencia (`route_audit.py`) compara primitivas consecutivas. En GenCAD una ruta puede incluir ramificaciones y otras secuencias que no siguen un recorrido único. Un salto entre dos registros consecutivos no prueba que haya una pista cortada.

`connectivity_audit.py` aporta otra lectura: agrupa los segmentos de cada `ROUT` si sus **extremos** coinciden, dentro de la tolerancia indicada, **en la misma capa**. El orden de los registros ya no influye en esos contactos. No modifica el `.pv`.

## Criterios

- Cada segmento LINE o ARC aporta sus dos extremos originales. El arco no se aproxima ni se le atribuye un sentido de barrido.
- Se usa `layer_id`; dos extremos en distintas capas no se unen.
- La búsqueda espacial compara la distancia real, no solo la celda del índice. La tolerancia predeterminada es `0.0001` en unidades fuente, no milímetros.
- El análisis se limita a cada registro `ROUT`; no combina automáticamente rutas distintas aunque compartan `net_id`.
- Los registros vacíos (`primitive_start=0`, `primitive_count=0`) son válidos.
- Se señalan referencias rotas y coordenadas inválidas sin reemplazarlas.

## Lo que **no** demuestra

La cantidad de grupos no representa circuitos abiertos ni redes eléctricas independientes. Un grupo puede enlazarse mediante una vía, un pad, una intersección en mitad de una línea o geometría de cobre que este análisis no inspecciona. Tampoco se certifica que extremos coincidentes estén unidos eléctricamente. Los pines listados bajo `NETS` informan la asignación lógica declarada por el origen, pero no certifican la unión física del cobre.

La vinculación de vías entre capas requiere resolver su alcance (`span` y padstack); las intersecciones interiores exigen otras comprobaciones geométricas. Por eso no se infieren puentes entre capas ni se reparan rutas. Estas tareas quedan abiertas.

## Ejecutar

```bash
python connectivity_audit.py "generated/MS-7B79 r1.0.pv" --top 20 --output auditorias/contactos_local.json
```

Para tolerancia exacta, indicar `--tolerance 0`. `--top` limita el detalle de rutas, no el cálculo de totales.

## Referencia y seguimiento

La evaluación de la placa incluida está en `auditorias/2026-11-13_contactos_extremos.json`. Los datos se generaron con el archivo `generated/MS-7B79 r1.0.pv` recibido en la entrega anterior. No se aplicó normalización física ni corrección geométrica.

A futuro se necesitan pruebas separadas para contacto extremo–interior, pads, vías, capas y topología netlist frente a cobre. Cualquier relación inferida deberá ir etiquetada como tal y ser verificable con otro archivo de referencia.
