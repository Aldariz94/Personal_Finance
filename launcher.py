"""Punto de entrada para la versión empaquetada (.exe).

Arranca el servidor de Streamlit y abre la app en el navegador.
Los datos se guardan en la carpeta del usuario (~/MisFinanzas/finanzas.db)
para que sobrevivan a las actualizaciones de la app.
"""

import os
import sys
from pathlib import Path

from streamlit.web import cli as stcli


def base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent


if __name__ == "__main__":
    if getattr(sys, "frozen", False):
        data_dir = Path.home() / "MisFinanzas"
        data_dir.mkdir(exist_ok=True)
        os.environ.setdefault("FINANZAS_DB", str(data_dir / "finanzas.db"))

    # Sin este archivo, Streamlit pide un email por consola la primera vez
    # y deja la app colgada esperando una respuesta.
    credenciales = Path.home() / ".streamlit" / "credentials.toml"
    if not credenciales.exists():
        credenciales.parent.mkdir(exist_ok=True)
        credenciales.write_text('[general]\nemail = ""\n')

    # El cwd debe contener .streamlit/config.toml para que tome el tema oscuro
    os.chdir(base_dir())

    sys.argv = [
        "streamlit", "run", str(base_dir() / "app.py"),
        "--global.developmentMode=false",
        "--server.headless=false",
        "--server.fileWatcherType=none",
        "--browser.gatherUsageStats=false",
    ] + sys.argv[1:]
    sys.exit(stcli.main())
