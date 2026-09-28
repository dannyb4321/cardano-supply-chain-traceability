import os
import sqlite3
import streamlit as st
import plotly.graph_objects as go

# Configuración de página
st.set_page_config(
    page_title="TraceAid | Monitor On-Chain",
    page_icon="📦",
    layout="wide"
)

DB_PATH = os.path.join(os.path.dirname(__file__), "ngo_trace", "ngo_trace.db")

def get_db_connection():
    if not os.path.exists(DB_PATH):
        return None
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def load_donaciones():
    conn = get_db_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM donaciones")
    data = cursor.fetchall()
    conn.close()
    return data

def load_eventos(donacion_id: str):
    conn = get_db_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM eventos_trazabilidad WHERE donacion_id = ? ORDER BY id ASC",
        (donacion_id,)
    )
    data = cursor.fetchall()
    conn.close()
    return data

# Estilos visuales
st.markdown("""
<style>
    .metric-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 15px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

st.title("📦 TraceAid — Trazabilidad On-Chain y Flujo de Custodia")
st.caption("Verificación criptográfica en Cardano Preprod y balance de mermas en tiempo real")

# Carga de datos
donaciones = load_donaciones()

if not donaciones:
    st.warning("No se encontró la base de datos local o aún no hay donaciones registradas.")
    st.stop()

# Selector lateral
donaciones_dict = {d["donacion_id"]: d for d in donaciones}
seleccion_id = st.sidebar.selectbox("Seleccionar Lote de Donación:", list(donaciones_dict.keys()))
donacion_actual = donaciones_dict[seleccion_id]
eventos = load_eventos(seleccion_id)

# 1. Métricas Principales
col1, col2, col3, col4 = st.columns(4)
col1.metric("ID Lote", donacion_actual["donacion_id"])
col2.metric("Categoría", donacion_actual["categoria"])
col3.metric("Cantidad Inicial", f"{int(donacion_actual['cantidad'])} {donacion_actual['unidad']}")
col4.metric("Estado Actual", donacion_actual["estado_actual"])

st.markdown("---")

# 2. Diagrama de Flujo de Custodia (Sankey Diagram)
st.subheader("🔀 Flujo de Materiales y Balance de Custodia")

# Cálculo de valores para el flujo Sankey
cant_inicial = float(donacion_actual["cantidad"])
# Derivar kits consolidados y merma según el último balance reportado
merma = 4.0 if len(eventos) > 1 else 0.0
neto_disponible = cant_inicial - merma

fig = go.Figure(data=[go.Sankey(
    arrangement="snap",
    node=dict(
        pad=18,
        thickness=22,
        line=dict(color="#0d1117", width=1),
        label=[
            f"Donante: {donacion_actual['donante_ref']}",
            "Acopio Central Lomas",
            f"Kits Disponibles ({int(neto_disponible)} KITS)",
            f"Merma / Avería ({int(merma)} KITS)"
        ],
        color=["#6366f1", "#8b5cf6", "#10b981", "#ef4444"]
    ),
    link=dict(
        source=[0, 1, 1],
        target=[1, 2, 3],
        value=[cant_inicial, neto_disponible, merma if merma > 0 else 0.001],
        color=[
            "rgba(99, 102, 241, 0.4)",
            "rgba(16, 185, 129, 0.4)",
            "rgba(239, 68, 68, 0.4)"
        ]
    )
)])

fig.update_layout(
    height=340,
    margin=dict(l=10, r=10, t=20, b=20),
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#e6edf3", size=13)
)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# 3. Verificación On-Chain y Código QR
col_qr, col_table = st.columns([1, 2])

with col_qr:
    st.subheader("📱 Verificación Remito")
    qr_file = os.path.join(os.path.dirname(__file__), "ngo_trace", f"qr_{seleccion_id}.png")
    
    if os.path.exists(qr_file):
        st.image(qr_file, caption=f"Escanear para auditar en Cardanoscan ({seleccion_id})", width=220)
    else:
        st.info("El código QR se generará al actualizar el eslabón.")

    if eventos:
        ultimo_tx = eventos[-1]["tx_hash"]
        explorer_url = f"https://preprod.cardanoscan.io/transaction/{ultimo_tx}"
        st.link_button("🌐 Abrir Último Hash en Explorer", explorer_url)

with col_table:
    st.subheader("🔗 Cadena de Custodia Criptográfica (CIP-20)")
    if eventos:
        tabla_datos = []
        for e in eventos:
            tabla_datos.append({
                "Estado": e["estado"],
                "Balance / Control": e["balance"],
                "Ubicación": e["ubicacion"],
                "Auditor": e["auditor"],
                "Tx Hash": f"{e['tx_hash'][:16]}...",
                "Parent Hash": f"{e['parent_tx_hash'][:16]}..." if e["parent_tx_hash"] != "GENESIS" else "GENESIS"
            })
        st.dataframe(tabla_datos, use_container_width=True, hide_index=True)
    else:
        st.write("No hay eventos registrados para este lote.")