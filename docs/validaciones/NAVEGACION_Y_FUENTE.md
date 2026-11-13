# Navegación de la vista y elementos disponibles en GenCAD

## Controles de la vista HTML

- **Rueda del ratón:** acerca o aleja la placa tomando como referencia la posición del puntero. El gesto actúa solo dentro del SVG.
- **Botón derecho mantenido:** desplaza la vista. Se desactiva el menú contextual únicamente sobre el dibujo.
- **Restablecer vista:** recupera el encuadre inicial y muestra el nivel de zoom relativo (100 % al abrir).
- **Controles de capa y tipo:** siguen funcionando mientras se navega. Seleccionar un grupo de arte no altera la geometría.

Los límites de ampliación son relativos al encuadre inicial. El zoom modifica el `viewBox` del SVG, sin modificar coordenadas ni datos del archivo PVF.

## Inventario del CAD de referencia

Fuente: `MS-7B79 r1.0.cad`. Inventario reproducible mediante:

```sh
python source_features_audit.py "MS-7B79 r1.0.cad" --out auditorias/inventario.json
```

- **Serigrafía:** no hay capas llamadas SILK/LEGEND ni registros en la sección `$ARTWORKS`. Los 204 grupos `$BOARD` se asocian a TOP (143) y BOTTOM (61), pero no pueden clasificarse en bloque como serigrafía. Puede haber trazos de aspecto similar a una leyenda dentro de ARTWORK; la fuente no los etiqueta explícitamente.
- **Mecánica:** `$MECH` declara siete taladros con posición y diámetro. Están conservados en `HOLE` y aparecen en el SVG bajo el control **Taladros**.
- **Contorno:** no se ha identificado un borde mecánico explícito. Las líneas de `$BOARD` no se etiquetan como contorno físico sin evidencias.
- **Huellas:** hay 2.693 componentes, 2.450 en TOP y 243 en BOTTOM. Los 243 de BOTTOM llevan `FLIP` y `MIRRORY` en sus datos de `SHAPE`. Esto permite enfocar la siguiente revisión de transformaciones; no prueba que estén mal ubicados.

Las comprobaciones de geometría mecánica y serigrafía no deben depender exclusivamente del aspecto del dibujo. El inventario separa hechos explícitos de interpretaciones pendientes.

## Pendiente

Verificar en Edge/Chrome que la rueda y el arrastre sean cómodos con ratones y escalas de pantalla distintas. Revisar con casos sintéticos las transformaciones de pads en componentes `FLIP` y `MIRRORY` antes de modificar su representación.
