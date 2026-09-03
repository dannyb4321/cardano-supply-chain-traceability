use aiken/collection/list
use aiken/crypto.{VerificationKeyHash}
use cardano/transaction.{OutputReference, Transaction, placeholder}

/// Estado asociado a la carga / remito
pub type SupplyChainDatum {
  sender: VerificationKeyHash,
  transporter: VerificationKeyHash,
  auditor: VerificationKeyHash,
  remito_id: ByteArray,
}

/// Acciones operativas que pueden desbloquear o liquidar la custodia
pub type LogisticsAction {
  ConfirmDelivery
  ReportDiscrepancy
  CancelShipment
}

validator logistics_escrow {
  spend(
    datum: Option<SupplyChainDatum>,
    redeemer: LogisticsAction,
    _target_utxo: OutputReference,
    self: Transaction,
  ) {
    expect Some(d) = datum

    when redeemer is {
      ConfirmDelivery ->
        list.has(self.extra_signatories, d.auditor)

      ReportDiscrepancy ->
        list.has(self.extra_signatories, d.auditor) && list.has(
          self.extra_signatories,
          d.sender,
        )

      CancelShipment ->
        list.has(self.extra_signatories, d.sender)
    }
  }

  else(_) {
    fail
  }
}

// ==========================================
// PRUEBAS UNITARIAS ON-CHAIN
// ==========================================

test entrega_conforme_por_auditor_autorizado() {
  let auditor = #"0102030405"
  let sender = #"0607080910"
  let transporter = #"1112131415"
  
  let datum = SupplyChainDatum {
    sender,
    transporter,
    auditor,
    remito_id: "REM-2026-0827-NK",
  }
  let dummy_utxo = OutputReference {
    transaction_id: #"0000000000000000000000000000000000000000000000000000000000000000",
    output_index: 0,
  }
  let tx = Transaction { ..placeholder, extra_signatories: [auditor] }

  logistics_escrow.spend(Some(datum), ConfirmDelivery, dummy_utxo, tx)
}

test rechazar_si_auditor_no_firma() {
  let auditor = #"0102030405"
  let sender = #"0607080910"
  let transporter = #"1112131415"
  let intruso = #"9999999999"

  let datum = SupplyChainDatum {
    sender,
    transporter,
    auditor,
    remito_id: "REM-2026-0827-NK",
  }
  let dummy_utxo = OutputReference {
    transaction_id: #"0000000000000000000000000000000000000000000000000000000000000000",
    output_index: 0,
  }
  // Firma un tercero no autorizado
  let tx = Transaction { ..placeholder, extra_signatories: [intruso] }

  !logistics_escrow.spend(Some(datum), ConfirmDelivery, dummy_utxo, tx)
}

test discrepancia_requiere_doble_firma() {
  let auditor = #"0102030405"
  let sender = #"0607080910"
  let transporter = #"1112131415"

  let datum = SupplyChainDatum {
    sender,
    transporter,
    auditor,
    remito_id: "REM-2026-0827-NK",
  }
  let dummy_utxo = OutputReference {
    transaction_id: #"0000000000000000000000000000000000000000000000000000000000000000",
    output_index: 0,
  }
  
  // Ambas firmas presentes (Auditor + Sender)
  let tx = Transaction { ..placeholder, extra_signatories: [auditor, sender] }

  logistics_escrow.spend(Some(datum), ReportDiscrepancy, dummy_utxo, tx)
}