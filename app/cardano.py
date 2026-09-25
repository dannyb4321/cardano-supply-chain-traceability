import os
import datetime
from pathlib import Path
from dotenv import load_dotenv
from pycardano import (
    BlockFrostChainContext,
    Network,
    PaymentSigningKey,
    PaymentVerificationKey,
    Address,
    TransactionBuilder,
    TransactionOutput,
    CBORMetadata,
    Metadata,
)

# Cargar variables de entorno (.env)
load_dotenv()

BLOCKFROST_PROJECT_ID = os.getenv("BLOCKFROST_PROJECT_ID")
if not BLOCKFROST_PROJECT_ID:
    raise ValueError("Falta configurar BLOCKFROST_PROJECT_ID en el archivo .env")

# Contexto de red en Cardano Preprod
context = BlockFrostChainContext(
    project_id=BLOCKFROST_PROJECT_ID,
    base_url="https://cardano-preprod.blockfrost.io/api/v0",
)

# Localización de las llaves en keys/
BASE_DIR = Path(__file__).resolve().parent.parent
SKEY_PATH = BASE_DIR / "keys" / "backend_payment.skey"

if not SKEY_PATH.exists():
    raise FileNotFoundError(f"No se encontró la llave privada en: {SKEY_PATH}")

signing_key = PaymentSigningKey.load(str(SKEY_PATH))
verification_key = PaymentVerificationKey.from_signing_key(signing_key)
backend_address = Address(payment_part=verification_key.hash(), network=Network.TESTNET)


def get_backend_wallet_status() -> dict:
    """Verifica el estado y balance disponible de la billetera en Preprod."""
    utxos = context.utxos(backend_address)
    lovelace_total = sum(u.output.amount.coin for u in utxos)
    ada_balance = lovelace_total / 1_000_000

    return {
        "status": "online",
        "network": "Cardano Preprod (Testnet)",
        "address": str(backend_address),
        "ada_balance": ada_balance,
        "utxo_count": len(utxos),
    }


def publish_cip20_event(payload_data: dict) -> str:
    """
    Construye, firma con backend_payment.skey y despacha una transacción
    con metadatos CIP-20 (Label 674) hacia la blockchain.
    """
    builder = TransactionBuilder(context)
    builder.add_input_address(backend_address)

    # Envío de vuelta a la propia dirección para retener fondos (solo consume la tarifa de red)
    builder.add_output(TransactionOutput(backend_address, 1_500_000))

    # Formateo de metadatos CIP-20 (Label 674)
    metadata_dict = {
        674: {
            "msg": [
                f"ID:{payload_data.get('remito_id')}",
                f"ST:{payload_data.get('estado')}",
                f"LOC:{payload_data.get('ubicacion')}",
                f"AUD:{payload_data.get('auditor')}",
                f"TS:{datetime.datetime.now(datetime.timezone.utc).isoformat()}",
            ]
        }
    }

    if "parent_tx_hash" in payload_data and payload_data["parent_tx_hash"]:
        metadata_dict[674]["parent_tx"] = payload_data["parent_tx_hash"]

    builder.auxiliary_data = Metadata(CBORMetadata(metadata_dict))

    # Construir, firmar y enviar
    signed_tx = builder.build_and_sign([signing_key], change_address=backend_address)
    context.submit_tx(signed_tx)

    return str(signed_tx.id)


def fetch_remito_history(remito_id: str) -> list:
    """
    Consulta a Blockfrost para reconstruir la trazabilidad del remito mediante label 674.
    """
    import requests

    headers = {"project_id": BLOCKFROST_PROJECT_ID}
    url = f"https://cardano-preprod.blockfrost.io/api/v0/metadata/txs/labels/674?count=50&order=desc"
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return []

    events = []
    for entry in response.json():
        tx_hash = entry.get("tx_hash")
        json_meta = entry.get("json_metadata", {})

        # Si el metadato coincide con el remito buscado
        raw_msg = str(json_meta)
        if remito_id in raw_msg:
            events.append({
                "tx_hash": tx_hash,
                "metadata": json_meta,
            })

    return events