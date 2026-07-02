from datetime import date

import altair as alt
import pandas as pd
import streamlit as st

import db
from utils import CHART_COLOR, MESES, fmt, installment_number, last_installment_month, month_label

st.title("📊 Dashboard")

# --- Selector de mes -------------------------------------------------------

hoy = date.today()
col_mes, col_anio = st.columns([2, 1])
mes = col_mes.selectbox("Mes", range(1, 13), index=hoy.month - 1, format_func=lambda m: MESES[m - 1])
anio = col_anio.number_input("Año", min_value=2000, max_value=2100, value=hoy.year, step=1)

# --- Datos del mes ---------------------------------------------------------

ym = f"{anio:04d}-{mes:02d}"

incomes = db.incomes_df()
ingresos_mes = incomes[incomes["date"].str.startswith(ym)]["amount"].sum()

expenses = db.expenses_df()
gastos_mes = expenses[expenses["date"].str.startswith(ym)]

purchases = db.purchases_df()
purchases["cuota_n"] = purchases.apply(
    lambda p: installment_number(p["date"], p["installments"], anio, mes), axis=1
)
cuotas_mes = purchases[purchases["cuota_n"].notna()].copy()

total_gastos = gastos_mes["amount"].sum() + cuotas_mes["installment_value"].sum()

movs = db.savings_movements_df()
movs_mes = movs[movs["date"].str.startswith(ym)]
ahorro_mes = (
    movs_mes[movs_mes["kind"] == "deposito"]["amount"].sum()
    - movs_mes[movs_mes["kind"] == "retiro"]["amount"].sum()
)

te_queda = ingresos_mes - total_gastos - ahorro_mes

# --- KPIs -------------------------------------------------------------------

c1, c2, c3, c4 = st.columns(4)
c1.metric("Ingresos del mes", fmt(ingresos_mes))
c2.metric("Gastos del mes", fmt(total_gastos))
c3.metric(
    "Ahorro del mes",
    fmt(ahorro_mes),
    delta="retiraste de tus ahorros" if ahorro_mes < 0 else None,
    delta_color="off",
    help="Depósitos menos retiros de tus ahorros en el mes.",
)
c4.metric(
    "Te queda",
    fmt(te_queda),
    delta=f"{te_queda / ingresos_mes:.0%} de tus ingresos" if ingresos_mes else None,
    delta_color="normal" if te_queda >= 0 else "inverse",
)

if te_queda < 0:
    st.error("Este mes gastas más de lo que ingresa.")

st.divider()

# --- Desglose por categoría --------------------------------------------------

col_izq, col_der = st.columns(2)

with col_izq:
    st.subheader("Gasto por categoría")
    por_cat = pd.concat(
        [
            gastos_mes[["categoria", "amount"]],
            cuotas_mes[["categoria", "installment_value"]].rename(
                columns={"installment_value": "amount"}
            ),
        ]
    )
    if por_cat.empty:
        st.caption("Sin gastos este mes.")
    else:
        resumen = (
            por_cat.groupby("categoria", as_index=False)["amount"]
            .sum()
            .sort_values("amount", ascending=False)
        )
        resumen["etiqueta"] = resumen["amount"].map(fmt)
        barras = (
            alt.Chart(resumen)
            .mark_bar(color=CHART_COLOR, cornerRadiusEnd=4)
            .encode(
                x=alt.X("amount:Q", axis=None),
                y=alt.Y("categoria:N", sort="-x", title=None,
                        axis=alt.Axis(labelLimit=200), scale=alt.Scale(paddingInner=0.25)),
                tooltip=[
                    alt.Tooltip("categoria:N", title="Categoría"),
                    alt.Tooltip("etiqueta:N", title="Total"),
                ],
            )
        )
        etiquetas = barras.mark_text(align="left", dx=6, color="#C3C2B7").encode(
            text="etiqueta:N"
        )
        st.altair_chart(
            (barras + etiquetas)
            .properties(height=alt.Step(38))
            .configure_view(stroke=None),
            use_container_width=True,
        )

with col_der:
    st.subheader("Cuotas activas este mes")
    if cuotas_mes.empty:
        st.caption("No tienes cuotas que pagar este mes.")
    else:
        tabla = pd.DataFrame(
            {
                "Comercio": cuotas_mes["merchant"],
                "Cuota": cuotas_mes.apply(
                    lambda p: f"{int(p['cuota_n'])} de {p['installments']}", axis=1
                ),
                "Valor cuota": cuotas_mes["installment_value"].map(fmt),
                "Falta pagar": cuotas_mes.apply(
                    lambda p: fmt(
                        (p["installments"] - int(p["cuota_n"])) * p["installment_value"]
                    ),
                    axis=1,
                ),
                "Última cuota": cuotas_mes.apply(
                    lambda p: month_label(*last_installment_month(p["date"], p["installments"])),
                    axis=1,
                ),
            }
        )
        st.dataframe(tabla, hide_index=True, width="stretch")
        st.caption(
            f"Total en cuotas este mes: **{fmt(cuotas_mes['installment_value'].sum())}**"
        )
