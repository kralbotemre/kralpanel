import streamlit as st
import pandas as pd
import pandas_ta as ta
import requests
import time
from datetime import datetime, timedelta

coins = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "ADAUSDT", "DOGEUSDT", "TONUSDT", "AVAXUSDT", "TRXUSDT",
    "SHIBUSDT", "LINKUSDT", "DOTUSDT", "MATICUSDT", "LTCUSDT", "BCHUSDT", "ICPUSDT", "FILUSDT", "UNIUSDT", "PEPEUSDT",
    "WBTCUSDT", "ETCUSDT", "RNDRUSDT", "ARBUSDT", "OPUSDT", "STXUSDT", "SUIUSDT", "XLMUSDT", "INJUSDT", "MKRUSDT", "IMXUSDT",
    "APTUSDT", "TAOUSDT", "GRTUSDT", "NEARUSDT", "SEIUSDT", "TIAUSDT", "QNTUSDT", "AAVEUSDT", "JUPUSDT", "FLOWUSDT"
]

st.set_page_config(page_title="Kripto Kralı Otomatik Panel", page_icon="🦁", layout="centered")
st.title("🦁 Kripto Kralı Otomatik Sinyal Paneli")

selected_coin = st.selectbox("Coin seç:", coins)

def get_binance_klines(symbol, interval, limit=150):
    url = f"https://fapi.binance.com/fapi/v1/klines?symbol={symbol}&interval={interval}&limit={limit}"
    data = requests.get(url).json()
    df = pd.DataFrame(data, columns=[
        'time','open','high','low','close','volume','cclose','quote_vol',
        'trades','taker_buy_base','taker_buy_quote','ignore'
    ])
    # Tüm fiyat verilerini float'a çevir
    for col in ['open', 'high', 'low', 'close', 'volume']:
        df[col] = df[col].astype(float)
    return df

def signal_1h(df):
    rsi = ta.rsi(df['close'], length=14)
    stoch = ta.stoch(df['high'], df['low'], df['close'])
    volume = df['volume'].rolling(10).mean()
    qqe = ta.qqe(df['close'])
    last_rsi = rsi.iloc[-1]
    last_stoch = stoch['STOCHk_14_3_3'].iloc[-1]
    last_qqe = qqe['QQE_14_5.0'].iloc[-1] if 'QQE_14_5.0' in qqe else 50
    shorts = 0
    longs = 0
    if last_rsi < 45: shorts += 1
    elif last_rsi > 60: longs += 1
    if last_stoch < 30: shorts += 1
    elif last_stoch > 70: longs += 1
    if volume.iloc[-1] < volume.iloc[-10]: shorts += 1
    else: longs += 1
    if last_qqe < 50: shorts += 1
    elif last_qqe > 60: longs += 1
    if shorts >= 2: return "Short ağırlık, satış baskısı.", "short"
    elif longs >= 2: return "Long yönü güçlü, alış momentumu.", "long"
    else: return "Yön belirsiz, izlemekte fayda var.", "nötr"

def signal_2h(df):
    ema = ta.ema(df['close'], length=20)
    supertrend = ta.supertrend(df['high'], df['low'], df['close'])
    chop = ta.chop(df['high'], df['low'], df['close'])
    shorts = 0
    longs = 0
    if df['close'].iloc[-1] < ema.iloc[-1]: shorts += 1
    else: longs += 1
    if 'SUPERT_7_3.0' in supertrend and supertrend['SUPERT_7_3.0'].iloc[-1] < df['close'].iloc[-1]: longs += 1
    else: shorts += 1
    if chop.iloc[-1] < 38: shorts += 1
    elif chop.iloc[-1] > 62: longs += 1
    if shorts >= 2: return "Short taraf baskın, satış momentumu var.", "short"
    elif longs >= 2: return "Long yönünde güçlenme var.", "long"
    else: return "Yön belirsiz, izlemekte fayda var.", "nötr"

def signal_4h(df):
    macd = ta.macd(df['close'])
    bb = ta.bbands(df['close'])
    ttm = ta.squeeze(df['high'], df['low'], df['close'])
    shorts = 0
    longs = 0

    # BB column adlarını güvenli çek
    bb_low_col = [c for c in bb.columns if "BBL" in c][0]
    bb_up_col = [c for c in bb.columns if "BBU" in c][0]

    if 'MACDh_12_26_9' in macd and macd['MACDh_12_26_9'].iloc[-1] < 0: shorts += 1
    elif 'MACDh_12_26_9' in macd and macd['MACDh_12_26_9'].iloc[-1] > 0: longs += 1
    if df['close'].iloc[-1] < bb[bb_low_col].iloc[-1]: shorts += 1
    elif df['close'].iloc[-1] > bb[bb_up_col].iloc[-1]: longs += 1
    if 'SQZ_20_2.0_20_1.5' in ttm and ttm['SQZ_20_2.0_20_1.5'].iloc[-1] < 0: shorts += 1
    elif 'SQZ_20_2.0_20_1.5' in ttm and ttm['SQZ_20_2.0_20_1.5'].iloc[-1] > 0: longs += 1
    if shorts >= 2: return "Short sinyali, dikkatli ol.", "short"
    elif longs >= 2: return "Long sinyali güçleniyor.", "long"
    else: return "Yön belirsiz, beklemek mantıklı.", "nötr"

