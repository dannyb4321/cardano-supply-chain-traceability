import os
import sys
import qrcode

# Importar el conector a la base SQLite
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import obtener_ultimo_hash


def generar_qr_donacion(donacion_id: str):
    tx_hash = obtener_ultimo_hash(donacion_id)
    if tx_hash == "GENESIS":
        print(f"❌ No hay transacciones on-chain registradas para {donacion_id}")
        return

    # URL pública en el explorador de Cardano Preprod
    url = f"https://preprod.cardanoscan.io/transaction/{tx_hash}"

    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"qr_{donacion_id}.png")
    img.save(output_path)

    print("📱 Código QR generado con éxito:")
    print(f"   Archivo guardado: {output_path}")
    print(f"   Enlace On-Chain: {url}")


if __name__ == "__main__":
    generar_qr_donacion("DON-2026-BUE-01")