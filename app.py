import streamlit as st

from db import init_db

st.set_page_config(page_title="Mis Finanzas", page_icon="💰", layout="wide")

init_db()

pages = [
    st.Page("views/dashboard.py", title="Dashboard", icon="📊", default=True),
    st.Page("views/agregar.py", title="Agregar", icon="➕"),
    st.Page("views/ahorros.py", title="Ahorros", icon="🏦"),
    st.Page("views/historial.py", title="Historial", icon="📜"),
    st.Page("views/categorias.py", title="Categorías", icon="🏷️"),
]

st.navigation(pages).run()
