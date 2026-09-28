from fastapi import FastAPI, HTTPException, status
from app.schemas import CheckpointCreate, EventResponse, TraceHistoryResponse
from app.cardano import submit_event_onchain, get_traceability_onchain

app = FastAPI(
    title="Cardano Supply Chain Gateway",
    version="1.0.0",
    description="API REST de trazabilidad física y auditoría on-chain en Cardano Preprod (CIP-20)."
)


@app.get("/health", status_code=status.HTTP_200_OK, tags=["Sistema"])
def health_check():
    return {
        "status": "online",
        "network": "Cardano Preprod",
        "cip_standard": "CIP-20 (Label 674)"
    }


@app.post(
    "/api/v1/events/checkpoint",
    response_model=EventResponse,
    status_code=status.HTTP_202_ACCEPTED,
    tags=["Eventos On-Chain"]
)
def register_checkpoint(checkpoint: CheckpointCreate):
    """
    Firma y somete una transacción real en Cardano Preprod vinculada
    al hash del eslabón anterior.
    """
    try:
        tx_hash = submit_event_onchain(checkpoint.model_dump())
        return EventResponse(
            status="SUBMITTED",
            message=f"Eslabón '{checkpoint.estado}' firmado y emitido a Cardano Preprod.",
            remito_id=checkpoint.remito_id,
            tx_hash=tx_hash,
            cardanoscan_url=f"https://preprod.cardanoscan.io/transaction/{tx_hash}",
            parent_tx_hash=checkpoint.parent_tx_hash
        )
    except FileNotFoundError as fnf:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(fnf))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Fallo al transmitir la transacción a la red Cardano: {str(e)}"
        )


@app.get(
    "/api/v1/trace/{remito_id}",
    response_model=TraceHistoryResponse,
    status_code=status.HTTP_200_OK,
    tags=["Auditoría de Custodia"]
)
def get_trace(remito_id: str):
    """
    Consulta en tiempo real la cadena de bloques y retorna el historial cronológico
    de eslabones para el remito solicitado.
    """
    try:
        chain = get_traceability_onchain(remito_id)
        if not chain:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontraron eslabones on-chain para el remito '{remito_id}'."
            )
        return TraceHistoryResponse(
            remito_id=remito_id,
            total_checkpoints=len(chain),
            cadena_de_custodia=chain
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error consultando la blockchain: {str(e)}"
        )