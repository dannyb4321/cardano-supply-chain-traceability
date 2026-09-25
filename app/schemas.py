from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class EstadoCustodia(str, Enum):
    DESPACHADO = "DESPACHADO"
    EN_TRANSITO = "EN_TRANSITO"
    RECIBIDO_CONFORME = "RECIBIDO_CONFORME"
    DISCREPANCIA_AUDITORIA = "DISCREPANCIA_AUDITORIA"


def validar_longitud_cip20(v: str) -> str:
    """Valida que una cadena no supere el límite estricto de 64 bytes UTF-8 de Cardano CIP-20."""
    if len(v.encode("utf-8")) > 64:
        raise ValueError(f"El valor '{v}' supera el límite estricto de 64 bytes para CIP-20 ({len(v.encode('utf-8'))} bytes)")
    return v


# ==========================================
# MODELOS DE ENTRADA (REQUEST PAYLOADS)
# ==========================================

class DispatchCreate(BaseModel):
    """Payload para emitir el evento génesis de despacho físico."""
    remito_id: str = Field(..., examples=["REM-2026-0917-NK"], description="Identificador único del remito")
    categoria: str = Field(..., examples=["Calzado Deportivo"], description="Rubro o familia de productos")
    cantidad: int = Field(..., gt=0, examples=[500], description="Cantidad total declarada en remito")
    unidad: str = Field(default="PARES", examples=["PARES", "BULTOS", "PALLETS"], description="Unidad de medida logística")
    origen: str = Field(..., examples=["CD Central Esteban Echeverría"], description="Depósito o nave de origen")
    destino: str = Field(..., examples=["Bahía 02 CABA Sur"], description="Punto de entrega o cliente")
    transportista: str = Field(..., examples=["Logística Expreso"], description="Empresa u operador de transporte")
    auditor: str = Field(..., examples=["Claudio Bogado"], description="Operador responsable del despacho")

    @field_validator("remito_id", "categoria", "unidad", "origen", "destino", "transportista", "auditor")
    @classmethod
    def check_cip20_limits(cls, v: str) -> str:
        return validar_longitud_cip20(v)


class CheckpointCreate(BaseModel):
    """Payload para registrar un eslabón intermedio o final en la cadena de custodia."""
    remito_id: str = Field(..., examples=["REM-2026-0917-NK"])
    parent_tx_hash: str = Field(
        ...,
        min_length=64,
        max_length=64,
        examples=["d263f610059eac8379c050cb00d3f3e95978ea0d79d259d24f41d490d583f721"],
        description="Hash de la transacción previa para encadenamiento criptográfico"
    )
    estado: EstadoCustodia = Field(..., examples=[EstadoCustodia.DISCREPANCIA_AUDITORIA])
    balance: str = Field(..., examples=["488/500 (DISCREPANCIA: -12 U)"], description="Relevamiento físico o conteo ciego")
    ubicacion: str = Field(..., examples=["Bahía 02 CABA Sur"], description="Lugar físico donde se realiza el control")
    auditor: str = Field(..., examples=["Control Calidad Bahía"], description="Auditor o receptor que firma el eslabón")

    @field_validator("remito_id", "balance", "ubicacion", "auditor")
    @classmethod
    def check_cip20_limits(cls, v: str) -> str:
        return validar_longitud_cip20(v)


# ==========================================
# MODELOS DE SALIDA (RESPONSE PAYLOADS)
# ==========================================

class EventResponse(BaseModel):
    status: str
    message: str
    remito_id: str
    tx_hash: str
    cardanoscan_url: str
    parent_tx_hash: Optional[str] = None


class TraceCheckpoint(BaseModel):
    timestamp_utc: str
    estado: str
    balance: str
    ubicacion: str
    auditor: str
    tx_hash: str
    parent_tx_hash: Optional[str]


class TraceHistoryResponse(BaseModel):
    remito_id: str
    total_checkpoints: int
    cadena_de_custodia: List[TraceCheckpoint]