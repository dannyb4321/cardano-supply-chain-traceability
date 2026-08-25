import os
from blockfrost import BlockFrostApi, ApiError, ApiUrls

# =====================================================================
# CONFIGURACIÓN DE INFRAESTRUCTURA
# =====================================================================
# Se recomienda utilizar variables de entorno para proteger las API Keys
BLOCKFROST_PROJECT_ID = os.getenv("BLOCKFROST_PREPROD_KEY", "TU_API_KEY_AQUÍ")

# Reemplaza con tu dirección real de Preprod (debe empezar con "addr_test1"
# y tener la cadena completa, no un placeholder truncado)
TARGET_ADDRESS = "addr_test1qreeakrv59dcdf5hfes3gh0a2uj2qypavw9vhmafckvzhagkjp8wnszqtuevcepwg962ww3nmyfzhjwzxz8jep8nk6rq5vcha0"

try:
    # Inicialización del cliente apuntando explícitamente a la red Preprod
    api = BlockFrostApi(
        project_id="preprod9E4yPumqzfoWMywdP7oMtfVZ0NdS63AM",
        base_url=ApiUrls.preprod.value  # https://cardano-preprod.blockfrost.io/api/v0
    )

    print("=" * 60)
    print(f"CONSULTANDO ESTADO EN RED CARDANO: PREPROD")
    print("=" * 60)

    # 1. CONSULTA DE SALDOS GENERALES
    address_info = api.address(address=TARGET_ADDRESS)
    print(f"\n📊 INFORMACIÓN DE LA DIRECCIÓN:")
    print(f"-> Tipo de Cuenta: {address_info.type}")

    for amount in address_info.amount:
        if amount.unit == "lovelace":
            # 1 ADA = 1,000,000 Lovelaces
            ada_balance = int(amount.quantity) / 1_000_000
            print(f"-> Saldo en ADA: {ada_balance:,} tADA")
        else:
            print(f"-> Activo Nativo [{amount.unit}]: {amount.quantity}")

    # 2. CONSULTA DE UTXOs (Unspent Transaction Outputs)
    # Cardano utiliza el modelo UTXO; el saldo total es la suma de estos outputs
    address_utxos = api.address_utxos(address=TARGET_ADDRESS)
    print(f"\n🔎 MAPA DE UTXOs ACTIVOS ({len(address_utxos)} encontrados):")

    for index, utxo in enumerate(address_utxos, start=1):
        print(f"  [{index}] TxHashID: {utxo.tx_hash} (Índice: {utxo.output_index})")
        for asset in utxo.amount:
            if asset.unit == "lovelace":
                print(f"      - Monto: {int(asset.quantity) / 1_000_000} ADA")
            else:
                print(f"      - Token: {asset.unit} | Cantidad: {asset.quantity}")

    # 3. HISTORIAL Y METADATOS DE TRANSACCIONES
    # Extrae las últimas 3 transacciones para revisar si contienen metadatos adjuntos
    address_txs = api.address_transactions(address=TARGET_ADDRESS, count=3, order='desc')
    print(f"\n🗒 HISTORIAL RECIENTE Y METADATOS:")

    if not address_txs:
        print("-> No se registran transacciones previas en esta dirección.")
    else:
        for tx in address_txs:
            print(f"  - Transacción: {tx.tx_hash} (Bloque: {tx.block_height})")
            try:
                # Consulta específica de los metadatos adjuntos en la transacción (CIP-25 / CIP-20)
                tx_metadata = api.transaction_metadata(hash=tx.tx_hash)
                if tx_metadata:
                    for meta in tx_metadata:
                        print(f"      [Metadato Etiqueta {meta.label}]: {meta.json_metadata}")
                else:
                    print("      - Sin metadatos registrados en este hash.")
            except ApiError as metadata_error:
                print(f"      - Error al leer metadatos: {metadata_error}")

except ApiError as e:
    print(f"\n⚠️ Error operativo en la API de Blockfrost: {e}")
except Exception as e:
    print(f"\n⚠️ Falla inesperada en la ejecución del Script: {e}")

print("\n" + "=" * 60)
print("FIN DE LA EJECUCIÓN DEL PROCESO")
print("=" * 60)
