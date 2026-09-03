import os
import json
import qrcode
from dotenv import load_dotenv
from blockfrost import BlockFrostApi, ApiUrls, ApiError

# Cargar variables del archivo .env local
load_dotenv()

BLOCKFROST_PROJECT_ID = os.getenv("BLOCKFROST_PROJECT_ID")
TARGET_ADDRESS = os.getenv("TARGET_ADDRESS")
TX_HASH = "4644c89df2e6ab8dd732688b3ae5ed0646a3e1e0b050371d6862f77abcd227cc"

# Conexión con Blockfrost Preprod
api = BlockFrostApi(
    project_id=BLOCKFROST_PROJECT_ID,
    base_url=ApiUrls.preprod.value
)

def generar_qr_auditoria(tx_hash: str):
    print("=" * 65)
    print("GENERADOR DE CERTIFICADO & QR DE TRAZABILIDAD ON-CHAIN")
    print("=" * 65)

    explorer_url = f"https://preprod.cardanoscan.io/transaction/{tx_hash}"

    try:
        metadata = api.transaction_metadata(hash=tx_hash)
        
        print(f"\n[+] Validando datos de la transacción en Cardano:")
        print(f"  • Tx Hash: {tx_hash}")
        print(f"  • Enlace de Explorador: {explorer_url}")

        if metadata:
            print("\n[+] Metadatos verificados exitosamente:")
            for item in metadata:
                print(f"  • Label: {item.label} | Payload: {item.json_metadata}")

        # Configuración y generación del QR
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(explorer_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="#003366", back_color="white")
        output_file = "remito_qr_cardano.png"
        img.save(output_file)

        print("\n" + "=" * 65)
        print(f"✅ QR generado exitosamente: {output_file}")
        print("Escaneá la imagen generada con tu celular para abrir el registro on-chain.")
        print("=" * 65)

    except ApiError as e:
        print(f"[-] Error al consultar Blockfrost: {e}")
    except Exception as e:
        print(f"[-] Error: {e}")

if __name__ == "__main__":
    generar_qr_auditoria(TX_HASH)