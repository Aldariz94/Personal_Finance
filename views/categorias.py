import streamlit as st

import db

st.title("🏷️ Categorías")

st.caption(
    "Las categorías también se crean solas al escribir una nueva "
    "cuando agregas un gasto o una compra."
)

col_input, col_btn = st.columns([3, 1], vertical_alignment="bottom")
nueva = col_input.text_input("Nueva categoría", placeholder="Supermercado, Servicios, Entretenimiento…")
if col_btn.button("Agregar", type="primary"):
    if nueva.strip():
        db.get_or_create_category(nueva)
        st.rerun()
    else:
        st.warning("Escribe un nombre.")

st.divider()

uso = db.category_usage()
if uso.empty:
    st.caption("Todavía no tienes categorías.")
else:
    tabla = uso.rename(
        columns={"categoria": "Categoría", "gastos": "Gastos", "compras": "Compras"}
    )[["Categoría", "Gastos", "Compras"]]
    st.dataframe(tabla, hide_index=True, width="stretch")

    sin_uso = uso[(uso["gastos"] == 0) & (uso["compras"] == 0)]
    if not sin_uso.empty:
        with st.expander("🗑️ Eliminar una categoría sin uso"):
            opciones = {r["categoria"]: r["id"] for _, r in sin_uso.iterrows()}
            sel = st.selectbox("Categoría", options=list(opciones), index=None)
            if sel and st.button("Eliminar definitivamente"):
                db.delete_category(opciones[sel])
                st.rerun()
