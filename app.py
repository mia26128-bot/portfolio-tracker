import streamlit as st
import yfinance as yf
import pandas as pd
import time
from datetime import datetime, timedelta
import plotly.express as px

# Configurazione pagina
st.set_page_config(
    page_title="💰 Portfolio Live",
    page_icon="💰",
    layout="wide"
)

# CSS per styling e animazioni
st.markdown("""
<style>
    .live-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        background-color: #00ff00;
        border-radius: 50%;
        animation: pulse 1.5s infinite;
        margin-right: 8px;
    }
    @keyframes pulse {
        0% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.6; transform: scale(1.1); }
        100% { opacity: 1; transform: scale(1); }
    }
    .metric-positive { color: #00C851 !important; font-weight: bold; }
    .metric-negative { color: #ff4444 !important; font-weight: bold; }
    .refresh-counter {
        position: fixed;
        top: 70px;
        right: 20px;
        background: rgba(31, 78, 121, 0.9);
        color: white;
        padding: 8px 15px;
        border-radius: 20px;
        font-size: 14px;
        font-weight: bold;
        z-index: 1000;
        box-shadow: 0 2px 10px rgba(0,0,0,0.3);
    }
    .status-indicator {
        font-size: 18px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Inizializza session state
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = pd.DataFrame(columns=['Ticker', 'Quantità', 'Prezzo_Acquisto', 'Data_Acquisto'])
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = True
if 'refresh_counter' not in st.session_state:
    st.session_state.refresh_counter = 0
if 'last_prices' not in st.session_state:
    st.session_state.last_prices = {}

# Funzione ottimizzata per ottenere prezzi
@st.cache_data(ttl=5, show_spinner=False)
def get_live_price_fast(ticker):
    try:
        stock = yf.Ticker(ticker)
        
        # Per crypto - metodo più veloce
        if '-USD' in ticker:
            hist = stock.history(period="1d", interval="5m")
            if not hist.empty:
                return float(hist['Close'].iloc[-1])
        
        # Per azioni/ETF - usa info prima
        try:
            info = stock.info
            price = info.get('currentPrice', info.get('regularMarketPrice', info.get('previousClose')))
            if price and price > 0:
                return float(price)
        except:
            pass
        
        # Fallback con history
        hist = stock.history(period="2d", interval="1h")
        if not hist.empty:
            return float(hist['Close'].iloc[-1])
            
        return None
    except Exception:
        return None

@st.cache_data(ttl=3600)
def get_asset_name_fast(ticker):
    names = {
        'AAPL': 'Apple Inc', 'MSFT': 'Microsoft Corp', 'GOOGL': 'Alphabet',
        'TSLA': 'Tesla Inc', 'NVDA': 'NVIDIA Corp', 'AMZN': 'Amazon',
        'IWDA.AS': 'iShares MSCI World', 'SWDA.L': 'iShares MSCI World',
        'VWCE.AS': 'Vanguard All-World', 'VWCE.L': 'Vanguard All-World',
        'CSPX.L': 'iShares S&P 500', 'VUSA': 'Vanguard S&P 500',
        'BTC-USD': 'Bitcoin', 'ETH-USD': 'Ethereum', 'SOL-USD': 'Solana',
        'BNB-USD': 'Binance Coin', 'XRP-USD': 'XRP', 'TAO-USD': 'Bittensor',
        'ENI.MI': 'ENI SpA', 'ISP.MI': 'Intesa Sanpaolo', 'UCG.MI': 'UniCredit'
    }
    return names.get(ticker, ticker)

# Header con controlli
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.markdown('<span class="live-indicator"></span>**💰 PORTFOLIO LIVE TRACKER**', unsafe_allow_html=True)

with col2:
    refresh_status = "🟢 ON" if st.session_state.auto_refresh else "🔴 OFF"
    if st.button(f"⚡ Auto-Refresh {refresh_status}", key="toggle_refresh"):
        st.session_state.auto_refresh = not st.session_state.auto_refresh
        if st.session_state.auto_refresh:
            st.session_state.refresh_counter = 0
        st.rerun()

with col3:
    st.metric("🔄 Refresh", f"#{st.session_state.refresh_counter}")

# Sidebar compatta
with st.sidebar:
    st.header("➕ Aggiungi Asset")
    
    # Examples
    with st.expander("💡 Esempi Ticker"):
        st.write("**USA:** AAPL, MSFT, GOOGL, TSLA")
        st.write("**ETF:** IWDA.AS, VWCE.AS, CSPX.L")
        st.write("**Crypto:** BTC-USD, ETH-USD, SOL-USD")
        st.write("**Italia:** ENI.MI, ISP.MI, UCG.MI")
    
    # Form compatto
    with st.form("add_asset_form", clear_on_submit=True):
        new_ticker = st.text_input("Ticker:", placeholder="es: IWDA.AS").upper().strip()
        
        col1, col2 = st.columns(2)
        with col1:
            new_quantity = st.number_input("Quantità", min_value=0.0001, step=0.1, format="%.4f")
        with col2:
            new_price = st.number_input("Prezzo €", min_value=0.01, step=0.01, format="%.2f")
        
        submitted = st.form_submit_button("🚀 AGGIUNGI", type="primary", use_container_width=True)
        
        if submitted and new_ticker and new_quantity > 0 and new_price > 0:
            # Test veloce del ticker
            with st.spinner(f"Verifico {new_ticker}..."):
                test_price = get_live_price_fast(new_ticker)
            
            if test_price and test_price > 0:
                new_row = pd.DataFrame({
                    'Ticker': [new_ticker],
                    'Quantità': [new_quantity],
                    'Prezzo_Acquisto': [new_price],
                    'Data_Acquisto': [datetime.now().date()]
                })
                st.session_state.portfolio = pd.concat([st.session_state.portfolio, new_row], ignore_index=True)
                st.success(f"✅ {new_ticker} aggiunto!")
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"❌ {new_ticker} non trovato")
    
    # Gestione portfolio esistente
    if not st.session_state.portfolio.empty:
        st.markdown("---")
        st.subheader("🗑️ Rimuovi Asset")
        
        ticker_to_remove = st.selectbox("Seleziona:", [""] + st.session_state.portfolio['Ticker'].tolist())
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Rimuovi", type="secondary"):
                if ticker_to_remove:
                    st.session_state.portfolio = st.session_state.portfolio[
                        st.session_state.portfolio['Ticker'] != ticker_to_remove
                    ].reset_index(drop=True)
                    st.success(f"Rimosso {ticker_to_remove}")
                    st.rerun()
        
        with col2:
            if st.button("🗑️ Reset", type="secondary"):
                st.session_state.portfolio = pd.DataFrame(columns=['Ticker', 'Quantità', 'Prezzo_Acquisto', 'Data_Acquisto'])
                st.session_state.last_prices = {}
                st.success("Portfolio resettato!")
                st.rerun()

# Main content
if st.session_state.portfolio.empty:
    st.info("👈 Aggiungi il tuo primo asset dalla sidebar!")
    
    st.markdown("### 💡 Ticker Popolari da Provare:")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.code("🇺🇸 Azioni USA\nAAPL\nMSFT\nGOOGL\nTSLA")
    with col2:
        st.code("🌍 ETF Globali\nIWDA.AS\nVWCE.AS\nCSPX.L")
    with col3:
        st.code("₿ Crypto\nBTC-USD\nETH-USD\nSOL-USD")
    
    st.stop()

# Contatore refresh visivo
if st.session_state.auto_refresh:
    countdown_placeholder = st.empty()
    with countdown_placeholder.container():
        st.markdown(f'<div class="refresh-counter">⚡ Prossimo refresh in 5s</div>', unsafe_allow_html=True)

# Container principale
main_placeholder = st.empty()

with main_placeholder.container():
    # Calcola dati portfolio
    portfolio_data = []
    total_value = 0
    total_invested = 0
    
    # Process each asset
    for _, row in st.session_state.portfolio.iterrows():
        ticker = row['Ticker']
        quantity = row['Quantità']
        purchase_price = row['Prezzo_Acquisto']
        
        current_price = get_live_price_fast(ticker)
        name = get_asset_name_fast(ticker)
        
        if current_price and current_price > 0:
            current_value = quantity * current_price
            invested_value = quantity * purchase_price
            gain_loss = current_value - invested_value
            gain_loss_pct = (gain_loss / invested_value) * 100
            
            total_value += current_value
            total_invested += invested_value
            
            # Determina trend
            trend_icon = "➡️"
            if ticker in st.session_state.last_prices:
                old_price = st.session_state.last_prices[ticker]
                if current_price > old_price * 1.001:  # Soglia 0.1%
                    trend_icon = "📈"
                elif current_price < old_price * 0.999:
                    trend_icon = "📉"
            
            st.session_state.last_prices[ticker] = current_price
            
            portfolio_data.append({
                'Ticker': ticker,
                'Nome': name,
                'Qty': quantity,
                'Prezzo_Acq': purchase_price,
                'Prezzo_Att': current_price,
                'Valore': current_value,
                'Investito': invested_value,
                'GL_Euro': gain_loss,
                'GL_Pct': gain_loss_pct,
                'Trend': trend_icon
            })
    
    if portfolio_data:
        total_gl = total_value - total_invested
        total_ret = (total_gl / total_invested) * 100 if total_invested > 0 else 0
        
        # Metriche principali
        st.markdown("## 📊 Dashboard Live")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("💰 Valore Totale", f"€{total_value:,.2f}", f"€{total_gl:,.2f}")
        with col2:
            st.metric("💸 Investito", f"€{total_invested:,.2f}")
        with col3:
            st.metric("📈 Return %", f"{total_ret:.2f}%")
        with col4:
            avg_return = sum([p['GL_Pct'] for p in portfolio_data]) / len(portfolio_data)
            st.metric("🎯 Asset", len(portfolio_data), f"Avg: {avg_return:.1f}%")
        
        # Tabella live
        st.markdown("### 📈 Posizioni Live")
        
        # Prepara dati tabella
        table_data = []
        for p in portfolio_data:
            weight = (p['Valore'] / total_value) * 100 if total_value > 0 else 0
            
            table_data.append({
                'Ticker': p['Ticker'],
                'Nome': p['Nome'][:20] + "..." if len(p['Nome']) > 20 else p['Nome'],
                'Qty': f"{p['Qty']:.4f}",
                'Acq €': f"{p['Prezzo_Acq']:.2f}",
                'Live €': f"{p['Prezzo_Att']:.4f} {p['Trend']}",
                'Valore €': f"{p['Valore']:,.0f}",
                'G/L €': f"{p['GL_Euro']:,.0f}",
                'G/L %': f"{p['GL_Pct']:.1f}%",
                'Peso %': f"{weight:.1f}%"
            })
        
        df_table = pd.DataFrame(table_data)
        
        # Styling per gain/loss
        def highlight_performance(val):
            if isinstance(val, str):
                if 'G/L' in str(val) and '-' in str(val):
                    return 'color: #ff4444; font-weight: bold'
                elif 'G/L' in str(val) and str(val) not in ['0', '0.0%', '€0']:
                    return 'color: #00C851; font-weight: bold'
            return ''
        
        styled_df = df_table.style.applymap(highlight_performance)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # Grafici
        if len(portfolio_data) > 1:
            st.markdown("### 📊 Analisi Grafiche")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Asset allocation pie chart
                fig_pie = px.pie(
                    values=[p['Valore'] for p in portfolio_data],
                    names=[p['Ticker'] for p in portfolio_data],
                    title="🥧 Asset Allocation"
                )
                fig_pie.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_pie, use_container_width=True, key=f"pie_{st.session_state.refresh_counter}")
            
            with col2:
                # Performance bar chart
                fig_bar = px.bar(
                    x=[p['Ticker'] for p in portfolio_data],
                    y=[p['GL_Pct'] for p in portfolio_data],
                    title="📊 Performance %",
                    color=[p['GL_Pct'] for p in portfolio_data],
                    color_continuous_scale=['red', 'yellow', 'green']
                )
                fig_bar.update_layout(showlegend=False)
                st.plotly_chart(fig_bar, use_container_width=True, key=f"bar_{st.session_state.refresh_counter}")
        
        # Best/Worst performers
        st.markdown("### 🏆 Performance Summary")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            best = max(portfolio_data, key=lambda x: x['GL_Pct'])
            st.success(f"🏆 Top: {best['Ticker']} (+{best['GL_Pct']:.1f}%)")
        
        with col2:
            worst = min(portfolio_data, key=lambda x: x['GL_Pct'])
            st.error(f"📉 Bottom: {worst['Ticker']} ({worst['GL_Pct']:.1f}%)")
        
        with col3:
            st.info(f"⚖️ Diversificazione: {len(portfolio_data)} asset")
    
    else:
        st.error("❌ Nessun prezzo valido trovato. Verifica i ticker inseriti.")

# Footer con timestamp
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    status_text = "🟢 LIVE" if st.session_state.auto_refresh else "🔴 PAUSED"
    st.markdown(f"**Status:** {status_text}")

with col2:
    st.markdown(f"**🕐 Aggiornato:** {datetime.now().strftime('%H:%M:%S')}")

with col3:
    next_refresh = "5s" if st.session_state.auto_refresh else "Manual"
    st.markdown(f"**⚡ Prossimo:** {next_refresh}")

# Auto-refresh mechanism
if st.session_state.auto_refresh:
    # Incrementa counter
    st.session_state.refresh_counter += 1
    
    # Countdown con sleep
    time.sleep(5)
    
    # Pulisci cache per forzare nuove chiamate API
    get_live_price_fast.clear()
    
    # Ricarica l'app
    st.rerun()
