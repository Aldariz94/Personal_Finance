from datetime import date

import pandas as pd
import streamlit as st

import db
from utils import fmt

st.title("🏦 Ahorros")

cuentas = db.savings_accounts_df()

# --- Resumen de cuentas -------------------------------------------------------

if not cuentas.empty:
    st.metric("Total ahorrado", fmt(cuentas["balance"].sum()))
    tabla = pd.DataFrame(
        {
            "Nombre": cuentas["name"],
            "Banco": cuentas["bank"],
            "Ahorrado": cuentas["balance"].map(fmt),
        }
    )
    st.dataframe(tabla, hide_index=True, width="stretch")

st.divider()

tab_mover, tab_crear, tab_movimientos = st.tabs(
    ["💸 Depositar / Retirar", "➕ Crear ahorro", "📜 Movimientos"]
)

# --- Depositar / Retirar --------------------------------------------------------

with tab_mover:
    if cuentas.empty:
        st.caption("Primero crea un ahorro en la pestaña «Crear ahorro».")
    else:
        opciones = {
            f"{r['name']} — {r['bank']} ({fmt(r['balance'])})": r["id"]
            for _, r in cuentas.iterrows()
        }
        sel = st.selectbox("Ahorro", options=list(opciones), key="m_cuenta")
        cuenta_id = opciones[sel]
        m_monto = st.number_input("Monto", min_value=0, step=1000, key="m_monto")
        m_fecha = st.date_input("Fecha", value=date.today(), key="m_fecha")

        col_dep, col_ret = st.columns(2)
        if col_dep.button("Depositar", type="primary", width="stretch"):
            if m_monto <= 0:
                st.warning("El monto debe ser mayor que 0.")
            else:
                db.add_savings_movement(cuenta_id, m_fecha, m_monto, "deposito")
                st.success(f"Depósito de {fmt(m_monto)} guardado.")
                st.rerun()
        if col_ret.button("Retirar", width="stretch"):
            saldo = db.savings_balance(cuenta_id)
            if m_monto <= 0:
                st.warning("El monto debe ser mayor que 0.")
            elif m_monto > saldo:
                st.warning(f"No puedes retirar más de lo ahorrado ({fmt(saldo)}).")
            else:
                db.add_savings_movement(cuenta_id, m_fecha, m_monto, "retiro")
                st.success(f"Retiro de {fmt(m_monto)} guardado.")
                st.rerun()

        st.caption(
            "Lo que depositas se descuenta de «Te queda» en el dashboard ese mes; "
            "lo que retiras vuelve a estar disponible."
        )

# --- Crear ahorro -----------------------------------------------------------------

with tab_crear:
    a_nombre = st.text_input("Nombre del ahorro", placeholder="Vacaciones, Emergencias…", key="a_nombre")
    a_banco = st.text_input("Banco", placeholder="Banco Estado, Falabella…", key="a_banco")
    if st.button("Crear ahorro", type="primary"):
        if not a_nombre.strip():
            st.warning("Falta el nombre del ahorro.")
        elif not a_banco.strip():
            st.warning("Falta el banco.")
        else:
            db.add_savings_account(a_nombre, a_banco)
            st.success(f"Ahorro «{a_nombre.strip()}» creado.")
            st.rerun()

    if not cuentas.empty:
        with st.expander("🗑️ Eliminar un ahorro"):
            st.caption("Se borra la cuenta y todos sus movimientos. Esto no se puede deshacer.")
            opciones = {
                f"{r['name']} — {r['bank']} ({fmt(r['balance'])})": r["id"]
                for _, r in cuentas.iterrows()
            }
            sel = st.selectbox("Ahorro", options=list(opciones), index=None, key="a_del")
            if sel and st.button("Eliminar definitivamente", key="a_del_btn"):
                db.delete_savings_account(opciones[sel])
                st.rerun()

# --- Movimientos --------------------------------------------------------------------

with tab_movimientos:
    movs = db.savings_movements_df()
    if movs.empty:
        st.caption("Todavía no hay movimientos.")
    else:
        tabla = pd.DataFrame(
            {
                "Fecha": movs["date"],
                "Ahorro": movs["cuenta"],
                "Banco": movs["banco"],
                "Tipo": movs["kind"].map({"deposito": "Depósito ⬆️", "retiro": "Retiro ⬇️"}),
                "Monto": movs["amount"].map(fmt),
            }
        )
        st.dataframe(tabla, hide_index=True, width="stretch")
        with st.expander("🗑️ Eliminar un movimiento"):
            opciones = {
                f"{r['date']} — {r['cuenta']} — {r['kind']} {fmt(r['amount'])}": r["id"]
                for _, r in movs.iterrows()
            }
            sel = st.selectbox("Movimiento", options=list(opciones), index=None, key="mv_del")
            if sel and st.button("Eliminar definitivamente", key="mv_del_btn"):
                db.delete_savings_movement(opciones[sel])
                st.rerun()
