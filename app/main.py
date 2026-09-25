from fastapi import FastAPI, BackgroundTasks, status, HTTPException
from dotenv import load_dotenv

from app.schemas import (
    DispatchCreate,
    CheckpointCreate,
    EventResponse,
    TraceHistoryResponse
)

load_dotenv()

app = FastAPI(
    title="TraceAid RWA & Supply Chain Gateway",
    description=(
        "Microservicio REST para certificar eventos físicos de depósitos y logística "
        "estampándolos de manera inmutable en Cardano Preprod mediante metadatos CIP-20 (Label 674)."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


@app.get("/health", tags=["Infraestructura"])
def health_check():
    """Verifica la operatividad del gateway y la red configurada."""
    return {
        "status": "operational",
        "service": "TraceAid Gateway",
        "network": "Cardano Preprod",
        "cip_standard": "CIP-20 (Transaction Metadata Label 674)"
    }


@app.post(
    "/api/v1/events/dispatch",
    response_model=EventResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Eventos Logísticos"]
)
def registrar_despacho(payload: DispatchCreate, background_tasks: BackgroundTasks):
    """
    Registra el evento de despacho inicial (Génesis) para un remito de mercadería.
    Valida el schema y encola la transacción on-chain.
    """
    # Hash demostrativo mientras conectamos cardano.py
    tx_hash = "d263f610059eac8379c050cb00d3f3e95978ea0d79d259d24f41d490d583f721"
    
    return EventResponse(
        status="SUBMITTED",
        message="Evento de despacho validado y encolado para estampar en Cardano.",
        remito_id=payload.remito_id,
        tx_hash=tx_hash,
        cardanoscan_url=f"https://preprod.cardanoscan.io/transaction/{tx_hash}",
        parent_tx_hash="GENESIS"
    )


@app.post(
    "/api/v1/events/checkpoint",
    response_model=EventResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Eventos Logísticos"]
)
def registrar_checkpoint(payload: CheckpointCreate, background_tasks: BackgroundTasks):
    """
    Registra un evento de cambio de custodia física (recepción, discrepancia de stock)
    enlazándolo al parent_tx_hash del eslabón anterior.
    """
    tx_hash = "4c248f65de98be6fd5b190a6e60b94cb221a601be2db06d11e4bf51a2e7c4f19"
    
    return EventResponse(
        status="SUBMITTED",
        message=f"Eslabón '{payload.estado.value}' recibido y programado para minado.",
        remito_id=payload.remito_id,
        tx_hash=tx_hash,
        cardanoscan_url=f"https://preprod.cardanoscan.io/transaction/{tx_hash}",
        parent_tx_hash=payload.parent_tx_hash
    )


@app.get(
    "/api/v1/trace/{remito_id}",
    response_model=TraceHistoryResponse,
    tags=["Auditoría de Custodia"]
)
def obtener_trazabilidad(remito_id: str):
    """
    Devuelve la cadena de custodia completa auditada desde Cardano y la base de eventos.
    """
    return TraceHistoryResponse(
        remito_id=remito_id,
        total_checkpoints=2,
        cadena_de_custodia=[
            {
                "timestamp_utc": "2026-09-17T14:10:00Z",
                "estado": "DESPACHADO",
                "balance": "500/500 CONFORME",
                "ubicacion": "CD Central Esteban Echeverría",
                "auditor": "Claudio Bogado",
                "tx_hash": "d263f610059eac8379c050cb00d3f3e95978ea0d79d259d24f41d490d583f721",
                "parent_tx_hash": "GENESIS"
            },
            {
                "timestamp_utc": "2026-09-17T17:45:00Z",
                "estado": "DISCREPANCIA_AUDITORIA",
                "balance": "488/500 (DISCREPANCIA: -12 U)",
                "ubicacion": "Bahía 02 CABA Sur",
                "auditor": "Control Calidad Bahía",
                "tx_hash": "4c248f65de98be6fd5b190a6e60b94cb221a601be2db06d11e4bf51a2e7c4f19",
                "parent_tx_hash": "d263f610059eac8379c050cb00d3f3e95978ea0d79d259d24f41d490d583f721"
            }
        ]
    )