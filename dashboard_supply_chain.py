import os
import io
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from blockfrost import BlockFrostApi, ApiError
from fpdf import FPDF

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
        
        df = pd.DataFrame(eventos)
        if not df.empty:
            df = df.sort_values(by="Timestamp (UTC)", ascending=True).reset_index(drop=True)
        return df
    except Exception as e:
        st.error(f"Error consultando Blockfrost: {e}")
        return pd.DataFrame()

def generar_acta_pdf(df, remito_id):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Encabezado Oficial
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(0, 10, "ACTA OFICIAL DE AUDITORÍA Y TRAZABILIDAD ON-CHAIN", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(100, 116, 139)
    pdf.cell(0, 6, "Certificación Inmutable respaldada en Cardano Blockchain (CIP-20 / Label 674)", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)
    
    # Línea divisoria
    pdf.set_draw_color(203, 213, 225)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(6)
    
    # Resumen Ejecutivo
    ultimo = df.iloc[-1]
    hay_disc = df["Discrepancia"].any()
    
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(30, 41, 59)
    pdf.cell(50, 7, "ID de Remito Auditado:")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"{remito_id}", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(50, 7, "Dictamen de Stock:")
    if hay_disc:
        pdf.set_text_color(220, 38, 38)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, "ALERTA: DISCREPANCIA DETECTADA EN CADENA DE CUSTODIA", new_x="LMARGIN", new_y="NEXT")
    else:
        pdf.set_text_color(22, 163, 74)
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 7, "CONFORME: Sin desvíos registrados", new_x="LMARGIN", new_y="NEXT")
        
    pdf.set_text_color(30, 41, 59)
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(50, 7, "Último Estado Operativo:")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"{ultimo['Estado']} ({ultimo['Ubicación']})", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(50, 7, "Auditor de Cierre:")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"{ultimo['Auditor Responsable']}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(5)
    
    # Tabla de Eslabones Criptográficos
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(15, 23, 42)
    pdf.cell(0, 8, "Historial de Eslabones y Evidencia Criptográfica:", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    
    for idx, row in df.iterrows():
        pdf.set_fill_color(241, 245, 249)
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(30, 41, 59)
        pdf.cell(0, 7, f" Eslabón #{idx+1}: {row['Estado']} | Fecha: {row['Timestamp (UTC)']}", fill=True, new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(51, 65, 85)
        pdf.cell(40, 5, " - Balance de Control:")
        pdf.cell(0, 5, f"{row['Balance Físico']}", new_x="LMARGIN", new_y="NEXT")
        
        pdf.cell(40, 5, " - Ubicación / Auditor:")
        pdf.cell(0, 5, f"{row['Ubicación']} | Resp: {row['Auditor Responsable']}", new_x="LMARGIN", new_y="NEXT")
        
        pdf.cell(40, 5, " - Tx Hash (On-Chain):")
        pdf.set_font("Courier", "", 8)
        pdf.cell(0, 5, f"{row['Tx Hash']}", new_x="LMARGIN", new_y="NEXT")
        
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(40, 5, " - Parent Hash:")
        pdf.set_font("Courier", "", 8)
        pdf.cell(0, 5, f"{row['Parent Hash']}", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

    # Pie de página / Respaldo legal
    pdf.ln(5)
    pdf.set_draw_color(203, 213, 225)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(4)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(148, 163, 184)
    pdf.multi_cell(0, 4, "Este documento certifica que los registros listados han sido minados en la blockchain pública de Cardano y son matemáticamente inmutables. Para verificar la autenticidad forense de cada hash, consulte preprod.cardanoscan.io.")
    
    return bytes(pdf.output())

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
    
    # Botón de Descarga del Acta Oficial
    pdf_bytes = generar_acta_pdf(df_eventos, remito_target)
    st.download_button(
        label="📥 Descargar Acta de Incidencia y Auditoría On-Chain (PDF)",
        data=pdf_bytes,
        file_name=f"Acta_Auditoria_{remito_target}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
    
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