import os
import sys
import json
from dataclasses import dataclass
from dotenv import load_dotenv
from pycardano import (
    BlockFrostChainContext,
    Network,
    PaymentSigningKey,
    PaymentVerificationKey,
    Address,
    TransactionBuilder,
    TransactionOutput,
    PlutusData,
    PlutusV3Script,
    script_hash,
)

load_dotenv()

BLOCKFROST_PROJECT_ID = os.getenv("BLOCKFROST_PROJECT_ID")
if not BLOCKFROST_PROJECT_ID:
    print("❌ Error: BLOCKFROST_PROJECT_ID no encontrado en .env")
    sys.exit(1)

# 1. Definición del Datum exacto esperado por Aiken
@dataclass
class SupplyChainDatum(PlutusData):
    CONSTR_ID = 0
    sender: bytes
    transporter: bytes
    auditor: bytes
    remito_id: bytes

# 2. Conectar a Cardano Preprod
context = BlockFrostChainContext(
    project_id=BLOCKFROST_PROJECT_ID,
    base_url="https://cardano-preprod.blockfrost.io/api"
)

# 3. Cargar credenciales locales
skey = PaymentSigningKey.load("keys/backend_payment.skey")
vkey = PaymentVerificationKey.load("keys/backend_payment.vkey")
my_address = Address(vkey.hash(), network=Network.TESTNET)
my_pkh = bytes(vkey.hash())

# 4. Derivar la dirección del contrato desde plutus.json
with open("supply_chain_contract/plutus.json", "r", encoding="utf-8") as f:
    blueprint = json.load(f)

compiled_code = blueprint["validators"][0]["compiledCode"]
script = PlutusV3Script(bytes.fromhex(compiled_code))
contract_address = Address(script_hash(script), network=Network.TESTNET)

print("==================================================")
print(f"📦 Billetera origen: {my_address}")
print(f"🏦 Contrato Smart Contract: {contract_address}")
print("==================================================")

# 5. Configurar el Datum del envío
remito_id_str = "REM-2026-0827-NK"

# Asignamos tu propia clave como Remitente y Auditor para poder probar el desbloqueo
datum = SupplyChainDatum(
    sender=my_pkh,
    transporter=bytes.fromhex("11223344556677889900112233445566778899001122334455667788"),  # PKH ficticio de transporte
    auditor=my_pkh,
    remito_id=remito_id_str.encode("utf-8")
)

# 6. Construir transacción de bloqueo (3 tADA en Escrow)
builder = TransactionBuilder(context)
builder.add_input_address(my_address)

# Salida hacia el contrato con el Datum embebido (Inline Datum)
builder.add_output(
    TransactionOutput(
        address=contract_address,
        amount=3_000_000,  # 3 tADA de garantía
        datum=datum
    )
)

signed_tx = builder.build_and_sign([skey], change_address=my_address)

print("⏳ Enviando transacción de bloqueo a la blockchain...")
tx_hash = context.submit_tx(signed_tx)

print("\n✅ ¡Garantía y Remito bloqueados con éxito en el Smart Contract!")
print(f"🔑 Tx Hash: {tx_hash}")
print(f"🔍 Cardanoscan: https://preprod.cardanoscan.io/transaction/{tx_hash}")
print(f"📬 Revisar UTxO en el contrato: https://preprod.cardanoscan.io/address/{contract_address}")