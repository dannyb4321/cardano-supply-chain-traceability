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

# Permitir imports relativos del modulo ngo_trace
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from models import DonacionCreacion, EventoTrazabilidad
from database import registrar_donacion, guardar_evento, obtener_ultimo_hash

# 1. Configuración de Entorno y Conectividad
load_dotenv()
BLOCKFROST_PROJECT_ID = os.getenv("BLOCKFROST_PROJECT_ID")

if not BLOCKFROST_PROJECT_ID:
    raise ValueError("No se encontró BLOCKFROST_PROJECT_ID en el archivo .env")

context = BlockFrostChainContext(
    project_id=BLOCKFROST_PROJECT_ID,
    base_url="https://cardano-preprod.blockfrost.io/api"
)

# 2. Carga de Credenciales Criptográficas
skey_path = "keys/backend_payment.skey"
vkey_path = "keys/backend_payment.vkey"

if not os.path.exists(skey_path) or not os.path.exists(vkey_path):
    raise FileNotFoundError("Faltan las llaves en el directorio 'keys/'")

payment_skey = PaymentSigningKey.load(skey_path)
payment_vkey = PaymentVerificationKey.load(vkey_path)
my_address = Address(payment_vkey.hash(), network=Network.TESTNET)


def despachar_donacion_on_chain(
    donacion_id: str,
    categoria: str,
    cantidad: float,
    unidad: str,
    ubicacion: str,
    auditor: str,
    donante_ref: str = "EMPRESA_DONANTE_A"
):
    print(f"\n📦 Registrando donación localmente: {donacion_id}...")
    # 1. Registro en SQLite local
    registrar_donacion(donacion_id, categoria, cantidad, unidad, donante_ref)
    
    # 2. Obtención de hash previo (GENESIS si es el primer eslabón)
    parent_tx = obtener_ultimo_hash(donacion_id)
    balance_desc = f"{int(cantidad)}/{int(cantidad)} {unidad} (INGRESADO)"

    # 3. Modelado y validación de datos
    evento = EventoTrazabilidad(
        donacion_id=donacion_id,
        estado="DONACION_INGRESADA",
        balance=balance_desc,
        ubicacion=ubicacion,
        auditor=auditor,
        parent_tx=parent_tx
    )

    print("🔗 Construyendo transacción CIP-20 en Cardano Preprod...")
    metadata_payload = evento.to_cip20()
    auxiliary_data = AuxiliaryData(data=Metadata(metadata_payload))

    # 4. Transacción mínima on-chain (retorno de ADA a la misma wallet con metadatos)
    tx_builder = TransactionBuilder(context)
    tx_builder.add_input_address(my_address)
    tx_builder.add_output(TransactionOutput(my_address, 1_500_000))  # 1.5 tADA
    tx_builder.auxiliary_data = auxiliary_data

    signed_tx = tx_builder.build_and_sign(
        signing_keys=[payment_skey],
        change_address=my_address
    )

    print("🚀 Enviando transacción a la red Cardano...")
    context.submit_tx(signed_tx)
    tx_hash = str(signed_tx.id)

    # 5. Persistencia del hash y estado en SQLite
    guardar_evento(
        donacion_id=donacion_id,
        estado=evento.estado,
        balance=evento.balance,
        ubicacion=evento.ubicacion,
        auditor=evento.auditor,
        tx_hash=tx_hash,
        parent_tx=evento.parent_tx
    )

    print("\n✅ Evento registrado con éxito!")
    print(f"📄 Tx Hash: {tx_hash}")
    print(f"🔍 Explorer: https://preprod.cardanoscan.io/transaction/{tx_hash}")
    return tx_hash


if __name__ == "__main__":
    despachar_donacion_on_chain(
        donacion_id="DON-2026-BUE-01",
        categoria="ALIMENTOS_SECOS",
        cantidad=100.0,
        unidad="KITS",
        ubicacion="Centro de Acopio Lomas",
        auditor="Claudio Bogado",
        donante_ref="FUNDACION_COMUNITARIA"
    )