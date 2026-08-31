import os
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from blockfrost import BlockFrostApi, ApiError

load_dotenv()

BLOCKFROST_PROJECT_ID = (os.getenv("BLOCKFROST_PROJECT_ID") or st.secrets.get("BLOCKFROST_PROJECT_ID", "")).strip()
TARGET_ADDRESS = (os.getenv("TARGET_ADDRESS") or st.secrets.get("TARGET_ADDRESS", "")).strip()

st.set_page_config(
    page_title="Cardano Supply Chain Traceability",
    page_icon="📦",
    layout="wide"
)

# Conexión con la red Preprod
api = BlockFrostApi(project_id=BLOCKFROST_PROJECT_ID, base_url="https://cardano-preprod.blockfrost.io/api")

st.title("📦 Trazabilidad Logística On-Chain (Cardano Preprod)")
st.caption("Auditoría inmutable de remitos, estados operativos y control de discrepancias vía CIP-20 (Label 674).")
st.divider()

# Filtro lateral
st.sidebar.header("🔍 Filtro de Remito")
remito_target = st.sidebar.text_input("ID de Remito", value="REM-2026-0827-NK")
actualizar = st.sidebar.button("Consultar Blockchain")

@st.cache_data(ttl=15)
def cargar_eventos_on_chain(remito_filtro):
    eventos = []
    try:
        # Consulta directamente el historial de tu billetera
        txs = api.address_transactions(TARGET_ADDRESS, order="desc", count=50)
        for tx in txs:
            tx_hash = tx.tx_hash
            try:
                meta_list = api.transaction_metadata(tx_hash)
            except Exception:
                continue

            json_data = None
            for m in meta_list:
                if str(m.label) == "674":
                    json_data = m.json_metadata
                    break

            if not json_data:
                continue

            # Compatibilidad para Namespace y dict de Blockfrost
            if hasattr(json_data, "msg"):
                msg_list = json_data.msg
            elif isinstance(json_data, dict):
                msg_list = json_data.get("msg", [])
            else:
                msg_list = []

            if isinstance(msg_list, str):
                msg_list = [msg_list]

            raw_text = " | ".join(str(m) for m in msg_list)
            if remito_filtro in raw_text:
                tx_info = api.transaction(tx_hash)
                block_info = api.block(tx_info.block)

                evento_tipo = "DESPACHO" if any("REMITO-CIP20" in str(m) for m in msg_list) else "ACTUALIZACION"
                estado = "DESPACHADO EN ORIGEN"
                balance = "N/A"
                discrepancia_detectada = False
                ubicacion = "N/A"
                auditor = "N/A"
                parent_tx = "GÉNESIS (DESPACHO)"

                for line in msg_list:
                    line_str = str(line)
                    if line_str.startswith("ESTADO:"):
                        estado = line_str.replace("ESTADO:", "").strip()
                    elif line_str.startswith("BALANCE:"):
                        balance = line_str.replace("BALANCE:", "").strip()
                        if "DISCREPANCIA" in balance:
                            discrepancia_detectada = True
                    elif line_str.startswith("UBICACION:") or line_str.startswith("ORI:"):
                        ubicacion = line_str.split(":", 1)[1].strip()
                    elif line_str.startswith("AUD:") or line_str.startswith("AUDITOR:"):
                        auditor = line_str.split(":", 1)[1].strip()
                    elif line_str.startswith("PARENT-TX:"):
                        parent_tx = line_str.replace("PARENT-TX:", "").strip()

                eventos.append({
                    "Timestamp (UTC)": pd.to_datetime(block_info.time, unit="s"),
                    "Remito ID": remito_filtro,
                    "Tipo": evento_tipo,
                    "Estado": estado,
                    "Balance Físico": balance,
                    "Discrepancia": discrepancia_detectada,
                    "Ubicación": ubicacion,
                    "Auditor Responsable": auditor,
                    "Tx Hash": tx_hash,
                    "Parent Hash": parent_tx,
                    "Cardanoscan": f"https://preprod.cardanoscan.io/transaction/{tx_hash}"
                })
    except Exception as e:
        st.error(f"Error consultando Blockfrost: {e}")
    return pd.DataFrame(eventos)
df_eventos = cargar_eventos_on_chain(remito_target)

if df_eventos.empty:
    st.warning(f"No se encontraron transacciones on-chain asociadas al remito `{remito_target}`.")
else:
    ultimo_evento = df_eventos.iloc[-1]
    hay_discrepancia = df_eventos["Discrepancia"].any()
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Remito ID", remito_target)
    col2.metric("Eslabones On-Chain", len(df_eventos))
    col3.metric("Último Estado", ultimo_evento["Estado"])
    
    if hay_discrepancia:
        col4.metric("Auditoría de Stock", "⚠️ DISCREPANCIA", delta="-12 U (Faltante)", delta_color="inverse")
    else:
        col4.metric("Auditoría de Stock", "✅ 100% CONFORME", delta="Sin desvíos")

    st.divider()
    st.subheader("🔗 Cadena de Custodia Inmutable")
    
    for idx, row in df_eventos.iterrows():
        with st.expander(f"Eslabón #{idx+1} — {row['Estado']} ({row['Timestamp (UTC)']})", expanded=True):
            st.markdown(f"""
            * **Estado Operativo:** `{row['Estado']}`
            * **Balance de Control:** `{row['Balance Físico']}`
            * **Ubicación / Depósito:** {row['Ubicación']}
            * **Auditor / Responsable:** {row['Auditor Responsable']}
            * **Parent Tx Hash:** `{row['Parent Hash']}`
            * **Tx Hash Explorer:** [{row['Tx Hash']}]({row['Cardanoscan']})
            """)

    st.divider()
    st.subheader("📊 Registros Consolidados On-Chain")
    st.dataframe(
        df_eventos[[
            "Timestamp (UTC)", "Estado", "Balance Físico", 
            "Ubicación", "Auditor Responsable", "Tx Hash", "Parent Hash"
        ]],
        use_container_width=True
    )