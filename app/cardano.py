import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from blockfrost import BlockFrostApi
from pycardano import (
    BlockFrostChainContext,
    PaymentSigningKey,
    PaymentVerificationKey,
    Address,
    Network,
    TransactionBuilder,
    TransactionOutput,
    AuxiliaryData,
    Metadata,
)

load_dotenv()
BLOCKFROST_PROJECT_ID = os.getenv("BLOCKFROST_PROJECT_ID")

if not BLOCKFROST_PROJECT_ID:
    raise RuntimeError("BLOCKFROST_PROJECT_ID no está configurado en el archivo .env")

# Contexto de red para construir transacciones y cliente API para consultas
context = BlockFrostChainContext(
    project_id=BLOCKFROST_PROJECT_ID,
    base_url="https://cardano-preprod.blockfrost.io/api"
)
blockfrost_client = BlockFrostApi(
    project_id=BLOCKFROST_PROJECT_ID,
    base_url="https://cardano-preprod.blockfrost.io/api"
)


def get_backend_address() -> Address:
    """Carga la clave pública del backend y retorna su dirección Preprod."""
    vkey_path = os.path.join("keys", "backend_payment.vkey")
    vkey = PaymentVerificationKey.load(vkey_path)
    return Address(vkey.hash(), network=Network.TESTNET)


def submit_event_onchain(event_data: dict) -> str:
    """
    Construye, firma con la skey del backend y somete una transacción en Cardano Preprod
    con metadatos CIP-20 (Label 674).
    """
    skey_path = os.path.join("keys", "backend_payment.skey")
    if not os.path.exists(skey_path):
        raise FileNotFoundError(f"No se encontró la clave privada en: {skey_path}")

    skey = PaymentSigningKey.load(skey_path)
    my_address = get_backend_address()

    # Construcción de la transacción: auto-envío de 1.5 tADA para registrar metadatos
    builder = TransactionBuilder(context)
    builder.add_input_address(my_address)
    builder.add_output(TransactionOutput(my_address, 1_500_000))

    # Formateo estricto CIP-20 (Label 674)
    msg_lines = [
        f"remito_id: {event_data['remito_id']}",
        f"estado: {event_data['estado']}",
        f"balance: {event_data['balance']}",
        f"ubicacion: {event_data['ubicacion']}",
        f"auditor: {event_data['auditor']}",
        f"parent_tx: {event_data.get('parent_tx_hash') or 'GENESIS'}"
    ]

    metadata = {674: {"msg": msg_lines}}
    builder.auxiliary_data = AuxiliaryData(data=Metadata(metadata))

    # Firma y propagación
    signed_tx = builder.build_and_sign([skey], change_address=my_address)
    context.submit_tx(signed_tx)

    return str(signed_tx.id)


def get_traceability_onchain(remito_id: str) -> list:
    """
    Audita las transacciones de la dirección logística en Blockfrost,
    decodifica el label 674 y reconstruye la cadena de custodia.
    """
    my_address = str(get_backend_address())
    txs = blockfrost_client.address_transactions(my_address, order="asc")
    cadena = []

    for tx in txs:
        tx_hash = tx.tx_hash
        try:
            metas = blockfrost_client.transaction_metadata(tx_hash)
        except Exception:
            continue

        for m in metas:
            if str(m.label) == "674":
                raw = m.json_metadata
                data = {}

                if isinstance(raw, dict):
                    if "msg" in raw and isinstance(raw["msg"], list):
                        for line in raw["msg"]:
                            if isinstance(line, str) and ":" in line:
                                k, v = line.split(":", 1)
                                data[k.strip().lower()] = v.strip()
                    else:
                        for k, v in raw.items():
                            data[str(k).strip().lower()] = str(v).strip()

                target = data.get("remito_id") or data.get("remito")
                if target and str(remito_id).strip().upper() in str(target).upper():
                    ts = str(pd.to_datetime(tx.block_time, unit="s")) if tx.block_time else "Pendiente"
                    cadena.append({
                        "timestamp_utc": ts,
                        "estado": data.get("estado", "N/A"),
                        "balance": data.get("balance", "N/A"),
                        "ubicacion": data.get("ubicacion") or data.get("deposito") or "N/A",
                        "auditor": data.get("auditor") or data.get("responsable") or "N/A",
                        "tx_hash": tx_hash,
                        "parent_tx_hash": data.get("parent_tx_hash") or data.get("parent_tx") or "GENESIS"
                    })

    return cadena