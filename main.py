import time
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from mplfinance.original_flavor import candlestick_ohlc
from matplotlib.animation import FuncAnimation
from binance.client import Client
from binance.exceptions import BinanceAPIException
import os

# Initialisation de la connexion avec Binance
api_key = os.getenv("BINANCE_API_KEY")
api_secret = os.getenv("BINANCE_API_SECRET")
client = Client(api_key, api_secret)

# Paramètres de la stratégie et de simulation
symbol = 'BTCUSDT'
short_window = 5  # Moyenne mobile courte (5 périodes)
long_window = 20  # Moyenne mobile longue (20 périodes)
quantity = 0.001  # Quantité simulée de BTC à acheter/vendre
initial_balance = 100  # Solde initial en USDT

# Variables de simulation du portefeuille
balance = initial_balance
btc_balance = 0
last_trade_price = 0.0
entry_price = 0.0
in_position = False  # Indique si on est en position

# Historique pour le traçage
price_history = []
balance_history = []


def get_current_price(symbol):
    """ Récupère le prix actuel du symbole donné """
    try:
        ticker = client.get_symbol_ticker(symbol=symbol)
        return float(ticker['price'])
    except BinanceAPIException as e:
        print(f"Erreur d'API Binance : {e}")
        return None


def get_data(symbol, interval, lookback):
    """ Récupère les données de marché """
    klines = client.get_klines(symbol=symbol, interval=interval, limit=lookback)
    df = pd.DataFrame(klines, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume', 'close_time',
                                       'quote_asset_volume', 'number_of_trades', 'taker_buy_base_asset_volume',
                                       'taker_buy_quote_asset_volume', 'ignore'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['open'] = df['open'].astype(float)
    df['high'] = df['high'].astype(float)
    df['low'] = df['low'].astype(float)
    df['close'] = df['close'].astype(float)
    return df


def simulate_order(side, quantity):
    """ Simule l'exécution d'un ordre d'achat ou de vente """
    global balance, btc_balance, last_trade_price, entry_price, in_position

    current_price = get_current_price(symbol)
    if current_price is None:
        return  # Pas de mise à jour si l'API échoue

    if side == 'BUY' and not in_position:
        cost = current_price * quantity
        if balance >= cost:
            balance -= cost
            btc_balance += quantity
            entry_price = current_price
            in_position = True
            print(f"Achat simulé : {quantity} BTC à {entry_price} USDT")
        else:
            print("Solde insuffisant pour acheter.")

    elif side == 'SELL' and in_position:
        revenue = current_price * quantity
        balance += revenue
        btc_balance -= quantity
        pnl = (current_price - entry_price) * quantity
        in_position = False
        print(f"Vente simulée : {quantity} BTC à {current_price} USDT")
        print(f"PNL du trade : {pnl:.2f} USDT")
    else:
        print("Aucune action effectuée.")


def moving_average_strategy():
    """ Implémente une stratégie de moyenne mobile simple """
    global in_position

    df = get_data(symbol, Client.KLINE_INTERVAL_1MINUTE, long_window)
    df['MA_short'] = df['close'].rolling(window=short_window).mean()
    df['MA_long'] = df['close'].rolling(window=long_window).mean()

    ma_short = df['MA_short'].iloc[-1]
    ma_long = df['MA_long'].iloc[-1]
    current_price = df['close'].iloc[-1]

    if ma_short > ma_long and not in_position:
        simulate_order('BUY', quantity)
    elif ma_short < ma_long and in_position:
        simulate_order('SELL', quantity)

    price_history.append(current_price)
    balance_history.append(balance + btc_balance * current_price)

    print(f"Prix actuel: {current_price} USDT")
    print(f"Solde USDT: {balance}, Solde BTC: {btc_balance}")
    print(f"Valeur totale du portefeuille: {balance + btc_balance * current_price} USDT")


def update_graph(i):
    """ Met à jour l'interface graphique avec le prix et le portefeuille """
    df = get_data(symbol, Client.KLINE_INTERVAL_1MINUTE, long_window)
    moving_average_strategy()

    # Données pour le graphique en chandelier
    # Make sure to copy the DataFrame before modifying it
    ohlc = df[['timestamp', 'open', 'high', 'low', 'close']].copy()  # Use .copy() to create a new DataFrame
    ohlc['timestamp'] = ohlc['timestamp'].apply(mdates.date2num)  # Apply the transformation to the 'timestamp' column

    ax1.cla()  # Efface l'axe des chandeliers
    ax2.cla()  # Efface l'axe du portefeuille

    # Graphique en chandelier pour le prix de BTCUSDT
    ax1.set_title(f'Graphique BTC/USDT (Chandelier)')
    candlestick_ohlc(ax1, ohlc.values, width=0.0004, colorup='green', colordown='red')
    ax1.xaxis_date()
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax1.set_ylabel("Prix (USDT)")

    # Graphique de l'évolution du portefeuille
    ax2.plot(balance_history, label='Valeur du Portefeuille (USDT)', color='blue')
    ax2.set_title("Évolution du Portefeuille")
    ax2.set_xlabel("Temps")
    ax2.set_ylabel("Valeur (USDT)")
    ax2.legend()
'''

# Configuration de la visualisation
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
ani = FuncAnimation(fig, update_graph, interval=60000)  # Mise à jour toutes les 60 secondes

print("Démarrage de la stratégie de trading...")
plt.show()
'''
