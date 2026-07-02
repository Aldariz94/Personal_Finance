# Spec de PyInstaller para empaquetar la app como ejecutable.
# Uso: pyinstaller --noconfirm --clean MisFinanzas.spec

from PyInstaller.utils.hooks import collect_all

datas, binaries, hiddenimports = [], [], []
for pkg in ("streamlit", "altair"):
    d, b, h = collect_all(pkg)
    datas += d
    binaries += b
    hiddenimports += h

datas += [
    ("app.py", "."),
    ("db.py", "."),
    ("utils.py", "."),
    ("views", "views"),
    (".streamlit", ".streamlit"),
]

a = Analysis(
    ["launcher.py"],
    datas=datas,
    binaries=binaries,
    hiddenimports=hiddenimports,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    exclude_binaries=True,
    name="MisFinanzas",
    console=True,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name="MisFinanzas",
)
