import streamlit as st
import yfinance as yf
import pandas as pd
import time
from datetime import datetime
import plotly.express as px
import requests

# Configurazione pagina
st.set_page_config(
    page_title="💰 Portfolio Real-Time",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS per styling e animazioni
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1f4e79, #4472c4);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .gain {
        color: #00ff88 !important;
        font-weight: bold;
        text-shadow: 0 0 5px rgba(0, 255, 136, 0.3);
    }
    .loss {
        color: #ff4444 !important;
        font-weight: bold;
        text-shadow: 0 0 5px rgba(255, 68, 68, 0.3);
    }
    .live-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        background-color: #00ff00;
        border-radius: 50%;
        animation: pulse 2s infinite;
        margin-right: 8px;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.3; }
        100% { opacity: 1; }
    }
    .stDataFrame {
        font-size: 14px;
    }
    .big-number {
        font-size: 2em;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Inizializza session state
if 'portfolio' not in st.session_state:
    st.session_state.portfolio = pd.DataFrame(columns=['Ticker', 'Quantità', 'Prezzo_Acquisto', 'Data_Acquisto'])
if 'auto_refresh' not in st.session_state:
    st.session_state.auto_refresh = True
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()

# Funzione super veloce per prezzi
@st.cache_data(ttl=3, show_spinner=False)  # Cache solo 3 secondi
def get_live_price(ticker):
    try:
        # Prima prova con yfinance (più veloce)
        stock = yf.Ticker(ticker)
        
        # Per crypto, usa un approccio diverso
        if '-USD' in ticker:
            try:
                # API più veloce per crypto
                crypto_symbol = ticker.replace('-USD', '').lower()
                url = f"https://api.binance.com/api/v3/ticker/price?symbol={crypto_symbol.upper()}USDT"
                response = requests.get(url, timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    return float(data['price'])
            except:
                pass
        
        # Metodo standard
        hist = stock.history(period="1d", interval="1m")
        if not hist.empty:
            return round(hist['Close'].iloc[-1], 4)
        
        # Fallback
        info = stock.info
        price = info.get('currentPrice', info.get('regularMarketPrice'))
        return round(price, 4) if price else None
        
    except Exception as e:
        return None

@st.cache_data(ttl=1800, show_spinner=False)  # Cache 30 minuti per nomi
def get_asset_name(ticker):
    try:
        if '-USD' in ticker:
            crypto_names = {
                'BTC-USD': 'Bitcoin',
                'ETH-USD': 'Ethereum', 
                'SOL-USD': 'Solana',
                'BNB-USD': 'Binance Coin',
                'XRP-USD': 'XRP',
                'TAO-USD': 'Bittensor',
                'ADA-USD': 'Cardano',
                'DOT-USD': 'Polkadot',
                'LINK-USD': 'Chainlink'
            }
            return crypto_names.get(ticker, ticker.replace('-USD', ''))
        
        stock = yf.Ticker(ticker)
        info = stock.info
        name = info.get('longName', info.get('shortName', ticker))
        return name[:25] + "..." if len(name) > 25 else name
    except:
        return ticker

# Header con indicatore live
col1, col2 = st.columns([3, 1])
with col1:
    st.markdown('<span class="live-indicator"></span>**💰 PORTFOLIO REAL-TIME**', unsafe_allow_html=True)
with col2:
    if st.button("🔄 Toggle Auto-Refresh"):
        st.session_state.auto_refresh = not st.session_state.auto_refresh

# Sidebar per aggiungere asset
with st.sidebar:
    st.header("➕ Aggiungi Asset")
    
    # Esempi ticker
    with st.expander("💡 Ticker Popolari", expanded=False):
        st.write("**🇺🇸 Azioni USA:** AAPL, MSFT, GOOGL, TSLA, NVDA")
        st.write("**🌍 ETF:** IWDA.AS, VWCE.AS, CSPX.L, VUSA")  
        st.write("**₿ Crypto:** BTC-USD, ETH-USD, SOL-USD, XRP-USD, TAO-USD")
        st.write("**🇮🇹 Azioni IT:** ENI.MI, ISP.MI, UCG.MI")
    
    with st.form("add_asset", clear_on_submit=True):
        new_ticker = st.text_input("Ticker", placeholder="es: IWDA.AS, BTC-USD, AAPL").upper().strip()
        new_quantity = st.number_input("Quantità", min_value=0.0001, step=0.1, format="%.4f")
        new_price = st.number_input("Prezzo Acquisto €", min_value=0.01, step=0.01, format="%.2f")
        new_date = st.date_input("Data Acquisto", value=datetime.now().date())
        
        submitted = st.form_submit_button("🚀 AGGIUNGI", type="primary", use_container_width=True)
        
        if submitted and new_ticker and new_quantity > 0 and new_price > 0:
            with st.spinner(f'Verifico {new_ticker}...'):
                test_price = get_live_price(new_ticker)
            
            if test_price:
                new_row = pd.DataFrame({
                    'Ticker': [new_ticker],
                    'Quantità': [new_quantity], 
                    'Prezzo_Acquisto': [new_price],
                    'Data_Acquisto': [new_date]
                })
                st.session_state.portfolio = pd.concat([st.session_state.portfolio, new_row], ignore_index=True)
                st.success(f"✅ {new_ticker} aggiunto!")
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"❌ {new_ticker} non trovato!")
    
    st.markdown("---")
    
    # Gestione portfolio
    if not st.session_state.portfolio.empty:
        st.subheader("🗑️ Rimuovi Asset")
        ticker_to_remove = st.selectbox("Seleziona ticker da rimuovere:", 
                                       st.session_state.portfolio['Ticker'].tolist())
        if st.button("❌ Rimuovi", type="secondary"):
            st.session_state.portfolio = st.session_state.portfolio[
                st.session_state.portfolio['Ticker'] != ticker_to_remove
            ].reset_index(drop=True)
            st.success(f"🗑️ {ticker_to_remove} rimosso!")
            st.rerun()
    
    if st.button("🗑️ Cancella Tutto", type="secondary"):
        st.session_state.portfolio = pd.DataFrame(columns=['Ticker', 'Quantità', 'Prezzo_Acquisto', 'Data_Acquisto'])
        st.rerun()

# Main content
if st.session_state.portfolio.empty:
    st.info("👆 Aggiungi il tuo primo asset dalla barra laterale!")
    st.stop()

# Container principale che si aggiorna
main_container = st.container()

with main_container:
    # Calcola dati portfolio in tempo reale
    portfolio_data = []
    total_value = 0
    total_invested = 0
    
    # Progress bar per il caricamento
    progress_bar = st.progress(0)
    
    for idx, row in st.session_state.portfolio.iterrows():
        progress_bar.progress((idx + 1) / len(st.session_state.portfolio))
        
        ticker = row['Ticker']
        quantity = row['Quantità']
        purchase_price = row['Prezzo_Acquisto']
        purchase_date = row['Data_Acquisto']
        
        current_price = get_live_price(ticker)
        name = get_asset_name(ticker)
        
        if current_price and current_price > 0:
            current_value = quantity * current_price
            invested_value = quantity * purchase_price
            gain_loss = current_value - invested_value
            gain_loss_pct = (gain_loss / invested_value) * 100
            
            total_value += current_value
            total_invested += invested_value
            
            portfolio_data.append({
                'Ticker': ticker,
                'Nome': name,
                'Quantità': quantity,
                'Prezzo_Acquisto': purchase_price,
                'Prezzo_Attuale': current_price,
                'Valore_Totale': current_value,
                'Gain_Loss_Euro': gain_loss,
                'Gain_Loss_Pct': gain_loss_pct,
                'Data': purchase_date
            })
    
    progress_bar.empty()
    
    if portfolio_data:
        total_gain_loss = total_value - total_invested
        total_return = (total_gain_loss / total_invested) * 100 if total_invested > 0 else 0
        
        # Dashboard Metriche - Layout migliorato
        st.markdown("### 📊 Dashboard Real-Time")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "💰 Valore Totale", 
                f"€{total_value:.2f}",
                delta=f"€{total_gain_loss:.2f}"
            )
        
        with col2:
            st.metric(
                "💸 Capitale Investito", 
                f"€{total_invested:.2f}"
            )
        
        with col3:
            delta_color = "normal" if total_return >= 0 else "inverse"
            st.metric(
                "📈 Rendimento %", 
                f"{total_return:.1f}%",
                delta=f"€{total_gain_loss:.2f}"
            )
        
        with col4:
            avg_return = sum([item['Gain_Loss_Pct'] for item in portfolio_data]) / len(portfolio_data)
            st.metric(
                "🎯 Posizioni", 
                len(portfolio_data),
                delta=f"Avg: {avg_return:.1f}%"
            )
        
        # Tabella portfolio con styling avanzato  
        st.markdown("### 📈 Portfolio Dettagli")
        
        # Crea DataFrame per display
        display_data = []
        for item in portfolio_data:
            gain_loss_formatted = f"€{item['Gain_Loss_Euro']:.2f}"
            pct_formatted = f"{item['Gain_Loss_Pct']:.1f}%"
            weight = (item['Valore_Totale'] / total_value) * 100
            
            display_data.append({
                'Ticker': item['Ticker'],
                'Nome': item['Nome'],
                'Qty': f"{item['Quantità']:.4f}",
                'Prezzo Acq.': f"€{item['Prezzo_Acquisto']:.2f}",
                'Prezzo Att.': f"€{item['Prezzo_Attuale']:.4f}",
                'Valore Tot.': f"€{item['Valore_Totale']:.2f}",
                'G/L €': gain_loss_formatted,
                'G/L %': pct_formatted,
                'Peso %': f"{weight:.1f}%",
                'Data': item['Data'].strftime("%d/%m/%y") if hasattr(item['Data'], 'strftime') else str(item['Data'])[:10]
            })
        
        df = pd.DataFrame(display_data)
        
        # Styling condizionale
        def highlight_gains_losses(val):
            if 'G/L' in str(val) or '€' in str(val) and ('G/L' in str(val)):
                if '-' in str(val):
                    return 'color: #ff4444; font-weight: bold'
                elif str(val) != '€0.00' and str(val) != '0.0%':
                    return 'color: #00ff88; font-weight: bold'
            return ''
        
        styled_df = df.style.applymap(highlight_gains_losses)
        st.dataframe(styled_df, use_container_width=True, hide_index=True)
        
        # Grafico distribuzione
        col1, col2 = st.columns(2)
        
        with col1:
            if len(portfolio_data) > 1:
                st.markdown("#### 🥧 Asset Allocation")
                chart_df = pd.DataFrame([
                    {'Asset': item['Ticker'], 'Valore': item['Valore_Totale']} 
                    for item in portfolio_data
                ])
                fig = px.pie(chart_df, values='Valore', names='Asset',
                           color_discrete_sequence=px.colors.qualitative.Set3)
                fig.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig, use_container_width=True, key="pie_chart")
        
        with col2:
            st.markdown("#### 📊 Performance")
            perf_df = pd.DataFrame([
                {'Asset': item['Ticker'], 'Performance %': item['Gain_Loss_Pct']} 
                for item in portfolio_data
            ])
            fig_bar = px.bar(perf_df, x='Asset', y='Performance %',
                           color='Performance %',
                           color_continuous_scale=['red', 'yellow', 'green'])
            st.plotly_chart(fig_bar, use_container_width=True, key="bar_chart")
    
    # Footer con timestamp e auto-refresh
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status = "🟢 LIVE" if st.session_state.auto_refresh else "🔴 PAUSED"
        st.markdown(f"**Status:** {status}")
    
    with col2:
        st.markdown(f"**🕐 Aggiornato:** {datetime.now().strftime('%H:%M:%S')}")
    
    with col3:
        st.markdown(f"**⚡ Refresh:** {3 if st.session_state.auto_refresh else 0}s")

# Auto-refresh mechanism
if st.session_state.auto_refresh:
    time.sleep(3)  # Attendi 3 secondi
    st.rerun()  # Ricarica l'app