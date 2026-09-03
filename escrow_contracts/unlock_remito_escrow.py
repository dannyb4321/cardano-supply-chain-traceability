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
    Redeemer,
    script_hash,
)

load_dotenv()

BLOCKFROST_PROJECT_ID = os.getenv("BLOCKFROST_PROJECT_ID")
if not BLOCKFROST_PROJECT_ID:
    print("❌ Error: BLOCKFROST_PROJECT_ID no encontrado en .env")
    sys.exit(1)

# 1. Definición del Redeemer esperado por el contrato en Aiken
# ConfirmDelivery corresponde a CONSTR_ID = 0
@dataclass
class ConfirmDelivery(PlutusData):
    CONSTR_ID = 0

# 2. Conectar a Preprod
context = BlockFrostChainContext(
    project_id=BLOCKFROST_PROJECT_ID,
    base_url="https://cardano-preprod.blockfrost.io/api"
)

# 3. Cargar credenciales del Auditor / Destinatario
skey = PaymentSigningKey.load("keys/backend_payment.skey")
vkey = PaymentVerificationKey.load("keys/backend_payment.vkey")
my_address = Address(vkey.hash(), network=Network.TESTNET)
my_pkh = bytes(vkey.hash())

# 4. Derivar la dirección y el script del contrato
with open("supply_chain_contract/plutus.json", "r", encoding="utf-8") as f:
    blueprint = json.load(f)

compiled_code = blueprint["validators"][0]["compiledCode"]
script = PlutusV3Script(bytes.fromhex(compiled_code))
contract_address = Address(script_hash(script), network=Network.TESTNET)

print("==================================================")
print(f"🏦 Contrato Smart Contract: {contract_address}")
print(f"👤 Auditor / Destinatario: {my_address}")
print("==================================================")

# 5. Localizar el UTxO bloqueado en el contrato
contract_utxos = context.utxos(contract_address)

if not contract_utxos:
    print("❌ No se encontraron UTxOs bloqueados en el contrato.")
    sys.exit(1)

# Seleccionamos el UTxO más reciente en el contrato
target_utxo = contract_utxos[-1]
print(f"🎯 UTxO detectado en el contrato: {target_utxo.input.transaction_id}#{target_utxo.input.index}")
print(f"💰 Fondos retenidos: {target_utxo.output.amount.coin / 1_000_000} tADA")

# 6. Construir la transacción de liberación condicionada
builder = TransactionBuilder(context)

# Agregamos fondos de nuestra billetera para pagar las comisiones de gas y colateral
builder.add_input_address(my_address)

# Agregamos el UTxO del contrato inteligente junto con el Script y el Redeemer
builder.add_script_input(
    utxo=target_utxo,
    script=script,
    redeemer=Redeemer(ConfirmDelivery())
)

# Exigimos la firma del auditor en la transacción (extra_signatories requerido por Aiken)
builder.required_signers = [vkey.hash()]

# Enviamos los fondos liberados a la billetera de destino
builder.add_output(
    TransactionOutput(
        address=my_address,
        amount=target_utxo.output.amount.coin
    )
)

print("⏳ Construyendo y evaluando ejecución Plutus V3...")
signed_tx = builder.build_and_sign([skey], change_address=my_address)

print("🚀 Transmitiendo transacción de desbloqueo a la red...")
tx_hash = context.submit_tx(signed_tx)

print("\n✅ ¡FONDOS Y REMITO LIBERADOS POR SMART CONTRACT!")
print(f"🔑 Tx Hash: {tx_hash}")
print(f"🔍 Cardanoscan: https://preprod.cardanoscan.io/transaction/{tx_hash}")