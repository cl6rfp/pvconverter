"""Crea un ZIP portable a partir de la salida onedir de PyInstaller."""
from __future__ import annotations
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()
DIST = ROOT / "dist"
APP = DIST / "PV_Converter"
EXECUTABLE = APP / "PV_Converter.exe"


def package() -> Path:
    if not EXECUTABLE.is_file():
        raise FileNotFoundError(f"No se encontro el ejecutable: {EXECUTABLE}")
    files = sorted(path for path in APP.rglob("*") if path.is_file())
    if len(files) < 2:
        raise RuntimeError("La distribucion no contiene las dependencias necesarias")
    archive = DIST / f"PV_Converter_{VERSION}_Windows_x64.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as out:
        for path in files:
            out.write(path, path.relative_to(DIST))
        out.writestr("LEEME_WINDOWS.txt", (
            f"PV Converter beta {VERSION}\n"
            "Extrae la carpeta PV_Converter completa.\n"
            "Ejecuta PV_Converter\\PV_Converter.exe.\n"
            "No se necesita Python en el equipo de destino.\n"
            "En caso de aviso de SmartScreen, revisa primero el origen del archivo.\n"
            "La aplicacion no esta firmada digitalmente.\n"
        ))
    with zipfile.ZipFile(archive) as z:
        bad_file = z.testzip()
        if bad_file:
            raise RuntimeError(f"ZIP corrupto: {bad_file}")
    print(f"Paquete listo: {archive}")
    return archive


if __name__ == "__main__":
    try:
        package()
    except (RuntimeError, OSError, zipfile.BadZipFile) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
