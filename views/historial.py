from datetime import date

import pandas as pd
import streamlit as st

import db
from utils import fmt, installment_number, last_installment_month, month_label

st.title("📜 Historial")
st.caption(
    "Puedes **editar cualquier celda** haciendo doble clic, y **eliminar filas** "
    "seleccionándolas (casilla de la izquierda) y presionando el basurero o la "
    "tecla Supr. Al terminar, presiona «Guardar cambios»."
)

tab_compras, tab_gastos, tab_ingresos = st.tabs(["💳 Compras", "🧾 Gastos", "💵 Ingresos"])

hoy = date.today()


def _filtros(df, key, campo):
    """Filtro por texto + categoría. Devuelve el df filtrado."""
    col1, col2 = st.columns(2)
    texto = col1.text_input("Buscar por nombre", key=f"{key}_texto")
    if texto:
        df = df[df[campo].str.contains(texto, case=False, na=False)]
    cats = col2.multiselect(
        "Categoría", options=sorted(df["categoria"].unique()), key=f"{key}_cat"
    )
    if cats:
        df = df[df["categoria"].isin(cats)]
    return df


def _aplicar_cambios(original, editado, campos, actualizar, eliminar):
    """Compara el editor con la tabla original y aplica cambios a la base.

    Devuelve (actualizados, eliminados). Las filas agregadas en el editor
    (sin id) se ignoran: para agregar registros está la página Agregar.
    """
    editado = editado[editado["id"].notna()]
    orig_por_id = original.set_index("id")
    ids_editado = set(editado["id"])

    eliminados = 0
    for rid in orig_por_id.index:
        if rid not in ids_editado:
            eliminar(int(rid))
            eliminados += 1

    actualizados = 0
    for _, fila in editado.iterrows():
        orig = orig_por_id.loc[fila["id"]]
        if any(fila[c] != orig[c] for c in campos):
            actualizar(fila)
            actualizados += 1

    return actualizados, eliminados


def _guardar(key, original, editado, campos, actualizar, eliminar):
    if st.button("💾 Guardar cambios", key=f"{key}_save", type="primary"):
        act, elim = _aplicar_cambios(original, editado, campos, actualizar, eliminar)
        if act or elim:
            st.toast(f"Listo: {act} actualizado(s), {elim} eliminado(s).", icon="✅")
        else:
            st.toast("No había cambios que guardar.", icon="ℹ️")
        st.rerun()


# --- Compras -------------------------------------------------------------------

with tab_compras:
    compras = db.purchases_df()
    if compras.empty:
        st.caption("Todavía no registras compras.")
    else:
        compras = _filtros(compras, "hc", "merchant")
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

        original = pd.DataFrame(
            {
                "id": compras["id"],
                "Fecha": pd.to_datetime(compras["date"]).dt.date,
                "Comercio": compras["merchant"],
                "Categoría": compras["categoria"],
                "Total": compras["total_amount"],
                "Cuotas": compras["installments"],
                "Valor cuota": compras["installment_value"],
                "Estado": compras.apply(_estado, axis=1),
                "Última cuota": compras.apply(
                    lambda p: month_label(*last_installment_month(p["date"], p["installments"]))
                    if p["installments"] > 1
                    else "—",
                    axis=1,
                ),
            }
        ).reset_index(drop=True)

        editado = st.data_editor(
            original,
            key="hc_editor",
            hide_index=True,
            width="stretch",
            num_rows="dynamic",
            disabled=["Estado", "Última cuota"],
            column_config={
                "id": None,
                "Fecha": st.column_config.DateColumn(required=True),
                "Comercio": st.column_config.TextColumn(required=True),
                "Categoría": st.column_config.SelectboxColumn(
                    options=db.list_categories(), required=True
                ),
                "Total": st.column_config.NumberColumn(min_value=1, required=True),
                "Cuotas": st.column_config.NumberColumn(
                    min_value=1, max_value=60, step=1, required=True
                ),
                "Valor cuota": st.column_config.NumberColumn(min_value=1, required=True),
            },
        )
        _guardar(
            "hc",
            original,
            editado,
            ["Fecha", "Comercio", "Categoría", "Total", "Cuotas", "Valor cuota"],
            lambda f: db.update_purchase(
                int(f["id"]), f["Comercio"], f["Categoría"], int(f["Total"]),
                int(f["Cuotas"]), int(f["Valor cuota"]), f["Fecha"],
            ),
            db.delete_purchase,
        )

# --- Gastos ----------------------------------------------------------------------

with tab_gastos:
    gastos = db.expenses_df()
    if gastos.empty:
        st.caption("Todavía no registras gastos.")
    else:
        gastos = _filtros(gastos, "hg", "name")
        original = pd.DataFrame(
            {
                "id": gastos["id"],
                "Fecha": pd.to_datetime(gastos["date"]).dt.date,
                "Nombre": gastos["name"],
                "Categoría": gastos["categoria"],
                "Monto": gastos["amount"],
            }
        ).reset_index(drop=True)

        editado = st.data_editor(
            original,
            key="hg_editor",
            hide_index=True,
            width="stretch",
            num_rows="dynamic",
            column_config={
                "id": None,
                "Fecha": st.column_config.DateColumn(required=True),
                "Nombre": st.column_config.TextColumn(required=True),
                "Categoría": st.column_config.SelectboxColumn(
                    options=db.list_categories(), required=True
                ),
                "Monto": st.column_config.NumberColumn(min_value=1, required=True),
            },
        )
        _guardar(
            "hg",
            original,
            editado,
            ["Fecha", "Nombre", "Categoría", "Monto"],
            lambda f: db.update_expense(
                int(f["id"]), f["Nombre"], f["Categoría"], int(f["Monto"]), f["Fecha"]
            ),
            db.delete_expense,
        )

# --- Ingresos ----------------------------------------------------------------------

with tab_ingresos:
    ingresos = db.incomes_df()
    if ingresos.empty:
        st.caption("Todavía no registras ingresos.")
    else:
        original = pd.DataFrame(
            {
                "id": ingresos["id"],
                "Fecha": pd.to_datetime(ingresos["date"]).dt.date,
                "Monto": ingresos["amount"],
                "Nota": ingresos["note"].fillna(""),
            }
        ).reset_index(drop=True)

        editado = st.data_editor(
            original,
            key="hi_editor",
            hide_index=True,
            width="stretch",
            num_rows="dynamic",
            column_config={
                "id": None,
                "Fecha": st.column_config.DateColumn(required=True),
                "Monto": st.column_config.NumberColumn(min_value=1, required=True),
                "Nota": st.column_config.TextColumn(),
            },
        )
        _guardar(
            "hi",
            original,
            editado,
            ["Fecha", "Monto", "Nota"],
            lambda f: db.update_income(
                int(f["id"]), f["Fecha"], int(f["Monto"]), str(f["Nota"] or "")
            ),
            db.delete_income,
        )
