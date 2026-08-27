import os
from pycardano import PaymentSigningKey, PaymentVerificationKey, Address, Network

def generar_claves_backend():
    print("=" * 65)
    print("GENERADOR DE CLAVES CRIPTOGRÁFICAS - CARDANO BACKEND")
    print("=" * 65)
    
    os.makedirs("keys", exist_ok=True)
    
    skey = PaymentSigningKey.generate()
    vkey = PaymentVerificationKey.from_signing_key(skey)
    
    skey_path = "keys/backend_payment.skey"
    vkey_path = "keys/backend_payment.vkey"
    
    skey.save(skey_path)
    vkey.save(vkey_path)
    
    backend_address = Address(payment_part=vkey.hash(), network=Network.TESTNET)
    
    print(f"\n✅ Claves generadas exitosamente:")
    print(f"  • Clave Privada (skey): {skey_path}")
    print(f"  • Clave Pública (vkey): {vkey_path}")
    print(f"\n📬 DIRECCIÓN PÚBLICA DEL BACKEND (Preprod):")
    print(f"  {backend_address}")
    print("\n" + "=" * 65)

if __name__ == "__main__":
    generar_claves_backend()