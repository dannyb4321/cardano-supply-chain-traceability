# Informe Técnico de Riesgo Cuantitativo y Solvencia: Indigo Protocol (iUSD CDP System)

**Documento:** Evaluación de Riesgo de Liquidación y Capacidad de Absorción del Stability Pool  
**Protocolo:** Indigo Protocol (Cardano eUTxO Architecture)  
**Activo Sintético:** iUSD (Peg: 1.00 USD)  
**Colateral Subyacente:** ADA (Cardano Native Asset)  
**Fecha de Emisión:** Septiembre 2026  
**Versión:** 1.0.0 (Production-Ready Audit Release)  

---

## 1. Resumen Ejecutivo

El presente informe evalúa la robustez financiera y la solvencia operativa del sistema de Posiciones de Deuda Colateralizada (CDP) de **Indigo Protocol** en la red Cardano ante fluctuaciones adversas en el precio de mercado de ADA.

A través de un análisis cuantitativo de microdatos on-chain y la ejecución de modelos de estrés financiero (*stress testing*), se evaluó el comportamiento de una muestra representativa de 10 posiciones de deuda institucionales y minoristas bajo cuatro escenarios de mercado: **Línea Base ($0.40 ADA)**, **Corrección Normal (-15%)**, **Volatilidad Aguda (-30%)** y **Shock Sistémico / Flash Crash (-50%)**.

### Hallazgos Principales:
1. **Solvencia en Escenarios Moderados:** Ante caídas de hasta el **-30% en el precio de ADA ($0.28 USD)**, la liquidez actual del *Stability Pool* ($35,000.00 iUSD) resulta suficiente para liquidar holgadamente las posiciones insolventes sin generar deuda incobrable (*bad debt*), registrando un ratio de cobertura del **108.5%**.
2. **Punto de Quiebre de Liquidez (Insolvencia Crítica):** Ante un shock sistémico de **-50% ($0.20 USD)**, el 100% de las posiciones de la muestra ingresan en zona de liquidación simultánea, generando una demanda de absorción de **$63,250.00 iUSD**. Dado el tamaño del pool, se agota la liquidez disponible (cobertura del 55.3%), exponiendo al protocolo a un déficit neto de **$28,250.00 iUSD de deuda incobrable**, lo que pondría en riesgo el *peg* de iUSD en mercados secundarios.

---

## 2. Arquitectura de Deuda bajo el Modelo eUTxO

A diferencia de los protocolos basados en cuentas en Ethereum (donde el estado de un CDP reside en el almacenamiento global de un contrato), Indigo implementa un modelo **eUTxO (Extended Unspent Transaction Output)**:

* **CDP como UTxO Independiente:** Cada posición de deuda es un UTxO único custodiado por el validador Plutus de Indigo. El estado de la posición reside íntegramente en su **Datum**, conteniendo:
  * `owner_pkh`: Hash de clave pública del propietario.
  * `collateral_lovelace`: Cantidad de Lovelaces depositados.
  * `minted_iassets`: Cantidad de iUSD acuñados.
  * `cdp_id`: Token NFT que garantiza trazabilidad e indivisibilidad.
* **Liquidación Instantánea sin Subastas:** Para mitigar la contención de UTxOs y la congestión por guerras de gas (*gas wars*), Indigo no recurre a subastas inglesas lentas. En su lugar, utiliza el **Stability Pool**: los liquidadores (bots / Keepers) consumen el UTxO del CDP insolvente en una única transacción atómica, quemando iUSD del pool y transfiriendo el colateral ADA a los depositantes con un descuento de arbitraje predeterminado.

---

## 3. Formulación Matemática de Riesgo

### 3.1. Ratio de Colateralización ($CR$)
El ratio de solvencia de cada posición se define en tiempo real como:

$$CR = \frac{C_{\text{ADA}} \cdot P_{\text{ADA}}}{D_{\text{iUSD}} \cdot P_{\text{target}}}$$

Donde:
* $C_{\text{ADA}}$: Colateral depositado en ADA.
* $P_{\text{ADA}}$: Precio spot provisto por el oráculo on-chain (Charli3 / Orcfax).
* $D_{\text{iUSD}}$: Deuda nominal acuñada en iUSD.
* $P_{\text{target}}$: Valor de anclaje ($1.00 USD).

### 3.2. Minimum Collateralization Ratio ($MCR$) y Precio de Liquidación ($P_{\text{liq}}$)
El parámetro de gobernanza establece un **MCR del 120% (1.20)** para iUSD. Una posición se declara insolvente cuando $CR < MCR$.

El precio crítico de liquidación se despeja analíticamente:

$$P_{\text{liq}} = \frac{D_{\text{iUSD}} \cdot MCR}{C_{\text{ADA}}}$$

---

## 4. Auditoría de Posiciones y Ranking de Vulnerabilidad

Se analizó la distribución de colateral sobre una cartera agregada de **272,000 ADA** y **$63,250.00 iUSD** en circulación, clasificada por proximidad al precio de liquidación (precio spot base: **$0.40 USD**):

