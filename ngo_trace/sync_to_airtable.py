import os
import sqlite3
from dotenv import load_dotenv
from pyairtable import Api

load_dotenv()

AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID")

if not AIRTABLE_API_KEY or not AIRTABLE_BASE_ID:
    raise ValueError("Faltan AIRTABLE_API_KEY o AIRTABLE_BASE_ID en el archivo .env")

api = Api(AIRTABLE_API_KEY)
tabla_donaciones = api.table(AIRTABLE_BASE_ID, "Donaciones")
tabla_eventos = api.table(AIRTABLE_BASE_ID, "Eventos_Trazabilidad")

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ngo_trace.db")


def sincronizar_con_airtable():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("\n🔄 Sincronizando SQLite local con Airtable...")

    # 1. Sincronizar Donaciones maestras
    cursor.execute("SELECT * FROM donaciones")
    donaciones = cursor.fetchall()

    donaciones_airtable_map = {}

    for d in donaciones:
        records = tabla_donaciones.all(formula=f"{{donacion_id}} = '{d['donacion_id']}'")
        payload = {
            "donacion_id": d["donacion_id"],
            "categoria": d["categoria"],
            "cantidad_inicial": int(d["cantidad"]),
            "unidad": d["unidad"],
            "donante_ref": d["donante_ref"],
            "estado_actual": d["estado_actual"]
        }

        if records:
            rec_id = records[0]["id"]
            tabla_donaciones.update(rec_id, payload, typecast=True)
            print(f"  📝 Donación actualizada: {d['donacion_id']}")
        else:
            rec = tabla_donaciones.create(payload, typecast=True)
            rec_id = rec["id"]
            print(f"  ✨ Donación creada: {d['donacion_id']}")

        donaciones_airtable_map[d["donacion_id"]] = rec_id

    # 2. Sincronizar Eslabones On-Chain
    cursor.execute("SELECT * FROM eventos_trazabilidad")
    eventos = cursor.fetchall()

    for e in eventos:
        records = tabla_eventos.all(formula=f"{{tx_hash}} = '{e['tx_hash']}'")

        donacion_record_id = donaciones_airtable_map.get(e["donacion_id"])
        payload = {
            "donacion": [donacion_record_id] if donacion_record_id else [],
            "estado": e["estado"],
            "balance": e["balance"],
            "ubicacion": e["ubicacion"],
            "auditor": e["auditor"],
            "parent_tx_hash": e["parent_tx_hash"],
            "tx_hash": e["tx_hash"]
        }

        if not records:
            tabla_eventos.create(payload, typecast=True)
            print(f"  🔗 Eslabón sincronizado: {e['estado']} -> Tx: {e['tx_hash'][:16]}...")
        else:
            print(f"  ✔️ Eslabón ya registrado: {e['estado']}")

    conn.close()
    print("\n✅ Sincronización completada con éxito.")


if __name__ == "__main__":
    sincronizar_con_airtable()