# Panelde sinyalleri göster
st.subheader(f"{selected_coin} 1 Saatlik Analiz")
df1h = get_binance_klines(selected_coin, "1h")
msg1h, sig1h = signal_1h(df1h)
st.info(msg1h)

st.subheader(f"{selected_coin} 2 Saatlik Analiz")
df2h = get_binance_klines(selected_coin, "2h")
msg2h, sig2h = signal_2h(df2h)
st.info(msg2h)

st.subheader(f"{selected_coin} 4 Saatlik Analiz")
df4h = get_binance_klines(selected_coin, "4h")
msg4h, sig4h = signal_4h(df4h)
st.info(msg4h)

st.write("---")
st.subheader("🔥 3 Zaman Diliminde de Aynı Sinyali Veren Coinler")

# Sinyal izleme için session_state'te bir sözlük başlatıyoruz
if "sinyal_log" not in st.session_state:
    st.session_state["sinyal_log"] = {}

def add_signal_log(coin, sinyal, fiyat):
    now = datetime.now()
    log = st.session_state["sinyal_log"].get(coin, {"son_sinyal": None, "loglar": []})

    # Sinyal değişmişse ya da loglar boşsa, sıfırla
    if log["son_sinyal"] != sinyal or len(log["loglar"]) == 0:
        log = {"son_sinyal": sinyal, "loglar": [(now, fiyat)]}
    else:
        # En son kaydın zamanı
        son_zaman, _ = log["loglar"][-1]
        fark = now - son_zaman
        toplam_sure = now - log["loglar"][0][0]

        # Sinyal gelmeye başlayalı 2 saatten azsa, 15dkda bir ekle
        if toplam_sure < timedelta(hours=2) and fark >= timedelta(minutes=15):
            log["loglar"].append((now, fiyat))
        # 2 saatten fazlaysa, 30dkda bir ekle
        elif toplam_sure >= timedelta(hours=2) and fark >= timedelta(minutes=30):
            log["loglar"].append((now, fiyat))
        # Aksi halde ekleme (çok sık olmasın)
        else:
            pass

    st.session_state["sinyal_log"][coin] = log

if st.button("Taramayı Başlat (Full Senkron Sinyal)"):
    long_list = []
    short_list = []
    fiyatlar = {}
    prog = st.progress(0, text="Tarama başlatılıyor...")

    for idx, coin in enumerate(coins):
        try:
            df1 = get_binance_klines(coin, "1h")
            _, sig1 = signal_1h(df1)
            df2 = get_binance_klines(coin, "2h")
            _, sig2 = signal_2h(df2)
            df4 = get_binance_klines(coin, "4h")
            _, sig4 = signal_4h(df4)

            son_fiyat = df1['close'].iloc[-1]  # en güncel fiyat

            if sig1 == "long" and sig2 == "long" and sig4 == "long":
                long_list.append((coin, son_fiyat))
                add_signal_log(coin, "long", son_fiyat)
            elif sig1 == "short" and sig2 == "short" and sig4 == "short":
                short_list.append((coin, son_fiyat))
                add_signal_log(coin, "short", son_fiyat)
            else:
                # Sinyal değişirse logu sıfırla
                if coin in st.session_state["sinyal_log"]:
                    del st.session_state["sinyal_log"][coin]

        except Exception as e:
            continue
        prog.progress((idx+1)/len(coins), text=f"Taranıyor: {coin}")

    prog.empty()
    st.success("Tarama tamamlandı!")

    col1, col2 = st.columns(2)
    def yazdir(liste, tip):
        if liste:
            for coin, fiyat in liste:
                log = st.session_state["sinyal_log"].get(coin, None)
                if log:
                    saatler = []
                    for t, f in log["loglar"]:
                        saatler.append(f"{t.strftime('%H:%M')} - {f:.2f}$")
                    # Sadece ilk ve son kaydı göster, araya ... ekle
                    if len(saatler) > 3:
                        saat_str = saatler[0] + " ... " + saatler[-1]
                    else:
                        saat_str = " / ".join(saatler)
                    st.markdown(f"- **{coin}** <span style='font-size:12px;'>({tip.upper()} - {fiyat:.2f}$) &nbsp; <i>{saat_str}</i></span>", unsafe_allow_html=True)
                else:
                    st.markdown(f"- **{coin}** <span style='font-size:12px;'>({tip.upper()} - {fiyat:.2f}$)</span>", unsafe_allow_html=True)
        else:
            st.write("Yok.")

    with col1:
        st.markdown("🟢 **3 Periyotta da LONG Verenler:**")
        yazdir(long_list, "long")
    with col2:
        st.markdown("🔴 **3 Periyotta da SHORT Verenler:**")
        yazdir(short_list, "short")
