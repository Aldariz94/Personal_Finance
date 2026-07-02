from datetime import date

import pandas as pd
import streamlit as st

import db
from utils import fmt, installment_number, last_installment_month, month_label

st.title("📜 Historial")

tab_compras, tab_gastos, tab_ingresos = st.tabs(["💳 Compras", "🧾 Gastos", "💵 Ingresos"])

hoy = date.today()


def _filtros(df, key, con_categoria=True):
    """Filtro por texto + categoría. Devuelve el df filtrado."""
    col1, col2 = st.columns(2)
    texto = col1.text_input("Buscar por nombre", key=f"{key}_texto")
    if texto:
        campo = "merchant" if "merchant" in df.columns else "name"
        df = df[df[campo].str.contains(texto, case=False, na=False)]
    if con_categoria:
        cats = col2.multiselect(
            "Categoría", options=sorted(df["categoria"].unique()), key=f"{key}_cat"
        )
        if cats:
            df = df[df["categoria"].isin(cats)]
    return df


def _eliminar(df, etiqueta, borrar, key):
    """Expander para eliminar un registro por selección."""
    with st.expander("🗑️ Eliminar un registro"):
        opciones = {etiqueta(r): r["id"] for _, r in df.iterrows()}
        sel = st.selectbox("Registro", options=list(opciones), index=None, key=f"{key}_del")
        if sel and st.button("Eliminar definitivamente", key=f"{key}_del_btn"):
            borrar(opciones[sel])
            st.rerun()


# --- Compras -------------------------------------------------------------------

with tab_compras:
    compras = db.purchases_df()
    if compras.empty:
        st.caption("Todavía no registras compras.")
    else:
        compras = _filtros(compras, "hc")
        solo_activas = st.checkbox("Solo cuotas activas", key="hc_activas")

        compras["cuota_actual"] = compras.apply(
            lambda p: installment_number(p["date"], p["installments"], hoy.year, hoy.month),
            axis=1,
        )
        if solo_activas:
            compras = compras[compras["cuota_actual"].notna() & (compras["installments"] > 1)]

        def _estado(p):
            if p["installments"] == 1:
                return "Sin cuotas"
            if p["cuota_actual"] is not None:
                return f"Pagando ({int(p['cuota_actual'])} de {p['installments']})"
            fin_y, fin_m = last_installment_month(p["date"], p["installments"])
            if (hoy.year, hoy.month) > (fin_y, fin_m):
                return "Pagada ✅"
            return "Por empezar"

        tabla = pd.DataFrame(
            {
                "Fecha": compras["date"],
                "Comercio": compras["merchant"],
                "Categoría": compras["categoria"],
                "Total": compras["total_amount"].map(fmt),
                "Cuotas": compras["installments"],
                "Valor cuota": compras["installment_value"].map(fmt),
                "Estado": compras.apply(_estado, axis=1),
                "Última cuota": compras.apply(
                    lambda p: month_label(*last_installment_month(p["date"], p["installments"]))
                    if p["installments"] > 1
                    else "—",
                    axis=1,
                ),
            }
        )
        st.dataframe(tabla, hide_index=True, width="stretch")
        _eliminar(
            compras,
            lambda r: f"{r['date']} — {r['merchant']} — {fmt(r['total_amount'])} ({r['installments']} cuotas)",
            db.delete_purchase,
            "hc",
        )

# --- Gastos ----------------------------------------------------------------------

with tab_gastos:
    gastos = db.expenses_df()
    if gastos.empty:
        st.caption("Todavía no registras gastos.")
    else:
        gastos = _filtros(gastos, "hg")
        tabla = pd.DataFrame(
            {
                "Fecha": gastos["date"],
                "Nombre": gastos["name"],
                "Categoría": gastos["categoria"],
                "Monto": gastos["amount"].map(fmt),
            }
        )
        st.dataframe(tabla, hide_index=True, width="stretch")
        _eliminar(
            gastos,
            lambda r: f"{r['date']} — {r['name']} — {fmt(r['amount'])}",
            db.delete_expense,
            "hg",
        )

# --- Ingresos ----------------------------------------------------------------------

with tab_ingresos:
    ingresos = db.incomes_df()
    if ingresos.empty:
        st.caption("Todavía no registras ingresos.")
    else:
        tabla = pd.DataFrame(
            {
                "Fecha": ingresos["date"],
                "Monto": ingresos["amount"].map(fmt),
                "Nota": ingresos["note"].fillna(""),
            }
        )
        st.dataframe(tabla, hide_index=True, width="stretch")
        _eliminar(
            ingresos,
            lambda r: f"{r['date']} — {fmt(r['amount'])} {r['note'] or ''}".strip(),
            db.delete_income,
            "hi",
        )
