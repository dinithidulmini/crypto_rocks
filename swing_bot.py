import time
from binance.client import Client
import threading
from tradingview_ta import TA_Handler, Interval, Exchange
import pandas as pd
import numpy as np
import statistics
from binance import enums
from binance.client import Client
import threading
from tradingview_ta import TA_Handler, Interval, Exchange
from numerize import numerize
from discord import SyncWebhook
from datetime import datetime
import psycopg2
from emoji import emojize

#establishing the connection
conn = psycopg2.connect(
   database="gpu", user='postgres', password='postgres', host='127.0.0.1', port= '5432')

# Creating a cursor object using the cursor() method
cursor = conn.cursor()

# Executing an MYSQL function using the execute() method
cursor.execute("select version()")

# Fetch a single row using fetchone() method.
data = cursor.fetchone()

client = Client()

blue_circle = emojize(":blue_circle:")
red_circle = emojize(":red_circle:")
fire = emojize(":fire:")

exchange_info = client.futures_exchange_info()
symbol_details = exchange_info["symbols"]
# print(symbol_details)

list_of_all_futures_symbols = []
for symbol in symbol_details:
    if symbol["contractType"] == "PERPETUAL" and symbol["quoteAsset"] == "USDT" and symbol["status"] == "TRADING":
        pair_name = symbol["symbol"]
        list_of_all_futures_symbols.append(pair_name)

def check_rsi(symbol,type):
    while True:
        symbol_tv = f"{symbol}PERP"
        sol_handler = TA_Handler(symbol=symbol_tv, screener="Crypto", exchange="Binance",
                                 interval=Interval.INTERVAL_4_HOURS)
        sol_indicators = sol_handler.get_indicators()
        rsi_tv = float(sol_indicators["RSI"])
        # print(f"RSI from api = {rsi_tv}")

        if type == "LONG" and rsi_tv >= 30:
            current_price = float(client.futures_symbol_ticker(symbol=symbol)["price"])
            circle = blue_circle
            discord_message = f"\n=====================\n{circle} {type} : {symbol} {circle}\n=====================\n\nEntry Price: ${round(current_price, 2)}\n\nTP1 (2%): {round((current_price*1.02), 2)} \nTP2 (10%): {round((current_price*1.1), 2)}\nTP3 (20%): {round((current_price*1.2), 2)}\n\nSL: LAST SWING LOW"
            # print(discord_message)
            webhook = SyncWebhook.from_url(
                "https://discord.com/api/webhooks/1045410061960364132/rW-QCqn_qCkZKUsLVfvhCe5nUbI_D9YCPVXUDCTGn-LnNtvbXtsLyD23_fgzvz6W6cbu")
            webhook.send(discord_message)
            break
        if type == "SHORT" and rsi_tv <= 70:
            current_price = float(client.futures_symbol_ticker(symbol=symbol)["price"])
            circle = red_circle
            discord_message = f"\n=====================\n{circle} {type} : {symbol} {circle}\n=====================\n\nEntry Price: ${round(current_price, 2)}\n\nTP1 (2%): {round((current_price * 0.98), 2)} \nTP2 (10%): {round((current_price * 0.9), 2)}\nTP3 (20%): {round((current_price * 0.8), 2)}\n\nSL: LAST SWING HIGH"
            # print(discord_message)
            webhook = SyncWebhook.from_url(
                "https://discord.com/api/webhooks/1045410061960364132/rW-QCqn_qCkZKUsLVfvhCe5nUbI_D9YCPVXUDCTGn-LnNtvbXtsLyD23_fgzvz6W6cbu")
            webhook.send(discord_message)
            break

def start_bot(symbol):
    print("Starting...")

    while True:
        time.sleep(4)
        try:
            current_price = float(client.futures_symbol_ticker(symbol=symbol)["price"])

            if symbol == "BTCUSDT":
                print("checked BTC................")

            symbol_tv = f"{symbol}PERP"
            sol_handler = TA_Handler(symbol=symbol_tv, screener="Crypto", exchange="Binance",
                                     interval=Interval.INTERVAL_4_HOURS)
            sol_indicators = sol_handler.get_indicators()

            rsi_tv = float(sol_indicators["RSI"])
            # print(f"RSI from api = {rsi_tv}")

            klines_4h = client.futures_klines(symbol=symbol, interval="4h", limit=30)
            open_price_4h = float(klines_4h[-1][1])
            close_price_4h = float(klines_4h[-1][4])

            sum = 0
            averages = []
            for line in klines_4h:
                close_price = float(line[4])
                sum += close_price
                averages.append(close_price)
            # print(sum)
            # print(f"sum = {sum}")
            average = sum / 30
            # print(f"average = {average}")
            std_dev = statistics.stdev(averages)
            # print(f"std_dev = {std_dev}")

            upper_bb = average + (std_dev * 2)
            # print(f"My upper = {upper_bb}")

            lower_bb = average - (std_dev * 2)
            # print(f"My lower = {lower_bb}")

            if close_price_4h >= open_price_4h:
                if open_price_4h < lower_bb and rsi_tv < 30:
                    check_rsi(symbol=symbol,type="LONG")
            if close_price_4h < open_price_4h:
                if open_price_4h > upper_bb and rsi_tv > 70:
                    check_rsi(symbol=symbol,type="SHORT")

        except Exception as e:
            print(e)

for symbol in list_of_all_futures_symbols:
    start_bot(symbol=symbol)

start_bot()







