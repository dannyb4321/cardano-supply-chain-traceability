import sqlite3
import os
from typing import Optional, Dict, Any

DB_PATH = os.path.join(os.path.dirname(__file__), "ngo_trace.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Inicializa las tablas maestras de donaciones y eventos de auditoría."""
    conn = get_connection()
    cursor = conn.cursor()

    # Tabla maestra de la donación
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS donaciones (
            donacion_id TEXT PRIMARY KEY,
            categoria TEXT NOT NULL,
            cantidad REAL NOT NULL,
            unidad TEXT NOT NULL,
            donante_ref TEXT DEFAULT 'ANONIMO',
            estado_actual TEXT NOT NULL,
            creado_el TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Tabla de eslabones y evidencia on-chain
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS eventos_trazabilidad (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            donacion_id TEXT NOT NULL,
            estado TEXT NOT NULL,
            balance TEXT NOT NULL,
            ubicacion TEXT NOT NULL,
            auditor TEXT NOT NULL,
            parent_tx_hash TEXT NOT NULL,
            tx_hash TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (donacion_id) REFERENCES donaciones (donacion_id)
        )
    """)

    conn.commit()
    conn.close()


def registrar_donacion(donacion_id: str, categoria: str, cantidad: float, unidad: str, donante_ref: str = "ANONIMO") -> bool:
    """Registra una nueva donación ingresada en el centro de acopio."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO donaciones (donacion_id, categoria, cantidad, unidad, donante_ref, estado_actual)
            VALUES (?, ?, ?, ?, ?, 'DONACION_INGRESADA')
        """, (donacion_id, categoria, cantidad, unidad, donante_ref))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def obtener_ultimo_hash(donacion_id: str) -> str:
    """Obtiene el tx_hash del eslabón anterior para sostener la cadena criptográfica."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT tx_hash FROM eventos_trazabilidad
        WHERE donacion_id = ? AND tx_hash IS NOT NULL
        ORDER BY id DESC LIMIT 1
    """, (donacion_id,))
    row = cursor.fetchone()
    conn.close()
    return row["tx_hash"] if row and row["tx_hash"] else "GENESIS"


def guardar_evento(donacion_id: str, estado: str, balance: str, ubicacion: str, auditor: str, tx_hash: str, parent_tx: str):
    """Inserta el eslabón minado y actualiza el estado general de la donación."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO eventos_trazabilidad (donacion_id, estado, balance, ubicacion, auditor, parent_tx_hash, tx_hash)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (donacion_id, estado, balance, ubicacion, auditor, parent_tx, tx_hash))

    cursor.execute("""
        UPDATE donaciones SET estado_actual = ? WHERE donacion_id = ?
    """, (estado, donacion_id))

    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    print("Base de datos SQLite 'ngo_trace.db' inicializada con éxito.")