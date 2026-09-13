import os
import sqlite3
from typing import List, Tuple
from ngo_trace.models import DonacionSchema, EventoTrazabilidadSchema


class TraceabilityService:

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def listar_donaciones(self) -> List[DonacionSchema]:
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM donaciones").fetchall()
            return [
                DonacionSchema(
                    donacion_id=r["donacion_id"],
                    categoria=r["categoria"],
                    cantidad=float(r["cantidad"]),
                    unidad=r["unidad"],
                    donante_ref=r["donante_ref"],
                    estado_actual=r["estado_actual"],
                )
                for r in rows
            ]

    def obtener_donacion(self, donacion_id: str) -> DonacionSchema:
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM donaciones WHERE donacion_id = ?",
                (donacion_id,),
            ).fetchone()
            if not row:
                raise ValueError(f"Donación {donacion_id} no encontrada.")
            return DonacionSchema(
                donacion_id=row["donacion_id"],
                categoria=row["categoria"],
                cantidad=float(row["cantidad"]),
                unidad=row["unidad"],
                donante_ref=row["donante_ref"],
                estado_actual=row["estado_actual"],
            )

    def obtener_eventos(
        self, donacion_id: str
    ) -> List[EventoTrazabilidadSchema]:
        with self.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM eventos_trazabilidad WHERE donacion_id = ? ORDER BY id ASC",
                (donacion_id,),
            ).fetchall()
            return [
                EventoTrazabilidadSchema(
                    donacion_id=r["donacion_id"],
                    estado=r["estado"],
                    balance=r["balance"],
                    ubicacion=r["ubicacion"],
                    auditor=r["auditor"],
                    parent_tx_hash=r["parent_tx_hash"],
                    tx_hash=r["tx_hash"],
                )
                for r in rows
            ]

    def verificar_integridad_cadena(self, donacion_id: str) -> bool:
        """Verifica que cada eslabón apunte criptográficamente al Tx Hash del eslabón previo."""
        eventos = self.obtener_eventos(donacion_id)
        if not eventos:
            return False

        if eventos[0].parent_tx_hash != "GENESIS":
            return False

        for i in range(1, len(eventos)):
            if eventos[i].parent_tx_hash != eventos[i - 1].tx_hash:
                return False
        return True

    def calcular_balance_sankey(
        self, donacion_id: str
    ) -> Tuple[List[str], List[int], List[int], List[float]]:
        """Calcula de forma dinámica los nodos, conexiones y mermas para el gráfico Sankey."""
        donacion = self.obtener_donacion(donacion_id)
        eventos = self.obtener_eventos(donacion_id)

        total_inicial = int(donacion.cantidad)
        merma = 0
        conformes = total_inicial

        for ev in eventos:
            if "MERMA" in ev.balance.upper() and "-" in ev.balance:
                try:
                    partes = ev.balance.split("MERMA:")
                    merma_str = (
                        partes[1].split()[0].replace("-", "").strip()
                    )
                    merma = int(merma_str)
                    conformes = total_inicial - merma
                except Exception:
                    pass

        labels = [
            f"Donación Recibida ({total_inicial})",
            f"Acopio Lomas ({total_inicial})",
            f"Kits Conformes ({conformes})",
            f"Merma / Dañado ({merma})",
        ]

        sources = [0, 1, 1]
        targets = [1, 2, 3]
        values = [total_inicial, conformes, merma]

        return labels, sources, targets, values