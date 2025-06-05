import streamlit as st
import yfinance as yf
import plotly.graph_objs as go

st.set_page_config(page_title="Simulador de Portafolio", layout="wide")
st.title("📊 Simulador Financiero de Portafolio")

# =======================
# Cache para obtener precio (5 minutos)
# =======================
@st.cache_data(ttl=300)
def obtener_precio_cache(ticker):
    try:
        data = yf.Ticker(ticker)
        hist = data.history(period="1d")
        if hist.empty:
            return None
        return hist["Close"].iloc[-1]
    except Exception as e:
        return None

# =======================
# Inicialización del portafolio
# =======================
if "portafolio" not in st.session_state:
    st.session_state.portafolio = []

# =======================
# Agregar activos
# =======================
st.sidebar.header("➕ Agregar Inversión")
with st.sidebar.form("form_inversion"):
    ticker = st.text_input("Ticker (ej: AAPL)", max_chars=10).upper()
    cantidad = st.number_input("Cantidad de acciones", min_value=1, step=1)
    precio_compra = st.number_input("Precio de compra (USD)", min_value=0.0, format="%.2f")
    agregar = st.form_submit_button("Agregar")

    if agregar and ticker and cantidad > 0:
        st.session_state.portafolio.append({
            "ticker": ticker,
            "cantidad": cantidad,
            "precio_compra": precio_compra
        })
        st.success(f"✅ Agregado {cantidad} de {ticker}")
        # Aquí se elimina st.experimental_rerun()

# =======================
# Mostrar portafolio actual
# =======================
st.subheader("📌 Portafolio Actual")

if st.session_state.portafolio:
    datos = []
    for inv in st.session_state.portafolio:
        ticker = inv["ticker"]
        cantidad = inv["cantidad"]
        precio_actual = obtener_precio_cache(ticker)
        if precio_actual is None:
            st.warning(f"⚠️ No se encontraron datos para {ticker}. Verifica el ticker.")
            continue
        valor_actual = round(cantidad * precio_actual, 2)
        datos.append({
            "Ticker": ticker,
            "Cantidad": cantidad,
            "Precio compra": inv["precio_compra"],
            "Precio actual": round(precio_actual, 2),
            "Valor actual": valor_actual
        })
    if datos:
        st.dataframe(datos, use_container_width=True)
    else:
        st.warning("⚠️ No se pudo mostrar el portafolio. Revisa los tickers o tu conexión.")
else:
    st.info("No hay inversiones registradas aún.")

# =======================
# Simulación Global Ajustable y Detallada
# =======================
st.header("📈 Simulación Global del Portafolio (Ajustable y Detallada)")

if st.session_state.portafolio:
    st.markdown("Ajusta los porcentajes para simular distintos escenarios de mercado:")

    col1, col2, col3 = st.columns(3)
    with col1:
        pesimista_pct = st.slider("📉 Pesimista (%)", min_value=-90, max_value=0, value=-20)
    with col2:
        neutral_pct = st.slider("😐 Neutral (%)", min_value=-50, max_value=50, value=0)
    with col3:
        optimista_pct = st.slider("🚀 Optimista (%)", min_value=0, max_value=200, value=30)

    resultados = []
    total_actual_portafolio = 0

    for inv in st.session_state.portafolio:
        ticker = inv["ticker"]
        cantidad = inv["cantidad"]
        precio_actual = obtener_precio_cache(ticker)

        if precio_actual is None:
            st.warning(f"⚠️ Precio no disponible para {ticker}, omitido de la simulación.")
            continue

        valor_actual = cantidad * precio_actual
        total_actual_portafolio += valor_actual

        escenarios = {
            f"📉 Pesimista ({pesimista_pct}%)": precio_actual * (1 + pesimista_pct / 100),
            f"😐 Neutral ({neutral_pct}%)": precio_actual * (1 + neutral_pct / 100),
            f"🚀 Optimista ({optimista_pct}%)": precio_actual * (1 + optimista_pct / 100),
        }

        for nombre_esc, precio_simulado in escenarios.items():
            valor_futuro = cantidad * precio_simulado
            diferencia = valor_futuro - valor_actual
            rendimiento = (diferencia / valor_actual) * 100 if valor_actual != 0 else 0

            resultados.append({
                "Ticker": ticker,
                "Escenario": nombre_esc,
                "Valor actual ($)": round(valor_actual, 2),
                "Valor futuro ($)": round(valor_futuro, 2),
                "Diferencia ($)": round(diferencia, 2),
                "Rendimiento (%)": round(rendimiento, 2)
            })

    if resultados:
        st.subheader("📋 Resultados detallados por activo")
        st.dataframe(resultados, use_container_width=True)

        st.subheader("📊 Comparación por activo y escenario")
        fig = go.Figure()
        escenarios_unicos = sorted(set(r["Escenario"] for r in resultados))

        for escenario in escenarios_unicos:
            x = [r["Ticker"] for r in resultados if r["Escenario"] == escenario]
            y = [r["Valor futuro ($)"] for r in resultados if r["Escenario"] == escenario]
            fig.add_trace(go.Bar(name=escenario, x=x, y=y))

        fig.update_layout(title="Proyección por Escenario", barmode="group")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("🔢 Valor total del portafolio por escenario")
        resumen = {}
        for escenario in escenarios_unicos:
            total_escenario = sum(r["Valor futuro ($)"] for r in resultados if r["Escenario"] == escenario)
            diferencia = total_escenario - total_actual_portafolio
            rendimiento = (diferencia / total_actual_portafolio) * 100 if total_actual_portafolio != 0 else 0
            resumen[escenario] = {
                "Valor futuro total ($)": round(total_escenario, 2),
                "Diferencia total ($)": round(diferencia, 2),
                "Rendimiento total (%)": round(rendimiento, 2)
            }

        st.write(resumen)
    else:
        st.warning("⚠️ No hay resultados para mostrar. Verifica que todos los tickers sean válidos.")
