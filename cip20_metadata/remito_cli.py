import os
import sys
import argparse
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

def get_cardano_context_and_sender():
    if not os.path.exists(KEY_PATH):
        print(f"[-] Error: No se encontró la clave en {KEY_PATH}.")
        sys.exit(1)

    context = BlockFrostChainContext(
        project_id=BLOCKFROST_PROJECT_ID,
        base_url="https://cardano-preprod.blockfrost.io/api"
    )
    skey = PaymentSigningKey.load(KEY_PATH)
    vkey = PaymentVerificationKey.from_signing_key(skey)
    sender_addr = Address(payment_part=vkey.hash(), network=Network.TESTNET)
    return context, skey, sender_addr

def ejecutar_transaccion_cip20(msg_lines: list):
    context, skey, sender_addr = get_cardano_context_and_sender()

    # Payload estándar CIP-20 (Etiqueta 674)
    cip20_payload = {674: {"msg": [line[:60] for line in msg_lines]}}

    builder = TransactionBuilder(context)
    builder.add_input_address(sender_addr)

    dest_address = Address.from_primitive(TARGET_ADDRESS)
    builder.add_output(TransactionOutput(dest_address, Value(1500000)))

    metadata = Metadata(cip20_payload)
    builder.auxiliary_data = AuxiliaryData(AlonzoMetadata(metadata=metadata))

    print("\n[+] Construyendo y firmando transacción on-chain...")
    signed_tx = builder.build_and_sign(
        signing_keys=[skey],
        change_address=sender_addr
    )

    print("[+] Transmitiendo evento a Cardano Preprod...")
    context.submit_tx(signed_tx)

    tx_hash = signed_tx.transaction_body.hash().hex()
    explorer_url = f"https://preprod.cardanoscan.io/transaction/{tx_hash}"
    return tx_hash, explorer_url

def main():
    parser = argparse.ArgumentParser(description="CLI de Trazabilidad Logística On-Chain (Cardano Preprod / CIP-20)")
    subparsers = parser.add_subparsers(dest="comando", required=True)

    # Subcomando: Despacho Inicial
    parser_despacho = subparsers.add_parser("despacho", help="Emitir remito de despacho inicial")
    parser_despacho.add_argument("--remito", required=True, help="ID del Remito (ej: REM-2026-0824-NK)")
    parser_despacho.add_argument("--articulo", required=True, help="Descripción del material o producto")
    parser_despacho.add_argument("--lote", required=True, help="Código de lote")
    parser_despacho.add_argument("--unidades", type=int, required=True, help="Cantidad de unidades despachadas")
    parser_despacho.add_argument("--origen", required=True, help="Planta o depósito de origen")
    parser_despacho.add_argument("--destino", required=True, help="Destino final planificado")
    parser_despacho.add_argument("--auditor", required=True, help="Nombre/legajo del responsable")

    # Subcomando: Actualización de Estado (Tránsito / Recepción / Discrepancia)
    parser_update = subparsers.add_parser("evento", help="Registrar evento de ciclo de vida (Recepción, Discrepancia, etc.)")
    parser_update.add_argument("--remito", required=True, help="ID del Remito")
    parser_update.add_argument("--parent-tx", required=True, help="Hash de la transacción anterior")
    parser_update.add_argument("--estado", required=True, choices=["EN_TRANSITO", "RECIBIDO_CONFORME", "DISCREPANCIA_AUDITORIA", "EN_CUARENTENA", "RECHAZADO"], help="Nuevo estado logístico")
    parser_update.add_argument("--ubicacion", required=True, help="Ubicación física actual")
    parser_update.add_argument("--cant-decl", type=int, required=True, help="Cantidad declarada originalmente")
    parser_update.add_argument("--cant-rec", type=int, required=True, help="Cantidad física recibida en control")
    parser_update.add_argument("--obs", default="Sin novedades", help="Observaciones o detalle de discrepancia")
    parser_update.add_argument("--auditor", required=True, help="Nombre/legajo del responsable")

    args = parser.parse_args()

    print("=" * 65)
    print("OPERACIÓN LOGÍSTICA ON-CHAIN - CLI CARDANO")
    print("=" * 65)

    if args.comando == "despacho":
        msg = [
            f"REMITO-CIP20: {args.remito}",
            f"ART: {args.articulo}",
            f"LOTE: {args.lote}",
            f"CANT: {args.unidades} UNIDADES",
            f"ORI: {args.origen}",
            f"DES: {args.destino}",
            f"AUD: {args.auditor}",
            "ESTADO: DESPACHADO EN ORIGEN"
        ]
        tx_hash, url = ejecutar_transaccion_cip20(msg)
        print("\n✅ REMITO DE DESPACHO REGISTRADO")
        print(f"• Remito ID:   {args.remito}")
        print(f"• Tx Hash:     {tx_hash}")
        print(f"• Explorer:    {url}")

    elif args.comando == "evento":
        dif = args.cant_rec - args.cant_decl
        balance_str = "CONFORME" if dif == 0 else f"DISCREPANCIA: {dif:+d} U"
        msg = [
            f"REMITO-UPDATE: {args.remito}",
            f"PARENT-TX: {args.parent_tx}",
            f"ESTADO: {args.estado}",
            f"BALANCE: {args.cant_rec}/{args.cant_decl} ({balance_str})",
            f"UBICACION: {args.ubicacion}",
            f"OBS: {args.obs}",
            f"AUDITOR: {args.auditor}"
        ]
        tx_hash, url = ejecutar_transaccion_cip20(msg)
        print(f"\n✅ EVENTO [{args.estado}] REGISTRADO")
        print(f"• Remito ID:   {args.remito}")
        print(f"• Balance:     {args.cant_rec}/{args.cant_decl} ({balance_str})")
        print(f"• Tx Hash:     {tx_hash}")
        print(f"• Parent Hash: {args.parent_tx}")
        print(f"• Explorer:    {url}")

    print("=" * 65)

if __name__ == "__main__":
    main()