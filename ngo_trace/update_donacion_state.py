import os
import sys
from dotenv import load_dotenv
from pycardano import (
    BlockFrostChainContext,
    Network,
    PaymentSigningKey,
    PaymentVerificationKey,
    Address,
    TransactionBuilder,
    TransactionOutput,
    AuxiliaryData,
    Metadata
)

# Configurar path e importar persistencia
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import guardar_evento, obtener_ultimo_hash

# 1. Conectividad Cardano Preprod
load_dotenv()
BLOCKFROST_PROJECT_ID = os.getenv("BLOCKFROST_PROJECT_ID")

if not BLOCKFROST_PROJECT_ID:
    raise ValueError("No se encontro BLOCKFROST_PROJECT_ID en el archivo .env")

context = BlockFrostChainContext(
    project_id=BLOCKFROST_PROJECT_ID,
    base_url="https://cardano-preprod.blockfrost.io/api"
)

# 2. Credenciales
skey_path = "keys/backend_payment.skey"
vkey_path = "keys/backend_payment.vkey"

payment_skey = PaymentSigningKey.load(skey_path)
payment_vkey = PaymentVerificationKey.load(vkey_path)
my_address = Address(payment_vkey.hash(), network=Network.TESTNET)


def actualizar_estado_donacion(
    donacion_id: str,
    nuevo_estado: str,
    balance: str,
    ubicacion: str,
    auditor: str
):
    print(f"\n🔄 Actualizando cadena de custodia para: {donacion_id}...")

    # Recuperar hash anterior de SQLite
    parent_tx = obtener_ultimo_hash(donacion_id)
    print(f"🔗 Enlazando con Parent Tx Hash: {parent_tx}")

    # Construccion segura CIP-20 (estricto <= 64 bytes por elemento)
    msg_cip20 = [
        "protocol: ONG_TRACE_V1",
        f"donacion_id: {donacion_id}",
        f"estado: {nuevo_estado}",
        f"balance: {balance}",
        f"ubicacion: {ubicacion}",
        f"auditor: {auditor}"
    ]

    # Si es un hash de 64 caracteres, se divide en dos fragmentos de 32 bytes
    if len(parent_tx) > 50:
        msg_cip20.append(f"parent_tx_1: {parent_tx[:32]}")
        msg_cip20.append(f"parent_tx_2: {parent_tx[32:]}")
    else:
        msg_cip20.append(f"parent_tx: {parent_tx}")

    metadata_payload = {
        674: {
            "msg": msg_cip20
        }
    }
    auxiliary_data = AuxiliaryData(data=Metadata(metadata_payload))

    # Transaccion minima on-chain
    tx_builder = TransactionBuilder(context)
    tx_builder.add_input_address(my_address)
    tx_builder.add_output(TransactionOutput(my_address, 1_500_000))
    tx_builder.auxiliary_data = auxiliary_data

    signed_tx = tx_builder.build_and_sign(
        signing_keys=[payment_skey],
        change_address=my_address
    )

    print("🚀 Minando nuevo eslabón en Cardano Preprod...")
    context.submit_tx(signed_tx)
    tx_hash = str(signed_tx.id)

    # Persistir en SQLite
    guardar_evento(
        donacion_id=donacion_id,
        estado=nuevo_estado,
        balance=balance,
        ubicacion=ubicacion,
        auditor=auditor,
        tx_hash=tx_hash,
        parent_tx=parent_tx
    )

    print("\n✅ Eslabón sellado con éxito!")
    print(f"📄 Tx Hash: {tx_hash}")
    print(f"🔍 Explorer: https://preprod.cardanoscan.io/transaction/{tx_hash}")
    return tx_hash


if __name__ == "__main__":
    actualizar_estado_donacion(
        donacion_id="DON-2026-BUE-01",
        nuevo_estado="ENTREGA_CONFORME",
        balance="96 KITS ENTREGADOS (DISTRIBUCION FINAL)",
        ubicacion="Comedor Comunitario",
        auditor="Coordinacion Vecinal"
    )