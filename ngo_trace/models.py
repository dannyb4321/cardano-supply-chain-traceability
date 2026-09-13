from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class EstadoDonacion(str, Enum):
    DONACION_INGRESADA = "DONACION_INGRESADA"
    KIT_CONSOLIDADO = "KIT_CONSOLIDADO"
    ENTREGA_CONFORME = "ENTREGA_CONFORME"


class CIP20Message(BaseModel):
    """Validador estricto para el estándar CIP-20 (label 674) en Cardano.

    Garantiza que ninguna línea supere los 64 bytes UTF-8 para evitar
    rechazos al serializar en CBOR o al enviar la transacción a la red.
    """

    msg: List[str]

    @field_validator("msg")
    @classmethod
    def validar_limite_64_bytes(cls, lineas: List[str]) -> List[str]:
        for i, linea in enumerate(lineas):
            peso_bytes = len(linea.encode("utf-8"))
            if peso_bytes > 64:
                raise ValueError(
                    f"Línea {i} excede el límite CIP-20 de 64 bytes ({peso_bytes} bytes): '{linea}'"
                )
        return lineas

    def to_metadata_dict(self) -> dict:
        return {"674": {"msg": self.msg}}


class DonacionSchema(BaseModel):
    donacion_id: str = Field(..., min_length=3, max_length=30)
    categoria: str = Field(..., min_length=2, max_length=50)
    cantidad: float = Field(..., gt=0)
    unidad: str = Field(..., min_length=1, max_length=20)
    donante_ref: str = Field(..., min_length=2, max_length=100)
    estado_actual: EstadoDonacion = EstadoDonacion.DONACION_INGRESADA


class EventoTrazabilidadSchema(BaseModel):
    donacion_id: str
    estado: EstadoDonacion
    balance: str
    ubicacion: str = Field(..., min_length=2, max_length=100)
    auditor: str = Field(..., min_length=2, max_length=100)
    parent_tx_hash: str
    tx_hash: str

    @field_validator("tx_hash", "parent_tx_hash")
    @classmethod
    def validar_hashes(cls, valor: str) -> str:
        if valor == "GENESIS":
            return valor
        if len(valor) != 64 or not all(
            c in "0123456789abcdefABCDEF" for c in valor
        ):
            raise ValueError(
                f"Hash inválido '{valor}'. Debe ser 'GENESIS' o un hex de 64 caracteres."
            )
        return valor.lower()


if __name__ == "__main__":
    # Test de validación CIP-20
    test_ok = CIP20Message(
        msg=[
            "NGO-TRACE-v1:DON-2026-BUE-01",
            "STATUS:KIT_CONSOLIDADO",
            "BAL:96/100 KITS (MERMA:-4 KITS)",
        ]
    )
    print("✅ Validación CIP-20 OK:", test_ok.to_metadata_dict())

    try:
        CIP20Message(
            msg=[
                "Esta línea es intencionalmente demasiado larga para superar el límite estricto de sesenta y cuatro bytes de Cardano CIP-20"
            ]
        )
    except ValueError as e:
        print("🛡️ Captura exitosa de error CIP-20:", e)