# Cardano Supply Chain Traceability Prototype (eUTXO & Metadata)

Este proyecto implementa una arquitectura de trazabilidad logística y auditoría física-digital sobre la blockchain de **Cardano (Preprod Testnet)**, integrando el estándar de metadatos de transacciones con la API de Blockfrost y generación de códigos QR para piso operativo.

---

## 📌 Arquitectura del Sistema

1. **Registro de Despacho (On-Chain Settlement):**  
   Al emitir una orden de transporte o remito, los atributos críticos del envío (*Lote, Unidades, Origen, Destino, Inspector*) se serializan en un payload JSON y se anclan en los metadatos de una transacción eUTXO de Cardano.

2. **Auditoría Automatizada (Python + Blockfrost API):**  
   Un pipeline en Python escucha las transacciones de la billetera corporativa, extrae la carga útil (*payload*) y valida la integridad del estado logístico contra la red sin necesidad de un nodo local pesado.

3. **Verificación en Piso Físico (QR Tokenization):**  
   El sistema compila un certificado digital en un código QR dinámico que apunta directamente al explorador on-chain (`Cardanoscan`), permitiendo auditorías de mercadería en depósitos sin requerir credenciales de un ERP cerrado.

---

## 🛠️ Stack Tecnológico

* **Blockchain:** Cardano (Red Preprod - Protocolo Shelley / Babbage)
* **Lenguaje:** Python 3.14
* **SDK de Conexión:** `blockfrost-python` (Blockfrost API Gateway)
* **Generación Gráfica:** `qrcode`, `Pillow`
* **Explorador On-Chain:** Cardanoscan Preprod

---

## 🚀 Estructura de Archivos

* `audit_supply_chain.py`: Script de auditoría y extracción de metadatos on-chain.
* `generate_traceability_qr.py`: Generador de etiquetas QR para bultos y pallets.
* `remito_qr_cardano.png`: Salida gráfica generada lista para escaneo operativo.

---

## 🔍 Caso de Uso Resuelto
* **Problema:** Desvíos de mercadería, falsificación de remitos y falta de transparencia en la cadena de custodia física.
* **Solución:** Reconciliación inmutable y pública basada en el modelo eUTXO, reduciendo los costos de auditoría y eliminando intermediarios de validación.