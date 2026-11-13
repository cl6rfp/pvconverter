# Transformaciones y encuadre de pads

## Convención que usa el SVG

Las posiciones de los pines proceden de coordenadas locales de la huella. Para dibujarlos se refleja X cuando la huella contiene `MIRRORY`, se aplica `ROTATION` y por último se suma el origen del componente. Cada pad añade las rotaciones de pin y de entrada de padstack antes de esa transformación.

**Esto describe la implementación actual, no prueba que `MIRRORY` tenga esa semántica en todos los GenCAD.** Se mantiene el token original en PVF para que la interpretación pueda revisarse sin pérdida de información.

## Cambio de encuadre

La vista SVG utilizaba los centros de los pines para calcular su encuadre. Ahora incluye las cuatro esquinas de la envolvente local de cada pad tras aplicar todas las transformaciones. Estas esquinas dan límites conservadores: para geometrías irregulares pueden exceder el dibujo, pero evitan recortar pads grandes o rotados en el borde. No son dimensiones mecánicas exactas.

## Auditoría repetible

```bash
python component_transform.py "generated/MS-7B79 r1.0.pv" --output auditorias/transformaciones.json
python -m unittest -v test_component_transform
```

El informe distingue tokens de transformación conocidos y metadatos numéricos no interpretados. Estos últimos no se descartan ni se usan para mover componentes.

## Pendiente para cerrar la fidelidad GenCAD

- Contrastar el sentido del espejo y la interpretación de las entradas numéricas de `SHAPE` con especificación o CAD independiente.
- Reconocer, si existe en otras muestras, un borde mecánico auténtico; la placa actual no permite asegurarlo.
- Verificar el resultado sobre más archivos GenCAD. Una muestra que pase todas las pruebas no equivale a compatibilidad universal.
- Investigar el gran rango vertical de los pads en la muestra antes de tratarlo como error: podría proceder de la propia geometría de alguna huella.

El visor HTML es diagnóstico y basado en SVG con miles de nodos. La lentitud tras cargarlo es un problema conocido, reservado para el diseño del visor web acelerado por GPU; alternar 2D y 3D por sí solo no arregla el rendimiento.
