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

def registrar_evento_remito(
    remito_id: str,
    parent_tx_hash: str,
    estado: str,
    ubicacion: str,
    unidades_declaradas: int,
    unidades_recibidas: int,
    observaciones: str,
    auditor: str
):
    print("=" * 65)
    print(f"ACTUALIZACIÓN ON-CHAIN: {estado}")
    print("=" * 65)

    if not os.path.exists(KEY_PATH):
        print(f"[-] Error: No se encontró la clave en {KEY_PATH}.")
        return None

    context = BlockFrostChainContext(
        project_id=BLOCKFROST_PROJECT_ID,
        base_url="https://cardano-preprod.blockfrost.io/api"
    )

    skey = PaymentSigningKey.load(KEY_PATH)
    vkey = PaymentVerificationKey.from_signing_key(skey)
    sender_addr = Address(payment_part=vkey.hash(), network=Network.TESTNET)

    diferencia = unidades_recibidas - unidades_declaradas
    estado_stock = "CONFORME" if diferencia == 0 else f"DISCREPANCIA: {diferencia} U"

    cip20_payload = {
        674: {
            "msg": [
                f"REMITO-UPDATE: {remito_id[:48]}",
                f"PARENT-TX: {parent_tx_hash[:53]}",
                f"ESTADO: {estado[:54]}",
                f"BALANCE: {unidades_recibidas}/{unidades_declaradas} ({estado_stock[:20]})",
                f"UBICACION: {ubicacion[:51]}",
                f"OBSERVACION: {observaciones[:49]}",
                f"AUDITOR: {auditor[:53]}"
            ]
        }
    }

    builder = TransactionBuilder(context)
    builder.add_input_address(sender_addr)

    dest_address = Address.from_primitive(TARGET_ADDRESS)
    builder.add_output(TransactionOutput(dest_address, Value(1500000)))

    metadata = Metadata(cip20_payload)
    builder.auxiliary_data = AuxiliaryData(AlonzoMetadata(metadata=metadata))

    print(f"[+] Construyendo y firmando evento [{estado}]...")
    signed_tx = builder.build_and_sign(
        signing_keys=[skey],
        change_address=sender_addr
    )

    print("[+] Transmitiendo evento a Cardano Preprod...")
    context.submit_tx(signed_tx)

    tx_hash = signed_tx.transaction_body.hash().hex()
    explorer_url = f"https://preprod.cardanoscan.io/transaction/{tx_hash}"

    print("\n" + "=" * 65)
    print("✅ EVENTO REGISTRADO EXITOSAMENTE ON-CHAIN")
    print(f"• Remito ID:     {remito_id}")
    print(f"• Estado:        {estado}")
    print(f"• Balance:       {unidades_recibidas}/{unidades_declaradas} ({estado_stock})")
    print(f"• Tx Hash:       {tx_hash}")
    print(f"• Cardanoscan:   {explorer_url}")
    print("=" * 65)

    return tx_hash


if __name__ == "__main__":
    # Tx Hash inicial del despacho emitido en Semana 2
    TX_DESPACHO = "a7ef0b55c2a363ece93c86e8eba71dc68c61464116a0b1c27d5efd24dc6718b7"

    # EVENTO 1: RECEPCIÓN CONFORME EN DEPÓSITO
    registrar_evento_remito(
        remito_id="REM-2026-0824-NK",
        parent_tx_hash=TX_DESPACHO,
        estado="RECIBIDO_CONFORME",
        ubicacion="Depósito CABA Sur - Bahía 04",
        unidades_declaradas=750,
        unidades_recibidas=750,
        observaciones="Control ciego aprobado. Precintos intactos.",
        auditor="Claudio Bogado (Receiving Lead)"
    )