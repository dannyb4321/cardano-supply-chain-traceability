-- Query: Monitoreo de Solvencia y Zonas de Liquidación en Indigo Protocol
-- Plataforma objetivo: Dune / Flipside (Cardano eUTxO)

WITH cdp_positions AS (
    SELECT 
        output_address,
        tx_hash,
        -- Colateral depositado en ADA (convertido de Lovelaces a ADA)
        lovelace_amount / 1e6 AS collateral_ada,
        -- Deuda acuñada en el sintético correspondiente
        asset_amount AS minted_debt,
        asset_name,
        datum_parsed
    FROM cardano.utxos
    WHERE output_address IN (
        -- Dirección del validador de CDPs de Indigo
        'addr1w85750h2q50j...'
    )
    AND is_spent = FALSE
),
market_prices AS (
    -- Último precio de oráculo (ej. Charli3 / Orcfax)
    SELECT 
        0.40 AS ada_price_usd,
        1.00 AS iusd_target_price,
        1.20 AS mcr_iusd          -- 120% Minimum Collateral Ratio
)
SELECT 
    p.tx_hash,
    p.collateral_ada,
    p.minted_debt,
    -- CR = (Colateral ADA * Precio ADA) / (Deuda iUSD * Precio Objetivo)
    ROUND((p.collateral_ada * m.ada_price_usd) / (p.minted_debt * m.iusd_target_price) * 100, 2) AS cr_percent,
    -- Precio de liquidación: P_liq = (Deuda * MCR) / Colateral ADA
    ROUND((p.minted_debt * m.mcr_iusd) / p.collateral_ada, 4) AS liquidation_price_usd,
    -- Clasificación de riesgo cuantitativo
    CASE 
        WHEN ((p.collateral_ada * m.ada_price_usd) / (p.minted_debt * m.iusd_target_price)) < 1.20 THEN 'CRITICO - LIQUIDABLE'
        WHEN ((p.collateral_ada * m.ada_price_usd) / (p.minted_debt * m.iusd_target_price)) BETWEEN 1.20 AND 1.35 THEN 'ALTO RIESGO'
        WHEN ((p.collateral_ada * m.ada_price_usd) / (p.minted_debt * m.iusd_target_price)) BETWEEN 1.35 AND 1.60 THEN 'MODERADO'
        ELSE 'SALUDABLE'
    END AS risk_tier
FROM cdp_positions p
CROSS JOIN market_prices m
ORDER BY cr_percent ASC;