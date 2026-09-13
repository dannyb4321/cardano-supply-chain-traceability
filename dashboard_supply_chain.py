import os
from ngo_trace.services import TraceabilityService
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="NGO Chain Traceability", layout="wide", page_icon="📦"
)

DB_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "ngo_trace", "ngo_trace.db"
)
service = TraceabilityService(DB_PATH)

st.title("📦 Trazabilidad de Donaciones en Cardano")
st.caption(
    "Auditoría on-chain en tiempo real con modelo eUTxO y desacoplamiento de dominio"
)

donaciones = service.listar_donaciones()
if not donaciones:
    st.warning("No hay donaciones registradas en la base local.")
    st.stop()

# Selector de lote
ids = [d.donacion_id for d in donaciones]
lote_id = st.selectbox("Seleccionar Lote de Donación:", ids)
donacion = service.obtener_donacion(lote_id)
eventos = service.obtener_eventos(lote_id)
cadena_integra = service.verificar_integridad_cadena(lote_id)

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Categoría", donacion.categoria)
col2.metric("Cantidad Inicial", f"{donacion.cantidad} {donacion.unidad}")
col3.metric("Donante", donacion.donante_ref)
col4.metric("Estado Actual", donacion.estado_actual.value)
col5.metric("Integridad Cripto", "100% VÁLIDA" if cadena_integra else "ROTA")

st.divider()

# --- FLUJO DINÁMICO SANKEY ---
st.subheader("🌊 Flujo Físico y Balance de Custodia (Sankey Dinámico)")
labels, sources, targets, values = service.calcular_balance_sankey(lote_id)

fig = go.Figure(
    data=[
        go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=labels,
                color=["#6366f1", "#3b82f6", "#10b981", "#ef4444"],
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
                color=[
                    "rgba(99, 102, 241, 0.4)",
                    "rgba(16, 185, 129, 0.4)",
                    "rgba(239, 68, 68, 0.4)",
                ],
            ),
        )
    ]
)
fig.update_layout(height=320, margin=dict(l=10, r=10, t=25, b=10))
st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- HISTORIAL ON-CHAIN ---
st.subheader("⛓️ Cadena de Custodia Criptográfica (Cardano Preprod)")
for ev in eventos:
    with st.expander(
        f"📌 {ev.estado.value} — {ev.ubicacion}",
        expanded=True,
    ):
        st.write(f"**Auditor:** `{ev.auditor}` | **Balance:** `{ev.balance}`")
        st.code(
            f"Parent Tx: {ev.parent_tx_hash}\nCurrent Tx: {ev.tx_hash}",
            language="text",
        )
        st.markdown(
            f"[🔍 Ver Transacción en Cardanoscan](https://preprod.cardanoscan.io/transaction/{ev.tx_hash})"
        )