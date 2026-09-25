# Project Catalyst Proposal: TraceAid

**Project Title:** TraceAid: Open-Source eUTxO Supply Chain & Physical Custody Audit for Humanitarian NGOs  
**Target Category:** Cardano Use Cases: Real World / Open Source Solutions  
**Requested Funds:** 75,000 ADA  
**Duration:** 4 Months  
**Project Lead:** Claudio Daniel Bogado Centurión  
**GitHub Repository:** https://github.com/dannyb4321/cardano-supply-chain-traceability  

---

## 1. Problem Statement & Proposed Solution

### The Problem
Humanitarian organizations and grassroots NGOs face severe opacity in last-mile logistics. An estimated 15% to 25% of donated food, clothing, and medical supplies suffer discrepancies due to unaccounted waste, handling damage, and transit spoilage. Current tracking relies on disconnected paper manifests or expensive corporate ERPs that prevent public donors and independent oversight bodies from validating chain-of-custody proofs in real time.

### The Solution
TraceAid is an open-source, lightweight custody framework built on Cardano Preprod/Mainnet. By utilizing individual UTxOs to represent donation batches and enforcing CIP-20 standardized metadata (label 674), each operational transition (Intake, Consolidation/Inspection, Delivery) generates an immutable, tamper-proof cryptographic audit trail. Donors and community auditors verify shipments via dynamic Sankey flow models and public explorer links without third-party reliance.

---

## 2. Milestone Breakdown & Deliverables

### Milestone 1: Core Engine Hardening & Cryptographic Pipeline
* **Duration:** 1 Month
* **Budget:** 22,500 ADA (30%)
* **Deliverables:**
  * Centralized, resilient Blockfrost client with exponential backoff and rate-limit handling.
  * Pydantic schemas enforcing Cardano CIP-20 (64-byte limit) and eUTxO hash linking.
  * Automated test suite covering metadata serialization and state validation.
* **Acceptance Criteria:**
  * 100% pass rate on `pytest` test suite.
  * Validated mock transaction pipeline confirming parent-child hash integrity.
* **Evidence of Completion:**
  * Public GitHub commit with test reports and clean CI/CD workflow runs.

### Milestone 2: Operational Interface & Hardware Integration
* **Duration:** 1 Month
* **Budget:** 22,500 ADA (30%)
* **Deliverables:**
  * Multi-role Streamlit dashboard displaying batch metrics, dynamic Sankey balances, and cryptographic proofs.
  * QR dispatch engine generating encrypted labels for warehouse scanning.
  * Bidirectional sync layer linking on-chain data with local relational stores and external tables.
* **Acceptance Criteria:**
  * Interactive UI capable of parsing and visualizing custody loss/shrinkage in real time.
  * Functional scanning workflow from mobile/Zebra camera readers to ledger lookup.
* **Evidence of Completion:**
  * Live deployed demo web application and operational video demonstration.

### Milestone 3: Field Pilot Deployment (Grassroots NGO)
* **Duration:** 1 Month
* **Budget:** 18,750 ADA (25%)
* **Deliverables:**
  * Real-world trial tracking 1,000 physical food kits across 3 operational nodes (Acopio Central, Depósito, Comedor Comunitario).
  * Field training program for logistics operators on QR scanning and custody event creation.
  * Pilot incident and shrinkage report verified on Cardano Preprod.
* **Acceptance Criteria:**
  * At least 1,000 physical kits successfully tracked across all three states with corresponding on-chain transactions.
  * Zero untracked inventory discrepancies between physical tally and on-chain records.
* **Evidence of Completion:**
  * Published transaction registry with all 1,000 associated Tx Hashes on Cardanoscan, accompanied by a signed letter of confirmation from the participating NGO leadership.

### Milestone 4: Documentation, Ecosystem Value & Close-Out
* **Duration:** 1 Month
* **Budget:** 11,250 ADA (15%)
* **Deliverables:**
  * Production-ready deployment guide and API architecture documentation.
  * Comprehensive Project Close-out Report and 2-minute bilingual showcase video.
  * Modular developer toolkit for other NGOs looking to deploy on Cardano.
* **Acceptance Criteria:**
  * Complete, reproducible documentation enabling third-party deployment from scratch in under 30 minutes.
  * Submission of all required Catalyst Close-out forms and public repository release under Apache 2.0 / MIT license.
* **Evidence of Completion:**
  * Close-out report link, final demonstration video URL, and tagged `v1.0.0` GitHub release.

---

## 3. Detailed Budget Allocation

| Category | Description | Allocation (ADA) | % |
|:---|:---|:---:|:---:|
| **Backend & Smart Contracts** | Architecture refactoring, Pydantic validation, Blockfrost client, CIP-20 compliance | 25,000 ADA | 33.3% |
| **Frontend & UI/UX** | Streamlit dashboard, Sankey flow visualization, QR generator module | 20,000 ADA | 26.7% |
| **Field Logistics & Pilot Testing** | On-site deployment, hardware calibration (QR/scanners), operator onboarding | 15,000 ADA | 20.0% |
| **Testing, Audit & Security** | Automated Pytest suite, mock-chain stress testing, cryptographic verification | 8,000 ADA | 10.7% |
| **Documentation & Video Demo** | Bilingual guides, installation tutorials, community showcase video | 7,000 ADA | 9.3% |
| **Total Requested** | | **75,000 ADA** | **100%** |

---

## 4. Key Performance Indicators (KPIs) & Cardano Ecosystem Value

* **On-Chain Transactions Generated:** > 1,500 verifiable transactions across testing and pilot phases.
* **Shrinkage Detection Rate:** 100% of physical cargo loss accounted for within the metadata payload.
* **Developer Adoption:** Clean, forkable template repository for real-world eUTxO supply chain tracking.
* **Public Cardano Narrative:** Concrete proof of utility showcasing Cardano solving real-world humanitarian supply challenges beyond speculative trading.