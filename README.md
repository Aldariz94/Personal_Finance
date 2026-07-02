# 💰 Mis Finanzas

App local y personal para controlar tus finanzas: ingresos, gastos, compras en
cuotas y un dashboard que te dice cuánto te queda a fin de mes.

Todo corre **100% en tu computador**: no hay hosting, no hay cuentas, no hay
internet de por medio. Tus datos viven en un solo archivo (`finanzas.db`).

## Requisitos

- Windows 10/11 (también funciona en Mac/Linux)
- Python 3.10 o superior — descárgalo de [python.org](https://www.python.org/downloads/)
  (al instalar, marca la casilla **"Add Python to PATH"**)

## Instalación (una sola vez)

Abre una terminal (PowerShell) en esta carpeta y ejecuta:

```
pip install -r requirements.txt
```

## Cómo usarla

```
streamlit run app.py
```

Se abre sola en tu navegador (en `http://localhost:8501`). Para cerrarla,
vuelve a la terminal y presiona `Ctrl+C`.

## Qué hace

- **Dashboard**: ingresos del mes − (gastos + cuotas activas) = cuánto te queda.
  Con desglose por categoría y lista de cuotas activas.
- **Agregar**: ingresos (sueldo, bonos), gastos del día a día, y compras con
  tarjeta. Una compra en cuotas (ej. 24) aparece sola como gasto cada mes hasta
  que se paga la última cuota, y ahí desaparece.
- El valor de la cuota se calcula solo (total ÷ cuotas) pero puedes editarlo si
  el banco te cobra interés.
- Los nombres de gastos, comercios y categorías se guardan y se autocompletan:
  escribe para filtrar o elige de la lista.
- **Historial**: todas tus compras, gastos e ingresos, con filtros por nombre y
  categoría, y el estado de cada compra en cuotas (cuántas van, cuándo termina).

## Respaldo

Tus datos son el archivo `finanzas.db` (en esta misma carpeta). Para respaldar,
copia ese archivo a donde quieras (un pendrive, tu nube personal, etc.).