| CDP ID | Propietario / Perfil | Colateral (ADA) | Deuda (iUSD) | P. Liq ($ USD) | CR Base (%) | Margen de Seguridad | Nivel de Riesgo |
|:---|:---|:---:|:---:|:---:|:---:|:---:|:---:|
| **CDP-004** | Retail_User1 | 8,000 | $2,400.00 | $0.3600 | 133.3% | -10.0% | **Crítico** |
| **CDP-010** | Micro_CDP | 4,000 | $1,250.00 | $0.3750 | 128.0% | -6.3% | **Crítico** |
| **CDP-007** | Aggressive_01 | 10,000 | $3,100.00 | $0.3720 | 129.0% | -7.0% | **Crítico** |
| **CDP-005** | Retail_User2 | 12,000 | $3,800.00 | $0.3800 | 126.3% | -5.0% | **Crítico** |
| **CDP-002** | Trader_Beta | 15,000 | $4,500.00 | $0.3600 | 133.3% | -10.0% | **Crítico** |
| **CDP-009** | Swing_Trader | 18,000 | $5,200.00 | $0.3467 | 138.5% | -13.3% | **Alto** |
| **CDP-003** | Treasury_DAO | 50,000 | $12,000.00 | $0.2880 | 166.7% | -28.0% | **Moderado** |
| **CDP-001** | Whale_Alpha | 25,000 | $5,000.00 | $0.2400 | 200.0% | -40.0% | **Saludable** |
| **CDP-006** | Fund_Gamma | 30,000 | $6,000.00 | $0.2400 | 200.0% | -40.0% | **Saludable** |
| **CDP-008** | Institution_01 | 100,000 | $20,000.00 | $0.2400 | 200.0% | -40.0% | **Saludable** |

*Nota Metodológica:* El 60% de los CDPs (6 posiciones) operan con ratios de apalancamiento agresivos ($CR < 135\%$), lo que los hace vulnerables ante correcciones intradía estándar de mercado.

---

## 5. Simulación de Escenarios de Estrés (Stress Testing)

Se modeló el impacto acumulado sobre el protocolo considerando un fondo en el **Stability Pool de $35,000.00 iUSD**:

| Escenario | Precio Simulado ADA | Variación (%) | CDPs Liquidados | ADA en Riesgo | Deuda a Liquidar | Capacidad Stability Pool | Deuda Incobrable (Bad Debt) |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Línea Base** | $0.4000 | 0% | 0 / 10 | 0 ADA | $0.00 iUSD | 100.0% | $0.00 iUSD |
| **Corrección Normal** | $0.3400 | -15% | 6 / 10 | 67,000 ADA | $20,250.00 iUSD | 172.8% | $0.00 iUSD |
| **Volatilidad Alta** | $0.2800 | -30% | 7 / 10 | 117,000 ADA | $32,250.00 iUSD | 108.5% | $0.00 iUSD |
| **Flash Crash** | $0.2000 | -50% | 10 / 10 | 272,000 ADA | $63,250.00 iUSD | 55.3% | **$28,250.00 iUSD** |

### Análisis Dinámico por Fase de Contagio:
1. **Fase I ($0.34 USD - Shock de -15%):**  
   Cae la primera barrera defensiva conformada por los 6 CDPs minoristas y traders apalancados. Se liquidan **67,000 ADA** y se absorben **$20,250.00 iUSD**. El Stability Pool responde de manera óptima y retiene $14,750.00 iUSD de liquidez remanente.
2. **Fase II ($0.28 USD - Shock de -30%):**  
   Se activa la posición de tesorería descentralizada (`CDP-003`), elevando el colateral liquidado a **117,000 ADA** y la deuda acumulada a **$32,250.00 iUSD**. El Stability Pool opera al **92.1% de su capacidad total**, logrando contener el 100% de la deuda sin insolvencia.
3. **Fase III ($0.20 USD - Shock de -50%):**  
   Incluso las carteras institucionales más conservadoras (200% CR inicial) perforan el umbral del 120%. La deuda acumulada supera la capacidad física del pool en un **80.7%**. Al no haber suficientes iUSD en el pool para quemar la deuda, los Keepers no pueden liquidar las posiciones, generando **$28,250.00 iUSD de deuda incobrable**.

---

## 6. Dictamen Técnico y Recomendaciones de Gobernanza

1. **Parámetro MCR Dinámico por Escala:** El MCR fijo de 120% no discrimina entre posiciones pequeñas y ballenas institucionales. Se recomienda implementar un MCR escalonado (120% para posiciones < 10,000 ADA, y 135% para posiciones > 50,000 ADA) para reducir el impacto de liquidaciones masivas concentradas.
2. **Incentivos de Estabilidad (Stability Pool APR Boost):** Para prevenir el déficit en Fase III, la gobernanza debe fijar un mecanismo automático que aumente las recompensas en tokens $INDY cuando el ratio de cobertura del Stability Pool caiga por debajo del 120% de la deuda total en riesgo.
3. **Mecanismo Secundario de Liquidación (Redistribución de Deuda):** Incorporar un fallback inspirado en Liquity, donde la deuda y el colateral no absorbidos por el Stability Pool se redistribuyan proporcionalmente entre los CDPs solventes restantes, evitando la generación de deuda incobrable en la contabilidad del sistema.