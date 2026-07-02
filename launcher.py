"""Punto de entrada para la versión empaquetada (.exe).

Arranca el servidor de Streamlit en segundo plano y abre la app en una
ventana propia (modo app de Edge/Chrome, sin barra de direcciones).
Al cerrar esa ventana, el servidor se apaga solo y el proceso termina:
abrir y cerrar funciona como cualquier app normal.

Los datos se guardan en la carpeta del usuario (~/MisFinanzas/finanzas.db)
para que sobrevivan a las actualizaciones de la app.
"""

import os
import shutil
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path
from urllib.request import urlopen


def base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent


def puerto_libre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def buscar_navegador():
    """Ruta del navegador para la ventana de la app: Chrome primero, luego Edge."""
    if os.environ.get("MISFINANZAS_BROWSER"):
        return os.environ["MISFINANZAS_BROWSER"]
    candidatos = [
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%LocalAppData%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
    ]
    for c in candidatos:
        if c and os.path.exists(c):
            return c
    for nombre in ("google-chrome", "chromium", "chromium-browser", "msedge"):
        ruta = shutil.which(nombre)
        if ruta:
            return ruta
    return None


def esperar_servidor(url, segundos=120):
    for _ in range(segundos * 4):
        try:
            urlopen(url, timeout=1)
            return True
        except Exception:
            time.sleep(0.25)
    return False


def ventana_app(url, data_dir):
    """Espera el servidor, abre la ventana de la app y, al cerrarla, apaga todo."""
    if not esperar_servidor(url):
        os._exit(1)

    navegador = buscar_navegador()
    if navegador:
        # Un perfil propio obliga a que la ventana sea un proceso dedicado:
        # así sabemos exactamente cuándo el usuario la cierra.
        perfil = data_dir / "ventana"
        perfil.mkdir(parents=True, exist_ok=True)
        subprocess.run([
            navegador,
            f"--app={url}",
            f"--user-data-dir={perfil}",
            "--no-first-run",
            "--no-default-browser-check",
        ])
        os._exit(0)

    # Sin Edge/Chrome: pestaña normal + ventanita para salir de la app.
    import webbrowser
    webbrowser.open(url)
    try:
        import tkinter as tk

        raiz = tk.Tk()
        raiz.title("Mis Finanzas")
        tk.Label(
            raiz,
            text="Mis Finanzas está abierta en tu navegador.\n\n"
                 "Cierra esta ventana cuando quieras salir de la app.",
            padx=30, pady=30,
        ).pack()
        raiz.mainloop()
    except Exception:
        input("Presiona Enter para salir de Mis Finanzas...")
    os._exit(0)


if __name__ == "__main__":
    data_dir = Path.home() / "MisFinanzas"
    data_dir.mkdir(exist_ok=True)

    if getattr(sys, "frozen", False):
        os.environ.setdefault("FINANZAS_DB", str(data_dir / "finanzas.db"))
        # En modo ventana (sin consola) los streams no existen o no son
        # confiables, y Streamlit los necesita para sus mensajes. Todo va
        # a un log que además sirve para diagnosticar problemas.
        log = open(data_dir / "launcher.log", "w", buffering=1, encoding="utf-8", errors="replace")
        sys.stdout = log
        sys.stderr = log

    # Sin este archivo, Streamlit pide un email por consola la primera vez
    # y deja la app colgada esperando una respuesta.
    credenciales = Path.home() / ".streamlit" / "credentials.toml"
    if not credenciales.exists():
        credenciales.parent.mkdir(exist_ok=True)
        credenciales.write_text('[general]\nemail = ""\n')

    # El cwd debe contener .streamlit/config.toml para que tome el tema oscuro
    os.chdir(base_dir())

    puerto = puerto_libre()
    url = f"http://localhost:{puerto}"

    threading.Thread(target=ventana_app, args=(url, data_dir), daemon=True).start()

    try:
        from streamlit.web import cli as stcli

        sys.argv = [
            "streamlit", "run", str(base_dir() / "app.py"),
            "--global.developmentMode=false",
            "--server.headless=true",
            "--server.fileWatcherType=none",
            # Solo este PC puede abrir la app; nadie más en la red la ve.
            "--server.address=localhost",
            f"--server.port={puerto}",
            "--browser.gatherUsageStats=false",
        ] + sys.argv[1:]
        sys.exit(stcli.main())
    except SystemExit:
        raise
    except BaseException:
        import traceback

        print("El servidor de la app se cayó con este error:", file=sys.stderr)
        traceback.print_exc()
        raise
