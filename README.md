# Cardano Supply Chain Traceability & Smart Escrow

Sistema integral de trazabilidad logística, auditoría inmutable y custodia financiera condicional (*Escrow*) desarrollado sobre la blockchain de **Cardano (Preprod Testnet)**.

El sistema implementa una arquitectura híbrida desacoplada:
1. **Capa de Datos Operativos (CIP-20):** Registro de eventos inmutables en metadatos (Label `674`) para trazabilidad de despachos, tránsitos, mermas y auditorías de muelle.
2. **Capa Financiera y de Custodia (Plutus V3 / Aiken):** Smart contract en Aiken para retención y liberación condicionada de garantías operativas y pagos contra entrega conforme o informe de discrepancias.
3. **Capa de Aplicación y Reportería:** Dashboard forense interactivo en Streamlit con generación de actas periciales en formato PDF (`fpdf2`).

---

## 🏗 Arquitectura del Sistema

┌─────────────────────────────────┐
                        │    Dador de Carga / Remitente   │
                        └────────────────┬────────────────┘
                                         │
        ┌────────────────────────────────┴────────────────────────────────┐
        │ CIP-20 (Metadata 674)                                           │ Plutus V3 Escrow
        ▼                                                                 ▼
┌───────────────────────┐                                         ┌───────────────────────┐
│ Eventos de Despacho,  │                                         │ Contrato Inteligente  │
│ Tránsito y Auditoría  │                                         │  (Fondos Bloqueados)  │
└───────────┬───────────┘                                         └───────────┬───────────┘
│                                                                 │
│ Consultas vía Blockfrost API                                    │ Verificación de firmas
▼                                                                 ▼
┌───────────────────────┐                                         ┌───────────────────────┐
│   Dashboard Streamlit │ ◀───────────────────────────────────────│ Desbloqueo / Cobro    │
│  y Reportes Forenses  │                                         │ (Auditor / Remitente) │
└───────────────────────┘                                         └───────────────────────┘

---

## 📁 Estructura del Repositorio

```text
cardano-supply-chain-traceability/
├── cip20_metadata/             # Capa de Trazabilidad e Inmutabilidad CIP-20
│   ├── dispatch_remito_cip20.py      # Despacho inicial con metadatos on-chain
│   ├── update_remito_state.py        # Registro de cambios de estado y mermas
│   ├── audit_supply_chain.py         # Consulta y reconstrucción forense de eventos
│   ├── generate_traceability_qr.py   # Generador de etiquetas QR para bultos/remitos
│   └── remito_cli.py                 # CLI operativo de despacho rápido
│
├── escrow_contracts/           # Capa de Interacción con Smart Contracts (PyCardano)
│   ├── inspect_contract.py           # Inspección de bytecode y derivación de dirección
│   ├── lock_remito_escrow.py         # Depósito de garantía con Inline Datum
│   └── unlock_remito_escrow.py       # Liquidación condicional mediante Redeemer
│
├── supply_chain_contract/      # Validador on-chain desarrollado en Aiken
│   ├── validators/
│   │   └── supply_chain.ak           # Lógica Plutus V3 y pruebas unitarias
│   ├── aiken.toml                    # Configuración de compilador y librerías stdlib
│   └── plutus.json                   # Blueprint compilado para ejecución
│
├── keys/                       # Credenciales criptográficas (Excluidas de Git)
│   ├── backend_payment.skey          # Llave privada de firma
│   └── backend_payment.vkey          # Llave pública de verificación
│
├── dashboard_supply_chain.py   # Panel de control Streamlit y generador de actas PDF
├── generate_keys.py            # Generador determinista de pares de llaves ed25519
├── requirements.txt            # Dependencias del entorno Python
└── README.md                   # Documentación técnica

Lógica del Smart Contract (supply_chain.ak)
El validador logistics_escrow opera bajo el estándar Plutus V3, evaluando los siguientes parámetros en cada intento de consumo de un UTxO:

Datum (SupplyChainDatum):

sender: Hash de la llave de pago del remitente (VerificationKeyHash).

transporter: Hash de la llave de pago del transportista (VerificationKeyHash).

auditor: Hash de la llave de verificación del auditor de muelle (VerificationKeyHash).

remito_id: Identificador alfanumérico del remito/embarque (ByteArray).

Redeemers (LogisticsAction):

ConfirmDelivery (Constr 0): Permite la liberación de fondos hacia el destinatario/transportista. Requiere la firma criptográfica obligatoria del Auditor (extra_signatories).

ReportDiscrepancy (Constr 1): Habilita la redistribución o arbitraje de garantías en caso de faltantes o daños en mercadería. Requiere doble firma: Auditor + Remitente.

CancelShipment (Constr 2): Permite la recuperación del depósito al Remitente si el viaje es cancelado antes de iniciar ruta.

⚙️ Requisitos e Instalación
1. Prerrequisitos
Python 3.10+

Aiken v1.1.23+ (instalable mediante aikup)

Cuenta en Blockfrost.io con proyecto activo en Cardano Preprod.

2. Configuración de Entorno
Clonar el repositorio y preparar el archivo de variables:

PowerShell
git clone [https://github.com/dannyb4321/cardano-supply-chain-traceability.git](https://github.com/dannyb4321/cardano-supply-chain-traceability.git)
cd cardano-supply-chain-traceability
python -m pip install -r requirements.txt
Crear un archivo .env en la raíz:

Fragmento de código
BLOCKFROST_PROJECT_ID=preprodXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
Generar el par de llaves si se inicializa desde cero:

PowerShell
python generate_keys.py
🚀 Guía de Ejecución
1. Compilación y Test Unitario del Smart Contract
PowerShell
cd supply_chain_contract
aiken check
aiken build
cd ..
2. Operativa del Smart Contract Escrow
Derivar la dirección de script:

PowerShell
python escrow_contracts/inspect_contract.py
Bloquear fondos en custodia (3 tADA + Datum):

PowerShell
python escrow_contracts/lock_remito_escrow.py
Liberar fondos por entrega conforme (Redeemer ConfirmDelivery):

PowerShell
python escrow_contracts/unlock_remito_escrow.py
3. Trazabilidad de Estados CIP-20
Registrar despacho o actualización logística:

PowerShell
python cip20_metadata/dispatch_remito_cip20.py
python cip20_metadata/update_remito_state.py
4. Lanzar el Panel de Auditoría y Exportación PDF
PowerShell
python -m streamlit run dashboard_supply_chain.py
Acceder a http://localhost:8501 para auditar remitos y descargar el acta pericial con hash criptográfico y sello de tiempo on-chain.