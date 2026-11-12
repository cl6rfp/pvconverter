"""Simple Windows desktop GUI for the PV Converter prototype (Tkinter)."""
from __future__ import annotations
import os, threading, traceback
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from build_pv import build_model
from gencad_parser import parse_file
from pvf import write_pvf, read_pvf
from pv_geometry import geometry_report, export_svg

class PVConverterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('PV Converter')
        self.geometry('760x520')
        self.minsize(650,430)
        self.configure(bg='#151a22')
        self.pv_path=None
        style=ttk.Style(self); style.theme_use('clam')
        style.configure('TFrame',background='#151a22')
        style.configure('TLabel',background='#151a22',foreground='#e8edf4',font=('Segoe UI',10))
        style.configure('Title.TLabel',font=('Segoe UI',21,'bold'),foreground='#ffffff')
        style.configure('TButton',font=('Segoe UI',10),padding=9)
        style.configure('TCombobox',padding=5)
        root=ttk.Frame(self,padding=22); root.pack(fill='both',expand=True)
        ttk.Label(root,text='PV Converter',style='Title.TLabel').pack(anchor='w')
        ttk.Label(root,text='Importa GenCAD y genera archivos .pv independientes.').pack(anchor='w',pady=(4,18))
        actions=ttk.Frame(root); actions.pack(fill='x')
        ttk.Button(actions,text='Importar CAD y convertir a PV',command=self.convert).pack(fill='x',pady=5)
        ttk.Button(actions,text='Abrir archivo PV y validar',command=self.open_pv).pack(fill='x',pady=5)
        row=ttk.Frame(root); row.pack(fill='x',pady=(8,4))
        ttk.Label(row,text='Capa para vista previa:').pack(side='left')
        self.layer=tk.StringVar(value='ALL')
        ttk.Combobox(row,textvariable=self.layer,values=['ALL','TOP','INNER_1','INNER_2','BOTTOM'],state='readonly',width=14).pack(side='left',padx=10)
        self.components=tk.BooleanVar(value=False)
        ttk.Checkbutton(row,text='Mostrar referencias de componentes',variable=self.components).pack(side='left',padx=8)
        ttk.Button(root,text='Exportar vista geométrica SVG',command=self.export_preview).pack(fill='x',pady=5)
        ttk.Label(root,text='Registro de actividad').pack(anchor='w',pady=(16,5))
        self.log=tk.Text(root,height=12,bg='#0d1117',fg='#d7e0ea',insertbackground='white',relief='flat',wrap='word',font=('Consolas',9))
        self.log.pack(fill='both',expand=True)
        self.write('Listo. Selecciona un CAD para crear tu primer PV desde la aplicación.\n')

    def write(self,text):
        self.log.insert('end',str(text)+'\n'); self.log.see('end'); self.update_idletasks()

    def fail(self,exc):
        self.write('ERROR: '+str(exc))
        messagebox.showerror('PV Converter',str(exc))

    def convert(self):
        src=filedialog.askopenfilename(title='Seleccionar archivo GenCAD',filetypes=[('GenCAD','*.cad *.gcd'),('Todos los archivos','*.*')])
        if not src:return
        dst=filedialog.asksaveasfilename(title='Guardar archivo PV',defaultextension='.pv',initialfile=Path(src).stem+'.pv',filetypes=[('PV File','*.pv')])
        if not dst:return
        try:
            self.write('Leyendo: '+src)
            data,raw=parse_file(src)
            self.write('Fuente: '+str(len(raw))+' bytes. Preparando modelo PV Core...')
            blocks=build_model(data,raw)
            info=write_pvf(dst,blocks)
            self.pv_path=dst
            self.write(f'PV creado: {dst} ({info["file_size"]:,} bytes)')
            report=geometry_report(dst)
            self.write(f'Validación: {"CORRECTA" if report["valid"] else "REVISAR"}; {report["segments"]:,} segmentos, {report["vias"]:,} vías, {report["arc_records"]:,} arcos.')
            diagnostics=report.get('integrity_diagnostics')
            if diagnostics:
                counts=diagnostics['counts']
                route=diagnostics['route_summary']
                self.write(
                    'Integridad: '
                    f'{counts["blocking_errors"]} errores, {counts["warnings"]} avisos, '
                    f'{counts["ambiguous"]} casos ambiguos, {counts["informational"]} informativos.')
                self.write(
                    f'Continuidad: {route["connected_pairs"]:,} pares conectados, '
                    f'{route["disconnected_pairs"]:,} discontinuidades; '
                    f'{route["via_transitions_connected"]:,}/{route["via_transitions_checked"]:,} '
                    'transiciones con vía conectadas.')
            messagebox.showinfo('Conversión terminada',f'Archivo PV creado correctamente.\n\n{dst}\n\nTamaño: {info["file_size"]:,} bytes')
        except Exception as e:self.fail(e)

    def open_pv(self):
        path=filedialog.askopenfilename(title='Abrir archivo PV',filetypes=[('PV File','*.pv'),('Todos los archivos','*.*')])
        if not path:return
        try:
            doc=read_pvf(path); report=geometry_report(path); self.pv_path=path
            self.write(f'PV abierto: {path}')
            self.write(f'Formato {doc["version"][0]}.{doc["version"][1]} | {doc["file_size"]:,} bytes | {report["blocks"]} bloques')
            self.write(f'{report["components"]:,} componentes | {report["segments"]:,} segmentos | {report["vias"]:,} vías | {report["arc_records"]:,} arcos')
            self.write('Integridad de fuente SHA-256: '+('OK' if report['source_sha256_matches'] else 'NO VERIFICADA'))
            self.write('Referencias de rutas: '+('OK' if report['valid'] else 'REVISAR'))
            diagnostics=report.get('integrity_diagnostics')
            if diagnostics:
                counts=diagnostics['counts']
                self.write(
                    'Diagnóstico de integridad: '
                    f'{counts["blocking_errors"]} errores, {counts["warnings"]} avisos, '
                    f'{counts["ambiguous"]} casos ambiguos, {counts["informational"]} informativos.')
            messagebox.showinfo('PV validado',f'Archivo leído correctamente.\nComponentes: {report["components"]:,}\nSegmentos: {report["segments"]:,}\nVías: {report["vias"]:,}\nArcos: {report["arc_records"]:,}')
        except Exception as e:self.fail(e)

    def export_preview(self):
        path=self.pv_path
        if not path:
            path=filedialog.askopenfilename(title='Seleccionar archivo PV',filetypes=[('PV File','*.pv')])
            if not path:return
            self.pv_path=path
        dst=filedialog.asksaveasfilename(title='Guardar vista SVG',defaultextension='.svg',initialfile=Path(path).stem+'_preview.svg',filetypes=[('SVG','*.svg')])
        if not dst:return
        try:
            result=export_svg(path,dst,self.layer.get(),self.components.get())
            self.write(f'Vista SVG exportada: {dst}')
            if os.name=='nt': os.startfile(dst)
            messagebox.showinfo('Vista exportada','Se generó la vista SVG.\nSe abrirá en el navegador predeterminado.')
        except Exception as e:self.fail(e)

if __name__=='__main__':
    PVConverterApp().mainloop()
