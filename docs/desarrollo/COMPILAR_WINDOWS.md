# Compilar PV Converter para Windows

Versión objetivo: **0.001.0010 beta**. Este procedimiento se ejecuta en un ordenador Windows de 64 bits; la carpeta del proyecto no tiene que estar en `C:\`.

## Requisitos

- Windows 10/11 de 64 bits.
- Python **3.12 (64 bits)**, instalado desde <https://www.python.org/downloads/windows/> con el lanzador `py`.
- Conexión a Internet para instalar dependencias durante la primera compilación.
- Espacio libre para el entorno, dependencias y carpeta `dist`.
- El ZIP completo del proyecto de esta entrega, extraído a una carpeta con permiso de escritura.

## Compilar

1. Extrae el ZIP del proyecto. No ejecutes `build_windows.bat` desde dentro del ZIP comprimido.
2. En **Símbolo del sistema** comprueba `py -3.12 --version` y `py -3.12 -c "import struct; print(struct.calcsize('P') * 8)"` (debe mostrar `64`).
3. Haz doble clic en **`build_windows.bat`** desde la carpeta raíz, o ejecútalo desde CMD para poder leer los mensajes.
4. El script crea `.venv-build` sin tocar tus otros entornos, instala dependencias, ejecuta las pruebas unitarias y de arcos, genera `dist\PV_Converter\PV_Converter.exe` y empaqueta `dist\PV_Converter_0.001.0010_Windows_x64.zip`.
5. Si falla, **no distribuyas** la carpeta. Conserva el mensaje de error para corregirlo.

No copies únicamente el `.exe`: PyInstaller en modo `onedir` necesita también las bibliotecas de `dist\PV_Converter`. El ZIP generado incluye la carpeta completa.

## Comprobación manual obligatoria

1. Ejecuta `dist\PV_Converter\PV_Converter.exe` y comprueba que abre sin Python instalado en el destino.
2. Usa **Importar CAD y convertir a PV** con una copia de `MS-7B79 r1.0.cad` y guarda el resultado en una carpeta con permisos.
3. Comprueba que el archivo `.pv` existe y que la validación de integridad no muestra errores bloqueantes.
4. Usa **Abrir archivo PV y validar** y comprueba que lee el archivo recién generado.
5. Usa **Exportar vista geométrica SVG**. Abre el SVG en el navegador y comprueba que se visualiza.
6. Repite la apertura desde una carpeta distinta a la del proyecto, con espacios en la ruta, para detectar dependencias de rutas locales.
7. Si vas a distribuir el programa, prueba el ZIP extraído en otro ordenador Windows x64 sin Python.

**Estado:** el código y las pruebas del proyecto se han validado en Linux; el `.exe` no se ha generado ni ejecutado en Windows desde este entorno. Estas comprobaciones necesitan un equipo Windows.

## Resolución de problemas

- **`py` no se reconoce:** instala Python 3.12 x64 e incluye el lanzador de Python. Cierra y vuelve a abrir CMD.
- **Error al descargar paquetes:** comprueba red, proxy o antivirus. No desactives la protección del sistema como solución genérica.
- **El EXE no inicia:** ejecuta la compilación desde CMD, conserva los mensajes y comprueba que no hayas copiado solo el `.exe`.
- **Windows SmartScreen:** el ejecutable local no tiene firma de código. Comprueba su procedencia y revisa el aviso; para una distribución pública conviene utilizar firma digital.
- **No hay interfaz de instalación:** esta entrega genera una aplicación portable, no un instalador MSI/MSIX.
- **Rendimiento:** durante conversiones grandes la interfaz actual puede quedar ocupada temporalmente; esto no implica que la conversión haya fallado.

## Alcance

El programa importa **GenCAD**, no archivos `.pcb` arbitrarios. Se mantienen pendientes la certificación de `MIRRORY`, la identificación del contorno mecánico y las pruebas de compatibilidad con otros CAD. El futuro visor web es otro proyecto. Nunca mezcles el ZIP del código fuente de esta entrega con el ZIP portable de `dist`.
