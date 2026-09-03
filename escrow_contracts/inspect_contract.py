import json
import os
import sys
from pycardano import (
    PlutusV3Script,
    Address,
    Network,
    script_hash,
)

BLUEPRINT_PATH = os.path.join("supply_chain_contract", "plutus.json")

if not os.path.exists(BLUEPRINT_PATH):
    print(f"❌ Error: No se encontró el archivo {BLUEPRINT_PATH}")
    sys.exit(1)

# 1. Cargar el blueprint generado por Aiken
with open(BLUEPRINT_PATH, "r", encoding="utf-8") as f:
    blueprint = json.load(f)

validator = blueprint["validators"][0]
validator_title = validator["title"]
compiled_code_hex = validator["compiledCode"]

print("==================================================")
print(f"📦 Validador detectado: {validator_title}")
print("==================================================")

# 2. Instanciar el script Plutus V3
raw_cbor = bytes.fromhex(compiled_code_hex)
script = PlutusV3Script(raw_cbor)

# 3. Calcular Script Hash y Dirección On-Chain
s_hash = script_hash(script)
script_address = Address(s_hash, network=Network.TESTNET)

print(f"🔑 Script Hash: {s_hash.to_primitive().hex()}")
print(f"📬 Dirección del Contrato (Preprod): {script_address}")
print("==================================================")
print("Esta es la dirección pública donde se bloquearán las garantías de los remitos.")