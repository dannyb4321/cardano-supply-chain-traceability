import sqlite3
from ngo_trace.models import CIP20Message
from ngo_trace.services import TraceabilityService
import pytest


@pytest.fixture
def mock_db(tmp_path):
    """Base de datos SQLite aislada para validar lógica de negocio."""
    db_file = tmp_path / "test_ngo.db"
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE donaciones (
            id INTEGER PRIMARY KEY,
            donacion_id TEXT UNIQUE,
            categoria TEXT,
            cantidad REAL,
            unidad TEXT,
            donante_ref TEXT,
            estado_actual TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE eventos_trazabilidad (
            id INTEGER PRIMARY KEY,
            donacion_id TEXT,
            estado TEXT,
            balance TEXT,
            ubicacion TEXT,
            auditor TEXT,
            parent_tx_hash TEXT,
            tx_hash TEXT
        )
    """)

    cursor.execute(
        "INSERT INTO donaciones VALUES (1, 'DON-TEST-01', 'ALIMENTOS', 100.0, 'KITS', 'DONANTE_A', 'ENTREGA_CONFORME')"
    )

    h1 = "a" * 64
    h2 = "b" * 64
    h3 = "c" * 64

    cursor.execute(
        "INSERT INTO eventos_trazabilidad VALUES (1, 'DON-TEST-01', 'DONACION_INGRESADA', '100 KITS', 'Acopio', 'Auditor 1', 'GENESIS', ?)",
        (h1,),
    )
    cursor.execute(
        "INSERT INTO eventos_trazabilidad VALUES (2, 'DON-TEST-01', 'KIT_CONSOLIDADO', '96/100 KITS (MERMA:-4 KITS)', 'Depósito', 'Auditor 2', ?, ?)",
        (h1, h2),
    )
    cursor.execute(
        "INSERT INTO eventos_trazabilidad VALUES (3, 'DON-TEST-01', 'ENTREGA_CONFORME', '96 KITS ENTREGADOS', 'Comedor', 'Auditor 3', ?, ?)",
        (h2, h3),
    )

    conn.commit()
    conn.close()
    return str(db_file)


def test_cip20_valido():
    msg = CIP20Message(msg=["Línea 1 válida", "Línea 2 válida"])
    assert len(msg.msg) == 2
    assert "674" in msg.to_metadata_dict()


def test_cip20_excede_64_bytes():
    linea_larga = "a" * 65
    with pytest.raises(
        ValueError, match="excede el límite CIP-20 de 64 bytes"
    ):
        CIP20Message(msg=[linea_larga])


def test_integridad_cadena_hash(mock_db):
    service = TraceabilityService(mock_db)
    assert service.verificar_integridad_cadena("DON-TEST-01") is True


def test_balance_sankey_dinamico(mock_db):
    service = TraceabilityService(mock_db)
    labels, sources, targets, values = service.calcular_balance_sankey(
        "DON-TEST-01"
    )
    assert values == [100, 96, 4]
    assert "Merma / Dañado (4)" in labels[3]