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
    AlonzoMetadata,
    Metadata,
)

load_dotenv()

BLOCKFROST_PROJECT_ID = os.getenv("BLOCKFROST_PROJECT_ID")
TARGET_ADDRESS = os.getenv("TARGET_ADDRESS")

if not BLOCKFROST_PROJECT_ID or not TARGET_ADDRESS:
    print("❌ Error: BLOCKFROST_PROJECT_ID o TARGET_ADDRESS no configurados en .env")
    sys.exit(1)

# 1. Configurar contexto de red en Preprod
context = BlockFrostChainContext(
    project_id=BLOCKFROST_PROJECT_ID,
    base_url="https://cardano-preprod.blockfrost.io/api"
)

# 2. Cargar llaves criptográficas locales
key_dir = "keys"
skey_path = os.path.join(key_dir, "payment.skey")
vkey_path = os.path.join(key_dir, "payment.vkey")

if not os.path.exists(skey_path):
    print(f"❌ Error: No se encontró la llave privada en {skey_path}")
    sys.exit(1)

skey = PaymentSigningKey.load(skey_path)
vkey = PaymentVerificationKey.load(vkey_path)
my_address = Address(vkey.hash(), network=Network.TESTNET)


def actualizar_estado(remito_id, nuevo_estado, balance, ubicacion, auditor, parent_tx):
    print(f"\n🚀 Preparando actualización on-chain para Remito: {remito_id}")
    print(f"🔗 Parent TX: {parent_tx}")
    print(f"📍 Estado: {nuevo_estado} | Balance: {balance} | Ubicación: {ubicacion}")

    # Estructura CIP-20 (Label 674)
    msg_payload = [
        f"UPDATE-REMITO:{remito_id}",
        f"ESTADO:{nuevo_estado}",
        f"BALANCE:{balance}",
        f"UBICACION:{ubicacion}",
        f"AUDITOR:{auditor}",
        f"PARENT-TX:{parent_tx}"
    ]

    metadata_dict = {
        674: {
            "msg": msg_payload
        }
    }

    auxiliary_data = AuxiliaryData(
        data=AlonzoMetadata(
            metadata=Metadata(metadata_dict)
        )
    )

    # Construcción y firma de la transacción
    builder = TransactionBuilder(context)
    builder.add_input_address(my_address)
    builder.add_output(TransactionOutput(my_address, 1_000_000))  # 1 tADA de retorno
    builder.auxiliary_data = auxiliary_data

    signed_tx = builder.build_and_sign([skey], change_address=my_address)

    print("📦 Minando nuevo eslabón en Cardano Preprod...")
    tx_hash = context.submit_tx(signed_tx)

    print("\n✅ ¡Eslabón registrado con éxito!")
    print(f"🔑 Tx Hash: {tx_hash}")
    print(f"🔍 Cardanoscan: https://preprod.cardanoscan.io/transaction/{tx_hash}")
    return tx_hash


if __name__ == "__main__":
    print("=== REGISTRAR NUEVO ESLABÓN / ACTUALIZACIÓN ON-CHAIN ===")
    remito_id = input("ID de Remito [REM-2026-0827-NK]: ").strip() or "REM-2026-0827-NK"
    parent_tx = input("Parent Tx Hash (Hash del eslabón anterior): ").strip()
    
    if not parent_tx:
        print("❌ Error: Es obligatorio ingresar el Tx Hash previo para mantener la cadena de custodia.")
        sys.exit(1)

    nuevo_estado = input("Nuevo Estado [RECIBIDO_CONFORME / DISCREPANCIA_AUDITORIA]: ").strip() or "RECIBIDO_CONFORME"
    balance = input("Balance físico [ej. 500/500 (CONFORME) o 488/500 (DISCREPANCIA: -12 U)]: ").strip() or "500/500 (CONFORME)"
    ubicacion = input("Ubicación/Depósito [ej. Bahía 02 CABA Sur / Jaula Cuarentena]: ").strip() or "Bahía 02 CABA Sur"
    auditor = input("Auditor Responsable [ej. Claudio Bogado / Control Calidad]: ").strip() or "Claudio Bogado"

    actualizar_estado(remito_id, nuevo_estado, balance, ubicacion, auditor, parent_tx)