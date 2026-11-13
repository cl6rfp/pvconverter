# Entrega 011 — Preparación de ejecutable Windows

Versión 0.001.0009 beta · 2026-11-13.

## Alcance

Se prepara una distribución portable para Windows con PyInstaller sin modificar el parser GenCAD, PVF ni el renderizador. No se ha compilado un ejecutable de Windows en Linux.

## Cambios

- `build_windows.bat`: entorno aislado, selección explícita Python 3.12 x64, comprobación de pruebas, compilación y empaquetado.
- `requirements-build.txt`: versión fija de PyInstaller.
- `scripts/package_windows.py`: ZIP portable e inspección de integridad.
- `docs/desarrollo/COMPILAR_WINDOWS.md`: pasos reproducibles y lista de aceptación manual.
- `README.md`, `CHANGELOG.md`, `VERSION` e índice documental: versión y registro de entrega.

## Comprobaciones

Pendiente: construir el EXE y probarlo en Windows. Comprobado en Linux con Python 3.13: 76 pruebas unitarias superadas, pruebas sintéticas de dirección de arcos superadas, compilación de los nuevos scripts correcta. Se probó el empaquetador con archivos ficticios en una carpeta temporal y se comprobó que el ZIP generado no presentaba corrupción; esos archivos de prueba se eliminaron, no constituyen un EXE funcional. No se atribuye validación nativa de Windows.

## Pendientes

- Prueba manual del ejecutable en Windows 10/11 x64.
- Prueba de conversión y apertura de PV con el EXE empaquetado.
- Firma digital si se publica externamente.
- Compatibilidad GenCAD fuera del CAD de referencia y geometría no certificada.
