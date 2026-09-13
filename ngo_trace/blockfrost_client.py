import os
import time
from typing import Any, Dict, Optional
from dotenv import load_dotenv
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

load_dotenv()


class BlockfrostClient:
    """Cliente centralizado y resiliente para la API de Blockfrost (Cardano Preprod).

    Implementa reintentos automáticos con backoff exponencial para mitigar
    errores 429 (Rate Limit) y fallos transitorios de red (5xx).
    """

    BASE_URLS = {
        "preprod": "https://cardano-preprod.blockfrost.io/api/v0",
        "mainnet": "https://cardano-mainnet.blockfrost.io/api/v0",
    }

    def __init__(
        self,
        project_id: Optional[str] = None,
        network: str = "preprod",
        total_retries: int = 5,
        backoff_factor: float = 1.5,
    ) -> None:
        self.project_id = project_id or os.getenv("BLOCKFROST_PROJECT_ID")
        if not self.project_id:
            raise ValueError(
                "BLOCKFROST_PROJECT_ID no encontrado en variables de entorno."
            )

        self.network = network
        self.base_url = self.BASE_URLS.get(network, self.BASE_URLS["preprod"])

        # Configuración de reintentos exponenciales a nivel de sesión
        self.session = requests.Session()
        retry_strategy = Retry(
            total=total_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "OPTIONS"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        self.session.headers.update(
            {"project_id": self.project_id, "User-Agent": "NGO-Cardano-Trace/1.0"}
        )

    def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[bytes] = None,
        json_payload: Optional[Dict[str, Any]] = None,
        custom_headers: Optional[Dict[str, str]] = None,
    ) -> Any:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self.session.headers.copy()
        if custom_headers:
            headers.update(custom_headers)

        response = self.session.request(
            method=method,
            url=url,
            params=params,
            data=data,
            json=json_payload,
            headers=headers,
            timeout=15,
        )

        # Si agotó los reintentos y sigue fallando:
        if not response.ok:
            raise RuntimeError(
                f"[Blockfrost Error {response.status_code}] {url} -> {response.text}"
            )

        if "application/json" in response.headers.get("Content-Type", ""):
            return response.json()
        return response.content

    def get_health(self) -> Dict[str, Any]:
        """Verifica el estado del nodo y backend de Blockfrost."""
        return self._request("GET", "/health")

    def get_address_utxos(self, address: str) -> list:
        """Obtiene la lista de UTxOs disponibles para una dirección."""
        return self._request("GET", f"/addresses/{address}/utxos")

    def get_transaction(self, tx_hash: str) -> Dict[str, Any]:
        """Obtiene detalles de una transacción on-chain."""
        return self._request("GET", f"/txs/{tx_hash}")

    def get_transaction_metadata(self, tx_hash: str) -> list:
        """Obtiene los metadatos (CIP-20 u otros labels) de una transacción."""
        return self._request("GET", f"/txs/{tx_hash}/metadata")

    def submit_transaction(self, cbor_hex: str) -> str:
        """Envía una transacción serializada en CBOR hex crudo."""
        cbor_bytes = bytes.fromhex(cbor_hex)
        headers = {"Content-Type": "application/cbor"}
        response = self._request(
            "POST", "/tx/submit", data=cbor_bytes, custom_headers=headers
        )
        return (
            response if isinstance(response, str) else response.decode("utf-8")
        )

    def wait_for_tx(
        self, tx_hash: str, max_wait: int = 120, check_interval: int = 5
    ) -> bool:
        """Espera de forma bloqueante y segura hasta que la tx sea minada on-chain."""
        print(f"⏳ Esperando confirmación de {tx_hash[:16]}... en la mempool...")
        start_time = time.time()
        while time.time() - start_time < max_wait:
            try:
                self.get_transaction(tx_hash)
                print(f"✅ Transacción {tx_hash[:16]}... confirmada en bloque.")
                return True
            except RuntimeError:
                time.sleep(check_interval)
        raise TimeoutError(
            f"La transacción {tx_hash} no se minó tras {max_wait}s."
        )


if __name__ == "__main__":
    # Test de humo local
    client = BlockfrostClient()
    health = client.get_health()
    print("Estado del nodo:", health)