from datetime import date

import streamlit as st

import db
from utils import fmt

st.title("➕ Agregar")

tab_ingreso, tab_gasto, tab_compra = st.tabs(["💵 Ingreso", "🧾 Gasto", "💳 Compra"])

# --- Ingreso -----------------------------------------------------------------

with tab_ingreso:
    st.caption("Tu sueldo u otro ingreso del mes.")
    i_fecha = st.date_input("Fecha", value=date.today(), key="i_fecha")
    i_monto = st.number_input("Monto", min_value=0, step=1000, key="i_monto")
    i_nota = st.text_input("Nota (opcional)", placeholder="Sueldo, bono, etc.", key="i_nota")
    if st.button("Guardar ingreso", type="primary"):
        if i_monto <= 0:
            st.warning("El monto debe ser mayor que 0.")
        else:
            db.add_income(i_fecha, i_monto, i_nota)
            st.success(f"Ingreso de {fmt(i_monto)} guardado.")

# --- Gasto ---------------------------------------------------------------------

with tab_gasto:
    st.caption("Gastos del día a día: luz, agua, Steam, etc.")
    g_nombre = st.selectbox(
        "Nombre del gasto",
        options=db.expense_names(),
        index=None,
        accept_new_options=True,
        placeholder="Escribe para buscar o crear uno nuevo…",
        key="g_nombre",
    )
    g_categoria = st.selectbox(
        "Categoría",
        options=db.list_categories(),
        index=None,
        accept_new_options=True,
        placeholder="Escribe para buscar o crear una nueva…",
        key="g_categoria",
    )
    g_monto = st.number_input("Monto", min_value=0, step=100, key="g_monto")
    g_fecha = st.date_input("Fecha", value=date.today(), key="g_fecha")
    if st.button("Guardar gasto", type="primary"):
        if not g_nombre or not g_nombre.strip():
            st.warning("Falta el nombre del gasto.")
        elif not g_categoria or not g_categoria.strip():
            st.warning("Falta la categoría.")
        elif g_monto <= 0:
            st.warning("El monto debe ser mayor que 0.")
        else:
            db.add_expense(g_nombre, g_categoria, g_monto, g_fecha)
            st.success(f"Gasto «{g_nombre.strip()}» de {fmt(g_monto)} guardado.")

# --- Compra (con o sin cuotas) ---------------------------------------------------

with tab_compra:
    st.caption(
        "Compras con tarjeta. Con 1 cuota se paga completa ese mes; "
        "con más cuotas, cada mes se descuenta una hasta terminar."
    )
    c_comercio = st.selectbox(
        "Lugar de la compra",
        options=db.merchant_names(),
        index=None,
        accept_new_options=True,
        placeholder="Escribe para buscar o crear uno nuevo…",
        key="c_comercio",
    )
    c_categoria = st.selectbox(
        "Categoría",
        options=db.list_categories(),
        index=None,
        accept_new_options=True,
        placeholder="Escribe para buscar o crear una nueva…",
        key="c_categoria",
    )
    c_total = st.number_input("Monto total de la compra", min_value=0, step=1000, key="c_total")
    c_cuotas = st.number_input("Número de cuotas", min_value=1, max_value=60, value=1, step=1, key="c_cuotas")

    if c_cuotas > 1:
        sugerido = round(c_total / c_cuotas)
        # La key incluye total y cuotas: si cambian, el valor sugerido se recalcula,
        # pero una edición manual se conserva mientras no cambien.
        c_valor = st.number_input(
            "Valor de cada cuota",
            min_value=0,
            step=100,
            value=sugerido,
            key=f"c_valor_{c_total}_{c_cuotas}",
            help="Calculado como total ÷ cuotas. Edítalo si el banco cobra interés u otro cargo.",
        )
        if c_valor != sugerido:
            st.caption(
                f"Total en cuotas: {fmt(c_valor * c_cuotas)} "
                f"({fmt(c_valor * c_cuotas - c_total)} sobre el precio original)."
            )
    else:
        c_valor = c_total

    c_fecha = st.date_input("Fecha de la compra", value=date.today(), key="c_fecha")

    if st.button("Guardar compra", type="primary"):
        if not c_comercio or not c_comercio.strip():
            st.warning("Falta el lugar de la compra.")
        elif not c_categoria or not c_categoria.strip():
            st.warning("Falta la categoría.")
        elif c_total <= 0:
            st.warning("El monto debe ser mayor que 0.")
        elif c_cuotas > 1 and c_valor <= 0:
            st.warning("El valor de la cuota debe ser mayor que 0.")
        else:
            db.add_purchase(c_comercio, c_categoria, c_total, c_cuotas, c_valor, c_fecha)
            if c_cuotas > 1:
                st.success(
                    f"Compra en «{c_comercio.strip()}» guardada: "
                    f"{c_cuotas} cuotas de {fmt(c_valor)}."
                )
            else:
                st.success(f"Compra en «{c_comercio.strip()}» de {fmt(c_total)} guardada.")
