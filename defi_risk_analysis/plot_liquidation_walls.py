import os
import webbrowser
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_PATH = os.path.join(BASE_DIR, "data", "cdp_positions.csv")
HTML_OUTPUT = os.path.join(BASE_DIR, "liquidation_walls.html")

MCR = 1.20
PRECIO_BASE_ADA = 0.40
CAPACIDAD_STABILITY_POOL = 35000.0  # USD


def generar_grafico_liquidaciones():
    df = pd.read_csv(DATA_PATH)
    df["liq_price_usd"] = (df["minted_iusd"] * MCR) / df["collateral_ada"]

    # Ordenar por precio de liquidación descendente (los que quiebran primero)
    df = df.sort_values("liq_price_usd", ascending=False).reset_index(drop=True)
    df["deuda_acumulada_iusd"] = df["minted_iusd"].cumsum()
    df["ada_acumulado"] = df["collateral_ada"].cumsum()

    # Crear figura con eje Y secundario
    fig = make_subplots(
        rows=1,
        cols=1,
        specs=[[{"secondary_y": True}]],
    )

    # 1. Barras de Colateral ADA expuesto en cada nivel de precio
    fig.add_trace(
        go.Bar(
            x=[f"${p:.4f}" for p in df["liq_price_usd"]],
            y=df["collateral_ada"],
            name="Colateral en Riesgo (ADA)",
            marker_color="#3b82f6",
            opacity=0.75,
            hovertemplate="<b>%{x}</b><br>Colateral: %{y:,.0f} ADA<br>CDP: "
            + df["cdp_id"]
            + " ("
            + df["owner_ref"]
            + ")<extra></extra>",
        ),
        secondary_y=False,
    )

    # 2. Línea de Deuda Acumulada a Liquidar (iUSD)
    fig.add_trace(
        go.Scatter(
            x=[f"${p:.4f}" for p in df["liq_price_usd"]],
            y=df["deuda_acumulada_iusd"],
            name="Deuda Acumulada Exigible (iUSD)",
            mode="lines+markers",
            line=dict(color="#ef4444", width=3),
            marker=dict(size=8),
            hovertemplate="<b>%{x}</b><br>Deuda Acumulada: $%{y:,.2f} iUSD<extra></extra>",
        ),
        secondary_y=True,
    )

    # 3. Línea horizontal de Capacidad Máxima del Stability Pool ($35k)
    fig.add_hline(
        y=CAPACIDAD_STABILITY_POOL,
        line_dash="dash",
        line_color="#10b981",
        line_width=2,
        annotation_text=f"Capacidad Stability Pool (${CAPACIDAD_STABILITY_POOL:,.0f} iUSD)",
        annotation_position="top left",
        secondary_y=True,
    )

    # Ajustes estéticos y layout profesional
    fig.update_layout(
        title=dict(
            text="<b>Indigo Protocol — Paredes de Liquidación & Curva de Deuda</b><br><sup>Monitoreo de estrés de mercado sobre colaterales ADA y absorción del Stability Pool</sup>",
            x=0.05,
        ),
        template="plotly_dark",
        height=600,
        legend=dict(x=0.05, y=0.90, bgcolor="rgba(0,0,0,0.5)"),
        hovermode="x unified",
        margin=dict(l=40, r=40, t=80, b=40),
    )

    fig.update_xaxes(
        title_text="Precio Crítico de Liquidación de ADA (USD)",
        autorange="reversed",
    )
    fig.update_yaxes(
        title_text="Colateral ADA por Nivel de Precio",
        secondary_y=False,
        showgrid=False,
    )
    fig.update_yaxes(
        title_text="Deuda Acumulada iUSD", secondary_y=True, showgrid=True
    )

    # Guardar y abrir
    fig.write_html(HTML_OUTPUT)
    print(f"\n📊 Gráfico interactivo generado con éxito en: {HTML_OUTPUT}")
    webbrowser.open(f"file://{HTML_OUTPUT}")


if __name__ == "__main__":
    generar_grafico_liquidaciones()