else:
    st.info("Agrega al menos una inversión para usar la simulación.")
    # =======================
# 📉 Gráfico histórico de precios
# =======================
st.header("📉 Gráfico histórico de precios")

if st.session_state.portafolio:
    tickers_disponibles = [inv["ticker"] for inv in st.session_state.portafolio]
    ticker_hist = st.selectbox("Selecciona un activo para ver su histórico", tickers_disponibles)

    data = yf.Ticker(ticker_hist).history(period="6mo")
    if not data.empty:
        data["SMA20"] = data["Close"].rolling(window=20).mean()

        fig_hist = go.Figure()
        fig_hist.add_trace(go.Scatter(x=data.index, y=data["Close"], name="Precio cierre", line=dict(color='blue')))
        fig_hist.add_trace(go.Scatter(x=data.index, y=data["SMA20"], name="Media móvil 20d", line=dict(color='orange')))
        fig_hist.update_layout(title=f"Histórico de {ticker_hist}", xaxis_title="Fecha", yaxis_title="Precio (USD)")
        st.plotly_chart(fig_hist, use_container_width=True)
    else:
        st.warning(f"No se pudo obtener el histórico para {ticker_hist}.")

# =======================
# 📊 Comparación con Benchmarks
# =======================
st.header("📊 Comparación con Benchmarks (últimos 6 meses)")

tickers_benchmark = ["^GSPC", "^IXIC", "BTC-USD"]
nombres = {"^GSPC": "S&P 500", "^IXIC": "Nasdaq", "BTC-USD": "Bitcoin"}

rendimiento_portafolio = []
for inv in st.session_state.portafolio:
    ticker = inv["ticker"]
    precio_actual = obtener_precio_cache(ticker)
    if precio_actual:
        rendimiento = (precio_actual - inv["precio_compra"]) / inv["precio_compra"] * 100
        rendimiento_portafolio.append(rendimiento)

rend_total = sum(rendimiento_portafolio) / len(rendimiento_portafolio) if rendimiento_portafolio else 0

data_bench = yf.download(tickers_benchmark, period="6mo")["Close"]

if not data_bench.empty:
    fig_bench = go.Figure()
    for ticker in tickers_benchmark:
        if ticker in data_bench:
            serie = data_bench[ticker]
            serie_norm = (serie / serie.iloc[0]) * 100
            fig_bench.add_trace(go.Scatter(x=serie.index, y=serie_norm, name=nombres[ticker]))

    fig_bench.add_trace(go.Scatter(
        x=data_bench.index,
        y=[100 + rend_total] * len(data_bench),
        name="Mi portafolio",
        line=dict(color="black", dash="dash")
    ))

    fig_bench.update_layout(title="Comparación con Benchmarks", xaxis_title="Fecha", yaxis_title="Índice base 100")
    st.plotly_chart(fig_bench, use_container_width=True)
else:
    st.warning("No se pudieron obtener los datos de benchmarks.")

# =======================
# 🧠 Revisión de Diversificación
# =======================
st.header("🧠 Revisión de Diversificación")

if st.session_state.portafolio:
    total_valor = 0
    valores = {}
    for inv in st.session_state.portafolio:
        ticker = inv["ticker"]
        cantidad = inv["cantidad"]
        precio = obtener_precio_cache(ticker)
        if precio:
            valor = cantidad * precio
            total_valor += valor
            valores[ticker] = valor

    if total_valor > 0:
        st.subheader("Distribución del portafolio")
        fig_pie = go.Figure(data=[go.Pie(labels=list(valores.keys()), values=list(valores.values()))])
        st.plotly_chart(fig_pie, use_container_width=True)

        for ticker, valor in valores.items():
            porcentaje = (valor / total_valor) * 100
            if porcentaje > 50:
                st.warning(f"⚠️ Tienes el {porcentaje:.2f}% del portafolio en {ticker}. Considera diversificar.")
