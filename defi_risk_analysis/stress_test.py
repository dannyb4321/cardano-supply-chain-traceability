import os
import pandas as pd

DATA_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "data", "cdp_positions.csv"
)

# Parámetros base del protocolo
MCR = 1.20  # 120% Minimum Collateral Ratio para iUSD
PRECIO_BASE_ADA = 0.40  # USD
STABILITY_POOL_IUSD = 35000.0  # Liquidez disponible en el Stability Pool para absorber deuda


def cargar_posiciones() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    # Precio de liquidación individual: P_liq = (Deuda * MCR) / Colateral ADA
    df["liq_price_usd"] = (df["minted_iusd"] * MCR) / df["collateral_ada"]
    df["cr_base"] = (
        (df["collateral_ada"] * PRECIO_BASE_ADA) / df["minted_iusd"]
    ) * 100
    return df


def evaluar_escenario(
    df: pd.DataFrame, nombre: str, shock_pct: float
) -> dict:
    precio_simulado = PRECIO_BASE_ADA * (1.0 + shock_pct)
    cr_simulado = (
        (df["collateral_ada"] * precio_simulado) / df["minted_iusd"]
    ) * 100

    # Posiciones con CR < 120%
    insolventes = df[cr_simulado < (MCR * 100)]

    ada_liquidable = insolventes["collateral_ada"].sum()
    deuda_a_liquidar = insolventes["minted_iusd"].sum()
    cant_cdps = len(insolventes)

    # Cobertura del Stability Pool
    cobertura_pct = (
        (STABILITY_POOL_IUSD / deuda_a_liquidar * 100)
        if deuda_a_liquidar > 0
        else 100.0
    )
    deficit_deuda = max(0.0, deuda_a_liquidar - STABILITY_POOL_IUSD)

    return {
        "Escenario": nombre,
        "Precio ADA": f"${precio_simulado:.4f}",
        "Shock": f"{shock_pct*100:+.0f}%",
        "CDPs Liquidables": f"{cant_cdps} / {len(df)}",
        "ADA en Riesgo": f"{ada_liquidable:,.0f} ADA",
        "Deuda a Liquidar": f"${deuda_a_liquidar:,.2f} iUSD",
        "Capacidad SP": f"{cobertura_pct:.1f}%",
        "Deuda Incobrable": f"${deficit_deuda:,.2f} iUSD",
    }


def ejecutar_stress_test():
    df = cargar_posiciones()

    print("\n" + "=" * 80)
    print("      INDIGO PROTOCOL — REPORTE CUANTITATIVO DE RIESGO DE LIQUIDACIÓN")
    print(f"      Precio Base ADA: ${PRECIO_BASE_ADA:.2f} | MCR: {MCR*100:.0f}% | Stability Pool: ${STABILITY_POOL_IUSD:,.0f} iUSD")
    print("=" * 80 + "\n")

    # Tabla de posiciones ordenadas por cercanía al colapso
    print("--- RANKING DE VULNERABILIDAD DE POSICIONES (TOP CRÍTICAS) ---")
    pos_resumen = df[
        ["cdp_id", "owner_ref", "collateral_ada", "minted_iusd", "liq_price_usd", "cr_base"]
    ].sort_values("cr_base")
    pos_resumen.columns = [
        "CDP ID",
        "Owner",
        "Colateral (ADA)",
        "Deuda (iUSD)",
        "P. Liq ($)",
        "CR Inicial (%)",
    ]
    print(
        pos_resumen.to_string(
            index=False,
            formatters={
                "Colateral (ADA)": "{:,.0f}".format,
                "Deuda (iUSD)": "${:,.2f}".format,
                "P. Liq ($)": "${:.4f}".format,
                "CR Inicial (%)": "{:.1f}%".format,
            },
        )
    )

    # Matriz de Estrés
    escenarios = [
        ("Línea Base", 0.0),
        ("Corrección Normal", -0.15),
        ("Volatilidad Alta", -0.30),
        ("Shock Sistémico (Flash Crash)", -0.50),
    ]

    resultados = [
        evaluar_escenario(df, nombre, shock) for nombre, shock in escenarios
    ]
    df_resultados = pd.DataFrame(resultados)

    print("\n--- SIMULACIÓN DE ESCENARIOS DE ESTRÉS Y ABSORCIÓN DE SHOCK ---")
    print(df_resultados.to_string(index=False))
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    ejecutar_stress_test()