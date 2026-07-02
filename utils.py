"""Helpers compartidos: formato de moneda y aritmética de meses."""

from datetime import date

MESES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
]

# Un solo tono para las barras del dashboard (validado sobre superficie oscura)
CHART_COLOR = "#4C8BF5"
# Gris azulado para las etiquetas de valor junto a las barras
LABEL_COLOR = "#AEB9CE"


def fmt(amount):
    """$1.234.567 — separador de miles con punto, sin decimales."""
    return "$" + f"{amount:,.0f}".replace(",", ".")


def month_index(year, month):
    return year * 12 + month


def installment_number(purchase_date_iso, installments, year, month):
    """Número de cuota (desde 1) que corresponde pagar en (year, month).

    Devuelve None si la compra aún no empieza o ya está pagada en ese mes.
    La cuota 1 se paga el mes de la compra.
    """
    d = date.fromisoformat(purchase_date_iso)
    k = month_index(year, month) - month_index(d.year, d.month)
    if 0 <= k < installments:
        return k + 1
    return None


def last_installment_month(purchase_date_iso, installments):
    """(year, month) de la última cuota."""
    d = date.fromisoformat(purchase_date_iso)
    idx = month_index(d.year, d.month) + installments - 1
    return (idx - 1) // 12, (idx - 1) % 12 + 1


def month_label(year, month):
    return f"{MESES[month - 1]} {year}"
