import os
from dotenv import load_dotenv
from pycardano import (
    BlockFrostChainContext,
    PaymentSigningKey,
    PaymentVerificationKey,
    Address,
    Network,
    TransactionBuilder,
    TransactionOutput,
    Value,
    Metadata,
    AuxiliaryData,
    AlonzoMetadata,
)

load_dotenv()

BLOCKFROST_PROJECT_ID = os.getenv("BLOCKFROST_PROJECT_ID")
TARGET_ADDRESS = os.getenv("TARGET_ADDRESS")
KEY_PATH = "keys/backend_payment.skey"

def emitir_remito_cip20(articulo: str, lote: str, unidades: int, origen: str, destino: str, verificador: str):
    print("=" * 65)
    print("EMISOR AUTOMÁTICO DE REMITOS ON-CHAIN (CIP-20 / CARDANO)")
    print("=" * 65)

    if not os.path.exists(KEY_PATH):
        print(f"[-] Error: No se encontró la clave privada en {KEY_PATH}.")
        return

    # 1. Configurar contexto de red con Blockfrost Preprod
    context = BlockFrostChainContext(
        project_id=BLOCKFROST_PROJECT_ID,
        base_url="https://cardano-preprod.blockfrost.io/api"
    )

    # 2. Cargar llaves criptográficas del backend
    skey = PaymentSigningKey.load(KEY_PATH)
    vkey = PaymentVerificationKey.from_signing_key(skey)
    sender_addr = Address(payment_part=vkey.hash(), network=Network.TESTNET)

    print(f"[+] Dirección de emisión (Backend): {sender_addr}")

    # 3. Payload CIP-20 (Label 674)
    remito_cip20_payload = {
        674: {
            "msg": [
                "REMITO-CIP20: REM-2026-0824-NK",
                f"ART: {articulo[:58]}",
                f"LOTE: {lote[:57]}",
                f"CANT: {unidades} UNIDADES",
                f"ORI: {origen[:58]}",
                f"DES: {destino[:58]}",
                f"AUD: {verificador[:58]}",
                "ESTADO: DESPACHADO EN TRANSITO"
            ]
        }
    }

    # 4. Construcción y balanceo de la transacción
    builder = TransactionBuilder(context)
    builder.add_input_address(sender_addr)
    
    dest_address = Address.from_primitive(TARGET_ADDRESS)
    builder.add_output(TransactionOutput(dest_address, Value(1500000)))

    metadata = Metadata(remito_cip20_payload)
    builder.auxiliary_data = AuxiliaryData(AlonzoMetadata(metadata=metadata))

    print("\n[+] Construyendo, balanceando y firmando transacción con .skey...")
    signed_tx = builder.build_and_sign(
        signing_keys=[skey],
        change_address=sender_addr
    )

    # 5. Envío a la blockchain
    print("[+] Transmitiendo transacción a Cardano Preprod...")
    context.submit_tx(signed_tx)

    tx_hash = signed_tx.transaction_body.hash().hex()
    explorer_url = f"https://preprod.cardanoscan.io/transaction/{tx_hash}"

    print("\n" + "=" * 65)
    print("✅ REMITO PUBLICADO EXITOSAMENTE ON-CHAIN")
    print(f"• Tx Hash: {tx_hash}")
    print(f"• Cardanoscan: {explorer_url}")
    print("=" * 65)

    return tx_hash

if __name__ == "__main__":
    emitir_remito_cip20(
        articulo="Zapatillas Runner Pro X - Black Edition",
        lote="LOTE-NK-2026-9921",
        unidades=750,
        origen="Planta Central Ezeiza - Hub 01",
        destino="Centro Distribución CABA Sur",
        verificador="Claudio Bogado (Logistics Ops)"
    )